# -*- coding: utf-8 -*-
u"""
patch165 — sur telephone, la bulle noire du survol (« Eure (27) · Maroli
69 % … ») restait au milieu de la carte apres un toucher et la cachait
(Arkhannou, 25 octobre). Au doigt, pas de bulle de survol : le toucher
ouvre deja la fiche du departement ou de la commune, qui a sa croix.
"""
import io, os
ICI = os.path.dirname(os.path.abspath(__file__))
BASE = os.path.dirname(ICI) if os.path.basename(ICI) == '_patchs' else ICI
def lire(n):
    with io.open(os.path.join(BASE, n), encoding='utf-8') as f: return f.read()
def ecrire(n, s):
    with io.open(os.path.join(BASE, n), 'w', encoding='utf-8') as f: f.write(s)
def rempl(src, avant, apres, etiquette):
    n = src.count(avant)
    assert n == 1, u'%s : %d occurrences (attendu 1)' % (etiquette, n)
    return src.replace(avant, apres)
js = lire('app.js')
assert 'patch165' not in js, u'patch165 deja applique'
js = rempl(js, u"""  cv.addEventListener('pointermove', (e) => {
    if(mapDragging){ bulle.hidden = true; return; }""", u"""  cv.addEventListener('pointermove', (e) => {
    if(mapDragging){ bulle.hidden = true; return; }
    // patch165 : au doigt, pas de bulle (elle restait et cachait la carte)
    if(e.pointerType === 'touch'){ bulle.hidden = true; CV.survol = null; return; }""", 'survol')
ecrire('app.js', js)
print(u'patch165 applique. Lancer : python3 maj-version.py')
