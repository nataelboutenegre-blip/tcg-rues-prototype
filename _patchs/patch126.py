# -*- coding: utf-8 -*-
u"""
patch126 — Combat : chercher aussi par pseudo (idée d'Oshannir).
Taper le pseudo d'un joueur dans la recherche du Combat montre ses communes
(toutes raretés : depuis patch125, une recherche charge aussi les communes et
peu communes). Le nom de commune et le département marchent comme avant.
"""
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
js = lire('app.js')
assert 'patch126' not in js, u'patch126 deja applique'
js = rempl(js, u"""    cibles = cibles.filter(c => correspondRecherche(c.communes.nom, c.communes.departement, searchText));""",
u"""    // patch126 : le pseudo du proprietaire compte aussi
    cibles = cibles.filter(c => correspondRecherche(c.communes.nom, c.communes.departement, searchText)
      || (c.joueurs && c.joueurs.pseudo && sansAccents(c.joueurs.pseudo).includes(searchText)));""", u'recherche pseudo')
ecrire('app.js', js)
print(u'patch126 applique')
