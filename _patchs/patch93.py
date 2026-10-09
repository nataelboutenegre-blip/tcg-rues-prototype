# -*- coding: utf-8 -*-
u"""
patch93 — le Contrat en Terra (saison 2, CACHÉ tant que SAISON2 = false).
SQL : _sql/s2-8-terra-contrat.sql (terra_contrat_candidates,
terra_signer_contrat).

- En Terra, l'onglet Contrat travaille sur les DOUBLONS de la collection
  Terra : 10 doublons d'un palier -> 1 commune du palier au-dessus. On garde
  toujours un exemplaire de chaque commune ; une commune avec 5 doublons peut
  fournir 5 lignes du lot.
- La commune reçue est une commune que le joueur n'a pas encore (tant qu'il
  en reste dans le palier).
- Pas de liste « ne jamais sacrifier » ni de cadenas en Terra (rien ne peut
  être perdu), pas d'alerte monument, pas de « Voir sur la carte ».
- Collection Terra : un bouton « Contrat » à côté de « Vendre… » dès
  10 doublons d'un palier qui a un contrat.
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
assert 'ctTerra' not in js, u'patch93 deja applique'

# 1. outils ------------------------------------------------------------------
js = rempl(js, u"let contratSautes = 0;\n", u"""let contratSautes = 0;

// patch93 : en Terra, le contrat se fait sur les doublons de la collection
// Terra. Une ligne du lot = un exemplaire en trop ; une commune avec quatre
// doublons peut donc fournir quatre lignes. On garde toujours un exemplaire.
const ctTerra = () => enTerra();
function ctDeplier(rows){
  const out = [];
  for(const r of rows){
    const n = Math.max(0, Number(r.dispo) || 0);
    for(let k = 0; k < n; k++) out.push(Object.assign({}, r, { cle: r.commune_code + '#' + k }));
  }
  return out;
}
function ctTextes(){
  const sub = document.querySelector('#panel-contrat .sub');
  if(sub){
    if(sub.dataset.s1 === undefined) sub.dataset.s1 = sub.innerHTML;
    sub.innerHTML = ctTerra()
      ? 'Échange dix <b>doublons</b> contre une commune d\\'un palier au-dessus. Tu gardes toujours au moins un exemplaire de chaque commune, et tu reçois une commune que tu n\\'as <b>pas encore</b>, tirée au hasard.'
      : sub.dataset.s1;
  }
  const excl = document.getElementById('ctExcl');
  if(excl && ctTerra()) excl.hidden = true;
}
""", 'outils')

# 2. chargement --------------------------------------------------------------
js = rempl(js, u"""  if(!document.getElementById('ctTaux')) return;
  try{
    const res = await Promise.all(CONTRATS.map(c =>
      sb.rpc('contrat_candidates', { p_tier: c.de })));
    if(res.some(r => r.error)) throw res.find(r => r.error).error;
    contratDispo = {};
    CONTRATS.forEach((c, i) => { contratDispo[c.de] = res[i].data || []; });
""", u"""  if(!document.getElementById('ctTaux')) return;
  ctTextes();
  try{
    const terra = ctTerra();
    const res = await Promise.all(CONTRATS.map(c =>
      sb.rpc(terra ? 'terra_contrat_candidates' : 'contrat_candidates', { p_tier: c.de })));
    if(res.some(r => r.error)) throw res.find(r => r.error).error;
    contratDispo = {};
    CONTRATS.forEach((c, i) => {
      const rows = res[i].data || [];
      contratDispo[c.de] = terra ? ctDeplier(rows) : rows;
    });
""", 'chargement')

js = rempl(js, u"""async function loadContratEtExclusions(){
  const ok""", u"""async function loadContratEtExclusions(){
  // en Terra rien ne peut etre perdu : pas de liste d'exclusions
  if(ctTerra()){ await loadContrat(); return; }
  const ok""", 'exclusions')

# 3. remplacer une ligne -----------------------------------------------------
js = rempl(js, u"""  const toutes = contratDispo[contratChoisi.de] || [];
  const pris = new Set(contratLot.map(x => x.commune_code));
""", u"""  const terra = ctTerra();
  const unites = contratDispo[contratChoisi.de] || [];
  // en Terra, une ligne par commune dans la liste ; elle est « deja dans le
  // lot » quand tous ses doublons y sont
  const toutes = terra ? unites.filter(x => x.cle.endsWith('#0')) : unites;
  const dansLot = (code) => contratLot.filter(x => x.commune_code === code).length;
  const pris = new Set(terra
    ? toutes.filter(x => dansLot(x.commune_code) >= x.dispo).map(x => x.commune_code)
    : contratLot.map(x => x.commune_code));
""", 'changer pris')
js = rempl(js, u"""    const choisie = toutes.find(x => x.commune_code === b.dataset.code);
""", u"""    const choisie = terra
      ? unites.find(u => u.commune_code === b.dataset.code
          && !contratLot.some(l => l !== actuelle && l.cle === u.cle))
      : toutes.find(x => x.commune_code === b.dataset.code);
""", 'changer choix')

# la ligne : population + doublons en Terra, pas d'alerte monument
js = rempl(js, u"""${ctNb(x.population || 0)} hab.${monumentsNoms.has(x.commune_code) ?""",
           u"""${ctNb(x.population || 0)} hab.${ctTerra() ? ` · ${x.dispo} doublon${x.dispo > 1 ? 's' : ''}` : ''}${!ctTerra() && monumentsNoms.has(x.commune_code) ?""",
           'ligne hb', 2)

# 4. affichage ---------------------------------------------------------------
js = rempl(js, u"""      <b>${c.n} ${libelleTier(c.de).toLowerCase()}s → 1 ${libelleTier(c.vers).toLowerCase()}</b>""",
           u"""      <b>${c.n} ${ctTerra() ? 'doublons ' : ''}${libelleTier(c.de).toLowerCase()}s → 1 ${libelleTier(c.vers).toLowerCase()}</b>""",
           'taux')
js = rempl(js, u"""      vide.textContent = 'Il te faut au moins 10 communes d\\'un même palier, hors favoris, '""",
           u"""      vide.textContent = ctTerra()
        ? 'Il te faut au moins 10 doublons d\\'un même palier (commun ou peu commun). Les doublons arrivent en ouvrant des paquets.'
        : 'Il te faut au moins 10 communes d\\'un même palier, hors favoris, '""",
           'vide')
js = rempl(js, u"""  document.getElementById('ctInfo').textContent =
    `${contratChoisi.n} communes, les moins peuplées — favoris`""",
           u"""  document.getElementById('ctInfo').textContent = ctTerra()
    ? `${contratChoisi.n} doublons, les plus nombreux d'abord`
    : `${contratChoisi.n} communes, les moins peuplées — favoris`""",
           'info')
js = rempl(js, u"""      <button class="ct-cadenas" data-ct-exclure="${echapperTexte(x.commune_code)}" title="Ne plus jamais proposer ${echapperTexte(x.nom || x.commune_code)}">${ICONE_CADENAS}</button>
""", u"""      ${ctTerra() ? '' : `<button class="ct-cadenas" data-ct-exclure="${echapperTexte(x.commune_code)}" title="Ne plus jamais proposer ${echapperTexte(x.nom || x.commune_code)}">${ICONE_CADENAS}</button>`}
""", 'cadenas')
js = rempl(js, u"""  if(avert) avert.textContent =
    `Les ${contratChoisi.n} communes sacrifiées retournent au pot. C'est définitif.`""",
           u"""  if(avert) avert.textContent = ctTerra()
    ? `Les ${contratChoisi.n} doublons sont échangés, c'est définitif. Tu gardes au moins un exemplaire de chaque commune.`
    : `Les ${contratChoisi.n} communes sacrifiées retournent au pot. C'est définitif.`""",
           'avert')

js = rempl(js, u"""  const c = CONTRATS.find(x => (parTier[x.de] || 0) >= x.n);
  if(!c){ bloc.hidden = true; return; }""", u"""  const c = CONTRATS.find(x => (parTier[x.de] || 0) >= x.n);
  if(!c || ctTerra()){ bloc.hidden = true; return; }""", 'rappel')

# 5. signature ---------------------------------------------------------------
js = rempl(js, u"""    const { data, error } = await sb.rpc('signer_contrat',
      { p_codes: codes, p_vers: c.vers });""", u"""    const { data, error } = await sb.rpc(ctTerra() ? 'terra_signer_contrat' : 'signer_contrat',
      { p_codes: codes, p_vers: c.vers });""", 'signer')
js = rempl(js, u"""  let decor = [];
  try{
    const { data } = await sb.rpc('contrat_defile',""", u"""  let decor = [];
  // Terra : le serveur renvoie le decor avec la carte
  if(carte && Array.isArray(carte.decor)) decor = carte.decor;
  else try{
    const { data } = await sb.rpc('contrat_defile',""", 'decor')

js = rempl(js, u"""    if(txt) txt.textContent = `${libelleTier(c.vers).toLowerCase()} — `
      + `${c.n} communes sont retournées au pot. Celle-ci est à toi.`;""",
           u"""    if(txt) txt.textContent = `${libelleTier(c.vers).toLowerCase()} — ` + (ctTerra()
      ? (carte.nouvelle === false
          ? `${c.n} doublons échangés. Tu l'avais déjà : un exemplaire de plus.`
          : `${c.n} doublons échangés. Nouvelle dans ta collection !`)
      : `${c.n} communes sont retournées au pot. Celle-ci est à toi.`);""",
           'revelation')
js = rempl(js, u"""  const sauter = document.getElementById('ctSauter');
  let minuteur = null;
""", u"""  const sauter = document.getElementById('ctSauter');
  let minuteur = null;
  // Terra : la commune n'est pas sur la carte du Front
  if(ctTerra()){
    const bc = document.querySelector('#fenetre [data-ct="carte"]');
    if(bc) bc.remove();
  }
""", 'pas de carte')

js = rempl(js, u"""  await loadMyCollection();
  await loadContrat();
  if(carte && carte.nom){
    notifier({ type: 'succes', titre: 'Contrat honoré',
      texte: `${carte.nom} rejoint ta collection.` });
    if(carte.code) annoncerMonument(carte.code, carte.nom);
  }""", u"""  const terra = ctTerra();
  if(terra){ terraCharge = false; await chargerCollectionTerra(); }
  else await loadMyCollection();
  await loadContrat();
  if(carte && carte.nom){
    notifier({ type: 'succes', titre: 'Contrat honoré',
      texte: `${carte.nom} rejoint ta collection${terra ? ' Terra' : ''}.` });
    if(carte.code && !terra) annoncerMonument(carte.code, carte.nom);
  }""", 'terminer')

# 6. Collection Terra : raccourci vers le contrat -------------------------------
js = rempl(js, u"""<span><b>${fmtNombre(nbDbl)} doublon${nbDbl > 1 ? 's' : ''}</b> · jusqu'à ${fmtNombre(gainMax)} pts</span><button data-tc="vendre">Vendre…</button></div>""",
           u"""<span><b>${fmtNombre(nbDbl)} doublon${nbDbl > 1 ? 's' : ''}</b> · jusqu'à ${fmtNombre(gainMax)} pts</span><button data-tc="vendre">Vendre…</button>${CONTRATS.some(c => (dbl[c.de] || 0) >= c.n) ? '<button class="tc-ct" data-tc="contrat">Contrat</button>' : ''}</div>""",
           'raccourci')
js = rempl(js, u"""  if(b.dataset.tc === 'vendre') ouvrirVenteTerra();
}""", u"""  if(b.dataset.tc === 'vendre') ouvrirVenteTerra();
  if(b.dataset.tc === 'contrat'){
    const onglet = document.querySelector('.tab[data-tab="contrat"]');
    if(onglet) onglet.click();
  }
}""", 'raccourci clic')

ecrire('app.js', js)

css = lire('style.css')
assert '.tc-vente button.tc-ct' not in css
css = rempl(css, u".tc-vente b{ color:#5FD39D; }\n", u""".tc-vente b{ color:#5FD39D; }
.tc-vente button.tc-ct{ margin-left:0; background:transparent; color:#5FD39D; box-shadow:inset 0 0 0 1.5px #35B97E; }
""", 'css')
ecrire('style.css', css)
print(u'patch93 applique')
