# patch421 (12/11/2026) : « OVNI » sur la carte (Arkhannou, ASMFCB) : une image de l'animation de la bombe restait figée
# quand on touchait la carte pendant l'animation. bfxArreter effaçait le calque avec le repère de la carte encore actif
# (setTransform de bfxDessiner) : de loin, seule une partie du calque était effacée. On remet le repère à zéro avant d'effacer.
import sys
def rep(chemin, avant, apres, nb=1):
    t = open(chemin, encoding='utf-8').read()
    n = t.count(avant)
    if n != nb: sys.exit(f'{chemin} : {n} au lieu de {nb} pour {avant[:70]!r}')
    open(chemin, 'w', encoding='utf-8').write(t.replace(avant, apres))
rep('app.js', """  const c = document.getElementById('mapBombeFx');
  if(c) c.getContext('2d').clearRect(0, 0, c.width, c.height);""",
"""  const c = document.getElementById('mapBombeFx');
  if(c){ const x = c.getContext('2d'); x.setTransform(1, 0, 0, 1, 0, 0); x.clearRect(0, 0, c.width, c.height); }   // patch421 : tout le calque""")
print('patch421 OK')
