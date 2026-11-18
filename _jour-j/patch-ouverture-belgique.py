# Ouverture de la Belgique — le jeu (à lancer JUSTE APRÈS _sql/s3-32-belgique-entree.sql).
#  - la Belgique s'allume dans le jeu et sur la carte en direct (BELGIQUE_OUVERTE, patch462) ;
#  - AURORE_V '1' -> '2' : sinon les téléphones gardent l'ancien data/aurore.json (sans les 51 Aurore belges) ;
#  - direct.js?v=N -> N+1 (sinon les navigateurs gardent l'ancien fichier) ;
#  - « Source : Statbel » dans les mentions légales (licence CC BY 4.0 : obligatoire).
# Ensuite : python3 maj-version.py, puis commit de app.js + index.html + version.json + direct/
# + mentions-legales.html, puis push. La ligne de la cloche (data/nouveautes.json) : à écrire le jour même.
import os, re, sys
ARGS = [x for x in sys.argv[1:] if not x.startswith('--')]
R = ARGS[0] if ARGS else '.'
# --sans-direct-v : appelé par patch-jour-j-s3.py le 22/11, qui monte déjà direct.js?v=5 -> 6 dans le même envoi
SANS_V = '--sans-direct-v' in sys.argv
def rep(f, a, b):
    p = os.path.join(R, f); t = open(p, encoding='utf-8').read()
    if b in t and a not in t: print(f'{f} : déjà fait'); return
    assert t.count(a) == 1, (f, a, t.count(a))
    open(p, 'w', encoding='utf-8').write(t.replace(a, b)); print(f'{f} : ok')

rep('app.js', 'const BELGIQUE_OUVERTE = false;', 'const BELGIQUE_OUVERTE = true;')
rep('app.js', "const AURORE_V = '1';", "const AURORE_V = '2';")
deja = 'const BELGIQUE_OUVERTE = true;' in open(os.path.join(R, 'direct/direct.js'), encoding='utf-8').read()
rep('direct/direct.js', 'const BELGIQUE_OUVERTE = false;', 'const BELGIQUE_OUVERTE = true;')
for f in (() if (deja or SANS_V) else ('direct/index.html', 'direct/tiktok.html')):   # une seule fois
    p = os.path.join(R, f); t = open(p, encoding='utf-8').read()
    m = re.search(r'direct\.js\?v=(\d+)', t)
    if m:
        t = t.replace(m.group(0), f'direct.js?v={int(m.group(1)) + 1}')
        open(p, 'w', encoding='utf-8').write(t); print(f'{f} : direct.js?v={int(m.group(1)) + 1}')

ML = 'mentions-legales.html'
if 'Statbel' not in open(os.path.join(R, ML), encoding='utf-8').read():
    rep(ML, '<p>Les photos de monuments proviennent de Wikimedia Commons',
        '<p>Belgique : communes, contours et population au 1<sup>er</sup> janvier 2025, source : '
        '<a href="https://statbel.fgov.be/fr" rel="noopener">Statbel</a> (Direction générale Statistique, Statistics Belgium), '
        'sous licence <a href="https://creativecommons.org/licenses/by/4.0/deed.fr" rel="noopener">CC BY 4.0</a> ; '
        'secteurs statistiques regroupés par commune et contours simplifiés par TerraFront.</p>\n'
        '<p>Les photos de monuments proviennent de Wikimedia Commons')
else:
    print(f'{ML} : déjà fait')
