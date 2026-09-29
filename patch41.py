# -*- coding: utf-8 -*-
"""
patch41 — La barre du bas passe sur deux lignes sur telephone.

CAUSE
  Les onglets qui vont dans le menu « Plus » etaient declares a deux
  endroits :

    app.js    const ONGLETS_MENU = ['territoire', ..., 'contrat', 'succes'];
    style.css .tab[data-tab="territoire"], ... , .tab[data-tab="succes"]
              { display:none; }

  patch37 a ajoute 'contrat' a la liste JS et pas a la liste CSS.
  L'onglet Contrat restait donc dans la barre : sept elements au lieu de
  cinq, la barre passait sur deux lignes et « Plus » se retrouvait seul
  en dessous.

  Mon test du banc n'a rien vu parce qu'il cherchait un debordement
  horizontal. La barre ne deborde pas : elle revient a la ligne. Le test
  est corrige en meme temps (banc : une seule ligne, et exactement les
  onglets attendus).

CORRECTIF
  Une seule source : le CSS cache une CLASSE, et le JS pose cette classe
  a partir de ONGLETS_MENU au demarrage. Ajouter un onglet au menu
  suffira desormais, la barre suivra toute seule.
"""
import io, os

BASE = os.path.dirname(os.path.abspath(__file__))

def lire(n):
    with io.open(os.path.join(BASE, n), encoding='utf-8') as f:
        return f.read()

def ecrire(n, s):
    with io.open(os.path.join(BASE, n), 'w', encoding='utf-8') as f:
        f.write(s)

def rempl(src, avant, apres, etiquette):
    n = src.count(avant)
    assert n == 1, u'%s : %d occurrences (attendu 1)' % (etiquette, n)
    return src.replace(avant, apres)


# ---------------------------------------------------------------------------
#  style.css : on cache une classe, plus une liste de noms
# ---------------------------------------------------------------------------
css = lire('style.css')
css = rempl(css,
u"""    .tab[data-tab="territoire"], .tab[data-tab="communaute"], .tab[data-tab="bourse"],
    .tab[data-tab="echange"], .tab[data-tab="succes"]{ display:none; }""",
u"""    /* La classe est posee par app.js depuis ONGLETS_MENU. Ne jamais
       relister les onglets ici : les deux listes finiraient par diverger,
       c'est exactement ce qui a mis la barre sur deux lignes. */
    .tab.dans-le-menu{ display:none; }""",
u'masquage par classe')

ecrire('style.css', css)


# ---------------------------------------------------------------------------
#  app.js : poser la classe depuis la liste
# ---------------------------------------------------------------------------
js = lire('app.js')
js = rempl(js,
u"""function construireMenuPlus(){""",
u"""// La barre du bas ne garde que ONGLETS_BARRE. Les autres portent
// .dans-le-menu, que le CSS cache sous 720 px. C'est le seul endroit ou
// la repartition est decidee.
function marquerOngletsDuMenu(){
  for(const id of ONGLETS_MENU){
    const tab = document.querySelector(`.tab[data-tab="${id}"]`);
    if(tab) tab.classList.add('dans-le-menu');
  }
}
marquerOngletsDuMenu();

function construireMenuPlus(){""",
u'pose de la classe')

ecrire('app.js', js)

print(u'patch41 applique.')
