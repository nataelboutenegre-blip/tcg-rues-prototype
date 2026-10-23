# -*- coding: utf-8 -*-
u"""
patch155 — Bourse, « Vendre une commune » : la recherche accepte plusieurs
termes séparés par des virgules et des exclusions après un / (idée de Maroli),
comme Combat et Échange. Exemple : « Côtes-d'Armor, 29, 56 /Brest ».
Front et Terra.
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
assert 'patch155' not in js, u'patch155 deja applique'
js = rempl(js, u"""  const searchEl = document.getElementById('sellSearch');
  const searchText = sansAccents(searchEl ? searchEl.value.trim() : '');
  if(marcheTerra()) return renderVenteTerra(grid, searchText);""", u"""  const searchEl = document.getElementById('sellSearch');
  // patch155 : plusieurs termes (virgules) et exclusions apres un /
  const { recherche: rechVente, exclus: exclusVente } = separerExclusions(searchEl ? searchEl.value : '');
  const searchText = sansAccents(rechVente);
  if(marcheTerra()) return renderVenteTerra(grid, searchText, exclusVente);""", 'vente')
js = rempl(js, u"""  if(searchText){
    entries = entries.filter(e => correspondRecherche(e.nom, e.dept, searchText));
  }

  if(collectionMap.size === 0){""", u"""  if(searchText){
    entries = entries.filter(e => correspondUnTerme(e.nom, e.dept, searchText));
  }
  if(exclusVente.length) entries = entries.filter(e => !estExclu(e.nom, e.dept, '', exclusVente));

  if(collectionMap.size === 0){""", 'filtre vente')
js = rempl(js, u"""function renderVenteTerra(grid, searchText){""", u"""function renderVenteTerra(grid, searchText, exclus = []){""", 'terra sig')
js = rempl(js, u"""  if(searchText) entries = entries.filter(e => correspondRecherche(e.nom, e.dept, searchText));""",
u"""  if(searchText) entries = entries.filter(e => correspondUnTerme(e.nom, e.dept, searchText));
  if(exclus.length) entries = entries.filter(e => !estExclu(e.nom, e.dept, '', exclus));""", 'terra filtre')
ecrire('app.js', js)

h = lire('index.html')
h = rempl(h, u'''<input type="text" id="sellSearch" class="bourse-search" placeholder="Rechercher une commune ou un département…">''',
u'''<input type="text" id="sellSearch" class="bourse-search" placeholder="Communes ou départements, séparés par des virgules · /16 pour exclure">''', 'placeholder')
ecrire('index.html', h)
print(u'patch155 applique. Lancer : python3 maj-version.py')
