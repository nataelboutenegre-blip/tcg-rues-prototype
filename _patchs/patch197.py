# -*- coding: utf-8 -*-
u"""
patch197 — le bouton « Animation » du Tirage coupe aussi le balayage au
changement de mode (patch188). Aucun SQL.
"""
import io, os
ICI = os.path.dirname(os.path.abspath(__file__))
BASE = os.path.dirname(ICI) if os.path.basename(ICI) == '_patchs' else ICI
def lire(n):
    with io.open(os.path.join(BASE, n), encoding='utf-8') as f: return f.read()
def ecrire(n, s):
    with io.open(os.path.join(BASE, n), 'w', encoding='utf-8') as f: f.write(s)
js = lire('app.js')
assert 'patch197' not in js
avant = u"""function balayerMode(){
  let el"""
apres = u"""function balayerMode(){
  if(!ouvAnim) return;   // patch197 : le bouton « Animation » coupe aussi le balayage
  let el"""
assert js.count(avant) == 1
ecrire('app.js', js.replace(avant, apres))
print(u'patch197 applique. Lancer : python3 maj-version.py')
