# -*- coding: utf-8 -*-
u"""
patch181 — la bande du choix de vitrine commence à la place 1.
Elle héritait du centrage de l'étagère : avec 20 places plus larges que
l'écran, les premières places sortaient à gauche, hors de portée du défilement.
"""
import io, os
ICI = os.path.dirname(os.path.abspath(__file__))
BASE = os.path.dirname(ICI) if os.path.basename(ICI) == '_patchs' else ICI
p = os.path.join(BASE, 'style.css')
with io.open(p, encoding='utf-8') as f: css = f.read()
assert 'patch181' not in css
css += u"""
/* patch181 : la bande du choix de vitrine part de la place 1 */
.vt-etagere.vt-bande{ justify-content:flex-start; }
"""
with io.open(p, 'w', encoding='utf-8') as f: f.write(css)
print(u'patch181 appliqué')
