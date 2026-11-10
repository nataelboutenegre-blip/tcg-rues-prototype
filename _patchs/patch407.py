# patch407 (10/11/2026) : le paquet Terra suisse (saison 3), éteint tant que la Suisse ne l'est pas (SUISSE, patch330)
#  - Tirage (Terra) : choix « France | Suisse » au-dessus du paquet, retenu (localStorage tf-terra-pays) ;
#    paquet suisse (croix, « Paquet Suisse », bande rouge « 5 communes de Suisse ») ; terra_ouvrir_paquet(p_pays 'CH') (s3-8) ;
#  - cartes suisses (révélation, collection Terra, collection du Front) : badge « Suisse », liseré rouge, « Rang suisse » ;
#    fiche de la carte : « Rang en Suisse » ;
#  - Collection (Terra, Mes cartes) : choix « France | Suisse » (tf-coll-pays), grille, filtres et progression du pays choisi
#    (totaux suisses 27 / 218 / 652 / 953 / 260), compteur des deux pays ; le bloc des doublons reste pour toute la collection ;
#  - collectionMetro ne compte plus les communes suisses (compteur et pourcentage de Ma France) ;
#  - Ma France : départements touchés et complets sans les cantons (la carte montre les cantons, comme avant).
import sys, os
def rep(chemin, avant, apres, nb=1):
    t = open(chemin, encoding='utf-8').read()
    n = t.count(avant)
    if n != nb: sys.exit(f'{chemin} : {n} au lieu de {nb} pour {avant[:70]!r}')
    open(chemin, 'w', encoding='utf-8').write(t.replace(avant, apres))
A, C = 'app.js', 'style.css'
ICI = os.path.dirname(os.path.abspath(__file__))
if 'patch407 : le paquet Terra suisse' in open(A, encoding='utf-8').read(): sys.exit('déjà appliqué')

# --- Tirage : le paquet payé, le choix, l'habillage
rep(A, """async function payerPaquet(type){
""", """async function payerPaquet(type){
  tpPaquetPaye = null;   // patch407
""")
rep(A, """    const { data, error } = await briRpcPaquet('terra_ouvrir_paquet', { p_paye: type === 'achete' });   // patch269""",
"""    const { data, error } = await briRpcPaquet('terra_ouvrir_paquet', tpArgs({ p_paye: type === 'achete' }));   // patch269, patch407 : le pays""")
rep(A, """  const pack = makePackEl(type);
  sceneOuverture(zone).echelle.appendChild(pack);
  appelerPaquet(pack);   // patch124 : le paquet non ouvert appelle aussi""",
"""  const pack = makePackEl(type);
  if(enTerra()) tpHabiller(pack, tpPaquetPaye);   // patch407
  sceneOuverture(zone).echelle.appendChild(pack);
  appelerPaquet(pack);   // patch124 : le paquet non ouvert appelle aussi""")
rep(A, """  const pack = makePackEl(type);
  pack.dataset.pret = '1';""",
"""  const pack = makePackEl(type);
  pack.dataset.pret = '1';
  if(enTerra()) tpHabiller(pack, tpPays());   // patch407""")
rep(A, """  renderRoue();   // patch343
  renderZoneDepart();   // patch348
}""", """  renderRoue();   // patch343
  renderZoneDepart();   // patch348
  tpRendre();   // patch407
}""")

# --- les cartes suisses
rep(A, """(estOutremerCode(draw.code) ? ' outremer' : '') + bxg.cls""", """(estOutremerCode(draw.code) ? ' outremer' : '') + (estSuisseCode(draw.code) ? ' suisse' : '') + bxg.cls""")
rep(A, """<div class="carte-art">${estOutremerCode(draw.code) ? OM_BADGE : ''}""", """<div class="carte-art">${estOutremerCode(draw.code) ? OM_BADGE : estSuisseCode(draw.code) ? chBadge(false) : ''}""")
rep(A, """<div><span>${estOutremerCode(draw.code) ? 'Rang outre-mer' : 'Rang'}</span>""", """<div><span>${estOutremerCode(draw.code) ? 'Rang outre-mer' : estSuisseCode(draw.code) ? 'Rang suisse' : 'Rang'}</span>""")
rep(A, """<div class="mini ${e.tier.id}${au ? ' aurore' : ''}${estOutremerCode(e.code) ? ' outremer' : ''}""", """<div class="mini ${e.tier.id}${au ? ' aurore' : ''}${estOutremerCode(e.code) ? ' outremer' : ''}${estSuisseCode(e.code) ? ' suisse' : ''}""")
rep(A, """<div class="mini-art">${estOutremerCode(e.code) ? OM_BADGE_MINI : ''}""", """<div class="mini-art">${estOutremerCode(e.code) ? OM_BADGE_MINI : estSuisseCode(e.code) ? chBadge(true) : ''}""")
rep(A, """    <div class="mini ${entry.tier.id}${auroreFront(entry.code) ? ' aurore' : ''}""", """    <div class="mini ${entry.tier.id}${auroreFront(entry.code) ? ' aurore' : ''}${estSuisseCode(entry.code) ? ' suisse' : ''}""")
rep(A, """        <div class="mini-art">${artCommune(entry, entry.tier.id)}""", """        <div class="mini-art">${estSuisseCode(entry.code) ? chBadge(true) : ''}${artCommune(entry, entry.tier.id)}""")
rep(A, """lignes.push([estOutremerCode(code) ? 'Rang outre-mer' : 'Rang national',""", """lignes.push([estOutremerCode(code) ? 'Rang outre-mer' : estSuisseCode(code) ? 'Rang en Suisse' : 'Rang national',""")

# --- la collection : le pays choisi
rep(A, """function renderCollectionTerra(){
  const el = document.getElementById('terraColl');
  if(!el) return;
  const parTier = {};
  for(const e of terraCollection.values()) parTier[e.tier.id] = (parTier[e.tier.id] || 0) + 1;""",
"""function renderCollectionTerra(){
  const el = document.getElementById('terraColl');
  if(!el) return;
  const tcVue = tcVueCollection();   // patch407 : les cartes du pays choisi
  const parTier = {};
  for(const e of tcVue.values()) parTier[e.tier.id] = (parTier[e.tier.id] || 0) + 1;""")
rep(A, """  for(const e of terraCollection.values()) if(!estOutremer(e.dept)) parTierM[e.tier.id] = (parTierM[e.tier.id] || 0) + 1;
  const tot = totauxPaliers || {};""",
"""  for(const e of tcVue.values()) if(!estOutremer(e.dept)) parTierM[e.tier.id] = (parTierM[e.tier.id] || 0) + 1;
  const tot = totauxPaliers || {};
  const totV = SUISSE && tcPays() === 'CH' ? tcTotauxSuisse() : tot;   // patch407""")
rep(A, """  let nbAur = 0; for(const e of terraCollection.values()) if(e.aurore > 0) nbAur++;   // patch236""",
"""  let nbAur = 0; for(const e of tcVue.values()) if(e.aurore > 0) nbAur++;   // patch236""")
rep(A, """  let nbBri = 0; for(const e of terraCollection.values()) if(e.brillantes > 0 || e.eclat) nbBri++;   // patch269""",
"""  let nbBri = 0; for(const e of tcVue.values()) if(e.brillantes > 0 || e.eclat) nbBri++;   // patch269""")
rep(A, """  let nbEvt = 0; for(const e of terraCollection.values()) if(estCarteEvenement(e)) nbEvt++;   // patch282""",
"""  let nbEvt = 0; for(const e of tcVue.values()) if(estCarteEvenement(e)) nbEvt++;   // patch282""")
rep(A, """  const ordre = TIERS.filter(t => tot[t.id] || parTier[t.id]);""", """  const ordre = TIERS.filter(t => totV[t.id] || parTier[t.id]);""")
rep(A, """    <div class="coll-ligne-titre"><h1>Collection</h1>${compteurCollectionHtml(totalFrance)}</div>
    ${selecteurVueTerra()}
    <div class="tc-prog\"""",
"""    <div class="coll-ligne-titre"><h1>Collection</h1>${SUISSE ? tcCompteurHtml(totalFrance) : compteurCollectionHtml(totalFrance)}</div>
    ${selecteurVueTerra()}${SUISSE ? tpSelecteurHtml(tcPays(), true) : ''}
    <div class="tc-prog\"""")
rep(A, """      const n = parTierM[t.id] || 0, total = tot[t.id] ? Number(tot[t.id].total) : 0;""",
"""      const n = parTierM[t.id] || 0, total = totV[t.id] ? Number(totV[t.id].total) : 0;""")
rep(A, """data-tcf="tous">Toutes <span class="nb">${fmtNombre(terraCollection.size)}</span></button>""",
"""data-tcf="tous">Toutes <span class="nb">${fmtNombre(tcVue.size)}</span></button>""")
rep(A, """Doublons${terraFiltre === 'doublons' ? (terraDblCroissant ? ' ↑' : ' ↓') : ''} <span class="nb">${fmtNombre(nbDbl)}</span></button>""",
"""Doublons${terraFiltre === 'doublons' ? (terraDblCroissant ? ' ↑' : ' ↓') : ''} <span class="nb">${fmtNombre(SUISSE ? tcDoublonsVue(tcVue) : nbDbl)}</span></button>""")
rep(A, """id="tcRecherche" class="bourse-search coll-recherche" placeholder="Rechercher une commune ou un département…\"""",
"""id="tcRecherche" class="bourse-search coll-recherche" placeholder="${SUISSE && tcPays() === 'CH' ? 'Rechercher une commune ou un canton…' : 'Rechercher une commune ou un département…'}\"""")
rep(A, """    .filter(e => correspondRecherche(e.nom, e.dept, sansAccents(terraRecherche.trim())))
    .sort((a, b) => (terraFiltre === 'doublons'""",
"""    .filter(e => !SUISSE || estSuisseCode(e.code) === (tcPays() === 'CH'))   // patch407 : le pays choisi
    .filter(e => correspondRecherche(e.nom, e.dept, sansAccents(terraRecherche.trim())))
    .sort((a, b) => (terraFiltre === 'doublons'""")
rep(A, """    : `<p class="collection-empty">${terraCollection.size ? 'Aucune commune ne correspond.' : 'Ta collection Terra est vide : ouvre un paquet dans l’onglet Tirage.'}</p>`;""",
"""    : `<p class="collection-empty">${SUISSE && tcPays() === 'CH' && ![...terraCollection.keys()].some(estSuisseCode) ? 'Pas encore de commune suisse : choisis le paquet Suisse dans l’onglet Tirage.' : terraCollection.size ? 'Aucune commune ne correspond.' : 'Ta collection Terra est vide : ouvre un paquet dans l’onglet Tirage.'}</p>`;   // patch407""")
rep(A, """function clicCollectionTerra(e){
  if(clicCollections(e)) return;   // patch112""",
"""function clicCollectionTerra(e){
  const pz = e.target.closest('[data-tcp]');   // patch407 : France | Suisse
  if(pz){ tcChoisirPays(pz.dataset.tcp); return; }
  if(clicCollections(e)) return;   // patch112""")
rep(A, """  for(const e of terraCollection.values()) if(!estOutremer(e.dept)) n++;
  return n;""", """  for(const e of terraCollection.values()) if(!estOutremer(e.dept) && !estSuisseCode(e.code)) n++;   // patch407 : sans la Suisse
  return n;""")

# --- Ma France : les compteurs restent français (la carte montre déjà les cantons, patch330)
rep(A, """  const touches = Object.keys(MF.parDep).filter(d => COMMUNES_PAR_DEPT[d]).length;
  const complets = Object.keys(MF.parDep).filter(d => COMMUNES_PAR_DEPT[d] && MF.parDep[d] >= COMMUNES_PAR_DEPT[d]).length;
  const nbDepts = Object.keys(COMMUNES_PAR_DEPT).length;""",
"""  const touches = Object.keys(MF.parDep).filter(d => COMMUNES_PAR_DEPT[d] && !estCanton(d)).length;   // patch407 : sans les cantons
  const complets = Object.keys(MF.parDep).filter(d => COMMUNES_PAR_DEPT[d] && !estCanton(d) && MF.parDep[d] >= COMMUNES_PAR_DEPT[d]).length;
  const nbDepts = Object.keys(COMMUNES_PAR_DEPT).filter(d => !estCanton(d)).length;""")

open(A, 'a', encoding='utf-8').write(open(os.path.join(ICI, 'patch407-suisse.js'), encoding='utf-8').read())
open(C, 'a', encoding='utf-8').write(open(os.path.join(ICI, 'patch407-suisse.css'), encoding='utf-8').read())
print('patch407 OK')
