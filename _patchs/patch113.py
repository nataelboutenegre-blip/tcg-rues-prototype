# -*- coding: utf-8 -*-
u"""
patch113 — carte : les arrondissements de Paris, Lyon et Marseille prennent
la couleur de leur propriétaire.

Le jeu découpe ces trois villes en 45 arrondissements (75101-75120,
69381-69389, 13201-13216), mais les fichiers de contours n'avaient que la
ville entière (75056, 69123, 13055), un code qui n'est la carte de
personne : la ville restait grise, comme libre.

- contours/75.json, 69.json, 13.json : la ville entière est remplacée par
  ses arrondissements (contours officiels Etalab, Licence Ouverte,
  simplifiés au niveau de détail du reste de la carte, limites communes
  conservées).
- Les contours étaient demandés avec cache: 'force-cache' : un navigateur
  qui les avait déjà gardait l'ancienne version. On ajoute un numéro de
  version à l'adresse pour forcer le nouveau fichier.
- Les traits d'arrondissements dessinés par-dessus Paris (patch108)
  s'éteignent d'eux-mêmes : il n'y a plus de contour 75056 à découper.
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

def rempl(src, avant, apres, etiquette, n_attendu=1):
    n = src.count(avant)
    assert n == n_attendu, u'%s : %d occurrences (attendu %d)' % (etiquette, n, n_attendu)
    return src.replace(avant, apres)

for dep, code in (('75', '75101'), ('69', '69381'), ('13', '13201')):
    assert code in lire('contours/%s.json' % dep), u'contours/%s.json pas encore a jour' % dep

js = lire('app.js')
assert 'CONTOURS_V' not in js, u'patch113 deja applique'
js = rempl(js, u"async function chargerContours(dep){",
           u"// patch113 : monter ce numero quand un fichier de contours change\n"
           u"const CONTOURS_V = '2';\n"
           u"async function chargerContours(dep){", 'constante')
js = rempl(js, u"await fetch(`contours/${dep}.json`, { cache: 'force-cache' });",
           u"await fetch(`contours/${dep}.json?v=${CONTOURS_V}`, { cache: 'force-cache' });", 'carte', 2)
ecrire('app.js', js)
print(u'patch113 applique')
