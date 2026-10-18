# -*- coding: utf-8 -*-
u"""
patch142 — Échange, zone « Tu donnes » : plusieurs recherches séparées par
des virgules (« Bordeaux, Angoulême, 16 »), comme « Tu reçois ». Une commune
s'affiche si elle correspond à l'un des termes. Idée d'Arkhannou.
Saison 1 (mes communes) et Terra (mes doublons échangeables).
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
js = lire('app.js'); html = lire('index.html')
assert 'correspondUnTerme' not in js, u'patch142 deja applique'

js = rempl(js, u"""// Sieges en cours sur mes communes, regroupes : combien d'attaquants, meilleure serie""",
u"""// patch142 : « Bordeaux, Angouleme, 16 » -> la commune correspond a l'un des termes
function correspondUnTerme(nom, dept, recherche){
  const termes = String(recherche || '').split(/[,;]/).map(t => t.trim()).filter(Boolean);
  if(!termes.length) return true;
  return termes.some(t => correspondRecherche(nom, dept, t));
}

// Sieges en cours sur mes communes, regroupes : combien d'attaquants, meilleure serie""", u'fonction')

js = rempl(js, u"""    .filter(c => !engagees.has(c.code))
    .filter(c => correspondRecherche(c.nom, c.dept, rechercheM))""",
u"""    .filter(c => !engagees.has(c.code))
    .filter(c => correspondUnTerme(c.nom, c.dept, rechercheM))""", u'saison 1')

js = rempl(js, u"""    .filter(c => c.libres > 0)
    .filter(c => correspondRecherche(c.nom, c.dept, rechercheM))""",
u"""    .filter(c => c.libres > 0)
    .filter(c => correspondUnTerme(c.nom, c.dept, rechercheM))""", u'terra')

html = rempl(html, u"""        <input type="text" id="echSearchMien" class="bourse-search" placeholder="Rechercher une commune ou un département…">""",
u"""        <input type="text" id="echSearchMien" class="bourse-search" placeholder="Rechercher une commune ou un département…">
        <p class="ech-astuce">Combine avec des virgules : <b>Lyon, Brest, 16</b></p>""", u'astuce')

ecrire('app.js', js); ecrire('index.html', html)
print(u'patch142 applique')
