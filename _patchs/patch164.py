# -*- coding: utf-8 -*-
u"""
patch164 — le haut du bouton Front (« 40 / 40 énergie ») etait cache dans la
Collection (signale le 25 octobre) : l'en-tete collant de la Collection
remonte de 36 px (marge negative) et passait par-dessus le selecteur
Terra / Front. Le selecteur passe devant (z-index 4 > 3).
"""
import io, os
ICI = os.path.dirname(os.path.abspath(__file__))
BASE = os.path.dirname(ICI) if os.path.basename(ICI) == '_patchs' else ICI
p = os.path.join(BASE, 'style.css')
with io.open(p, encoding='utf-8') as f: css = f.read()
assert 'patch164' not in css, u'patch164 deja applique'
avant = u".mode-bascule{ display:grid; grid-template-columns:1fr 1fr; gap:4px; padding:4px; margin:0 0 16px;"
assert css.count(avant) == 1
css = css.replace(avant, u"/* patch164 : devant l'en-tete collant de la Collection */\n.mode-bascule{ position:relative; z-index:4; display:grid; grid-template-columns:1fr 1fr; gap:4px; padding:4px; margin:0 0 16px;")
with io.open(p, 'w', encoding='utf-8') as f: f.write(css)
print(u'patch164 applique. Lancer : python3 maj-version.py')
