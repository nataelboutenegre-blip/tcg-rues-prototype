# Ouverture du Luxembourg — le jeu (à lancer JUSTE APRÈS _sql/s3-35-luxembourg-entree.sql).
#  - le Luxembourg s'allume dans le jeu et sur la carte en direct (LUXEMBOURG_OUVERT, patch467) ;
#  - direct.js?v=N -> N+1 (sinon les navigateurs gardent l'ancien fichier), sauf --sans-direct-v ;
#  - les sources dans les mentions légales (ACT, CC0 ; registre national RNPP).
#  Pas d'Aurore luxembourgeoises : AURORE_V ne bouge pas ici.
# Le 22/11, patch-jour-j-s3.py l'appelle avec --sans-direct-v (il monte déjà direct.js?v dans le même envoi).
import os, re, sys
ARGS = [x for x in sys.argv[1:] if not x.startswith('--')]
R = ARGS[0] if ARGS else '.'
SANS_V = '--sans-direct-v' in sys.argv
def rep(f, a, b):
    p = os.path.join(R, f); t = open(p, encoding='utf-8').read()
    if b in t and a not in t: print(f'{f} : déjà fait'); return
    assert t.count(a) == 1, (f, a, t.count(a))
    open(p, 'w', encoding='utf-8').write(t.replace(a, b)); print(f'{f} : ok')

rep('app.js', 'const LUXEMBOURG_OUVERT = false;', 'const LUXEMBOURG_OUVERT = true;')
deja = 'const LUXEMBOURG_OUVERT = true;' in open(os.path.join(R, 'direct/direct.js'), encoding='utf-8').read()
rep('direct/direct.js', 'const LUXEMBOURG_OUVERT = false;', 'const LUXEMBOURG_OUVERT = true;')
for f in (() if (deja or SANS_V) else ('direct/index.html', 'direct/tiktok.html')):
    p = os.path.join(R, f); t = open(p, encoding='utf-8').read()
    m = re.search(r'direct\.js\?v=(\d+)', t)
    if m:
        t = t.replace(m.group(0), f'direct.js?v={int(m.group(1)) + 1}')
        open(p, 'w', encoding='utf-8').write(t); print(f'{f} : direct.js?v={int(m.group(1)) + 1}')

ML = 'mentions-legales.html'
if 'cadastre et de la topographie' not in open(os.path.join(R, ML), encoding='utf-8').read():
    rep(ML, '<p>Les photos de monuments proviennent de Wikimedia Commons',
        '<p>Luxembourg : contours des communes et des cantons, source : Administration du cadastre et de la topographie '
        '(<a href="https://data.public.lu/fr/datasets/limites-administratives-du-grand-duche-de-luxembourg/" rel="noopener">data.public.lu</a>, '
        'CC0), contours simplifiés par TerraFront ; population par commune : Registre national des personnes physiques '
        '(Centre des technologies de l’information de l’État, <a href="https://data.public.lu/" rel="noopener">data.public.lu</a>, octobre 2026).</p>\n'
        '<p>Les photos de monuments proviennent de Wikimedia Commons')
else:
    print(f'{ML} : déjà fait')
