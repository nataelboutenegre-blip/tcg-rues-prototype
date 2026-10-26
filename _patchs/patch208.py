# -*- coding: utf-8 -*-
u"""
patch208 — 1) les contours de la carte changent (communes manquantes ajoutées
par _sql/contours-manquants.py) : CONTOURS_V passe à 4 pour que les
navigateurs rechargent les fichiers ; 2) le sélecteur Mes cartes / Ma France /
Collections / Monuments tient sur un téléphone étroit (il débordait).
Aucun SQL (le monument de Besançon a son propre fichier).
"""
import io, os
ICI = os.path.dirname(os.path.abspath(__file__))
BASE = os.path.dirname(ICI) if os.path.basename(ICI) == '_patchs' else ICI
def lire(n):
    with io.open(os.path.join(BASE, n), encoding='utf-8') as f: return f.read()
def ecrire(n, s):
    with io.open(os.path.join(BASE, n), 'w', encoding='utf-8') as f: f.write(s)

js = lire('app.js')
assert 'patch208' not in js
a = u"const CONTOURS_V = '3';   // patch130 : communes nouvelles"
assert js.count(a) == 1
ecrire('app.js', js.replace(a, u"const CONTOURS_V = '4';   // patch208 : ~160 communes manquantes ajoutées (patch130 : communes nouvelles)"))

css = lire('style.css')
assert 'patch208' not in css
css = css.rstrip('\n') + u"""

/* ---------- patch208 : le sélecteur de la Collection tient sur un téléphone ---------- */
.mf-vue{ max-width: 100%; overflow-x: auto; scrollbar-width: none; }
.mf-vue::-webkit-scrollbar{ display: none; }
.mf-vue button{ flex: none; white-space: nowrap; }
@media (max-width: 460px){
  /* quatre colonnes égales : le texte passe sur deux lignes plutôt que de déborder */
  .mf-vue{ display: grid; grid-template-columns: repeat(4, minmax(0, 1fr)); gap: 2px; padding: 3px; overflow: visible; }
  .mf-vue button{ min-width: 0; white-space: normal; padding: 6px 4px; font-size: .76rem; line-height: 1.15; text-align: center; }
}
@media (max-width: 360px){ .mf-vue button{ padding: 6px 2px; font-size: .7rem; } }
"""
ecrire('style.css', css)
print(u'patch208 applique. Lancer : python3 maj-version.py')
