# -*- coding: utf-8 -*-
u"""
patch94 — Bourse et Échange en Terra (saison 2, CACHÉ tant que SAISON2 = false).
SQL : _sql/s2-9-terra-bourse-echange.sql.

Règle décidée le 9 octobre : on ne vend et on n'échange que des DOUBLONS.
En saison 2, Bourse et Échange n'existent qu'en Terra : ils passent sur les
fonctions terra_* dès que SAISON2 = true.

Bourse :
- « Vendre une commune » liste les doublons de la collection Terra
  (« 3 doublons »), avec « Vendre au jeu » (prix de revente Terra) et
  « Mettre en vente » ; une commune en vente affiche son annonce et
  « Retirer ».
- Marché : les annonces Terra, avec l'étiquette « NOUVELLE POUR TOI » sur
  les communes absentes de ma collection.
Échange :
- « Tu donnes » : mes doublons du palier (moins ceux déjà promis) ;
  « Tu reçois » : les doublons des autres joueurs, ceux qui me manquent en
  premier, avec l'étiquette « NOUVELLE POUR TOI ».
- La même commune peut être proposée par plusieurs joueurs : la cible est
  repérée par commune + propriétaire.
Rien ne change en saison 1.
"""
import io, os

ICI = os.path.dirname(os.path.abspath(__file__))
BASE = os.path.dirname(ICI) if os.path.basename(ICI) == '_patchs' else ICI

def lire(n):
    with io.open(os.path.join(BASE, n), encoding='utf-8') as f:
        return f.read()

def ecrire(n, s):
    with io.open(os.path.join(BASE, n), 'w', encoding='utf-8') as f:
        f.write(s)

def rempl(src, avant, apres, etiquette, n_attendu=1):
    n = src.count(avant)
    assert n == n_attendu, u'%s : %d occurrences (attendu %d)' % (etiquette, n, n_attendu)
    return src.replace(avant, apres)

js = lire('app.js')
assert 'marcheTerra' not in js, u'patch94 deja applique'
assert 'ctTerra' in js, u'patch93 doit etre applique avant'

# 1. outils + Bourse : chargement ----------------------------------------------
js = rempl(js, u"""let myListings = new Map();

async function loadBourse(){
  const { data: userData } = await sb.auth.getUser();""", u"""let myListings = new Map();

// patch94 : en saison 2, Bourse et Echange n'existent qu'en Terra et
// travaillent sur les doublons de la collection Terra
const marcheTerra = () => SAISON2;
const TAG_NEUF = '<span class="tg-neuf">NOUVELLE POUR TOI</span>';
const TEXTES_TERRA = {
  bourse: 'Vends tes <b>doublons</b> au jeu ou à d\\'autres joueurs, et achète ceux des autres. Tu gardes toujours un exemplaire de chaque commune.',
  echange: 'Propose un troc à un autre joueur : un de tes <b>doublons</b> contre un des siens, de la même rareté. Tu gardes toujours un exemplaire de chaque commune.',
};
function textesMarche(id){
  const sub = document.querySelector('#panel-' + id + ' .sub');
  if(!sub) return;
  if(sub.dataset.s1 === undefined) sub.dataset.s1 = sub.innerHTML;
  sub.innerHTML = marcheTerra() ? TEXTES_TERRA[id] : sub.dataset.s1;
}
let marcheTerraLignes = [];

async function loadBourseTerra(){
  textesMarche('bourse');
  const joueurRow = await monEtat();
  document.getElementById('soldeValue').textContent = joueurRow ? joueurRow.solde : '—';
  soldeBourse = joueurRow ? joueurRow.solde : null;
  const [m] = await Promise.all([sb.rpc('terra_marche'), terraCharge ? null : chargerCollectionTerra()]);
  if(m.error) console.error(m.error);
  marcheTerraLignes = m.data || [];
  myListings = new Map(marcheTerraLignes.filter(a => a.mienne).map(a => [a.commune_code, a.prix]));
  renderSellableGrid();
  renderMarketGrid(marcheTerraLignes.map(a => ({
    id: a.id, commune_code: a.commune_code, prix: a.prix, joueur_id: a.vendeur, je_l_ai: a.je_l_ai,
    communes: { nom: a.nom, departement: a.departement, tier: a.tier }, joueurs: { pseudo: a.pseudo },
  })), (marcheTerraLignes.find(a => a.mienne) || {}).vendeur || ID_MOI);
}

async function loadBourse(){
  if(marcheTerra()) return loadBourseTerra();
  const { data: userData } = await sb.auth.getUser();""", 'bourse chargement')

# 2. Bourse : mes doublons a vendre ----------------------------------------------
js = rempl(js, u"""  const searchText = sansAccents(searchEl ? searchEl.value.trim() : '');

  let entries = Array.from(collectionMap.values()).sort((a,b) => {""", u"""  const searchText = sansAccents(searchEl ? searchEl.value.trim() : '');
  if(marcheTerra()) return renderVenteTerra(grid, searchText);

  let entries = Array.from(collectionMap.values()).sort((a,b) => {""", 'vente terra')

js = rempl(js, u"""function renderMarketGrid(market, myUid){""", u"""function renderVenteTerra(grid, searchText){
  let entries = [...terraCollection.values()]
    .filter(e => e.exemplaires > 1 || myListings.has(e.code))
    .sort((a, b) => TIERS.indexOf(a.tier) - TIERS.indexOf(b.tier) || b.exemplaires - a.exemplaires || b.pop - a.pop);
  const total = entries.length;
  if(sellFilterTier !== 'tous') entries = entries.filter(e => e.tier.id === sellFilterTier);
  if(searchText) entries = entries.filter(e => correspondRecherche(e.nom, e.dept, searchText));
  if(!total){
    grid.innerHTML = '<p class="collection-empty">Tu n\\'as aucun doublon pour l\\'instant. Ils arrivent en ouvrant des paquets.</p>';
    return;
  }
  if(!entries.length){
    grid.innerHTML = '<p class="collection-empty">Aucun doublon ne correspond à la recherche.</p>';
    return;
  }
  const ligne = (e) => {
    const n = e.exemplaires - 1;
    const prixAnnonce = myListings.get(e.code);
    const actions = prixAnnonce
      ? `<span class="chip-vente">En vente à ${Number(prixAnnonce).toLocaleString('fr-FR')} pts</span>
         <div class="ligne-actions"><button class="btn-p contour" data-action="retirer" data-code="${e.code}">Retirer</button></div>`
      : `<div class="ligne-actions"><button class="btn-p contour" data-action="vendre-jeu" data-code="${e.code}">Vendre au jeu <b>${TERRA_REVENTE[e.tier.id]}</b></button>
         <button class="btn-p or" data-action="mettre-vente" data-code="${e.code}">Mettre en vente</button></div>`;
    return `
      <div class="ligne ${e.tier.id}">
        <div class="ligne-texte">
          <span class="ligne-nom">${echapperTexte(e.nom)}</span>
          <span class="ligne-detail">${DEPT_NAMES[e.dept] ? DEPT_NAMES[e.dept] + ' ' : ''}(${e.dept}), ${e.tier.label.toLowerCase()} · ${n > 0 ? n + ' doublon' + (n > 1 ? 's' : '') : 'plus de doublon'}</span>
        </div>
        ${actions}
      </div>`;
  };
  afficherParLots(grid, entries, ligne, ['terra', sellFilterTier, searchText, entries.length].join('|'));
}

function renderMarketGrid(market, myUid){""", 'vente terra fonction')

# 3. Bourse : marche -------------------------------------------------------------
js = rempl(js, u"""      : `<button class="btn-p or" data-action="acheter" data-code="${a.commune_code}" ${tropCher ? 'disabled title="Solde insuffisant"' : ''}>Acheter</button>`;""",
           u"""      : `<button class="btn-p or" data-action="acheter" data-code="${a.commune_code}"${a.id ? ` data-id="${a.id}"` : ''} ${tropCher ? 'disabled title="Solde insuffisant"' : ''}>Acheter</button>`;""",
           'acheter id')
js = rempl(js, u"""          <span class="ligne-nom">${c.nom}</span>
          <span class="ligne-detail">${DEPT_NAMES[c.departement] ? DEPT_NAMES[c.departement] + ' ' : ''}(${c.departement}), ${tier.label.toLowerCase()}, ${vendeur}</span>""",
           u"""          <span class="ligne-nom">${echapperTexte(c.nom)}${a.je_l_ai === false && !isMine ? TAG_NEUF : ''}</span>
          <span class="ligne-detail">${DEPT_NAMES[c.departement] ? DEPT_NAMES[c.departement] + ' ' : ''}(${c.departement}), ${tier.label.toLowerCase()}, ${vendeur}</span>""",
           'marche tag')

# 4. Bourse : actions ------------------------------------------------------------
js = rempl(js, u"""  btn.disabled = true;
  try{
    if(action === 'vendre-jeu'){""", u"""  btn.disabled = true;
  try{
    if(marcheTerra() && ['vendre-jeu', 'mettre-vente', 'retirer', 'acheter'].includes(action)){
      await actionBourseTerra(action, code, btn);
      return;
    }
    if(action === 'vendre-jeu'){""", 'actions aiguillage')

js = rempl(js, u"""function renderMarketGrid(market, myUid){""", u"""async function actionBourseTerra(action, code, btn){
  const e = terraCollection.get(code);
  if(action === 'vendre-jeu'){
    const { data, error } = await sb.rpc('terra_vendre', { p_code: code, p_n: 1 });
    if(error) throw error;
    const r = data && data[0];
    notifier({ type: 'succes', titre: `Doublon de ${e ? e.nom : 'la commune'} vendu au jeu`, texte: r ? `+${r.gain} pts` : '' });
  } else if(action === 'mettre-vente'){
    const prix = await demanderPrix({ nom: e ? e.nom : 'Cette commune', rachat: e ? TERRA_REVENTE[e.tier.id] : 1 });
    if(!prix){ btn.disabled = false; return; }
    const { error } = await sb.rpc('terra_mettre_en_vente', { p_code: code, p_prix: prix });
    if(error) throw error;
    notifier({ type: 'succes', titre: 'Annonce publiée', texte: `Un doublon de ${e ? e.nom : 'la commune'} est en vente à ${prix.toLocaleString('fr-FR')} pts` });
  } else if(action === 'retirer'){
    const { error } = await sb.rpc('terra_retirer_de_la_vente', { p_code: code });
    if(error) throw error;
    notifier({ type: 'info', titre: 'Annonce retirée', texte: 'Le doublon revient dans ta collection.' });
  } else if(action === 'acheter'){
    const { data, error } = await sb.rpc('terra_acheter', { p_id: Number(btn.dataset.id) });
    if(error) throw error;
    const r = data && data[0];
    notifier({ type: 'succes', titre: r ? `${r.nom} rejoint ta collection` : 'Commune achetée',
               texte: r && r.nouvelle ? 'Nouvelle commune !' : 'Un exemplaire de plus.' });
  }
  terraCharge = false;
  await chargerCollectionTerra();
  await loadBourse();
  loadPackStatus();
}

function renderMarketGrid(market, myUid){""", 'actions terra')

# 5. Echange ---------------------------------------------------------------------
js = rempl(js, u"""async function chargerEchangesEnCours(){
  const { data, error } = await sb.rpc('mes_echanges');""", u"""async function chargerEchangesEnCours(){
  const { data, error } = await sb.rpc(marcheTerra() ? 'terra_mes_echanges' : 'mes_echanges');""", 'mes echanges 1')
js = rempl(js, u"""async function loadBadgeEchanges(){
  const { data, error } = await sb.rpc('mes_echanges');""", u"""async function loadBadgeEchanges(){
  const { data, error } = await sb.rpc(marcheTerra() ? 'terra_mes_echanges' : 'mes_echanges');""", 'mes echanges 2')
js = rempl(js, u"""async function loadEchanges(){
  await chargerEchangesEnCours();""", u"""async function loadEchanges(){
  textesMarche('echange');
  if(marcheTerra() && !terraCharge) await chargerCollectionTerra();
  await chargerEchangesEnCours();""", 'load echanges')

js = rempl(js, u"""          <b>${echapperTexte(e.je_recois_nom)}</b>
          <small>(${echapperTexte(e.je_recois_dept)})</small>""", u"""          <b>${echapperTexte(e.je_recois_nom)}</b>
          <small>(${echapperTexte(e.je_recois_dept)})</small>${e.nouvelle === true ? TAG_NEUF : ''}""", 'ligne neuf')

js = rempl(js, u"""  const engagees = new Set((echangesEnCours || []).map(e => e.je_donne_code));

  const duPalier = [...collectionMap.values()]""", u"""  const engagees = new Set((echangesEnCours || []).map(e => e.je_donne_code));
  if(marcheTerra()) return renderEchangeMienTerra(zone, rechercheM);

  const duPalier = [...collectionMap.values()]""", 'mien aiguillage')

js = rempl(js, u"""async function chargerCiblesEchange(){""", u"""// Terra : mes doublons du palier, moins ceux deja promis dans mes
// propositions envoyees (le serveur applique la meme regle)
function renderEchangeMienTerra(zone, rechercheM){
  const promis = {};
  for(const e of echangesEnCours || []) if(e.sens === 'envoye') promis[e.je_donne_code] = (promis[e.je_donne_code] || 0) + 1;
  const duPalier = [...terraCollection.values()]
    .filter(c => c.tier.id === echangeTier && c.exemplaires > 1);
  const miennes = duPalier
    .map(c => Object.assign({}, c, { libres: c.exemplaires - 1 - (promis[c.code] || 0) }))
    .filter(c => c.libres > 0)
    .filter(c => correspondRecherche(c.nom, c.dept, rechercheM))
    .sort((a, b) => a.nom.localeCompare(b.nom, 'fr'));
  if(!miennes.length){
    zone.innerHTML = rechercheM
      ? '<p class="collection-empty">Aucun de tes doublons ne correspond à cette recherche.</p>'
      : (duPalier.length
         ? '<p class="collection-empty">Tous tes doublons de cette rareté sont déjà promis dans une proposition.</p>'
         : '<p class="collection-empty">Tu n\\'as aucun doublon de cette rareté.</p>');
    echangeMien = null;
    majResumeEchange();
    return;
  }
  if(echangeMien && !miennes.some(c => c.code === echangeMien)) echangeMien = null;
  zone.innerHTML = miennes.map(c => `
    <button class="ech-item ${echangeTier} ${echangeMien === c.code ? 'choisi' : ''}" data-mien="${echapperTexte(c.code)}">
      <b>${echapperTexte(c.nom)}</b>
      <small>${echapperTexte(c.dept)} · ${c.libres} doublon${c.libres > 1 ? 's' : ''}</small>
    </button>`).join('');
  majResumeEchange();
}
const cleCible = (c) => c.commune_code + '|' + (c.proprietaire || '');

async function chargerCiblesEchange(){""", 'mien terra')

js = rempl(js, u"""  const { data, error } = await sb.rpc('cibles_echange', {""",
           u"""  const { data, error } = await sb.rpc(marcheTerra() ? 'terra_cibles_echange' : 'cibles_echange', {""", 'cibles rpc')
js = rempl(js, u"""  if(echangeCible && !echangeCibles.some(c => c.commune_code === echangeCible.commune_code)) echangeCible = null;

  zone.innerHTML = echangeCibles.map(c => `
    <button class="ech-item ${echangeTier} ${echangeCible && echangeCible.commune_code === c.commune_code ? 'choisi' : ''}" data-cible="${echapperTexte(c.commune_code)}">
      <b>${echapperTexte(c.nom)}</b>""", u"""  if(echangeCible && !echangeCibles.some(c => cleCible(c) === cleCible(echangeCible))) echangeCible = null;

  zone.innerHTML = echangeCibles.map(c => `
    <button class="ech-item ${echangeTier} ${echangeCible && cleCible(echangeCible) === cleCible(c) ? 'choisi' : ''}" data-cible="${echapperTexte(cleCible(c))}">
      <b>${echapperTexte(c.nom)}${c.nouvelle === true ? TAG_NEUF : ''}</b>""", 'cibles rendu')
js = rempl(js, u"""  const c = echangeCibles.find(x => x.commune_code === b.dataset.cible);
  echangeCible = (echangeCible && echangeCible.commune_code === b.dataset.cible) ? null : c;""",
           u"""  const c = echangeCibles.find(x => cleCible(x) === b.dataset.cible);
  echangeCible = (echangeCible && cleCible(echangeCible) === b.dataset.cible) ? null : c;""", 'cibles clic')

js = rempl(js, u"""  const mienne = collectionMap.get(echangeMien);
  const commission = COMMISSION_ECHANGE[echangeTier] || 1;""", u"""  const mienne = (marcheTerra() ? terraCollection : collectionMap).get(echangeMien);
  const commission = COMMISSION_ECHANGE[echangeTier] || 1;""", 'resume')

js = rempl(js, u"""    const { data, error } = await sb.rpc('proposer_echange', {
      p_ma_commune: echangeMien, p_sa_commune: echangeCible.commune_code
    });""", u"""    const { data, error } = marcheTerra()
      ? await sb.rpc('terra_proposer_echange', {
          p_ma_commune: echangeMien, p_sa_commune: echangeCible.commune_code, p_autre: echangeCible.proprietaire })
      : await sb.rpc('proposer_echange', {
          p_ma_commune: echangeMien, p_sa_commune: echangeCible.commune_code
        });""", 'proposer')

js = rempl(js, u"""      const { data, error } = await sb.rpc('accepter_echange', { p_id: Number(accepter.dataset.accepter) });
      if(error) throw error;
      const r = data && data[0];
      notifier({ type: 'succes', titre: 'Échange conclu', texte: r ? r.message : '' });
      await loadMyCollection();
      await loadOthersPossessions();""", u"""      const { data, error } = await sb.rpc(marcheTerra() ? 'terra_accepter_echange' : 'accepter_echange', { p_id: Number(accepter.dataset.accepter) });
      if(error) throw error;
      const r = data && data[0];
      notifier({ type: 'succes', titre: 'Échange conclu', texte: r ? r.message + (r.nouvelle ? ' — nouvelle commune !' : '') : '' });
      if(marcheTerra()){ terraCharge = false; await chargerCollectionTerra(); }
      else { await loadMyCollection(); await loadOthersPossessions(); }""", 'accepter')
js = rempl(js, u"""      const { data, error } = await sb.rpc('refuser_echange', { p_id: Number(refuser.dataset.refuser) });""",
           u"""      const { data, error } = await sb.rpc(marcheTerra() ? 'terra_refuser_echange' : 'refuser_echange', { p_id: Number(refuser.dataset.refuser) });""", 'refuser')

ecrire('app.js', js)

css = lire('style.css')
assert '.tg-neuf' not in css
css += u"""
/* patch94 : commune absente de ma collection Terra (Bourse, Echange) */
.tg-neuf{ display:inline-block; margin-left:7px; padding:2px 7px; border-radius:999px; background:#35B97E; color:#0B2A1D;
  font-size:.56rem; font-weight:800; letter-spacing:.05em; vertical-align:2px; white-space:nowrap; }
.ech-face > .tg-neuf{ align-self:flex-start; margin:4px 0 0; color:#0B2A1D; font-size:.56rem; }
"""
ecrire('style.css', css)
print(u'patch94 applique')
