# -*- coding: utf-8 -*-
u"""
patch185 — quêtes du Front : le plafond d'énergie de quêtes affiché passe à 35.
SQL : _sql/s2-27-quetes-energie.sql (plafond 35 + 3 quêtes Front), à passer AVANT.
Les nouvelles quêtes s'affichent toutes seules (liste lue sur le serveur).
"""
import io, os
ICI = os.path.dirname(os.path.abspath(__file__))
BASE = os.path.dirname(ICI) if os.path.basename(ICI) == '_patchs' else ICI
def lire(n):
    with io.open(os.path.join(BASE, n), encoding='utf-8') as f: return f.read()
def ecrire(n, s):
    with io.open(os.path.join(BASE, n), 'w', encoding='utf-8') as f: f.write(s)
js = lire('app.js')
avant = u"${ej} / 20 d'énergie de quêtes"
apres = u"${ej} / 35 d'énergie de quêtes"
assert apres not in js, u'patch185 deja applique'
assert js.count(avant) == 1, u'plafond : %d occurrences (attendu 1)' % js.count(avant)
ecrire('app.js', js.replace(avant, apres))
print(u'patch185 applique. Lancer : python3 maj-version.py')
