# -*- coding: utf-8 -*-
u"""
patch190 — la carte en grand : inclinee fort sur un cote, elle ne montrait
plus que son cadre (dore pour une legendaire). Cause : content-visibility:auto
sur .mini (optimisation de la grille de la collection) ; en 3D le navigateur
croit le contenu hors champ et ne le dessine plus. Desactive pour la carte
en grand seulement. Aucun SQL.
"""
import io, os
ICI = os.path.dirname(os.path.abspath(__file__))
BASE = os.path.dirname(ICI) if os.path.basename(ICI) == '_patchs' else ICI
def lire(n):
    with io.open(os.path.join(BASE, n), encoding='utf-8') as f: return f.read()
def ecrire(n, s):
    with io.open(os.path.join(BASE, n), 'w', encoding='utf-8') as f: f.write(s)
css = lire('style.css')
avant = u""".c3d-base > .mini{ width: 100%; height: 100%; }"""
apres = u""".c3d-base > .mini{ width: 100%; height: 100%; content-visibility: visible; contain: none; }   /* patch190 */"""
assert 'patch190' not in css, u'patch190 deja applique'
assert css.count(avant) == 1, u'%d occurrences (attendu 1)' % css.count(avant)
ecrire('style.css', css.replace(avant, apres))
print(u'patch190 applique. Lancer : python3 maj-version.py')
