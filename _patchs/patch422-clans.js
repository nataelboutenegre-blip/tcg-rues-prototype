
// ---------- patch422 (12/11/2026) : le clan sur le profil, la fiche d'un clan, les pseudos du tchat (idée d'Oshannir) ----------
// Sur le profil d'un joueur, son clan (blason, nom, sigle, rang) ; le toucher ouvre la fiche du clan : ses membres,
// chacun ouvre son profil, et « Voir son territoire ». Dans le tchat du clan, le pseudo de l'auteur et les @pseudo
// mentionnés ouvrent le profil ; taper « @ » propose les pseudos. On passe d'une fiche à l'autre sans refermer le fond.
let clansInfos = { lu: 0, parTag: new Map(), parId: new Map() };
let fermerClanFiche = null, clanFicheEnCours = null;
async function chargerClansInfos(force){
  if(!CLANS) return clansInfos;
  if(!force && clansInfos.parTag.size && Date.now() - clansInfos.lu < 5 * 60000) return clansInfos;
  try{
    const [cl, cf] = await Promise.all([sb.rpc('clans_classement'), sb.rpc('clans_en_formation')]);
    if(cl.error && cf.error) return clansInfos;
    const parTag = new Map(), parId = new Map();
    (cl.error ? [] : cl.data || []).forEach((x, i) => { const o = { ...x, id: x.clan_id, rang: i + 1 }; parTag.set(x.tag, o); parId.set(x.clan_id, o); });
    (cf.error ? [] : cf.data || []).forEach(x => {
      if(parTag.has(x.tag)) return;
      const o = { ...x, id: x.clan_id, rang: 0, formation: true }; parTag.set(x.tag, o); parId.set(x.clan_id, o);
    });
    clansInfos = { lu: Date.now(), parTag, parId };
  }catch(e){ /* le clan n'est qu'un plus sur le profil */ }
  return clansInfos;
}
function clanDuJoueur(id){
  if(!CLANS || !id || !clansCarte.size) return null;
  const k = clansCarte.get(id);
  if(!k) return null;
  return clansInfos.parTag.get(k.tag) || { tag: k.tag, couleur: k.couleur, nom: null, id: null };
}
function rangClanTexte(c){
  return c.rang ? `${c.rang}${c.rang === 1 ? 'er' : 'e'} des clans` : c.formation ? 'clan en formation' : '';
}
function clanProfilHtml(p){
  const c = clanDuJoueur(p.id);
  if(!c) return '';
  const r = rangClanTexte(c);
  return `<div class="pr-clan-l"><button type="button" class="pr-clan" ${c.id ? `data-clan-fiche="${echapperTexte(c.id)}"` : 'disabled'}
      style="--clan:${echapperTexte(c.couleur || '#E07A2E')}" aria-label="Voir le clan ${echapperTexte(c.nom || c.tag)}">
    ${blasonHtml(c.tag, c.couleur, true)}
    <span class="pr-clan-txt"><b>${echapperTexte(c.nom || 'Clan ' + c.tag)}</b><small>${echapperTexte(c.tag)}${r ? ' · ' + r : ''}</small></span>
    ${c.id ? '<span class="pr-clan-fl" aria-hidden="true">›</span>' : ''}</button></div>`;
}
// d'une fiche à l'autre : on oublie celle qu'on quitte, sans faire disparaître le fond
function quitterFiches(sauf){
  if(sauf !== 'profil' && fermerProfil){ const f = fermerProfil; fermerProfil = null; profilEnCours = null; if(f.detacher) f.detacher(); }
  if(sauf !== 'clan' && fermerClanFiche){ const f = fermerClanFiche; fermerClanFiche = null; clanFicheEnCours = null; if(f.detacher) f.detacher(); }
}
async function ouvrirFicheClan(id){
  if(!id) return;
  const [infos, mb] = await Promise.all([chargerClansInfos(),
    sb.rpc('clan_membres_voir', { p_clan: id }).then(r => r, () => ({ error: true }))]);
  const c = infos.parId.get(id);
  if(!c || mb.error || !Array.isArray(mb.data)){
    notifier({ type: 'info', titre: 'Clan indisponible', texte: 'Cette fiche n’est pas disponible pour le moment.' });
    return;
  }
  clanFicheEnCours = { ...c, membres: mb.data };
  rendreFicheClan();
}
function rendreFicheClan(){
  const c = clanFicheEnCours;
  if(!c) return;
  const nb = (x) => Number(x || 0).toLocaleString('fr-FR');
  const moiId = monUidClan || window.__monId;
  const membres = [...c.membres].sort((a, b) => (b.chef - a.chef) || (b.bras_droit - a.bras_droit) || ((b.communes || 0) - (a.communes || 0)));
  const actifs = membres.filter(m => membreActif(m)).length;
  const communes = membres.reduce((s, m) => s + Number(m.communes || 0), 0);
  const estLeMien = membres.some(m => m.joueur_id === moiId);
  const lignes = membres.map(m => {
    const j = joursDepuis(m.dernier_jour), actif = membreActif(m);
    const etat = actif ? 'Actif' : (j === null ? 'Pas encore joué' : `Absent depuis ${j} jour${j > 1 ? 's' : ''}`);
    return `<div class="cl-mb"><span class="av" aria-hidden="true">${echapperTexte((m.pseudo || '?')[0].toUpperCase())}</span>
      <div class="qui"><button type="button" class="cl-mb-pseudo" data-cf-profil="${echapperTexte(m.joueur_id)}">${echapperTexte(m.pseudo)}${m.joueur_id === moiId ? ' <small>(toi)</small>' : ''}</button>
        <div class="cl-mb-info"><span class="cl-mb-point${actif ? '' : ' off'}" aria-hidden="true"></span>${etat}${m.chef ? ' · <span class="cl-mb-chef">Chef</span>' : m.bras_droit ? ' · <span class="cl-mb-chef bd">Bras droit</span>' : ''}</div></div>
      <span class="cl-mb-nb"><b>${nb(m.communes)}</b> commune${m.communes > 1 ? 's' : ''}</span></div>`;
  }).join('');
  const chiffres = [[`${membres.length}<small>/8</small>`, 'membres'], [nb(actifs), actifs > 1 ? 'actifs' : 'actif'], [nb(communes), 'communes']];
  if(c.rang && c.moyenne != null) chiffres.push([nb(c.moyenne), 'par membre actif']);
  const r = rangClanTexte(c);
  const html = `
    <div class="fenetre profil clan-fiche" role="dialog" aria-modal="true" aria-labelledby="cfNom" style="--joueur:${echapperTexte(c.couleur || '#E07A2E')};--clan:${echapperTexte(c.couleur || '#E07A2E')}">
      <div class="pr-tete">
        <button class="pr-fermer" data-cf="fermer" aria-label="Fermer">✕</button>
        <div class="cf-blason">${blasonHtml(c.tag, c.couleur)}</div>
        <h2 id="cfNom">${echapperTexte(c.nom)}</h2>
        <p class="pr-sous"><span class="cf-tag">${echapperTexte(c.tag)}</span>${r ? ` · ${c.rang ? `<span class="pr-rang">${c.rang}${c.rang === 1 ? 'er' : 'e'}</span> des clans` : r}` : ''}</p>
      </div>
      <div class="pr-corps">
        <div class="pr-chiffres cf-chiffres n${chiffres.length}">${chiffres.map(([v, l]) =>
          `<div class="pr-ch"><b>${v}</b><span>${l}</span></div>`).join('')}</div>
        <h3>Membres</h3>
        <div class="cf-membres">${lignes || '<p class="pr-vide">Aucun membre.</p>'}</div>
        <p class="cf-note">Touche un pseudo pour voir son profil.</p>
        <div class="pr-actions"><button class="pr-btn principal" data-cf="territoire">Voir son territoire</button>${estLeMien
          ? '<button class="pr-btn" data-cf="onglet">Ouvrir l’onglet Clan</button>' : ''}</div>
      </div>
    </div>`;
  quitterFiches('clan');
  if(fermerClanFiche && fermerClanFiche.detacher) fermerClanFiche.detacher();
  fermerClanFiche = ouvrirFenetre(html, () => { clanFicheEnCours = null; fermerClanFiche = null; });
}
document.addEventListener('click', (e) => {
  const fiche = e.target.closest('[data-clan-fiche]');
  if(fiche){ ouvrirFicheClan(fiche.dataset.clanFiche); return; }
  const pr = e.target.closest('[data-cf-profil], [data-tc-profil]');
  if(pr){ ouvrirProfil(pr.dataset.cfProfil || pr.dataset.tcProfil); return; }
  const b = e.target.closest('[data-cf]');
  if(!b || !clanFicheEnCours) return;
  const c = clanFicheEnCours, a = b.dataset.cf;
  if(a === 'fermer'){ if(fermerClanFiche) fermerClanFiche(null); return; }
  if(a === 'onglet'){
    if(fermerClanFiche) fermerClanFiche(null);
    const t = document.querySelector('.tab[data-tab="clan"]'); if(t) t.click();
    return;
  }
  if(a === 'territoire'){
    const moiId = monUidClan || window.__monId;
    joueursSurlignes = new Set(c.membres.map(m => m.joueur_id === moiId ? ID_MOI : m.joueur_id));
    CV.donneesSignature = '';
    if(fermerClanFiche) fermerClanFiche(null);
    const onglet = document.querySelector('.tab[data-tab="territoire"]');
    if(onglet) onglet.click();
    renderMapOverlay();
    demanderDessin();
    const carte = document.getElementById('mapWrap');
    if(carte && carte.scrollIntoView) carte.scrollIntoView({ behavior: 'smooth', block: 'center' });
  }
});

// --- le tchat : les @pseudo deviennent des liens, et « @ » propose les pseudos
const normPseudo = (s) => String(s || '').normalize('NFD').replace(/[̀-ͯ]/g, '').toLowerCase();
let tchatIdx = { cle: '', map: new Map(), liste: [] };
function tchatIndex(){
  const c = clanCache && clanCache.moi && clanCache.moi.clan;
  const cl = Array.isArray(classementDonnees) ? classementDonnees : [];
  const cle = [typeof othersMap !== 'undefined' ? othersMap.size : 0, tchat.pseudos.size, c ? (c.membres || []).length : 0, cl.length, clansCarteVersion].join('|');
  if(tchatIdx.cle === cle) return tchatIdx;
  const map = new Map();
  const ajouter = (id, pseudo, clan) => {
    if(!id || !pseudo) return;
    const k = normPseudo(pseudo);
    if(!map.has(k) || clan) map.set(k, { id, pseudo, clan: !!clan });
  };
  try{ if(typeof othersMap !== 'undefined') for(const e of othersMap.values()) ajouter(e.joueurId, e.pseudo, false); }catch(e){}
  cl.forEach(l => { if(l && l.joueur_id) ajouter(l.joueur_id, l.pseudo, false); });
  for(const [id, p] of tchat.pseudos) ajouter(id, p, true);
  if(c) (c.membres || []).forEach(x => ajouter(x.id, x.pseudo, true));
  const liste = [...map.entries()].sort((a, b) => b[0].length - a[0].length);   // le plus long d'abord : « Jean Pierre » avant « Jean »
  tchatIdx = { cle, map, liste };
  return tchatIdx;
}
const MOT = /[\p{L}\p{N}_]/u;
function tchatTexteHtml(texte, idx){
  const t = String(texte || '');
  if(!t.includes('@') || !idx.liste.length) return { html: echapperTexte(t), moi: false };
  const moiId = window.__monId;
  let html = '', i = 0, moi = false;
  for(let at = t.indexOf('@'); at >= 0; at = t.indexOf('@', at + 1)){
    if(at < i || (at > 0 && MOT.test(t[at - 1]))) continue;   // pas au milieu d'un mot (adresse mail…)
    let trouve = null;
    for(const [k, x] of idx.liste){
      const bout = t.substr(at + 1, x.pseudo.length);
      if(bout.length === x.pseudo.length && normPseudo(bout) === k && !MOT.test(t[at + 1 + x.pseudo.length] || '')){ trouve = x; break; }
    }
    if(!trouve) continue;
    const estMoi = trouve.id === moiId;
    if(estMoi) moi = true;
    html += echapperTexte(t.slice(i, at)) + `<button type="button" class="tc-mention${estMoi ? ' moi' : ''}" data-tc-profil="${echapperTexte(trouve.id)}">@${echapperTexte(trouve.pseudo)}</button>`;
    i = at + 1 + trouve.pseudo.length;
  }
  return { html: html + echapperTexte(t.slice(i)), moi };
}
function tchatSuggerer(champ){
  const box = document.getElementById('tcSuggest');
  if(!box) return;
  const pos = champ.selectionStart == null ? champ.value.length : champ.selectionStart;
  const m = champ.value.slice(0, pos).match(/(^|[^\p{L}\p{N}_])@([^@\n]{0,20})$/u);
  const vider = () => { box.hidden = true; box.innerHTML = ''; };
  if(!m) return vider();
  const frag = normPseudo(m[2]), moiId = window.__monId;
  const cands = [...tchatIndex().map.values()]
    .filter(x => x.id !== moiId && normPseudo(x.pseudo).startsWith(frag))
    .sort((a, b) => (b.clan - a.clan) || a.pseudo.localeCompare(b.pseudo, 'fr')).slice(0, 5);
  if(!cands.length) return vider();
  box.innerHTML = cands.map(x => `<button type="button" data-tc-mention="${echapperTexte(x.pseudo)}">@${echapperTexte(x.pseudo)}${blasonPseudo(x.id)}</button>`).join('');
  box.hidden = false;
}
function tchatInsererMention(pseudo){
  const champ = document.getElementById('tcTexte');
  if(!champ) return;
  const pos = champ.selectionStart == null ? champ.value.length : champ.selectionStart;
  const avant = champ.value.slice(0, pos), apres = champ.value.slice(pos);
  const at = avant.lastIndexOf('@');
  if(at < 0) return;
  const debut = avant.slice(0, at) + '@' + pseudo + ' ';
  champ.value = (debut + apres).slice(0, 300);
  const p = Math.min(debut.length, champ.value.length);
  champ.focus(); try{ champ.setSelectionRange(p, p); }catch(e){}
  const box = document.getElementById('tcSuggest'); if(box){ box.hidden = true; box.innerHTML = ''; }
}
document.addEventListener('input', (e) => { if(e.target && e.target.id === 'tcTexte') tchatSuggerer(e.target); });
document.addEventListener('pointerdown', (e) => {
  const s = e.target.closest && e.target.closest('[data-tc-mention]');
  if(s){ e.preventDefault(); tchatInsererMention(s.dataset.tcMention); }   // le clavier du téléphone reste ouvert
});
document.addEventListener('click', (e) => {
  const s = e.target.closest('[data-tc-mention]');
  if(s && s.isConnected) tchatInsererMention(s.dataset.tcMention);   // au clavier (Entrée sur une suggestion)
});
document.addEventListener('focusout', (e) => {
  if(!e.target || e.target.id !== 'tcTexte') return;
  setTimeout(() => { const b = document.getElementById('tcSuggest'); if(b && document.activeElement !== e.target){ b.hidden = true; b.innerHTML = ''; } }, 200);
});
document.addEventListener('submit', (e) => {
  if(!e.target.closest('#tcForm')) return;
  const b = document.getElementById('tcSuggest'); if(b){ b.hidden = true; b.innerHTML = ''; }
});
