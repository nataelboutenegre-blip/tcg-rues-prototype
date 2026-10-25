# -*- coding: utf-8 -*-
u"""
patch169 — vitrine du profil sur grand ecran : les cinq cases prenaient
toute la largeur, la mini-carte s'etirait (nom minuscule, carte vide).
Les cases ne depassent plus 132 px et l'etagere se centre ; le numero de
la carte (n° 79 / 302) revient sur la fiche (toujours cache dans la bande).
"""
import io, os
ICI = os.path.dirname(os.path.abspath(__file__))
BASE = os.path.dirname(ICI) if os.path.basename(ICI) == '_patchs' else ICI
p = os.path.join(BASE, 'style.css')
with io.open(p, encoding='utf-8') as f: css = f.read()
assert 'patch169' not in css, u'patch169 deja applique'
avant = u"  display:grid; grid-template-columns:repeat(5, minmax(0, 1fr)); gap:7px;\n  padding:14px 10px 16px; border-radius:14px;"
assert css.count(avant) == 1
css = css.replace(avant, u"  /* patch169 : des cases de 132 px au plus, centrees */\n  display:grid; grid-template-columns:repeat(5, minmax(0, 132px)); justify-content:center; gap:7px;\n  padding:14px 10px 16px; border-radius:14px;")
with io.open(p, 'w', encoding='utf-8') as f: f.write(css)
print(u'patch169 applique. Lancer : python3 maj-version.py')
