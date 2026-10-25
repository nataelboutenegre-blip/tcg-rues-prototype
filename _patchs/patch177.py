# -*- coding: utf-8 -*-
u"""
patch177 — filtre « Clans » de la carte : seuls les territoires des joueurs
qui sont dans un clan restent affichés (demande de Nataël, 25 octobre).
Les autres joueurs disparaissent de la carte et de la légende tant que le
filtre est allumé ; ton propre territoire aussi si tu n'as pas de clan.
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
assert 'patch177' not in js, u'patch177 deja applique'
js = rempl(js, u"""  if(CLANS && CALQUES.clans) peindreClans(CV.donnees.joueurs);   // patch110
""", u"""  if(CLANS && CALQUES.clans){
    peindreClans(CV.donnees.joueurs);   // patch110
    // patch177 : le filtre Clans ne montre que les joueurs qui sont dans un clan
    const { liste, joueurs } = CV.donnees;
    for(const [id, j] of [...joueurs]){
      if(j.clan) continue;
      if(id === ID_MOI) j.nb = 0; else joueurs.delete(id);
    }
    CV.donnees.liste = liste.filter(e => { const j = joueurs.get(e.joueur); return j && j.clan; });
  }
""", 'filtre clans')
ecrire('app.js', js)
print(u'patch177 applique')
