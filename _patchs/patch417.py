# patch417 (11/11/2026) : « Mes points », le détail de mon score du Front (idée d'Oshannir)
# Toucher sa propre ligne du classement du Front ouvre la fiche « Mes points » (avant : son profil, qui reste
# à un bouton de la fiche) ; « Mes points » aussi sous la légende, à côté de « Comment c'est calculé ? ».
# Cartes par rareté, victoires, départements avec leur palier, régions, bâtiments, bombes, rébellions.
# Lu par s2-137 (mon_score_detail) : mêmes calculs que le classement, pour le joueur connecté seulement.
import sys
def rep(chemin, avant, apres, nb=1):
    t = open(chemin, encoding='utf-8').read()
    n = t.count(avant)
    if n != nb: sys.exit(f'{chemin} : {n} au lieu de {nb} pour {avant[:70]!r}')
    open(chemin, 'w', encoding='utf-8').write(t.replace(avant, apres))
A, C = 'app.js', 'style.css'
if 'patch417' in open(A, encoding='utf-8').read(): sys.exit('déjà appliqué')
rep(A, """  const ligne = e.target.closest('[data-joueur-id]');
  if(ligne) ouvrirProfil(ligne.dataset.joueurId);
});""", """  const ligne = e.target.closest('[data-joueur-id]');
  if(ligne && SAISON2 && classementMode === 'general' && ligne.classList.contains('moi')){ ouvrirMesPoints(ligne.dataset.joueurId); return; }   // patch417
  if(ligne) ouvrirProfil(ligne.dataset.joueurId);
});""")
rep(A, """  const bouton = `<button type="button" class="cl-calc-btn" data-cl-calc aria-expanded="${clCalcOuvert}">${clCalcOuvert ? 'Masquer le calcul' : 'Comment c’est calculé ?'}</button>`;""",
"""  const bouton = '<span class="cl-calc-btns">'   // patch417 : « Mes points » et « Comment c'est calculé ? » ensemble
    + (quoi === 'front' && classementDonnees.some(l => l.est_moi) ? '<button type="button" class="cl-calc-btn" data-mp-ouvrir>Mes points</button>' : '')
    + `<button type="button" class="cl-calc-btn" data-cl-calc aria-expanded="${clCalcOuvert}">${clCalcOuvert ? 'Masquer le calcul' : 'Comment c’est calculé ?'}</button></span>`;""")
open(A, 'a', encoding='utf-8').write(open('_patchs/patch417-points.js', encoding='utf-8').read())
open(C, 'a', encoding='utf-8').write(open('_patchs/patch417-points.css', encoding='utf-8').read())
print('patch417 OK')
