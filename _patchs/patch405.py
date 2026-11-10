# patch405 (10-11/11/2026) : le siège dans le jeu (saison 3), éteint tant que le serveur ne l'allume pas
# (siege_actif, s3-7). « ?siege=test » l'allume dans l'interface seulement (banc, aperçu).
#  - la fiche de siège (feuille) à la place de la fiche d'attaque et des assauts depuis la liste ;
#  - Défendre : les sièges contre moi, Renforcer, Garnison, Laisser filer ;
#  - Attaquer : mes sièges en cours au-dessus des cibles ; l'engagement et le tri par chances cachés.
import sys, os
def rep(chemin, avant, apres, nb=1):
    t = open(chemin, encoding='utf-8').read()
    n = t.count(avant)
    if n != nb: sys.exit(f'{chemin} : {n} au lieu de {nb} pour {avant[:70]!r}')
    open(chemin, 'w', encoding='utf-8').write(t.replace(avant, apres))
A, C = 'app.js', 'style.css'
ICI = os.path.dirname(os.path.abspath(__file__))

rep(A, """async function majEnergie(){
  if(!SAISON2) return;""",
"""async function majEnergie(){
  if(!SAISON2) return;
  if(!sgLu) sgChargerActif();   // patch405 : le siège est-il allumé ?""")

rep(A, """async function ouvrirAttaque(code){
  const el = document.getElementById('mapPanneau');""",
"""async function ouvrirAttaque(code){
  if(SIEGE){ ouvrirSiege(code); return; }   // patch405 : la fiche de siège
  const el = document.getElementById('mapPanneau');""")

rep(A, """    } else if(action === 'attaquer'){
      // bloque le rafraichissement auto de la grille pendant l'attaque en cours""",
"""    } else if(action === 'assieger' || (action === 'attaquer' && SIEGE)){   // patch405
      btn.disabled = false;
      ouvrirSiege(code);
      return;
    } else if(action === 'attaquer'){
      // bloque le rafraichissement auto de la grille pendant l'attaque en cours""")

rep(A, """    if(etatClasse === 'pret'){
      bouton = `<button class="cible-attaquer ca-att" data-action="attaquer" data-code="${c.commune_code}">Attaquer <span class="ca-pastille"><b>${coutTexte(cout)}</b> · <i>${vrai ? vrai.chances + ' %' : '…'}</i></span></button>`;""",
"""    if(etatClasse === 'pret' && SIEGE){   // patch405 : on assiège, l'énergie dépend de la résistance
      const sgEst = { commun: 8, peucommun: 8, rare: 9, epique: 15, legendaire: 27 }[tier ? tier.id : 'commun'] || 8;
      bouton = `<button class="cible-attaquer ca-att" data-action="assieger" data-code="${c.commune_code}">Assiéger <span class="ca-pastille"><b>≈ ${sgEst} ⚡</b></span></button>`;
    } else if(etatClasse === 'pret'){
      bouton = `<button class="cible-attaquer ca-att" data-action="attaquer" data-code="${c.commune_code}">Attaquer <span class="ca-pastille"><b>${coutTexte(cout)}</b> · <i>${vrai ? vrai.chances + ' %' : '…'}</i></span></button>`;""")

rep(A, """async function loadMenaces(){
  await chargerDefPrio();""",
"""async function loadMenaces(){
  if(SIEGE){ await loadMenacesSiege(); return; }   // patch405
  await chargerDefPrio();""")

rep(A, """async function loadCombat(){
  const { data: userData } = await sb.auth.getUser();""",
"""async function loadCombat(){
  if(SIEGE) sgChargerMes();   // patch405
  const { data: userData } = await sb.auth.getUser();""")

rep(A, """  const blocDanger = danger.length""", """  let blocDanger = danger.length""")
rep(A, """    : `<div class="mfo-t mfo-calme"><i>✓</i><span>Aucune de tes communes n'est attaquée.</span></div>`;""",
"""    : `<div class="mfo-t mfo-calme"><i>✓</i><span>Aucune de tes communes n'est attaquée.</span></div>`;
  if(SIEGE) blocDanger = sgMfoDanger();   // patch405""")
rep(A, """  const blocAtt = `<div class="mfo-t"><div class="mfo-h"><span>⚔ Mes attaques en cours</span>""",
"""  let blocAtt = `<div class="mfo-t"><div class="mfo-h"><span>⚔ Mes attaques en cours</span>""")
rep(A, """      : '<p class="mfo-p">Aucune attaque en cours. <button type="button" class="mfo-lien" data-mfo="attaquer">Choisir une cible ›</button></p>'}</div>`;""",
"""      : '<p class="mfo-p">Aucune attaque en cours. <button type="button" class="mfo-lien" data-mfo="attaquer">Choisir une cible ›</button></p>'}</div>`;
  if(SIEGE) blocAtt = sgMfoAttaques();   // patch405""")

t = open(A, encoding='utf-8').read()
if 'patch405 : le siège (saison 3, s3-7)' in t: sys.exit('déjà appliqué')
open(A, 'a', encoding='utf-8').write(open(os.path.join(ICI, 'patch405-siege.js'), encoding='utf-8').read())
open(C, 'a', encoding='utf-8').write(open(os.path.join(ICI, 'patch405-siege.css'), encoding='utf-8').read())
print('patch405 OK')
