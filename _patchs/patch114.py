# -*- coding: utf-8 -*-
u"""
patch114 — Règles : les vraies bornes des chances d'attaque (signalé par Wally).

La FAQ disait « entre 10 et 90 % ». Ce sont les bornes de sécurité du
serveur, jamais atteintes. Lu en production le 11 octobre : de 23 %
(prudente, à distance) à 80 % (offensive, entourée de tes communes).
Texte seulement.
"""
import io, os

ICI = os.path.dirname(os.path.abspath(__file__))
BASE = os.path.dirname(ICI) if os.path.basename(ICI) == '_patchs' else ICI

def lire(n):
    with io.open(os.path.join(BASE, n), encoding='utf-8') as f:
        return f.read()

def ecrire(n, s):
    with io.open(os.path.join(BASE, n), 'w', encoding='utf-8') as f:
        f.write(s)

h = lire('index.html')
avant = u"Tes chances restent toujours comprises entre 10 et 90 %."
assert h.count(avant) == 1, u'phrase introuvable (deja corrigee ?)'
h = h.replace(avant, u"Tes chances vont donc de <b>23 %</b> (prudente, à distance) à <b>80 %</b> (offensive, entourée de tes communes).")
ecrire('index.html', h)
print(u'patch114 applique')
