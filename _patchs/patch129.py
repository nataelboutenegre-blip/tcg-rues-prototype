# -*- coding: utf-8 -*-
u"""patch129 — Rafale : le bouton « Partir » devient « Lancer le chrono » (demande de Nataël)."""
import io, os
ICI = os.path.dirname(os.path.abspath(__file__))
BASE = os.path.dirname(ICI) if os.path.basename(ICI) == '_patchs' else ICI
def lire(n):
    with io.open(os.path.join(BASE, n), encoding='utf-8') as f: return f.read()
def ecrire(n, s):
    with io.open(os.path.join(BASE, n), 'w', encoding='utf-8') as f: f.write(s)
def rempl(src, avant, apres, etiquette, n_attendu=1):
    n = src.count(avant)
    assert n == n_attendu, u'%s : %d occurrences (attendu %d)' % (etiquette, n, n_attendu)
    return src.replace(avant, apres)
js = lire('app.js'); html = lire('index.html')
html = rempl(html, u'id="rfPartir">Partir</button>', u'id="rfPartir">Lancer le chrono</button>', u'bouton')
js = rempl(js, u"p.parti ? 'Reprendre' : 'Partir'", u"p.parti ? 'Reprendre' : 'Lancer le chrono'", u'libelle')
ecrire('app.js', js); ecrire('index.html', html)
print(u'patch129 applique')
