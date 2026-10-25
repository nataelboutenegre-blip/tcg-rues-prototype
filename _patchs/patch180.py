# -*- coding: utf-8 -*-
u"""
patch180 — deux vitrines sur le profil : Terra et Front (idée du 25 octobre).
Un onglet en haut de la vitrine passe de l'une à l'autre. Chacune a 20 places.
La vitrine Front montre les communes qu'on tient : si on t'en prend une,
elle quitte la vitrine d'elle-même. Demande _sql/s2-24-vitrine-front.sql
(sans lui, le site marche comme avant, et la vitrine Front refuse
d'enregistrer).
La recherche du choix ignore aussi les accents (Heric trouve Héric).
"""
import io, os
ICI = os.path.dirname(os.path.abspath(__file__))
BASE = os.path.dirname(ICI) if os.path.basename(ICI) == '_patchs' else ICI
def lire(n):
    with io.open(os.path.join(BASE, n), encoding='utf-8') as f: return f.read()
def ecrire(n, s):
    with io.open(os.path.join(BASE, n), 'w', encoding='utf-8') as f: f.write(s)
def rempl(src, avant, apres, etiquette):
    n = src.count(avant)
    assert n == 1, u'%s : %d occurrences (attendu 1)' % (etiquette, n)
    return src.replace(avant, apres)
js = lire('app.js'); css = lire('style.css')
assert 'patch180' not in js

# la lecture garde la source de chaque carte
js = rempl(js, u"""    exemplaires: 1, rank: r.rang, tierSize: r.palier_total, aurore: r.aurore ? 1 : 0, auroreS1: s1.has(r.code), photo: photos.get(r.code) || '' }));""",
u"""    exemplaires: 1, rank: r.rang, tierSize: r.palier_total, aurore: r.aurore ? 1 : 0,
    source: r.source === 'front' ? 'front' : 'terra',   // patch180
    auroreS1: r.source !== 'front' && s1.has(r.code), photo: photos.get(r.code) || '' }));""", 'lecture')

# le bloc du profil : onglets Terra / Front
js = rempl(js, u"""function blocVitrine(cartes, moi){
  if(!SAISON2 || (!cartes.length && !moi)) return '';
  const cases = [];""",
u"""// patch180 : deux vitrines, Terra et Front. L'onglet choisi est retenu.
let vitrineVue = 'terra';
const vitrineBlocs = new Map();
let vitrineBlocN = 0;
const vitrineDe = (cartes, source) => (cartes || []).filter(c => (c.source || 'terra') === source);
function blocVitrine(toutes, moi){
  if(!SAISON2 || (!toutes.length && !moi)) return '';
  const id = ++vitrineBlocN;
  vitrineBlocs.set(id, { toutes, moi });
  if(vitrineBlocs.size > 30) vitrineBlocs.delete(vitrineBlocs.keys().next().value);
  const nT = vitrineDe(toutes, 'terra').length, nF = vitrineDe(toutes, 'front').length;
  let vue = vitrineVue;
  // chez un autre joueur, on ne montre pas une vitrine vide si l'autre est remplie
  if(!moi && vue === 'terra' && !nT && nF) vue = 'front';
  if(!moi && vue === 'front' && !nF && nT) vue = 'terra';
  const cartes = vitrineDe(toutes, vue);
  const onglet = (s, nom, n) => `<button type="button" role="tab" class="vt-onglet${vue === s ? ' actif' : ''}" aria-selected="${vue === s}" data-vt-onglet="${s}" data-vt-bloc="${id}">${nom}<span>${n}</span></button>`;
  const onglets = (moi || (nT && nF)) ? `<div class="vt-onglets" role="tablist">${onglet('terra', 'Terra', nT)}${onglet('front', 'Front', nF)}</div>` : '';
  const aide = vue === 'front'
    ? `Expose jusqu'à ${VITRINE_MAX} communes que tu tiens dans le Front. Si on t'en prend une, elle quitte ta vitrine.`
    : `Expose jusqu'à ${VITRINE_MAX} cartes de ta collection Terra : tout le monde les verra sur ton profil.`;
  const cases = [];""", 'bloc debut')
js = rempl(js, u"""  return `<div class="vt-bloc">
      <div class="vt-titre"><h3>Vitrine</h3>${lien}</div>
      <div class="vt-etagere${cartes.length ? ' cliquable' : ''}"${cartes.length ? ' data-vt-voir' : ''}>${cases.join('')}</div>
      ${moi && !cartes.length ? `<p class="vt-aide">Expose jusqu'à ${VITRINE_MAX} cartes de ta collection : tout le monde les verra sur ton profil.</p>` : ''}
    </div>`;
}""",
u"""  return `<div class="vt-bloc" data-vt-source="${vue}">
      <div class="vt-titre"><h3>Vitrine</h3>${onglets}${lien}</div>
      <div class="vt-etagere${cartes.length ? ' cliquable' : ''}"${cartes.length ? ' data-vt-voir' : ''}>${cases.join('')}</div>
      ${moi && !cartes.length ? `<p class="vt-aide">${aide}</p>` : ''}
    </div>`;
}
const sourceVitrine = (el) => { const b = el && el.closest('.vt-bloc'); return b && b.dataset.vtSource === 'front' ? 'front' : 'terra'; };
document.addEventListener('click', (e) => {
  const o = e.target.closest('[data-vt-onglet]');
  if(!o) return;
  vitrineVue = o.dataset.vtOnglet === 'front' ? 'front' : 'terra';
  const d = vitrineBlocs.get(Number(o.dataset.vtBloc));
  const bloc = o.closest('.vt-bloc');
  if(d && bloc) bloc.outerHTML = blocVitrine(d.toutes, d.moi);
});""", 'bloc fin')

# la grande vitrine : son titre dit laquelle
js = rempl(js, u"""function ouvrirGrandeVitrine(cartes, moi, pseudo, apres){
  const vides = moi ? VITRINE_MAX - cartes.length : 0;""",
u"""function ouvrirGrandeVitrine(cartes, moi, pseudo, apres, source){
  const vides = moi ? VITRINE_MAX - cartes.length : 0;""", 'grande')
js = rempl(js, u"""      <p class="vt-surtitre">Vitrine</p>
      <h2 id="vtgTitre">""", u"""      <p class="vt-surtitre">Vitrine ${source === 'front' ? 'Front' : 'Terra'}</p>
      <h2 id="vtgTitre">""", 'grande titre')

# depuis la fiche d'un joueur
js = rempl(js, u"""  const p = profilEnCours;
  const cartes = p.vitrine || [];
  if(fermerProfil) fermerProfil(null);
  setTimeout(() => {
    if(modif){ ouvrirChoixVitrine(cartes, 'fiche'); return; }
    ouvrirGrandeVitrine(cartes, !!p.est_moi, p.pseudo, (v) => {
      if(v === 'modifier') setTimeout(() => ouvrirChoixVitrine(cartes, 'fiche'), 200);
      else setTimeout(() => { profilEnCours = p; rendreProfil(); }, 200);
    });
  }, 200);""",
u"""  const p = profilEnCours;
  const cartes = p.vitrine || [];
  const src = sourceVitrine(voir || modif);
  if(fermerProfil) fermerProfil(null);
  setTimeout(() => {
    if(modif){ ouvrirChoixVitrine(cartes, 'fiche', src); return; }
    ouvrirGrandeVitrine(vitrineDe(cartes, src), !!p.est_moi, p.pseudo, (v) => {
      if(v === 'modifier') setTimeout(() => ouvrirChoixVitrine(cartes, 'fiche', src), 200);
      else setTimeout(() => { profilEnCours = p; rendreProfil(); }, 200);
    }, src);
  }, 200);""", 'fiche joueur')

# depuis le panneau Profil
js = rempl(js, u"""  const vt = (profilPanneau || {}).vitrine || [];
  if(e.target.closest('[data-pr="vitrine"]')) ouvrirChoixVitrine(vt, 'panneau');
  if(e.target.closest('[data-vt-voir]')) ouvrirGrandeVitrine(vt, true, (profilPanneau || {}).pseudo, (v) => {
    if(v === 'modifier') setTimeout(() => ouvrirChoixVitrine(vt, 'panneau'), 200);
  });""",
u"""  const vt = (profilPanneau || {}).vitrine || [];
  const src = sourceVitrine(e.target);
  if(e.target.closest('[data-pr="vitrine"]')) ouvrirChoixVitrine(vt, 'panneau', src);
  if(e.target.closest('[data-vt-voir]')) ouvrirGrandeVitrine(vitrineDe(vt, src), true, (profilPanneau || {}).pseudo, (v) => {
    if(v === 'modifier') setTimeout(() => ouvrirChoixVitrine(vt, 'panneau', src), 200);
  }, src);""", 'panneau')

# le choix : Terra ou Front
js = rempl(js, u"""async function ouvrirChoixVitrine(actuelle, retour){
  if(!terraCharge) await chargerCollectionTerra();
  let choix = actuelle.map(c => c.code).filter(code => terraCollection.has(code));
  let recherche = '';
  const rangTier = (t) => TIERS.findIndex(x => x.id === t.id);
  const toutes = [...terraCollection.values()].sort((a, b) =>""",
u"""async function ouvrirChoixVitrine(actuelle, retour, source){
  const front = source === 'front';   // patch180
  if(!front && !terraCharge) await chargerCollectionTerra();
  const reserve = front
    ? new Map([...collectionMap.values()].map(e => [e.code, { ...e, exemplaires: 1, aurore: AURORE && AURORE[e.code] ? 1 : 0 }]))
    : terraCollection;
  let choix = vitrineDe(actuelle, front ? 'front' : 'terra').map(c => c.code).filter(code => reserve.has(code));
  let recherche = '';
  const rangTier = (t) => TIERS.findIndex(x => x.id === t.id);
  const toutes = [...reserve.values()].sort((a, b) =>""", 'choix debut')
js = rempl(js, u"""      <h2 id="vtTitre">Ma vitrine</h2>
      <p class="vt-aide">Choisis jusqu'à ${VITRINE_MAX} cartes, dans l'ordre où tu veux les montrer : les ${VITRINE_FICHE} premières s'affichent sur ton profil. Touche une carte de la vitrine pour la retirer.</p>""",
u"""      <h2 id="vtTitre">Ma vitrine ${front ? 'Front' : 'Terra'}</h2>
      <p class="vt-aide">Choisis jusqu'à ${VITRINE_MAX} cartes, dans l'ordre où tu veux les montrer : les ${VITRINE_FICHE} premières s'affichent sur ton profil. Touche une carte de la vitrine pour la retirer.${front ? ' Si on te prend une commune, elle quitte ta vitrine.' : ''}</p>""", 'choix titre')
js = rempl(js, u"""      const c = choix[i] && terraCollection.get(choix[i]);""", u"""      const c = choix[i] && reserve.get(choix[i]);""", 'choix case')
js = rempl(js, u"""    const liste = toutes.filter(c => !q || c.nom.toLowerCase().includes(q) || c.dept === dep || c.dept.toLowerCase() === q).slice(0, 150);""",
u"""    const qs = sansAccents(recherche.trim());
    const liste = toutes.filter(c => !q || correspondRecherche(c.nom, c.dept, qs) || c.dept === dep).slice(0, 150);""", 'choix recherche')
js = rempl(js, u"""    const { error } = await sb.rpc('terra_vitrine_definir', { p_codes: choix });""",
u"""    const { error } = await sb.rpc(front ? 'terra_vitrine_definir_front' : 'terra_vitrine_definir', { p_codes: choix });""", 'choix rpc')

# Personnaliser : le compte ne parle que de la vitrine Terra
js = rempl(js, u"""    grVitrine = r.error ? null : (r.data || []).length;""",
u"""    grVitrine = r.error ? null : (r.data || []).filter(x => x.source !== 'front').length;""", 'garde-robe')

css += u"""
/* patch180 : les onglets Terra / Front de la vitrine */
.vt-titre{ gap:10px; align-items:center; }
.vt-titre h3{ margin-right:auto; }
.vt-onglets{ display:inline-flex; gap:2px; padding:2px; border-radius:999px; background:rgba(255,255,255,.07); margin-bottom:9px; }
.vt-onglet{ font:inherit; font-size:.74rem; font-weight:600; color:var(--brume); background:none; border:0; border-radius:999px; padding:4px 11px; cursor:pointer; display:inline-flex; gap:5px; align-items:baseline; }
.vt-onglet span{ font-size:.66rem; opacity:.7; font-weight:500; }
.vt-onglet.actif{ background:var(--c-legendaire); color:var(--encre); }
.vt-onglet.actif span{ opacity:.75; }
.vt-titre .vt-modifier{ margin-left:0; }
"""
ecrire('app.js', js); ecrire('style.css', css)
print(u'patch180 appliqué')
