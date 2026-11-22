// ---------- patch492 : le motif de territoire (Boutique › Atelier › Mon territoire) ----------
// Un motif = jusqu'à 8 calques (formes, lignes, trames, lettres) qui se répètent par-dessus la couleur du joueur.
// Le serveur vérifie tout (s3-46) ; ici : le chargement, le dessin sur la carte et l'éditeur.
const MOT_MAX = 8, MOT_MAX_LETTRES = 3, MOT_BROUILLON = 'tf-motif-brouillon';
const MOT_VIS_DEBUT = 3, MOT_VIS_PLEIN = 8;   // en pixels par kilomètre : en dessous le motif est caché, au-dessus il est entier
const MOT_PACKS = { heraldique: 'Formes Héraldique', nature: 'Formes Nature', cartographe: 'Formes Cartographe', tissus: 'Trames Tissus' };
const MOT_CATS = ['Formes', 'Lignes', 'Symboles', 'Héraldique', 'Nature', 'Cartographe', 'Lettres'];
const MOT_COULEURS = ['#FFFFFF', '#E8E2D4', '#FFE08A', '#F0B429', '#FF8A3D', '#F0505A', '#9E2B45', '#E85DA8', '#A06CFF', '#7FD4FF', '#3D8BFF', '#2456C8', '#2EC4C4', '#3FCF8E', '#2F7D55', '#0B1424'];
const motLum = (h) => { const n = parseInt(String(h).slice(1), 16), r = (n >> 16) / 255, g = (n >> 8 & 255) / 255, b = (n & 255) / 255; return .2126 * r + .7152 * g + .0722 * b; };
const motType = (c) => c.forme === 'lettre' ? 'forme' : (MTF.FORME[c.forme] || {}).type || 'forme';
const motCopie = (o) => JSON.parse(JSON.stringify(o));
const motL = (forme, couleur, x, y, t, o = {}) => ({ forme, couleur, x, y, t, r: o.r || 0, a: o.a == null ? 1 : o.a, fx: !!o.fx, fy: !!o.fy, lettre: o.lettre || null, e: o.e || 'aucun' });
const motModele = (calques, o = {}) => ({ densite: o.densite || 42, intensite: o.intensite || 80, quinconce: !!o.quinconce, calques });
const MOT_MODELES = [
  ['Constellation', motModele([motL('etoile5', '#FFE08A', 30, 32, 34, { a: .95, e: 'ombre' }), motL('etincelle', '#FFFFFF', 74, 70, 30, { a: .9 }),
    motL('etoile5', '#FFFFFF', 80, 18, 13, { a: .7 }), motL('cercle', '#FFFFFF', 18, 80, 6, { a: .8 })], { densite: 58, intensite: 88 })],
  ['Vichy', motModele([motL('bande', '#FFFFFF', 50, 25, 250, { a: .45 }), motL('bande', '#FFFFFF', 25, 50, 250, { r: 90, a: .45 })], { densite: 26, intensite: 92 })],
  ['Marinière', motModele([motL('bande', '#FFFFFF', 50, 25, 70, { a: .9 }), motL('bande', '#FFFFFF', 50, 75, 70, { a: .9 })], { densite: 40, intensite: 92 })],
  ['Écossais', motModele([motL('bande', '#0B1424', 50, 50, 180, { a: .5 }), motL('bande', '#0B1424', 50, 50, 180, { r: 90, a: .5 }),
    motL('bandefine', '#3FCF8E', 50, 50, 110, { a: .75 }), motL('bandefine', '#3FCF8E', 50, 50, 110, { r: 90, a: .75 }),
    motL('bandefine', '#FFE08A', 50, 6, 70, { a: .65 }), motL('bandefine', '#FFE08A', 6, 50, 70, { r: 90, a: .65 })], { densite: 46, intensite: 92 })],
  ['Art déco', motModele([motL('ecaille', '#F0B429', 50, 40, 100, { a: .95 }), motL('ecaille', '#F0B429', 50, 51.5, 52, { a: .95 }), motL('cercle', '#F0B429', 50, 60, 9, { a: .95 })], { quinconce: true, densite: 40, intensite: 90 })],
  ['Grecque', motModele([motL('grecque', '#E8E2D4', 50, 50, 100, { a: .85 })], { densite: 46, intensite: 90 })],
  ['Argyle', motModele([motL('losanges', '#0B1424', 50, 50, 100, { a: .35 }), motL('croisillons', '#FFE08A', 50, 50, 100, { a: .7 })], { densite: 44, intensite: 90 })],
  ['Pois', motModele([motL('cercle', '#FFFFFF', 50, 50, 34, { a: .85 })], { quinconce: true, densite: 30, intensite: 85 })],
  ['Fleurs de lys', motModele([motL('lys', '#FFE08A', 50, 50, 62, { a: .95, e: 'relief' })], { quinconce: true, densite: 46, intensite: 88 })],
  ['Hermine', motModele([motL('hermine', '#0B1424', 50, 50, 58, { a: .92 })], { quinconce: true, densite: 42, intensite: 88 })],
  ['Forêt', motModele([motL('sapin', '#E8E2D4', 50, 50, 60, { a: .6, e: 'relief' })], { quinconce: true, densite: 38, intensite: 85 })],
  ['Cartographe', motModele([motL('courbes', '#0B1424', 50, 50, 98, { a: .45 }), motL('epingle', '#FFFFFF', 50, 47, 30, { a: .95, e: 'ombre' })], { densite: 64, intensite: 85 })],
  ['Pied-de-poule', motModele([motL('piedpoule', '#0B1424', 50, 50, 100, { a: .9 })], { densite: 26, intensite: 85 })],
];

/* ---------- chargement ---------- */
async function motifsCharger(){
  try{
    const { data, error } = await sb.rpc('motifs_territoire');
    if(error){ if(fonctionAbsente(error)) MTF.ouvert = false; return; }
    MTF.ouvert = true;
    MOTIFS.clear();
    for(const r of data || []) if(r && r.motif && Array.isArray(r.motif.calques) && r.motif.calques.length) MOTIFS.set(r.joueur_id, r.motif);
    MTF.moi = window.__monId ? (MOTIFS.get(window.__monId) || null) : null;
    MTF.pats.clear();
    if(MOTIFS.size) motFormesCharger().then(() => { try{ demanderDessin(); }catch(e){} }).catch(() => {});
    try{ if(typeof rendreCalques === 'function') rendreCalques(); }catch(e){}
  }catch(e){}
}
function motFormesCharger(){
  if(!MTF.formesP) MTF.formesP = fetch('motifs-formes.json?v=' + VERSION_JEU).then(r => { if(!r.ok) throw new Error('formes'); return r.json(); }).then(l => {
    for(const f of l){ f.p = new Path2D(f.d); MTF.FORME[f.id] = f; }
    MTF.formes = l; return l;
  }).catch(e => { MTF.formesP = null; throw e; });
  return MTF.formesP;
}
async function motMoiCharger(){
  try{
    const { data, error } = await sb.rpc('mon_motif');
    if(error){ if(fonctionAbsente(error)) MTF.ouvert = false; return false; }
    if(!data) return false;
    MTF.ouvert = data.ouvert !== false; MTF.lu = true;
    MTF.moi = data.motif && Array.isArray(data.motif.calques) && data.motif.calques.length ? data.motif : null;
    MTF.packs = data.packs || []; MTF.bloque = data.bloque_jusqu || null;
    MTF.modo = !!data.moderateur; MTF.signalements = Number(data.signalements) || 0;
    if(window.__monId){ if(MTF.moi) MOTIFS.set(window.__monId, MTF.moi); else MOTIFS.delete(window.__monId); }
    if(MTF.modo && MTF.signalements){ const r = await sb.rpc('motifs_signales'); MTF.signales = r.error ? [] : (r.data || []); } else MTF.signales = [];
    return true;
  }catch(e){ return false; }
}
function motMaCouleur(){ return maCouleurChoisie || (window.__monId ? couleurAuto(window.__monId) : '#5EB1EF'); }
function motPossede(f){ return !f || !f.pack || MTF.packs.includes(f.pack); }
function motPacksManquants(m){ return [...new Set((m.calques || []).map(c => MTF.FORME[c.forme]).filter(f => f && !motPossede(f)).map(f => f.pack))]; }
function motPackArticle(pack){ return (bqeAcces && bqeCat && (bqeCat.articles || []).find(x => x.id === 'motifs-' + pack)) || null; }
function motPrixPack(pack){ const a = motPackArticle(pack); return a ? euros(bqePrixMoi(a)) : 'bientôt en vente'; }

/* ---------- dessin d'un calque et de la tuile ---------- */
function motDessinerForme(ctx, c, S, dx, dy, couleur, contour){
  const k = S / 100, type = motType(c), sx = c.fx ? -1 : 1, sy = c.fy ? -1 : 1;
  let ex, ey;
  ctx.save();
  ctx.translate((c.x + dx) * k, (c.y + dy) * k);
  if(type === 'forme'){ ctx.rotate(c.r * Math.PI / 180); ex = sx * c.t / 100 * k; ey = sy * c.t / 100 * k; }
  else if(type === 'ligne'){ ctx.rotate(c.r === 90 ? Math.PI / 2 : 0); ex = sx * k; ey = sy * c.t / 100 * k; }
  else { ctx.rotate(c.r === 90 ? Math.PI / 2 : 0); ex = sx * k; ey = sy * k; }
  ctx.scale(ex, ey);
  ctx.translate(-50, -50);
  ctx.fillStyle = couleur;
  const f = MTF.FORME[c.forme];
  const lettre = c.forme === 'lettre';
  if(lettre){ ctx.font = '900 92px "Big Shoulders Display", Impact, sans-serif'; ctx.textAlign = 'center'; ctx.textBaseline = 'middle'; }
  if(contour){
    ctx.strokeStyle = contour; ctx.lineJoin = 'round'; ctx.lineWidth = 2 * 2.4 * k / Math.sqrt(Math.abs(ex * ey));
    if(lettre) ctx.strokeText(c.lettre || 'A', 50, 54); else if(f) ctx.stroke(f.p);
  }
  if(lettre) ctx.fillText(c.lettre || 'A', 50, 54); else if(f) ctx.fill(f.p);
  ctx.restore();
}
function motDessinerCalque(ctx, c, S){   // S = taille de la tuile en px
  const a0 = ctx.globalAlpha, a = c.a == null ? 1 : c.a;
  ctx.globalAlpha = a0 * a;
  if(c.e === 'ombre'){ ctx.globalAlpha = a0 * a * .45; motDessinerForme(ctx, c, S, 1.6, 2.2, '#000'); ctx.globalAlpha = a0 * a; }
  if(c.e === 'relief'){
    ctx.globalAlpha = a0 * a * .5; motDessinerForme(ctx, c, S, 1, 1.4, '#000');
    ctx.globalAlpha = a0 * a * .45; motDessinerForme(ctx, c, S, -.7, -.9, '#FFF');
    ctx.globalAlpha = a0 * a;
  }
  motDessinerForme(ctx, c, S, 0, 0, c.couleur, c.e === 'contour' ? (motLum(c.couleur) > .55 ? '#0B1424' : '#FFFFFF') : null);
  ctx.globalAlpha = a0;
}
function motDessinerTuile(ctx, S, m){
  ctx.clearRect(0, 0, S, S);
  ctx.save(); ctx.beginPath(); ctx.rect(0, 0, S, S); ctx.clip();
  for(const c of m.calques || []) for(const dx of [-1, 0, 1]) for(const dy of [-1, 0, 1]){
    ctx.save(); ctx.translate(dx * S, dy * S); motDessinerCalque(ctx, c, S); ctx.restore();
  }
  ctx.restore();
}
// la tuile qui se répète (deux rangées si quinconce)
function motTuile(m, px){
  const t = document.createElement('canvas'); t.width = px; t.height = px; motDessinerTuile(t.getContext('2d'), px, m);
  if(!m.quinconce) return t;
  const q = document.createElement('canvas'); q.width = px; q.height = px * 2; const g = q.getContext('2d');
  g.drawImage(t, 0, 0); g.drawImage(t, px / 2, px); g.drawImage(t, -px / 2, px);
  return q;
}
// une bande d'aperçu : la couleur du joueur, le motif par-dessus, à sa taille réelle
function motBande(cnv, m, couleur){
  const d = window.devicePixelRatio || 1, r = cnv.getBoundingClientRect();
  cnv.width = Math.max(2, Math.round((r.width || 300) * d)); cnv.height = Math.max(2, Math.round((r.height || 60) * d));
  const g = cnv.getContext('2d');
  g.fillStyle = couleur; g.fillRect(0, 0, cnv.width, cnv.height);
  if(!m || !MTF.formes || !(m.calques || []).length) return;
  const pat = g.createPattern(motTuile(m, Math.max(8, Math.round((m.densite || 42) * d))), 'repeat');
  g.globalAlpha = (m.intensite || 80) / 100; g.fillStyle = pat; g.fillRect(0, 0, cnv.width, cnv.height); g.globalAlpha = 1;
}

/* ---------- sur la carte du jeu ---------- */
function motVisibilite(){
  if(!mapBounds) return 0;
  const pxKm = MAP_H * echelleCarte() * mapZoom / ((mapBounds.latMax - mapBounds.latMin) * 111.19);
  return Math.max(0, Math.min(1, (pxKm - MOT_VIS_DEBUT) / (MOT_VIS_PLEIN - MOT_VIS_DEBUT)));
}
function motPeindre(ctx, id, chemin, k){
  if(CALQUES.motifs === false || !MTF.formes) return;
  const m = id === ID_MOI ? MTF.moi : MOTIFS.get(id);
  if(!m) return;
  const vis = motVisibilite();
  if(vis <= 0) return;
  const px = Math.max(8, Math.round((m.densite || 42) * CV.dpr));
  let e = MTF.pats.get(id);
  if(!e || e.m !== m || e.px !== px){ e = { m, px, pat: ctx.createPattern(motTuile(m, px), 'repeat') }; MTF.pats.set(id, e); }
  if(!e.pat) return;
  if(e.pat.setTransform) e.pat.setTransform(new DOMMatrix().scale(1 / k));   // la tuile garde sa taille à l'écran
  ctx.globalAlpha = opaciteJoueur(id, vis * (m.intensite || 80) / 100);
  ctx.fillStyle = e.pat; ctx.fill(chemin);
  ctx.globalAlpha = 1;
}

/* ---------- Boutique › Atelier › Mon territoire ---------- */
function motBlocAtelier(){
  if(MTF.ouvert === false) return `<div class="atb-bloc"><p class="atb-note" style="margin:0">Bientôt ici : <b>ton motif de territoire</b>, à composer toi-même (formes, lignes, symboles, couleurs).</p></div>`;
  const jusqu = MTF.bloque ? new Date(MTF.bloque).toLocaleDateString('fr-FR', { weekday: 'long', day: 'numeric', month: 'long' }) : null;
  const sig = MTF.modo && (MTF.signales || []).length ? `<div class="atb-bloc mot-modo"><div class="atb-h">Modération <small>${MTF.signales.length} motif${MTF.signales.length > 1 ? 's' : ''} signalé${MTF.signales.length > 1 ? 's' : ''}</small></div>
      ${MTF.signales.map((s, i) => `<div class="mot-sig"><canvas class="mot-bande" data-mot-sig="${i}"></canvas>
        <div><b>${echapperTexte(s.pseudo || 'Joueur')}</b><small>${Number(s.nb) || 1} signalement${Number(s.nb) > 1 ? 's' : ''}</small></div>
        <button type="button" class="mot-mini" data-mot-modo="classer" data-j="${echapperTexte(s.joueur_id)}">Laisser</button>
        <button type="button" class="mot-mini rouge" data-mot-modo="retirer" data-j="${echapperTexte(s.joueur_id)}">Retirer</button></div>`).join('')}
      <p class="atb-note">Retirer efface le motif et empêche le joueur d'en refaire un pendant 3 jours.</p></div>` : '';
  return `<div class="atb-bloc mot-atb">
      <div class="atb-h">Mon motif <small>${MTF.moi ? 'en place' : 'aucun pour l’instant'}</small></div>
      <canvas class="mot-bande" data-mot-bande="moi"></canvas>
      <p class="atb-note">Un dessin à toi, qui se répète sur ton territoire par-dessus ta couleur. Tous les joueurs le voient en zoomant sur la carte. De loin, il s'efface.</p>
      ${jusqu ? `<p class="atb-note mot-alerte">Ton motif a été retiré par la modération. Tu pourras en refaire un à partir de ${echapperTexte(jusqu)}.</p>`
              : `<button type="button" class="atb-btn" data-mot="ouvrir">${MTF.moi ? 'Modifier mon motif' : 'Composer mon motif'}</button>`}
    </div>${sig}`;
}
function motApresRendu(racine){
  const dessiner = () => {
    const b = racine.querySelector('[data-mot-bande="moi"]');
    if(b) motBande(b, MTF.moi, motMaCouleur());
    racine.querySelectorAll('[data-mot-sig]').forEach(c => { const s = (MTF.signales || [])[+c.dataset.motSig]; if(s) motBande(c, s.motif, s.couleur || couleurAuto(s.joueur_id)); });
  };
  dessiner();
  if(!MTF.formes && MTF.ouvert !== false) motFormesCharger().then(dessiner).catch(() => {});
  if(!MTF.lu && !MTF.lecture){ MTF.lecture = motMoiCharger().then(ok => { MTF.lecture = null; if(ok && atbVue === 'territoire') atbRendre(); }); }
}
async function motClicAtelier(e){
  if(e.target.closest('[data-mot="ouvrir"]')){ motOuvrir(); return true; }
  const m = e.target.closest('[data-mot-modo]');
  if(m){
    m.disabled = true;
    const { error } = await sb.rpc('motif_moderer', { p_joueur: m.dataset.j, p_retirer: m.dataset.motModo === 'retirer' });
    if(error) notifier({ type: 'erreur', titre: 'Modération', texte: messageLisible(error.message) });
    else notifier({ type: 'succes', titre: m.dataset.motModo === 'retirer' ? 'Motif retiré' : 'Signalement classé', texte: '' });
    await motMoiCharger(); await motifsCharger(); atbRendre();
    return true;
  }
  return false;
}

/* ---------- la fiche d'un joueur : son motif, et le signaler ---------- */
function motProfilHtml(p){
  if(!p || p.est_moi || !MOTIFS.has(p.id)) return '';
  return `<canvas class="mot-bande pr-motif" data-mot-profil="${echapperTexte(p.id)}" aria-label="Son motif de territoire"></canvas>`;
}
function motProfilSignalerHtml(p){
  if(!p || p.est_moi || !MOTIFS.has(p.id)) return '';
  return `<button type="button" class="pr-bloquer" data-mot-signaler="${echapperTexte(p.id)}">Signaler son motif de territoire</button>`;
}
function motProfilApres(){
  const c = document.querySelector('#fenetre [data-mot-profil]');
  if(!c) return;
  const id = c.dataset.motProfil, go = () => { if(c.isConnected) motBande(c, MOTIFS.get(id), colorForPlayer(id)); };
  if(MTF.formes) go(); else motFormesCharger().then(go).catch(() => {});
}
document.getElementById('fenetre').addEventListener('click', async (e) => {
  const b = e.target.closest('[data-mot-signaler]');
  if(!b) return;
  if(!b.classList.contains('confirmer')){ b.classList.add('confirmer'); b.textContent = 'Toucher encore pour signaler ce motif'; return; }
  b.disabled = true;
  const { data, error } = await sb.rpc('motif_signaler', { p_joueur: b.dataset.motSignaler });
  if(error){ notifier({ type: 'erreur', titre: 'Signalement', texte: messageLisible(error.message) }); b.disabled = false; return; }
  b.textContent = data && data.deja ? 'Déjà signalé' : 'Motif signalé, merci';
});

/* ---------- la boutique : un pack de formes ---------- */
function motApercuPack(a){
  const pack = String(a.id).replace(/^motifs-/, '');
  const fs = (MTF.formes || []).filter(f => f.pack === pack);
  return `<div class="mot-pack-apercu">${fs.map(f => `<figure><svg viewBox="0 0 100 100" aria-hidden="true"><path d="${f.d}"/></svg><figcaption>${echapperTexte(f.nom)}</figcaption></figure>`).join('')
    || '<p>Des formes en plus pour ton motif de territoire.</p>'}</div>`;
}
async function motAcheterPack(pack){
  try{ await bqeVerifierAcces(); }catch(e){}
  try{ await motFormesCharger(); }catch(e){}
  const a = motPackArticle(pack);
  if(!a){ notifier({ type: 'info', titre: 'Indisponible', texte: 'Ce pack n’est pas en vente pour le moment.' }); return; }
  motGarder();
  bqeOuvrirFiche(a.id, 'motif');
}
async function motRetourAchat(){
  await motMoiCharger();
  const t = document.querySelector('.tab[data-tab="atelierbq"]');
  if(t) t.click();
  atbVue = 'territoire'; atbRendre();
  motOuvrir();
}

/* ---------- l'éditeur ---------- */
const ME = { M: null, sel: 0, cat: 'Formes', cible: null, vue: { cx: -2, cy: 6, z: 12 }, carte: null, ptrs: new Map(), tire: null, raf: 0, autres: null, envoi: false };
const motEl = (id) => document.getElementById(id);
function motGarder(){ try{ if(ME.M) localStorage.setItem(MOT_BROUILLON, JSON.stringify(ME.M)); }catch(e){} }
function motNet(o){
  const m = { densite: Math.max(18, Math.min(90, Number(o.densite) || 42)), intensite: Math.max(15, Math.min(100, Number(o.intensite) || 80)), quinconce: !!o.quinconce,
    calques: (o.calques || []).slice(0, MOT_MAX).filter(c => c && (c.forme === 'lettre' || MTF.FORME[c.forme])).map(c => ({ ...motL(c.forme, c.couleur || '#FFFFFF', Number(c.x) || 0, Number(c.y) || 0, Number(c.t) || 50, c) })) };
  return m;
}
function motDepart(){
  try{ const s = localStorage.getItem(MOT_BROUILLON); if(s){ const o = JSON.parse(s); if(o && Array.isArray(o.calques)) return motNet(o); } }catch(e){}
  if(MTF.moi) return motNet(motCopie(MTF.moi));
  return motCopie(MOT_MODELES[0][1]);
}
async function motOuvrir(){
  if(ME.ouverture) return;
  ME.ouverture = true;
  try{
    await motFormesCharger();
    if(!ME.carte) ME.carte = await fetch('motifs-apercu.json?v=' + VERSION_JEU).then(r => r.json()).then(l => l.map(([nom, x, y, d, o]) => ({ nom, x, y, o, p: new Path2D(d) }))).catch(() => []);
    if(!MTF.lu) await motMoiCharger();
    if(bqeAcces === null) try{ await bqeVerifierAcces(); }catch(x){}   // les packs en vente, et leur prix
  }catch(e){ ME.ouverture = false; notifier({ type: 'erreur', titre: 'Mon motif', texte: 'L’éditeur ne s’est pas chargé. Réessaie dans un instant.' }); return; }
  ME.ouverture = false;
  if(MTF.bloque){ notifier({ type: 'info', titre: 'Mon motif', texte: 'Ton motif a été retiré par la modération pour quelques jours.' }); return; }
  ME.M = motDepart(); ME.sel = 0; ME.cat = 'Formes';
  const voisin = (i, fond) => ({ fond, m: motCopie(MOT_MODELES[i][1]) });
  ME.autres = { r: voisin(1, '#E5484D'), v: voisin(10, '#12A594'), o: voisin(5, '#F76B15'), p: voisin(0, '#8E7CF6'), c: { fond: '#2EC4B6', m: null } };
  let ec = motEl('motEcran');
  if(!ec){
    ec = document.createElement('div'); ec.id = 'motEcran'; ec.className = 'mot-ecran';
    ec.setAttribute('role', 'dialog'); ec.setAttribute('aria-modal', 'true'); ec.setAttribute('aria-label', 'Mon motif de territoire');
    document.body.appendChild(ec);
  }
  ec.innerHTML = `
    <div class="mot-tete"><button type="button" class="mot-retour" data-mot-e="fermer" aria-label="Fermer">‹</button><h2>Mon motif</h2>
      <button type="button" class="mot-pt" data-mot-e="modeles">Modèles</button><button type="button" class="mot-pt" data-mot-e="hasard" aria-label="Au hasard">🎲</button></div>
    <div class="mot-corps">
      <div class="mot-carte"><canvas id="motCv"></canvas>
        <div class="mot-zoom"><button type="button" data-mot-e="zplus" aria-label="Zoomer">+</button><button type="button" data-mot-e="zmoins" aria-label="Dézoomer">−</button></div>
        <div class="mot-leg" id="motLeg"></div></div>
      <div class="mot-edit">
        <div class="mot-tuile"><canvas id="motTc"></canvas><div class="mot-aide">Glisse pour déplacer le calque</div></div>
        <div class="mot-calques"><h3>Calques <span id="motNbc"></span></h3><div class="mot-liste" id="motListe"></div></div>
      </div>
      <div class="mot-bloc" id="motBlocCalque"></div>
      <div class="mot-bloc">
        <h3>Sur mon territoire</h3>
        <div class="mot-ligne"><label for="motDensite">Taille du motif</label><input type="range" id="motDensite" min="18" max="90" step="1"><output id="motODensite"></output></div>
        <div class="mot-ligne"><label for="motIntensite">Intensité</label><input type="range" id="motIntensite" min="15" max="100" step="1"><output id="motOIntensite"></output></div>
        <div class="mot-bascule"><span>Rangées décalées (en quinconce)</span><button type="button" class="mot-sw" id="motQuinconce" role="switch" aria-label="Rangées décalées"></button></div>
        <p class="mot-note">Le fond, c'est <b>ta couleur</b> (elle se change dans « Ma couleur sur la carte »). ${meVoirDore() ? 'Sur ta propre carte tu te vois en doré : ton motif s’y pose sur le doré. ' : ''}De loin, le motif s'efface pour que les raretés, les clans et les bâtiments restent lisibles.</p>
      </div>
    </div>
    <div class="mot-pied"><button type="button" class="mot-sec" data-mot-e="retirer">Retirer mon motif</button><button type="button" class="mot-ok" data-mot-e="enregistrer">Enregistrer</button></div>
    <div class="mot-voile" id="motVFormes" hidden><div class="mot-feuille">
      <div class="mot-t"><h2>Choisir une forme</h2><button type="button" class="mot-x" data-mot-ferme="motVFormes" aria-label="Fermer">×</button></div>
      <div class="mot-cats" id="motCats"></div><p class="mot-pack" id="motPack"></p><div id="motGrille"></div></div></div>
    <div class="mot-voile" id="motVModeles" hidden><div class="mot-feuille">
      <div class="mot-t"><h2>Partir d'un modèle</h2><button type="button" class="mot-x" data-mot-ferme="motVModeles" aria-label="Fermer">×</button></div>
      <div class="mot-modeles" id="motModeles"></div><p class="mot-note">Chaque modèle se modifie ensuite calque par calque. Il s'affiche ici sur ta couleur.</p></div></div>
    <div class="mot-voile" id="motVPacks" hidden><div class="mot-feuille">
      <div class="mot-t"><h2>Formes d'un pack</h2><button type="button" class="mot-x" data-mot-ferme="motVPacks" aria-label="Fermer">×</button></div>
      <div id="motPacksCorps"></div></div></div>`;
  ec.hidden = false;
  document.documentElement.classList.add('mot-ouvert');
  motBrancher(ec);
  requestAnimationFrame(() => { ec.classList.add('visible'); motRedim(); });
  (document.fonts && document.fonts.ready ? document.fonts.ready : Promise.resolve()).then(() => { if(!ec.hidden) motRedim(); });
}
function motFermer(){
  const ec = motEl('motEcran');
  if(!ec || ec.hidden) return;
  ec.classList.remove('visible'); ec.hidden = true; ec.innerHTML = '';
  document.documentElement.classList.remove('mot-ouvert');
  window.removeEventListener('resize', motRedim);
  document.removeEventListener('keydown', motTouche);
  ME.ptrs.clear(); ME.tire = null;
}
function motTouche(e){
  if(e.key !== 'Escape') return;
  const f = document.getElementById('fenetre');
  if(f && !f.hidden) return;
  const v = document.querySelector('#motEcran .mot-voile:not([hidden])');
  if(v){ v.hidden = true; return; }
  motFermer();
}
function motBrancher(ec){
  window.addEventListener('resize', motRedim);
  document.addEventListener('keydown', motTouche);
  ec.onclick = (e) => {
    const f = e.target.closest('[data-mot-ferme]');
    if(f){ motEl(f.dataset.motFerme).hidden = true; return; }
    if(e.target.classList.contains('mot-voile')){ e.target.hidden = true; return; }
    const b = e.target.closest('[data-mot-e]');
    if(!b) return;
    const a = b.dataset.motE;
    if(a === 'fermer') motFermer();
    else if(a === 'modeles') motModelesOuvrir();
    else if(a === 'hasard') motHasard();
    else if(a === 'zplus'){ ME.vue.z = Math.min(40, ME.vue.z * 1.35); motCarteBientot(); }
    else if(a === 'zmoins'){ ME.vue.z = Math.max(2, ME.vue.z / 1.35); motCarteBientot(); }
    else if(a === 'enregistrer') motEnregistrer(false);
    else if(a === 'retirer') motRetirer(b);
  };
  // la carte d'aperçu : déplacer et zoomer
  const cv = motEl('motCv'), ptrs = ME.ptrs;
  cv.addEventListener('pointerdown', (e) => { try{ cv.setPointerCapture(e.pointerId); }catch(x){} ptrs.set(e.pointerId, { x: e.clientX, y: e.clientY }); });
  cv.addEventListener('pointermove', (e) => {
    if(!ptrs.has(e.pointerId)) return;
    const a = ptrs.get(e.pointerId);
    if(ptrs.size === 1){ ME.vue.cx -= (e.clientX - a.x) / ME.vue.z; ME.vue.cy -= (e.clientY - a.y) / ME.vue.z; }
    else if(ptrs.size === 2){
      const [p, q] = [...ptrs.values()], d0 = Math.hypot(p.x - q.x, p.y - q.y);
      ptrs.set(e.pointerId, { x: e.clientX, y: e.clientY });
      const [p2, q2] = [...ptrs.values()], d1 = Math.hypot(p2.x - q2.x, p2.y - q2.y);
      ME.vue.z = Math.max(2, Math.min(40, ME.vue.z * d1 / Math.max(1, d0)));
    }
    ptrs.set(e.pointerId, { x: e.clientX, y: e.clientY }); motCarteBientot();
  });
  ['pointerup', 'pointercancel'].forEach(t => cv.addEventListener(t, (e) => ptrs.delete(e.pointerId)));
  cv.addEventListener('wheel', (e) => { e.preventDefault(); ME.vue.z = Math.max(2, Math.min(40, ME.vue.z * Math.exp(-e.deltaY * .0015))); motCarteBientot(); }, { passive: false });
  // la tuile : glisser le calque choisi
  const tc = motEl('motTc');
  tc.addEventListener('pointerdown', (e) => {
    const c = ME.M.calques[ME.sel]; if(!c) return;
    try{ tc.setPointerCapture(e.pointerId); }catch(x){} ME.tire = { x: e.clientX, y: e.clientY, cx: c.x, cy: c.y };
  });
  tc.addEventListener('pointermove', (e) => {
    const c = ME.M.calques[ME.sel]; if(!ME.tire || !c) return;
    const r = tc.getBoundingClientRect(), k = 100 / (r.width / 2);
    c.x = Math.round(((ME.tire.cx + (e.clientX - ME.tire.x) * k) % 100 + 100) % 100);
    c.y = Math.round(((ME.tire.cy + (e.clientY - ME.tire.y) * k) % 100 + 100) % 100);
    motTout(false);
    const sx = motEl('motSX'), sy = motEl('motSY');
    if(sx){ sx.value = c.x; sx.nextElementSibling.textContent = c.x; } if(sy){ sy.value = c.y; sy.nextElementSibling.textContent = c.y; }
  });
  ['pointerup', 'pointercancel'].forEach(t => tc.addEventListener(t, () => { if(ME.tire){ ME.tire = null; motGarder(); motRendreCalques(); } }));
  motEl('motDensite').oninput = () => { ME.M.densite = +motEl('motDensite').value; motEl('motODensite').textContent = ME.M.densite; motTout(false); };
  motEl('motIntensite').oninput = () => { ME.M.intensite = +motEl('motIntensite').value; motEl('motOIntensite').textContent = ME.M.intensite + ' %'; motTout(false); };
  ['motDensite', 'motIntensite'].forEach(id => motEl(id).onchange = motGarder);
  motEl('motQuinconce').onclick = () => { ME.M.quinconce = !ME.M.quinconce; motGarder(); motTout(true); };
}
function motRedim(){
  const cv = motEl('motCv'), tc = motEl('motTc');
  if(!cv || !tc) return;
  const d = window.devicePixelRatio || 1;
  let r = cv.getBoundingClientRect(); cv.width = Math.max(2, Math.round(r.width * d)); cv.height = Math.max(2, Math.round(r.height * d));
  r = tc.getBoundingClientRect(); tc.width = Math.max(2, Math.round(r.width * d)); tc.height = Math.max(2, Math.round(r.height * d));
  motTout(true);
}
function motTout(complet){
  motDessinerGrandeTuile(); motCarteBientot();
  if(complet){ motRendreCalques(); motRendreBloc(); motRendreTerritoire(); }
}
function motCarteBientot(){ if(!ME.raf) ME.raf = requestAnimationFrame(() => { ME.raf = 0; motDessinerCarte(); }); }
function motDessinerCarte(){
  const cv = motEl('motCv'); if(!cv) return;
  const cx = cv.getContext('2d'), d = window.devicePixelRatio || 1, W = cv.width, H = cv.height, z = ME.vue.z, M = ME.M, fondMoi = motMaCouleur();
  cx.setTransform(1, 0, 0, 1, 0, 0); cx.fillStyle = '#0E1A2E'; cx.fillRect(0, 0, W, H);
  cx.setTransform(z * d, 0, 0, z * d, W / 2 - ME.vue.cx * z * d, H / 2 - ME.vue.cy * z * d);
  const vis = Math.max(0, Math.min(1, (z - MOT_VIS_DEBUT) / (MOT_VIS_PLEIN - MOT_VIS_DEBUT)));
  const pat = (m) => { const p = cx.createPattern(motTuile(m, Math.max(8, Math.round(m.densite * d))), 'repeat'); p.setTransform(new DOMMatrix().scale(1 / (z * d))); return p; };
  const pats = { moi: vis > 0 && M.calques.length ? pat(M) : null };
  for(const k in ME.autres) pats[k] = vis > 0 && ME.autres[k].m ? pat(ME.autres[k].m) : null;
  for(const c of ME.carte || []){
    const fond = c.o === 'moi' ? fondMoi : c.o ? ME.autres[c.o].fond : null;
    cx.fillStyle = fond || 'rgba(22,48,79,.75)'; cx.globalAlpha = fond ? .9 : 1; cx.fill(c.p); cx.globalAlpha = 1;
    const p = pats[c.o];
    if(p){ cx.globalAlpha = vis * (c.o === 'moi' ? M.intensite : ME.autres[c.o].m.intensite) / 100; cx.fillStyle = p; cx.fill(c.p); cx.globalAlpha = 1; }
  }
  cx.lineWidth = 0.6 / z; cx.strokeStyle = 'rgba(11,20,36,.85)';
  for(const c of ME.carte || []) cx.stroke(c.p);
  cx.lineWidth = 1.6 / z; cx.strokeStyle = 'rgba(255,255,255,.6)';
  for(const c of ME.carte || []) if(c.o === 'moi') cx.stroke(c.p);
  cx.setTransform(1, 0, 0, 1, 0, 0);
  const leg = motEl('motLeg');
  if(leg) leg.innerHTML = vis === 0 ? '<b>Vue de loin</b> : le motif est caché, seule ta couleur compte.'
    : vis < 1 ? '<b>À mi-distance</b> : le motif apparaît doucement.' : '<b>De près</b> : ton motif (bordé de blanc) au milieu d’autres joueurs.';
}
function motDessinerGrandeTuile(){
  const tc = motEl('motTc'); if(!tc) return;
  const tx = tc.getContext('2d'), W = tc.width, S = W / 2, M = ME.M, fond = motMaCouleur();
  tx.setTransform(1, 0, 0, 1, 0, 0); tx.globalAlpha = 1; tx.fillStyle = fond; tx.fillRect(0, 0, W, W);
  const t = motTuile(M, Math.max(2, Math.round(S)));
  tx.globalAlpha = .45;
  const h = M.quinconce ? S * 2 : S;
  for(let y = -h; y < W + h; y += h) for(let x = -S; x < W + S; x += S) tx.drawImage(t, W / 4 + x, W / 4 + y);
  tx.globalAlpha = 1;
  tx.save(); tx.beginPath(); tx.rect(W / 4, W / 4, S, S); tx.clip(); tx.fillStyle = fond; tx.fillRect(W / 4, W / 4, S, S);
  tx.globalAlpha = M.intensite / 100; tx.drawImage(t, W / 4, W / 4); tx.restore();
  tx.globalAlpha = 1; tx.strokeStyle = 'rgba(255,255,255,.7)'; tx.setLineDash([4, 4]); tx.lineWidth = 1.5; tx.strokeRect(W / 4 + .5, W / 4 + .5, S - 1, S - 1); tx.setLineDash([]);
  const c = M.calques[ME.sel];
  if(c){ const k = S / 100; tx.strokeStyle = '#F0B429'; tx.lineWidth = 2; tx.beginPath(); tx.arc(W / 4 + c.x * k, W / 4 + c.y * k, motType(c) === 'forme' ? Math.max(6, c.t * k / 2) : 10, 0, Math.PI * 2); tx.stroke(); }
}
function motVignette(cnv, fn){ const d = window.devicePixelRatio || 1, r = cnv.getBoundingClientRect(); const s = Math.max(2, Math.round((r.width || 40) * d)); cnv.width = s; cnv.height = s; fn(cnv.getContext('2d'), s); }
function motVignetteCalque(g, s, c, fond){
  g.fillStyle = fond || '#0E1A2E'; g.fillRect(0, 0, s, s);
  const ty = motType(c), cc = { ...c, x: 50, y: 50, t: ty === 'forme' ? 84 : ty === 'ligne' ? 100 : c.t, a: 1, e: 'aucun' };
  if(ty === 'plein'){ g.save(); g.scale(.5, .5); for(const dx of [0, 1]) for(const dy of [0, 1]){ g.save(); g.translate(dx * s, dy * s); motDessinerCalque(g, cc, s); g.restore(); } g.restore(); }
  else motDessinerCalque(g, cc, s);
}
function motNomCalque(c){ return c.forme === 'lettre' ? 'Lettre ' + (c.lettre || 'A') : (MTF.FORME[c.forme] || {}).nom || c.forme; }
function motNbLettres(){ return ME.M.calques.filter(c => c.forme === 'lettre').length; }
function motRendreCalques(){
  const M = ME.M, l = motEl('motListe'); if(!l) return;
  motEl('motNbc').textContent = `${M.calques.length}/${MOT_MAX}`;
  l.innerHTML = M.calques.map((c, i) => `<button type="button" class="mot-cq${i === ME.sel ? ' on' : ''}" data-i="${i}"><canvas></canvas><span>${echapperTexte(motNomCalque(c))}</span>${!motPossede(MTF.FORME[c.forme]) ? '<i>Pack</i>' : ''}</button>`).join('')
    + `<button type="button" class="mot-ajout" id="motAjout" ${M.calques.length >= MOT_MAX ? 'disabled' : ''}>+ Ajouter un calque</button>`;
  l.querySelectorAll('.mot-cq').forEach(b => { const i = +b.dataset.i; motVignette(b.querySelector('canvas'), (g, s) => motVignetteCalque(g, s, M.calques[i], motMaCouleur())); b.onclick = () => { ME.sel = i; motTout(true); }; });
  motEl('motAjout').onclick = () => motOuvrirFormes(null);
}
function motRendreBloc(){
  const M = ME.M, c = M.calques[ME.sel], b = motEl('motBlocCalque'); if(!b) return;
  if(!c){ b.innerHTML = '<h3>Calque</h3><p class="mot-note">Aucun calque : ajoute une forme pour commencer, ou pars d\'un modèle.</p>'; return; }
  const f = MTF.FORME[c.forme], ty = motType(c);
  const seg = (id, opts, val) => `<div class="mot-seg" id="${id}">${opts.map(([v, t]) => `<button type="button" data-v="${v}" class="${String(v) === String(val) ? 'on' : ''}">${t}</button>`).join('')}</div>`;
  b.innerHTML = `<h3>Calque ${ME.sel + 1}</h3>
    <button type="button" class="mot-forme-btn" id="motBForme"><canvas></canvas><span>${echapperTexte(motNomCalque(c))}</span><small>${f && f.pack ? (motPossede(f) ? 'À toi' : MOT_PACKS[f.pack] + ' · ' + motPrixPack(f.pack)) : 'Changer ›'}</small></button>
    <div class="mot-couleurs" id="motCoulCalque">${MOT_COULEURS.map(x => `<button type="button" style="background:${x}" data-c="${x}" class="${x === c.couleur ? 'on' : ''}" aria-label="Couleur ${x}"></button>`).join('')}</div>
    ${ty === 'forme' ? `<div class="mot-ligne"><label>Taille</label><input type="range" id="motST" min="6" max="150" value="${c.t}"><output>${c.t}</output></div>
      <div class="mot-ligne"><label>Rotation</label><input type="range" id="motSR" min="0" max="355" step="5" value="${c.r}"><output>${c.r}°</output></div>`
    : `${ty === 'ligne' ? `<div class="mot-ligne"><label>Épaisseur</label><input type="range" id="motST" min="20" max="260" step="5" value="${c.t}"><output>${c.t} %</output></div>` : ''}
      <div class="mot-ligne"><label>Sens</label>${seg('motSSens', ty === 'ligne' ? [[0, 'Horizontal'], [90, 'Vertical']] : [[0, 'Normal'], [90, 'Tourné']], c.r === 90 ? 90 : 0)}</div>`}
    <div class="mot-ligne"><label>Opacité</label><input type="range" id="motSA" min="10" max="100" value="${Math.round(c.a * 100)}"><output>${Math.round(c.a * 100)} %</output></div>
    <div class="mot-ligne"><label>${ty === 'forme' ? 'Position X' : 'Décalage X'}</label><input type="range" id="motSX" min="0" max="100" value="${c.x}"><output>${c.x}</output></div>
    <div class="mot-ligne"><label>${ty === 'forme' ? 'Position Y' : 'Décalage Y'}</label><input type="range" id="motSY" min="0" max="100" value="${c.y}"><output>${c.y}</output></div>
    <div class="mot-ligne"><label>Effet</label>${seg('motSEffet', [['aucun', 'Aucun'], ['ombre', 'Ombre'], ['relief', 'Relief'], ['contour', 'Contour']], c.e || 'aucun')}</div>
    <div class="mot-outils">
      <button type="button" data-o="fx">⇋ Miroir</button><button type="button" data-o="fy">⇵ Miroir</button>
      <button type="button" data-o="haut">↑ Devant</button><button type="button" data-o="bas">↓ Derrière</button>
      <button type="button" data-o="dup">Dupliquer</button><button type="button" data-o="sup" class="sup">Supprimer</button>
    </div>`;
  motVignette(b.querySelector('#motBForme canvas'), (g, s) => motVignetteCalque(g, s, c, motMaCouleur()));
  motEl('motBForme').onclick = () => motOuvrirFormes(ME.sel);
  b.querySelectorAll('#motCoulCalque button').forEach(x => x.onclick = () => { c.couleur = x.dataset.c; motGarder(); motTout(true); });
  const lier = (id, cle, fn, aff) => { const i = motEl(id); if(!i) return; i.oninput = () => { c[cle] = fn(+i.value); i.nextElementSibling.textContent = aff(+i.value); motTout(false); }; i.onchange = () => { motGarder(); motRendreCalques(); }; };
  lier('motST', 't', v => v, v => ty === 'ligne' ? v + ' %' : v); lier('motSR', 'r', v => v, v => v + '°'); lier('motSA', 'a', v => v / 100, v => v + ' %'); lier('motSX', 'x', v => v, v => v); lier('motSY', 'y', v => v, v => v);
  const segs = (id, fn) => { const e = motEl(id); if(e) e.querySelectorAll('button').forEach(x => x.onclick = () => { fn(x.dataset.v); motGarder(); motTout(true); }); };
  segs('motSSens', v => { c.r = +v; }); segs('motSEffet', v => { c.e = v; });
  b.querySelectorAll('[data-o]').forEach(x => x.onclick = () => {
    const o = x.dataset.o, cs = M.calques;
    if(o === 'fx' || o === 'fy') c[o] = !c[o];
    else if(o === 'haut' && ME.sel < cs.length - 1){ [cs[ME.sel], cs[ME.sel + 1]] = [cs[ME.sel + 1], cs[ME.sel]]; ME.sel++; }
    else if(o === 'bas' && ME.sel > 0){ [cs[ME.sel], cs[ME.sel - 1]] = [cs[ME.sel - 1], cs[ME.sel]]; ME.sel--; }
    else if(o === 'dup'){
      if(cs.length >= MOT_MAX) return notifier({ type: 'info', titre: 'Mon motif', texte: `${MOT_MAX} calques au plus.` });
      if(c.forme === 'lettre' && motNbLettres() >= MOT_MAX_LETTRES) return notifier({ type: 'info', titre: 'Mon motif', texte: `${MOT_MAX_LETTRES} lettres au plus par motif.` });
      cs.splice(ME.sel + 1, 0, { ...motCopie(c), x: (c.x + 25) % 100 }); ME.sel++;
    }
    else if(o === 'sup'){ cs.splice(ME.sel, 1); ME.sel = Math.max(0, Math.min(ME.sel, cs.length - 1)); }
    motGarder(); motTout(true);
  });
}
function motRendreTerritoire(){
  const M = ME.M; if(!motEl('motDensite')) return;
  motEl('motDensite').value = M.densite; motEl('motODensite').textContent = M.densite;
  motEl('motIntensite').value = M.intensite; motEl('motOIntensite').textContent = M.intensite + ' %';
  motEl('motQuinconce').classList.toggle('on', !!M.quinconce); motEl('motQuinconce').setAttribute('aria-checked', String(!!M.quinconce));
}
/* la bibliothèque de formes */
function motOuvrirFormes(i){ ME.cible = i; motEl('motVFormes').hidden = false; motRendreFormes(); }
function motRendreFormes(){
  motEl('motCats').innerHTML = MOT_CATS.map(c => `<button type="button" class="${c === ME.cat ? 'on' : ''}" data-c="${c}">${c}</button>`).join('');
  motEl('motCats').querySelectorAll('button').forEach(b => b.onclick = () => { ME.cat = b.dataset.c; motRendreFormes(); });
  const g = motEl('motGrille'), pk = motEl('motPack');
  if(ME.cat === 'Lettres'){
    pk.innerHTML = `Gratuit · <b>${MOT_MAX_LETTRES} lettres au plus par motif</b>, pour éviter qu'on écrive des mots.`;
    g.innerHTML = `<div class="mot-lettres">${'ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789'.split('').map(l => `<button type="button" data-l="${l}">${l}</button>`).join('')}</div>`;
    g.querySelectorAll('[data-l]').forEach(b => b.onclick = () => motChoisir('lettre', b.dataset.l));
    return;
  }
  const fs = MTF.formes.filter(f => f.cat === ME.cat);
  const packs = [...new Set(fs.map(f => f.pack).filter(Boolean))];
  pk.innerHTML = packs.length ? packs.map(p => motPossede({ pack: p }) ? `<b>${MOT_PACKS[p]}</b> : à toi` : `<b>${MOT_PACKS[p]} · ${motPrixPack(p)}</b>`).join(' · ')
      + (fs.some(f => !f.pack) ? ' · le reste est gratuit' : '') + (packs.some(p => !motPossede({ pack: p })) ? '. Tu peux tout essayer avant d’acheter.' : '.')
    : 'Gratuit pour tous.';
  g.innerHTML = `<div class="mot-grille">${fs.map(f => `<button type="button" data-f="${f.id}"><canvas></canvas><span>${echapperTexte(f.nom)}</span>${motPossede(f) ? '' : '<em>🔒</em>'}</button>`).join('')}</div>`;
  g.querySelectorAll('[data-f]').forEach(b => {
    motVignette(b.querySelector('canvas'), (x, s) => motVignetteCalque(x, s, { forme: b.dataset.f, couleur: '#F2E6C8', r: 0, a: 1, t: 100, x: 50, y: 50, e: 'aucun' }));
    b.onclick = () => motChoisir(b.dataset.f);
  });
}
function motChoisir(forme, lettre){
  const M = ME.M, ancien = ME.cible != null ? M.calques[ME.cible] : null;
  if(forme === 'lettre' && !(ancien && ancien.forme === 'lettre') && motNbLettres() >= MOT_MAX_LETTRES) return notifier({ type: 'info', titre: 'Mon motif', texte: `${MOT_MAX_LETTRES} lettres au plus par motif.` });
  if(ancien){ const t0 = motType(ancien); ancien.forme = forme; ancien.lettre = lettre || null; const t1 = motType(ancien); if(t0 !== t1){ ancien.t = t1 === 'forme' ? 50 : 100; ancien.r = 0; } }
  else {
    if(M.calques.length >= MOT_MAX) return notifier({ type: 'info', titre: 'Mon motif', texte: `${MOT_MAX} calques au plus.` });
    const ty = forme === 'lettre' ? 'forme' : MTF.FORME[forme].type;
    M.calques.push(motL(forme, motLum(motMaCouleur()) > .55 ? '#0B1424' : '#FFFFFF', 50, 50, ty === 'forme' ? 50 : 100, { a: ty === 'forme' ? .85 : .6, lettre })); ME.sel = M.calques.length - 1;
  }
  motEl('motVFormes').hidden = true; motGarder(); motTout(true);
}
function motModelesOuvrir(){
  const z = motEl('motModeles'), fond = motMaCouleur();
  z.innerHTML = MOT_MODELES.map(([n, m], i) => `<button type="button" data-m="${i}"><canvas></canvas>${echapperTexte(n)}${motPacksManquants(m).length ? ' <em>🔒</em>' : ''}</button>`).join('');
  motEl('motVModeles').hidden = false;
  z.querySelectorAll('[data-m]').forEach(b => {
    const m = MOT_MODELES[+b.dataset.m][1];
    motVignette(b.querySelector('canvas'), (g, s) => { g.fillStyle = fond; g.fillRect(0, 0, s, s); const t = motTuile(m, Math.round(s / 2)); g.globalAlpha = m.intensite / 100; const h = m.quinconce ? s : s / 2; for(let y = 0; y < s; y += h) for(let x = 0; x < s; x += s / 2) g.drawImage(t, x, y); g.globalAlpha = 1; });
    b.onclick = () => { ME.M = motCopie(m); ME.sel = 0; motEl('motVModeles').hidden = true; motGarder(); motTout(true); };
  });
}
function motHasard(){
  const pick = (a) => a[Math.floor(Math.random() * a.length)], hasard = (a, b) => a + Math.random() * (b - a);
  const clair = motLum(motMaCouleur()) < .55;
  const tons = clair ? ['#FFFFFF', '#E8E2D4', '#FFE08A', '#F0B429', '#7FD4FF'] : ['#0B1424', '#2456C8', '#9E2B45', '#2F7D55'];
  const libres = MTF.formes.filter(motPossede);
  const formes = libres.filter(f => f.type === 'forme' && !['carre', 'carrearrondi', 'demicercle', 'ecaille'].includes(f.id));
  const trames = libres.filter(f => f.type !== 'forme');
  const cs = [];
  if(Math.random() < .45) cs.push(motL(pick(trames).id, pick(tons), 50, 50, 100, { a: hasard(.18, .35), r: pick([0, 0, 90]) }));
  cs.push(motL(pick(formes).id, pick(tons), 50, 50, Math.round(hasard(44, 66)), { a: hasard(.8, .95), e: pick(['aucun', 'aucun', 'relief', 'ombre']) }));
  if(Math.random() < .5) cs.push(motL(pick(['etoile5', 'cercle', 'etincelle', 'losange']), pick(tons), 0, 0, Math.round(hasard(8, 16)), { a: .75 }));
  cs.forEach(c => { c.a = Math.round(c.a * 100) / 100; });
  ME.M = motModele(cs, { densite: Math.round(hasard(34, 52)), intensite: Math.round(hasard(80, 92)), quinconce: Math.random() < .6 });
  ME.sel = cs.length > 1 && cs[0].t === 100 ? 1 : 0; motGarder(); motTout(true);
}
/* enregistrer, retirer */
function motProposerPacks(packs){
  const z = motEl('motPacksCorps');
  const vente = packs.some(p => motPackArticle(p));
  z.innerHTML = `<p class="mot-note" style="margin-top:0">Ton motif utilise des formes que tu n'as pas encore. ${vente ? 'Pour l\'enregistrer :' : 'Ces formes ne sont pas encore en vente : tu peux les essayer, pas les enregistrer.'}</p>`
    + packs.map(p => `<div class="mot-packl"><div><b>${MOT_PACKS[p] || p}</b><small>${MTF.formes.filter(f => f.pack === p).length} formes, gardées à vie</small></div>
        <button type="button" class="mot-ok" data-mot-pack="${p}" ${motPackArticle(p) ? '' : 'disabled'}>${motPackArticle(p) ? motPrixPack(p) : 'Bientôt'}</button></div>`).join('')
    + `<button type="button" class="mot-sec large" id="motSansPacks">Retirer ces formes de mon motif</button>`;
  z.querySelectorAll('[data-mot-pack]').forEach(b => b.onclick = () => motAcheterPack(b.dataset.motPack));
  motEl('motSansPacks').onclick = () => {
    ME.M.calques = ME.M.calques.filter(c => motPossede(MTF.FORME[c.forme])); ME.sel = 0;
    motEl('motVPacks').hidden = true; motGarder(); motTout(true);
  };
  motEl('motVPacks').hidden = false;
}
async function motEnregistrer(vide){
  if(ME.envoi) return;
  const m = vide ? { calques: [] } : ME.M;
  if(!vide){
    if(!m.calques.length){ notifier({ type: 'info', titre: 'Mon motif', texte: 'Ajoute au moins une forme, ou touche « Retirer mon motif ».' }); return; }
    const packs = motPacksManquants(m);
    if(packs.length){ motProposerPacks(packs); return; }
  }
  ME.envoi = true;
  const { data, error } = await sb.rpc('motif_enregistrer', { p_motif: m });
  ME.envoi = false;
  if(error){ notifier({ type: 'erreur', titre: 'Mon motif', texte: messageLisible(error.message) }); return; }
  MTF.moi = data && data.motif ? data.motif : null;
  if(window.__monId){ if(MTF.moi) MOTIFS.set(window.__monId, MTF.moi); else MOTIFS.delete(window.__monId); }
  MTF.pats.clear();
  try{ localStorage.removeItem(MOT_BROUILLON); }catch(e){}
  try{ rendreCalques(); demanderDessin(); }catch(e){}
  motFermer();
  try{ atbRendre(); }catch(e){}
  notifier({ type: 'succes', titre: MTF.moi ? 'Motif enregistré' : 'Motif retiré', texte: MTF.moi ? 'Tous les joueurs le voient en zoomant sur ton territoire.' : 'Ton territoire retrouve sa couleur unie.' });
}
function motRetirer(b){
  if(!MTF.moi){ try{ localStorage.removeItem(MOT_BROUILLON); }catch(e){} motFermer(); return; }
  if(!b.classList.contains('confirmer')){ b.classList.add('confirmer'); b.textContent = 'Toucher encore pour retirer'; setTimeout(() => { if(b.isConnected){ b.classList.remove('confirmer'); b.textContent = 'Retirer mon motif'; } }, 4000); return; }
  motEnregistrer(true);
}
