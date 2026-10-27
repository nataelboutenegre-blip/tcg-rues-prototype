# -*- coding: utf-8 -*-
u"""
patch223 — la vitrine suit le mode (demande de Nataël, 27/10).

Sur un profil, la vitrine s'ouvre sur Terra quand on joue en Terra, sur Front
quand on joue en Front. Un onglet choisi à la main reste tant qu'on ne change
pas de mode. Chez un autre joueur, on garde la règle : pas de vitrine vide si
l'autre est remplie.
"""
import io, os
ICI = os.path.dirname(os.path.abspath(__file__))
BASE = os.path.dirname(ICI) if os.path.basename(ICI) == '_patchs' else ICI
def lire(n):
    with io.open(os.path.join(BASE, n), encoding='utf-8') as f: return f.read()
def ecrire(n, s):
    with io.open(os.path.join(BASE, n), 'w', encoding='utf-8') as f: f.write(s)
def rep(s, a, b, n=1):
    c = s.count(a); assert c == n, ('MATCH', a[:70], 'trouve', c, 'attendu', n); return s.replace(a, b)

s = lire('app.js')
s = rep(s, "let vitrineVue = 'terra';",
 "// patch223 : la vitrine suit le mode ; un onglet choisi à la main vaut tant qu'on reste dans ce mode.\nlet vitrineVue = null;")
s = rep(s, "  let vue = vitrineVue;\n",
 "  let vue = (vitrineVue && vitrineVue.mode === modeJeu) ? vitrineVue.vue : (modeJeu === 'front' ? 'front' : 'terra');\n")
s = rep(s, "  vitrineVue = o.dataset.vtOnglet === 'front' ? 'front' : 'terra';\n",
 "  vitrineVue = { mode: modeJeu, vue: o.dataset.vtOnglet === 'front' ? 'front' : 'terra' };\n")
ecrire('app.js', s)
print('patch223 ok')
