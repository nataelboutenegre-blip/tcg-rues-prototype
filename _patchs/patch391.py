# patch391 (9/11/2026) : roue du Front, 50 tours par jour (s2-130). Règles et repli du jeu.
import sys
def rep(chemin, avant, apres, nb=1):
    t = open(chemin, encoding='utf-8').read()
    n = t.count(avant)
    if n != nb: sys.exit(f'{chemin} : {n} au lieu de {nb} pour {avant[:60]!r}')
    open(chemin, 'w', encoding='utf-8').write(t.replace(avant, apres))
rep('index.html', '<b>30 tours par jour</b> au plus', '<b>50 tours par jour</b> au plus')
rep('index.html', 'ne compte pas dans les 30. Les chances', 'ne compte pas dans les 50. Les chances')
rep('app.js', "hors des ${Number(ROUE && ROUE.par_jour) || 30} du jour", "hors des ${Number(ROUE && ROUE.par_jour) || 50} du jour")
print('patch391 ok')
