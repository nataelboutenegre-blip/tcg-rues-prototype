# -*- coding: utf-8 -*-
u"""
patch218 — recherche du Combat de Front alignée sur l'Échange (signalé par H34VEN).
Avant : la virgule faisait un OU (« Arkhannou, 63 » = toutes les communes
d'Arkhannou + toutes celles du 63). Maintenant : ET entre catégories, OU à
l'intérieur, comme l'Échange — « Arkhannou, 63 » = les communes d'Arkhannou
DANS le 63. Un terme est classé département (numéro ou nom), sinon pseudo d'un
propriétaire présent, sinon nom de commune. Testé au banc avec les vraies
fonctions (codeDepartement, correspondRecherche). Sans SQL.
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

js = lire('app.js')
assert 'patch218' not in js
js = rep(js,
  u"""  if(searchText){
    // patch126 : le pseudo du proprietaire compte aussi ; patch149 : plusieurs termes, separes par des virgules
    const termes = searchText.split(/[,;]/).map(t => t.trim()).filter(Boolean);
    cibles = cibles.filter(c => termes.some(t => correspondRecherche(c.communes.nom, c.communes.departement, t)
      || (c.joueurs && c.joueurs.pseudo && sansAccents(c.joueurs.pseudo).includes(t))));
  }""",
  u"""  if(searchText){
    // patch218 : comme l'Echange — pseudo ET departement ET nom (ET entre categories,
    // OU a l'interieur). « Arkhannou, 63 » = les communes d'Arkhannou DANS le 63.
    const owners = new Set(combatCibles.map(c => c.joueurs && c.joueurs.pseudo).filter(Boolean).map(x => sansAccents(x)));
    const deps = [], pseudos = [], noms = [];
    for(const t of searchText.split(/[,;]/).map(s => s.trim()).filter(Boolean)){
      const d = codeDepartement(t) || t;
      if(/^(\\d{2,3}|2a|2b)$/i.test(d)){ deps.push(d.toUpperCase()); continue; }
      if([...owners].some(x => x.includes(t))) pseudos.push(t); else noms.push(t);
    }
    cibles = cibles.filter(c => {
      const dept = String(c.communes.departement).toUpperCase();
      const ps = c.joueurs && c.joueurs.pseudo ? sansAccents(c.joueurs.pseudo) : '';
      return (!deps.length || deps.includes(dept))
          && (!pseudos.length || pseudos.some(t => ps.includes(t)))
          && (!noms.length || noms.some(t => correspondRecherche(c.communes.nom, c.communes.departement, t)));
    });
  }""")
ecrire('app.js', js)
print('patch218 ok')
