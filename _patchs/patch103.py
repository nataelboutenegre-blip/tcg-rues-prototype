# -*- coding: utf-8 -*-
u"""
patch103 — « Mes départements » : jusqu'à 50 au lieu de 5 (demande de Nataël,
10 octobre). SQL : _sql/defense-departements-50.sql (à passer avant le push,
sinon le serveur refuse toujours au-delà de 5).
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

js = lire('app.js')
js = rempl(js, u"const DEF_PRIO_MAX = 5;", u"const DEF_PRIO_MAX = 50;", 'max')
js = rempl(js, u"Choisis jusqu\\'à 5 départements : leurs communes attaquées passent en tête.",
           u"Choisis tes départements (jusqu\\'à 50) : leurs communes attaquées passent en tête.", 'aide')
ecrire('app.js', js)
print(u'patch103 applique')
