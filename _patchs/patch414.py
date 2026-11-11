# patch414 (11/11/2026) : la Suisse, restes du jeu et carte en direct (éteint tant que SUISSE_OUVERTE vaut false)
# Jeu (app.js) :
#  - « Jura » dans une recherche : le département 39 ET le canton du Jura (avant : seulement le 39 ;
#    un mot qui vise un seul département, comme « Doubs », ne change pas). Les exclusions de contrat restent françaises.
#  - la bulle d'un numéro de département : pour un canton, la carte de la Suisse avec le canton en or
#    (avant : pas de carte, seulement le nom) ;
#  - « dans le canton de Vaud (VD) », « du Valais », « des Grisons » (bombes) ; « canton » au lieu de « département »
#    dans le message de la bombe préparée et dans la sourdine de la cloche.
# Carte en direct (direct/direct.js, aussi utilisée par tiktok.html) : même interrupteur (SUISSE_OUVERTE, ?suisse=test) :
#  cadre élargi vers l'est, cantons et communes suisses, lacs, frontière suisse plus marquée, noms des cantons
#  (fil, recherche), bouton « Tout », pied « Les 37 000 communes de France et de Suisse ».
# Rien ne change avec la Suisse éteinte.
import sys, os
def rep(chemin, avant, apres, nb=1):
    t = open(chemin, encoding='utf-8').read()
    n = t.count(avant)
    if n != nb: sys.exit(f'{chemin} : {n} au lieu de {nb} pour {avant[:70]!r}')
    open(chemin, 'w', encoding='utf-8').write(t.replace(avant, apres))
A, DJ = 'app.js', 'direct/direct.js'
if 'patch414' in open(A, encoding='utf-8').read(): sys.exit('déjà appliqué')

# ---------- jeu ----------
# 1. Jura
rep(A, """  // « Jura » : le département 39 passe avant le canton (les clés numériques viennent d'abord)
  const exact = codes.find(c => noms(c).includes(t));
  if(exact) return exact;""",
"""  // « Jura » : le département 39 passe avant le canton (les clés numériques viennent d'abord)
  // patch414 : et les recherches prennent les deux (codesDepartements)
  const exacts = codes.filter(c => noms(c).includes(t));
  if(exacts.length > 1) codeDepartement.plusieurs = exacts;
  if(exacts.length) return exacts[0];""")
rep(A, """  return un ? [un] : plusieurs.length ? plusieurs : departementsRegion(texte);""",
"""  return plusieurs.length > 1 ? plusieurs : un ? [un] : plusieurs.length ? plusieurs : departementsRegion(texte);   // patch414 : « jura » = 39 et JU""")
rep(A, """  { const ks = codesDepartements(saisi);   // patch368 : « corse » = 2A et 2B ; patch369 : une région""",
"""  { const ks = codesDepartements(saisi).filter(k => !estCanton(k));   // patch368 : « corse » = 2A et 2B ; patch369 : une région ; patch414 : pas de canton (contrats français)""")

# 2. la bulle d'un canton
rep(A, """var depChemins = null, depCheminsP = null, depBulle = null, depBulleCible = null;
function depCheminsCharger(){
  if(depChemins) return Promise.resolve(depChemins);
  if(!depCheminsP) depCheminsP = fetch('contours-departements.json', { cache: 'force-cache' }).then(r => r.json()).then(C => {
    const k = Math.cos(46.5 * Math.PI / 180);
    let x0 = 1e9, x1 = -1e9, y0 = 1e9, y1 = -1e9;
    Object.values(C).forEach(rs => rs.forEach(r => r.forEach(p => { const x = p[0] * k, y = -p[1]; if(x < x0) x0 = x; if(x > x1) x1 = x; if(y < y0) y0 = y; if(y > y1) y1 = y; })));
    const e = 190 / Math.max(x1 - x0, y1 - y0), ox = (200 - (x1 - x0) * e) / 2, oy = (200 - (y1 - y0) * e) / 2;
    depChemins = {};
    Object.keys(C).forEach(d => {
      depChemins[d] = C[d].map(r => 'M' + r.map(p => ((p[0] * k - x0) * e + ox).toFixed(1) + ' ' + ((-p[1] - y0) * e + oy).toFixed(1)).join('L') + 'Z').join('');
    });
    return depChemins;
  }).catch(() => { depCheminsP = null; return null; });
  return depCheminsP;
}""", """var depChemins = null, depCheminsP = null, depBulle = null, depBulleCible = null;
var depCheminsCH = null, depCheminsCHP = null, depCheminsCHHaut = 200;   // patch414 : les cantons, sur la carte de la Suisse
// carre : la France tient dans 200 × 200 ; sinon (la Suisse, plus large que haute) 200 de large et la hauteur qu'il faut
function depCheminsTracer(C, carre){
  const k = Math.cos(46.5 * Math.PI / 180);
  let x0 = 1e9, x1 = -1e9, y0 = 1e9, y1 = -1e9;
  Object.values(C).forEach(rs => rs.forEach(r => r.forEach(p => { const x = p[0] * k, y = -p[1]; if(x < x0) x0 = x; if(x > x1) x1 = x; if(y < y0) y0 = y; if(y > y1) y1 = y; })));
  const e = 190 / Math.max(x1 - x0, y1 - y0), ox = (200 - (x1 - x0) * e) / 2, oy = carre ? (200 - (y1 - y0) * e) / 2 : 5;
  if(!carre) depCheminsCHHaut = Math.ceil((y1 - y0) * e + 10);
  const out = {};
  Object.keys(C).forEach(d => {
    out[d] = C[d].map(r => 'M' + r.map(p => ((p[0] * k - x0) * e + ox).toFixed(1) + ' ' + ((-p[1] - y0) * e + oy).toFixed(1)).join('L') + 'Z').join('');
  });
  return out;
}
function depCheminsCharger(suisse){
  if(suisse){
    if(depCheminsCH) return Promise.resolve(depCheminsCH);
    if(!depCheminsCHP) depCheminsCHP = fetch('data/contours-cantons.json?v=1', { cache: 'force-cache' }).then(r => r.json())
      .then(C => (depCheminsCH = depCheminsTracer(C, false))).catch(() => { depCheminsCHP = null; return null; });
    return depCheminsCHP;
  }
  if(depChemins) return Promise.resolve(depChemins);
  if(!depCheminsP) depCheminsP = fetch('contours-departements.json', { cache: 'force-cache' }).then(r => r.json())
    .then(C => (depChemins = depCheminsTracer(C, true))).catch(() => { depCheminsP = null; return null; });
  return depCheminsP;
}""")
rep(A, """  const C = await depCheminsCharger();
  if(depBulleCible !== b) return;
  const carte = C && C[d] ? `<svg viewBox="0 0 200 200" aria-hidden="true">""",
"""  const ch = estCanton(d), C = await depCheminsCharger(ch);   // patch414
  if(depBulleCible !== b) return;
  const carte = C && C[d] ? `<svg viewBox="0 0 200 ${ch ? depCheminsCHHaut : 200}" aria-hidden="true">""")

# 3. les mots
rep(A, """const dansDept = (d) => `dans le ${d}${DEPT_NAMES && DEPT_NAMES[d] ? ' (' + DEPT_NAMES[d] + ')' : ''}`;""",
"""// patch414 : un canton : « dans le canton de Vaud (VD) », « du Valais », « des Grisons », « d’Argovie »
const CANTON_DE = { VS: 'du Valais', TI: 'du Tessin', JU: 'du Jura', GR: 'des Grisons' };
const cantonDe = (d) => CANTON_DE[d] || (/^[AEIOUÉ]/i.test(CANTONS[d] || '') ? 'd’' : 'de ') + (CANTONS[d] || d);
const motDep = (d) => estCanton(d) ? 'canton' : 'département';
const dansDept = (d) => estCanton(d) ? `dans le canton ${cantonDe(d)} (${d})`
  : `dans le ${d}${DEPT_NAMES && DEPT_NAMES[d] ? ' (' + DEPT_NAMES[d] + ')' : ''}`;""")
rep(A, """Tout le monde sait qu’une bombe se prépare dans ton département.` });""",
"""Tout le monde sait qu’une bombe se prépare dans ton ${motDep(BATIMENTS && BATIMENTS.centre && BATIMENTS.centre.dept)}.` });   // patch414""")
rep(A, """<b>dans tout le département</b>""", """<b>dans tout le ${motDep(d)}</b>""")
rep(A, """texte: 'Tu ne seras plus prévenu des attaques dans ce département. Ça se réactive dans les réglages de la cloche.' });""",
"""texte: `Tu ne seras plus prévenu des attaques dans ce ${motDep(d)}. Ça se réactive dans les réglages de la cloche.` });   // patch414""")

# ---------- carte en direct ----------
rep(DJ, """const VUE = { lon0: -5.25, lon1: 9.65, lat0: 41.3, lat1: 51.15 }, W = 1080, H = 1060;""",
"""// patch414 : la Suisse (saison 3), même interrupteur que le jeu : SUISSE_OUVERTE le jour J, ?suisse=test pour essayer
const SUISSE_OUVERTE = false;
const SUISSE = SUISSE_OUVERTE || /[?&]suisse=test\\b/.test(location.search);
const CANTONS = {"AG":"Argovie","AI":"Appenzell Rhodes-Intérieures","AR":"Appenzell Rhodes-Extérieures","BE":"Berne","BL":"Bâle-Campagne","BS":"Bâle-Ville","FR":"Fribourg","GE":"Genève","GL":"Glaris","GR":"Grisons","JU":"Jura","LU":"Lucerne","NE":"Neuchâtel","NW":"Nidwald","OW":"Obwald","SG":"Saint-Gall","SH":"Schaffhouse","SO":"Soleure","SZ":"Schwytz","TG":"Thurgovie","TI":"Tessin","UR":"Uri","VD":"Vaud","VS":"Valais","ZG":"Zoug","ZH":"Zurich"};
if(SUISSE) Object.assign(DEPT_NAMES, CANTONS);
const VUE = { lon0: -5.25, lon1: SUISSE ? 10.8 : 9.65, lat0: 41.3, lat1: 51.15 }, W = 1080, H = 1060;""")
rep(DJ, """const D = { id: null, cat: null, chemins: new Map(), depBords: [], clans: new Map(),""",
"""const D = { id: null, cat: null, chemins: new Map(), depBords: [], lacs: null, frontiere: null, clans: new Map(),""")
rep(DJ, """  const deps = await fetch('../contours-departements.json', { cache: 'force-cache' }).then((r) => r.json());
  for(const [dep, rings] of Object.entries(deps)){ if(dep.length === 2) D.depBords.push(chemin(rings)); }
  const liste = Object.keys(deps).filter((d) => d.length === 2);""",
"""  const deps = await fetch('../contours-departements.json', { cache: 'force-cache' }).then((r) => r.json());
  for(const [dep, rings] of Object.entries(deps)){ if(dep.length === 2) D.depBords.push(chemin(rings)); }
  const liste = Object.keys(deps).filter((d) => d.length === 2);
  if(SUISSE){   // patch414 : les cantons, les lacs et la frontière
    const lire = (f) => fetch('../data/' + f + '?v=1', { cache: 'force-cache' }).then((r) => r.ok ? r.json() : null).catch(() => null);
    const [cantons, lacs, frontiere] = await Promise.all([lire('contours-cantons.json'), lire('lacs-suisse.json'), lire('suisse-frontiere.json')]);
    for(const [c, rings] of Object.entries(cantons || {})){ D.depBords.push(chemin(rings)); liste.push(c); }
    if(lacs) D.lacs = chemin(lacs);
    if(frontiere) D.frontiere = chemin(frontiere);
  }""")
rep(DJ, """function bords(){
  ctx.strokeStyle = 'rgba(169,188,212,.22)'; ctx.lineWidth = 0.8 / Math.sqrt(VU.k);
  for(const p of D.depBords) ctx.stroke(p);""",
"""function bords(){
  if(D.lacs){ ctx.fillStyle = MER; ctx.fill(D.lacs); }   // patch414 : les lacs par-dessus les communes du bord (Léman)
  ctx.strokeStyle = 'rgba(169,188,212,.22)'; ctx.lineWidth = 0.8 / Math.sqrt(VU.k);
  for(const p of D.depBords) ctx.stroke(p);
  if(D.frontiere){ ctx.strokeStyle = 'rgba(169,188,212,.55)'; ctx.lineWidth = 1.6 / Math.sqrt(VU.k); ctx.stroke(D.frontiere); }""")
rep(DJ, """(async function demarrer(){
  ajuster(); heure();""",
"""(async function demarrer(){
  ajuster(); heure();
  if(SUISSE){   // patch414
    const z = document.getElementById('zFrance'); if(z) z.textContent = 'Tout';
    const p = document.querySelector('.pied span'); if(p) p.textContent = 'Les 37 000 communes de France et de Suisse, à prendre. Gratuit.';
  }""")
for f in ('direct/index.html', 'direct/tiktok.html'):
    rep(f, '<script defer src="direct.js?v=4"></script>', '<script defer src="direct.js?v=5"></script>')
print('patch414 OK')
