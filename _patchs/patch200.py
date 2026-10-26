# -*- coding: utf-8 -*-
u"""
patch200 — le dos carte par carte (Terra et Front) et la révélation de la
grande vitrine (les cartes arrivent de dos et se retournent une par une).
- fiche de ma carte Terra / Front : rangée « Dos de cette carte » ;
- Modifier ma vitrine : petit dos sur chaque carte exposée, panneau de choix ;
- Profil › Personnaliser : bloc « Carte par carte » + « Choisir les cartes » ;
- la vitrine d'un joueur montre le dos choisi pour chaque carte.
Le Tirage garde le dos principal.
SQL : _boutique-euros/11-dos-carte-par-carte.sql (à passer avant de pousser).
"""
import io, os
ICI = os.path.dirname(os.path.abspath(__file__))
BASE = os.path.dirname(ICI) if os.path.basename(ICI) == '_patchs' else ICI
def lire(n):
    with io.open(os.path.join(BASE, n), encoding='utf-8') as f: return f.read()
def ecrire(n, s):
    with io.open(os.path.join(BASE, n), 'w', encoding='utf-8') as f: f.write(s)

BLOC_JS = r'''// ---------- patch200 : le dos carte par carte ----------
// Une carte (Terra ou Front) peut avoir son propre dos. Il se voit quand on la
// retourne : sa fiche, sa vitrine. Le Tirage garde le dos principal (sinon le
// dos dévoilerait la carte avant qu'on la retourne).
let mesDosCartes = null;   // Map 'terra|83137' -> { dos, nom } ; null = pas encore chargé
async function chargerMesDosCartes(force){
  if(mesDosCartes && !force) return mesDosCartes;
  const m = new Map();
  try{
    const { data, error } = await sb.rpc('dos_cartes', { p_joueur: window.__monId });
    if(!error) for(const r of data || []) m.set(r.source + '|' + r.code, { dos: r.dos, nom: r.nom });
  }catch(e){}
  mesDosCartes = m;
  return m;
}
// la clé du dos d'une de mes cartes, ou undefined = mon dos principal
function dosDeMaCarte(source, code){
  const r = mesDosCartes && mesDosCartes.get(source + '|' + code);
  return r ? dosCle(r.dos === 'origine' ? null : r.dos) : undefined;
}
async function dosPossedes(){
  if(!gardeRobe){ try{ const { data } = await sb.rpc('garde_robe'); if(data) gardeRobe = data; }catch(e){} }
  return (gardeRobe && gardeRobe.dos_liste) || [];
}
const nomDosCourt = (n) => String(n || '').replace(/^Dos /, '');
// un petit dos, à partir de sa clé (« neon », « origine »…)
function miniDosHtml(cle, classe){
  return dosApercuHtml('dos-' + (cle || 'origine')).replace('class="bq-dos-apercu"', `class="bq-dos-apercu ${classe || 'dc-mini'}"`);
}
function choixDosHtml(source, code){
  if(!SAISON2) return '';
  return `<div class="dc-choix" data-dc-src="${source}" data-dc-code="${echapperTexte(code)}">
      <div class="dc-tete"><span>Dos de cette carte</span><small class="dc-etat"></small></div>
      <div class="dc-rangee" role="group" aria-label="Dos de cette carte"><span class="dc-attente">Chargement…</span></div>
      <p class="dc-aide">Se voit quand on retourne la carte : ici, et chez ceux qui regardent ta vitrine.</p>
    </div>`;
}
// remplit un .dc-choix ; apres(cle) reçoit la clé du nouveau dos (undefined = mon dos)
async function remplirChoixDos(el, apres){
  if(!el) return;
  el._apres = apres;   // la même rangée peut servir pour plusieurs cartes (vitrine)
  const [liste] = await Promise.all([dosPossedes(), chargerMesDosCartes()]);
  if(!el.isConnected) return;
  const dessiner = () => {
    const source = el.dataset.dcSrc, code = el.dataset.dcCode;
    const r = mesDosCartes.get(source + '|' + code);
    const actuel = r ? r.dos : '';
    const opts = [{ val: '', nom: 'Mon dos', cle: document.body.dataset.dos || 'origine' }]
      .concat(liste.map(o => ({ val: o.id || 'origine', nom: nomDosCourt(o.nom), cle: dosCle(o.id) })));
    el.querySelector('.dc-rangee').innerHTML = opts.map(o => `<button type="button" class="dc-opt${o.val === actuel ? ' on' : ''}" data-dc-val="${echapperTexte(o.val)}" aria-pressed="${o.val === actuel}">
        ${miniDosHtml(o.cle)}<span>${echapperTexte(o.nom)}</span></button>`).join('');
    const choisi = opts.find(o => o.val === actuel);
    const etat = el.querySelector('.dc-etat');
    if(etat) etat.textContent = actuel ? (choisi ? choisi.nom : '') : 'suit ton dos principal';
  };
  el._dessiner = dessiner;
  dessiner();
  if(el.dataset.arme) return;
  el.dataset.arme = '1';
  el.addEventListener('click', async (e) => {
    const b = e.target.closest('[data-dc-val]');
    if(!b || b.disabled) return;
    const source = el.dataset.dcSrc, code = el.dataset.dcCode;
    const val = b.dataset.dcVal;
    el.querySelectorAll('.dc-opt').forEach(x => { x.disabled = true; });
    const { error } = await sb.rpc('dos_cartes_definir', { p_source: source, p_codes: [code], p_dos: val || null });
    el.querySelectorAll('.dc-opt').forEach(x => { x.disabled = false; });
    if(error){ notifier({ type: 'erreur', titre: 'Impossible', texte: messageLisible(error.message) }); return; }
    if(val) mesDosCartes.set(source + '|' + code, { dos: val, nom: (mesDosCartes.get(source + '|' + code) || {}).nom || '' });
    else mesDosCartes.delete(source + '|' + code);
    el._dessiner();
    if(el._apres) el._apres(dosDeMaCarte(source, code));
  });
}
// change le dos d'une carte en grand (et la retourne pour le montrer)
function majDosC3d(c3d, cle, retourner){
  const base = c3d && c3d.querySelector('.c3d-dos .c3d-base');
  const fb = base && base.querySelector('.c3d-dosint');
  if(!fb) return;
  const ancien = base.querySelector('.c3d-dosde');
  if(cle){
    let w = ancien;
    if(!w){ w = document.createElement('div'); w.className = 'bq-dos-apercu c3d-dosde'; base.insertBefore(w, fb); w.appendChild(fb); }
    w.dataset.dos = cle;
  } else if(ancien) ancien.replaceWith(fb);
  if(retourner){ const carte = c3d.querySelector('.c3d-carte'); if(carte) carte.classList.add('retournee'); }
}
// une fiche à moi : la carte prend son dos, la rangée de choix se remplit
function armerDosFiche(boite, source, code){
  if(!SAISON2 || !boite) return;
  const c3d = boite.querySelector('.c3d');
  chargerMesDosCartes().then(() => { if(c3d && c3d.isConnected) majDosC3d(c3d, dosDeMaCarte(source, code), false); });
  remplirChoixDos(boite.querySelector('.dc-choix'), (cle) => majDosC3d(c3d, cle, true));
}

// la grande vitrine : les cartes arrivent de dos et se retournent une par une
function placeVitrineHtml(c, i, n){
  const pas = Math.min(.2, 2.4 / Math.max(1, n));
  return `<div class="vt-place vtg-rev" data-vtg-carte="${i}" style="--vtg-d:${(.55 + i * pas).toFixed(2)}s"><span class="vt-rang">${i + 1}</span>
      <div class="vtg-tourne">
        <div class="vtg-face">${miniTerra({ ...c, exemplaires: 1 })}</div>
        <div class="vtg-dos">${miniDosHtml(c.dos || document.body.dataset.dos || 'origine', 'vtg-dosde')}</div>
      </div></div>`;
}
const vtgDejaVues = new WeakSet();
function armerRevelationVitrine(boite, cartes){
  if(!boite) return;
  const deja = cartes && vtgDejaVues.has(cartes);
  if(cartes) vtgDejaVues.add(cartes);
  const fin = (p) => { p.classList.add('vtg-fini'); const d = p.querySelector('.vtg-dos'); if(d) d.remove(); };
  const places = [...boite.querySelectorAll('.vtg-rev')];
  if(deja || matchMedia('(prefers-reduced-motion: reduce)').matches){ places.forEach(fin); return; }
  for(const p of places){
    // le dos (188 x 263 dans le jeu) est mis à l'échelle de la carte de la vitrine
    const d = p.querySelector('.vtg-dosde'), e = d && d.querySelector('.bq-dos-echelle');
    if(e && p.offsetWidth){ const k = p.offsetWidth / 188; e.style.transform = `scale(${k})`; e.style.height = (p.offsetHeight / k) + 'px'; }
    const t = p.querySelector('.vtg-tourne');
    if(t) t.addEventListener('animationend', () => fin(p), { once: true });
    setTimeout(() => fin(p), 6000);   // filet : l'animation coupée ne laisse pas de dos
  }
}

// Profil › Personnaliser : les cartes qui ont leur propre dos
function blocDosCartesHtml(){
  if(!mesDosCartes) return '';
  const liste = gardeRobe ? gardeRobe.dos_liste || [] : [];
  const nomDe = (id) => { const o = liste.find(x => (x.id || 'origine') === id); return o ? nomDosCourt(o.nom) : ''; };
  const lignes = [...mesDosCartes.entries()].sort((a, b) => a[1].nom.localeCompare(b[1].nom, 'fr'));
  return `<div class="gr-titre">Carte par carte <span>${lignes.length} carte${lignes.length > 1 ? 's' : ''}</span></div>
    ${lignes.length ? `<div class="gr-dc-liste">${lignes.map(([cle, r]) => {
      const [source] = cle.split('|');
      return `<div class="gr-dc-ligne">${miniDosHtml(dosCle(r.dos === 'origine' ? null : r.dos), 'dc-mini')}
        <div class="gr-dc-nom"><b>${echapperTexte(r.nom)}</b><span>${source === 'front' ? 'Front' : 'Terra'} · ${echapperTexte(nomDe(r.dos))}</span></div>
        <button type="button" class="bq-btn secondaire" data-gr-dc-retirer="${echapperTexte(cle)}">Mon dos</button></div>`;
    }).join('')}</div>` : '<p class="gr-dc-vide">Aucune carte n\'a son propre dos : elles suivent toutes ton dos principal.</p>'}
    <div class="gr-dc-bas"><button type="button" class="bq-btn secondaire" data-gr-dc-choisir>Choisir les cartes</button>
      <small>Terra et Front. Une carte vendue, échangée ou prise prend le dos de son nouveau propriétaire.</small></div>`;
}
document.getElementById('grCorps').addEventListener('click', async (e) => {
  const r = e.target.closest('[data-gr-dc-retirer]');
  if(r){
    r.disabled = true;
    const [source, code] = r.dataset.grDcRetirer.split('|');
    const { error } = await sb.rpc('dos_cartes_definir', { p_source: source, p_codes: [code], p_dos: null });
    if(error){ notifier({ type: 'erreur', titre: 'Impossible', texte: messageLisible(error.message) }); r.disabled = false; return; }
    mesDosCartes.delete(r.dataset.grDcRetirer);
    renderGardeRobe();
    return;
  }
  if(e.target.closest('[data-gr-dc-choisir]')) ouvrirChoixDosCartes();
});

// choisir un dos, puis les cartes qui le portent
async function ouvrirChoixDosCartes(){
  const liste = await dosPossedes();
  if(!terraCharge) await chargerCollectionTerra();
  let dos = (liste.find(o => o.id) || liste[0] || {}).id || 'origine';
  let source = modeJeu === 'front' ? 'front' : 'terra';
  let choix = new Set(), recherche = '';
  const rangTier = (t) => TIERS.findIndex(x => x.id === t.id);
  const cartesDe = (s) => [...(s === 'front' ? collectionMap.values() : terraCollection.values())]
    .sort((a, b) => rangTier(a.tier) - rangTier(b.tier) || a.nom.localeCompare(b.nom, 'fr'));
  const fermer = ouvrirFenetre(`
    <div class="fenetre vt-choix dc-fenetre" role="dialog" aria-modal="true" aria-labelledby="dcTitre">
      <h2 id="dcTitre">Donner un dos à des cartes</h2>
      <p class="vt-aide">Choisis un dos, puis touche les cartes qui le porteront.</p>
      <div class="dc-rangee" id="dcDos" role="group" aria-label="Le dos"></div>
      <div class="dc-sources" role="group" aria-label="Mode">
        <button type="button" data-dc-source="terra">Terra</button><button type="button" data-dc-source="front">Front</button>
      </div>
      <p class="vt-compte" id="dcCompte"></p>
      <input type="search" id="dcRecherche" class="bourse-search" placeholder="Rechercher une commune ou un département…" autocomplete="off">
      <div class="vt-grille" id="dcGrille"></div>
      <p class="prix-erreur" id="dcErreur" role="alert"></p>
      <div class="prix-boutons">
        <button type="button" class="open-btn secondary" data-dc="annuler">Annuler</button>
        <button type="button" class="open-btn" data-dc="ok">Enregistrer</button>
      </div>
    </div>`);
  const boite = document.querySelector('#fenetre .dc-fenetre');
  if(!boite) return;
  const dessiner = () => {
    boite.querySelector('#dcDos').innerHTML = liste.map(o => { const v = o.id || 'origine';
      return `<button type="button" class="dc-opt${v === dos ? ' on' : ''}" data-dc-dos="${echapperTexte(v)}" aria-pressed="${v === dos}">${miniDosHtml(dosCle(o.id))}<span>${echapperTexte(nomDosCourt(o.nom))}</span></button>`; }).join('');
    boite.querySelectorAll('[data-dc-source]').forEach(b => b.setAttribute('aria-pressed', String(b.dataset.dcSource === source)));
    boite.querySelector('#dcCompte').innerHTML = `<b>${choix.size}</b> carte${choix.size > 1 ? 's' : ''} choisie${choix.size > 1 ? 's' : ''}`;
    const q = recherche.trim().toLowerCase();
    const dep = q ? codeDepartement(q) : null;
    const qs = sansAccents(recherche.trim());
    const cartes = cartesDe(source).filter(c => !q || correspondRecherche(c.nom, c.dept, qs) || c.dept === dep).slice(0, 150);
    boite.querySelector('#dcGrille').innerHTML = cartes.map(c => `<button type="button" class="vt-carte${choix.has(c.code) ? ' pris' : ''}" data-dc-code="${echapperTexte(c.code)}" aria-pressed="${choix.has(c.code)}">
        ${miniVitrine({ ...c, aurore: source === 'front' ? (AURORE && AURORE[c.code] ? 1 : 0) : c.aurore })}${choix.has(c.code) ? '<span class="vt-num">✓</span>' : ''}</button>`).join('')
      || '<p class="collection-empty">Aucune carte ne correspond.</p>';
  };
  dessiner();
  boite.querySelector('#dcRecherche').addEventListener('input', (e) => { recherche = e.target.value; dessiner(); });
  boite.addEventListener('click', async (e) => {
    const d = e.target.closest('[data-dc-dos]');
    if(d){ dos = d.dataset.dcDos; dessiner(); return; }
    const s = e.target.closest('[data-dc-source]');
    if(s){ if(s.dataset.dcSource !== source){ source = s.dataset.dcSource; choix = new Set(); } dessiner(); return; }
    const c = e.target.closest('[data-dc-code]');
    if(c){ const k = c.dataset.dcCode; if(choix.has(k)) choix.delete(k); else choix.add(k); dessiner(); return; }
    const b = e.target.closest('[data-dc]');
    if(!b) return;
    if(b.dataset.dc === 'annuler'){ fermer(null); return; }
    if(!choix.size){ boite.querySelector('#dcErreur').textContent = 'Touche au moins une carte.'; return; }
    b.disabled = true; b.textContent = 'Enregistrement…';
    const { error } = await sb.rpc('dos_cartes_definir', { p_source: source, p_codes: [...choix], p_dos: dos });
    if(error){ boite.querySelector('#dcErreur').textContent = messageLisible(error.message); b.disabled = false; b.textContent = 'Enregistrer'; return; }
    fermer(null);
    await chargerMesDosCartes(true);
    renderGardeRobe();
    notifier({ type: 'succes', titre: 'Dos posé', texte: `${choix.size} carte${choix.size > 1 ? 's' : ''} ${choix.size > 1 ? 'ont' : 'a'} maintenant ce dos.` });
  });
}

'''
BLOC_CSS = r'''
/* ---------- patch200 : le dos carte par carte, la révélation de la grande vitrine ---------- */
.dc-mini{ width: 47px; height: 65.75px; margin: 0; flex: none; }
.dc-mini .bq-dos-echelle{ transform: scale(.25); }
.dc-choix{ width: min(360px, 100%); margin: 14px auto 0; text-align: left; background: rgba(15,31,56,.6); border: 1px solid rgba(169,188,212,.18); border-radius: 14px; padding: 10px 12px; display: grid; gap: 8px; }
.dc-tete{ display: flex; justify-content: space-between; align-items: baseline; gap: 8px; }
.dc-tete span{ font-size: .68rem; font-weight: 700; letter-spacing: .14em; text-transform: uppercase; color: var(--brume); }
.dc-tete small{ font-size: .76rem; color: var(--brume); }
.dc-rangee{ display: flex; gap: 8px; overflow-x: auto; padding-bottom: 4px; scrollbar-width: thin; }
.dc-attente{ font-size: .8rem; color: var(--brume); padding: 8px 0; }
.dc-opt{ flex: none; display: flex; flex-direction: column; align-items: center; gap: 5px; min-width: 62px; padding: 6px; border-radius: 10px; cursor: pointer;
  background: transparent; border: 1px solid rgba(169,188,212,.16); color: #fff; font: inherit; }
.dc-opt span{ font-size: .7rem; font-weight: 600; white-space: nowrap; }
.dc-opt.on{ border-color: var(--c-legendaire); background: rgba(240,180,41,.12); }
.dc-opt:disabled{ opacity: .6; cursor: default; }
.dc-opt:focus-visible{ outline: 2px solid #fff; outline-offset: 2px; }
.dc-aide{ margin: 0; font-size: .74rem; line-height: 1.45; color: var(--brume); }
/* la vitrine : le petit dos de chaque carte exposée */
.vt-bande > .vt-case-w{ position: relative; flex: 0 0 66px; width: 66px; min-width: 0; }
.vt-case-w > .vt-case .mini{ width: 100%; }
.vt-dos-pastille{ position: absolute; right: -5px; top: -7px; z-index: 3; width: 26px; height: 35px; padding: 2px; border-radius: 5px; cursor: pointer;
  background: var(--nuit, #0B1830); border: 2px solid rgba(244,247,251,.85); box-shadow: 0 4px 10px rgba(0,0,0,.5); }
.vt-dos-pastille:focus-visible{ outline: 2px solid var(--c-legendaire); outline-offset: 2px; }
.vt-pastille-dos{ width: 18px; height: 25.2px; margin: 0; border-radius: 3px; overflow: hidden; }
.vt-pastille-dos .bq-dos-echelle{ transform: scale(.0958); }
.vt-dos-panneau{ background: rgba(15,31,56,.85); border: 1px solid rgba(240,180,41,.35); border-radius: 14px; padding: 10px 12px; margin: 0 0 12px; text-align: left; }
.vt-dos-panneau .dc-choix{ width: auto; margin: 0; padding: 0; background: none; border: 0; }
.vt-dos-haut{ display: flex; justify-content: space-between; align-items: center; gap: 8px; margin-bottom: 4px; }
.vt-dos-haut b{ font-family: var(--titre); font-size: 1.15rem; }
.vt-dos-haut button{ width: 40px; height: 40px; border-radius: 50%; border: 1px solid rgba(169,188,212,.25); background: transparent; color: #fff; cursor: pointer; font: inherit; }
/* Profil › Personnaliser */
.gr-dc-liste{ display: grid; gap: 6px; margin-bottom: 10px; }
.gr-dc-ligne{ display: grid; grid-template-columns: 47px minmax(0, 1fr) auto; gap: 10px; align-items: center; padding: 6px 8px; border-radius: 10px; background: rgba(8,19,37,.5); border: 1px solid rgba(169,188,212,.12); }
.gr-dc-nom{ min-width: 0; display: flex; flex-direction: column; }
.gr-dc-nom b{ white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
.gr-dc-nom span{ font-size: .78rem; color: var(--brume); }
.gr-dc-ligne .bq-btn{ margin: 0; }
.gr-dc-vide{ margin: 0 0 10px; font-size: .85rem; color: var(--brume); }
.gr-dc-bas{ display: grid; gap: 6px; justify-items: start; }
.gr-dc-bas small{ font-size: .76rem; color: var(--brume); }
.dc-fenetre .dc-rangee{ margin: 4px 0 10px; }
.dc-sources{ display: inline-flex; padding: 3px; border-radius: 999px; background: var(--nuit-2, #162C4B); border: 1px solid rgba(169,188,212,.16); }
.dc-sources button{ min-height: 40px; padding: 8px 18px; border-radius: 999px; border: 0; background: none; color: var(--brume); font: inherit; font-weight: 600; cursor: pointer; }
.dc-sources button[aria-pressed="true"]{ background: #F4F7FB; color: #0F1F38; }
/* la grande vitrine : les cartes arrivent de dos et se retournent une par une */
.vtg-rev{ perspective: 700px; }
.vtg-tourne{ position: relative; transform-style: preserve-3d; animation: vtgRetourne .6s cubic-bezier(.45,.05,.2,1) var(--vtg-d, .5s) both; }
.vtg-face{ transform: rotateY(180deg); backface-visibility: hidden; -webkit-backface-visibility: hidden; }
.vtg-dos{ position: absolute; inset: 0; backface-visibility: hidden; -webkit-backface-visibility: hidden; }
.vtg-dosde{ position: absolute; inset: 0; width: auto; height: auto; margin: 0; border-radius: 10px; overflow: hidden; box-shadow: 0 10px 18px rgba(0,0,0,.5); }
.vtg-fini .vtg-tourne{ animation: none; transform: none; }
.vtg-fini .vtg-face{ transform: none; }
@keyframes vtgRetourne{ from{ transform: rotateY(0deg); } to{ transform: rotateY(180deg); } }
@media (prefers-reduced-motion: reduce){ .vtg-tourne{ animation: none; } .vtg-face{ transform: none; } .vtg-dos{ display: none; } }
'''
REMPL = [('${carte3dDebut(150, 225, 1.65)}${miniTerra(e)}${carte3dFin()}</div>', "${carte3dDebut(150, 225, 1.65)}${miniTerra(e)}${carte3dFin(dosDeMaCarte('terra', code))}${choixDosHtml('terra', code)}</div>"), ("    armerCarte3d(boite.querySelector('.c3d'));\n    boite.addEventListener('click', async (ev) => {", "    armerCarte3d(boite.querySelector('.c3d'));\n    armerDosFiche(boite, 'terra', code);   // patch200\n    boite.addEventListener('click', async (ev) => {"), ('aurore: auroreFront(entry.code) ? 1 : 0 })}${carte3dFin()}', "aurore: auroreFront(entry.code) ? 1 : 0 })}${carte3dFin(entry.perdue ? undefined : dosDeMaCarte('front', entry.code))}${entry.perdue ? '' : choixDosHtml('front', entry.code)}"), ("armerCarte3d(boite.querySelector('.c3d'));   // patch179", "armerCarte3d(boite.querySelector('.c3d'));   // patch179\n  if(!entry.perdue) armerDosFiche(boite, 'front', entry.code);   // patch200"), ('  let s1 = new Set();   // patch170', "  const dosCartes = new Map();   // patch200 : le dos choisi pour chaque carte exposée\n  try{ const r5 = await sb.rpc('dos_cartes', { p_joueur: id });\n    if(!r5.error) for(const x of r5.data || []) dosCartes.set(x.source + '|' + x.code, dosCle(x.dos === 'origine' ? null : x.dos)); }catch(err){}\n  let s1 = new Set();   // patch170"), ('    dos,\n    auroreS1:', "    dos: dosCartes.get((r.source === 'front' ? 'front' : 'terra') + '|' + r.code) || dos,\n    auroreS1:"), ('${cartes.map((c, i) => `<div class="vt-place" data-vtg-carte="${i}"><span class="vt-rang">${i + 1}</span>${miniTerra({ ...c, exemplaires: 1 })}</div>`).join(\'\')}', "${cartes.map((c, i) => placeVitrineHtml(c, i, cartes.length)).join('')}"), ("  document.querySelector('#fenetre .vt-grande').addEventListener('click', (e) => {", "  armerRevelationVitrine(document.querySelector('#fenetre .vt-grande'), cartes);   // patch200\n  document.querySelector('#fenetre .vt-grande').addEventListener('click', (e) => {"), ("  const front = source === 'front';   // patch180\n", "  const front = source === 'front';   // patch180\n  if(SAISON2) await chargerMesDosCartes();   // patch200\n"), ('      cases.push(c ? `<button type="button" class="vt-case" data-vt-retirer="${echapperTexte(c.code)}" aria-label="Retirer ${echapperTexte(c.nom)}">${miniVitrine(c)}</button>`', '      const dosC = c && SAISON2 && mesDosCartes ? (dosDeMaCarte(front ? \'front\' : \'terra\', c.code) || document.body.dataset.dos || \'origine\') : null;   // patch200\n      cases.push(c ? `<div class="vt-case-w"><button type="button" class="vt-case" data-vt-retirer="${echapperTexte(c.code)}" aria-label="Retirer ${echapperTexte(c.nom)}">${miniVitrine(c)}</button>${dosC ? `<button type="button" class="vt-dos-pastille" data-vt-dos="${echapperTexte(c.code)}" aria-label="Changer le dos de ${echapperTexte(c.nom)}">${miniDosHtml(dosC, \'vt-pastille-dos\')}</button>` : \'\'}</div>`'), ('<div class="vt-etagere vt-bande" id="vtApercu"></div>', '<div class="vt-etagere vt-bande" id="vtApercu"></div>\n      ${SAISON2 ? `<div class="vt-dos-panneau" id="vtDosPanneau" hidden><div class="vt-dos-haut"><b class="vt-dos-titre"></b><button type="button" data-vt-dos-fermer aria-label="Fermer">✕</button></div>${choixDosHtml(front ? \'front\' : \'terra\', \'\')}</div>` : \'\'}'), ("const r = e.target.closest('[data-vt-retirer]');", "if(e.target.closest('[data-vt-dos-fermer]')){ document.getElementById('vtDosPanneau').hidden = true; return; }   // patch200\n    if(e.target.closest('#vtDosPanneau')) return;\n    const pd = e.target.closest('[data-vt-dos]');\n    if(pd){\n      const pan = document.getElementById('vtDosPanneau'), c = reserve.get(pd.dataset.vtDos);\n      pan.hidden = false;\n      pan.querySelector('.vt-dos-titre').textContent = 'Dos de ' + (c ? c.nom : '');\n      const ch = pan.querySelector('.dc-choix'); ch.dataset.dcCode = pd.dataset.vtDos;\n      remplirChoixDos(ch, () => dessiner());\n      return;\n    }\n    const r = e.target.closest('[data-vt-retirer]');"), ('<div class="gr-objets">${dos.map(o => tuile(\'dos\', o, dosApercuHtml(o.id))).join(\'\')}</div>', '<div class="gr-objets">${dos.map(o => tuile(\'dos\', o, dosApercuHtml(o.id))).join(\'\')}</div>\n      ${SAISON2 ? blocDosCartesHtml() : \'\'}'), ('  gardeRobe = data;\n  renderGardeRobe();', '  gardeRobe = data;\n  if(SAISON2) await chargerMesDosCartes(true);   // patch200\n  renderGardeRobe();'), ('  appliquerDos(data.dos);\n  // patch175', '  appliquerDos(data.dos);\n  chargerMesDosCartes(true);   // patch200 : les dos carte par carte\n  // patch175'), ('// ---------- patch179 : la carte en grand, inclinable et retournable ----------', '__BLOC__// ---------- patch179 : la carte en grand, inclinable et retournable ----------')]

js = lire('app.js')
assert 'patch200' not in js
for avant, apres in REMPL:
    assert js.count(avant) == 1, avant[:60]
    js = js.replace(avant, apres.replace('__BLOC__', BLOC_JS))
ecrire('app.js', js)
css = lire('style.css')
assert 'patch200' not in css
ecrire('style.css', css.rstrip('\n') + '\n' + BLOC_CSS)
print(u'patch200 applique. Lancer : python3 maj-version.py')
