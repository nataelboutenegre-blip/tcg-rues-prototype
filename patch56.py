# -*- coding: utf-8 -*-
u"""
patch56 — La barre du bas du telephone.

CE QUI CHANGE
  La barre garde quatre onglets plus le bouton Plus — c'est le maximum
  mesure, du plus petit iPhone au plus grand. Elle passe de

      Tirage · Collection · Combat · Defense
  a
      Tirage · Territoire · Combat · Defense

  La Collection descend dans le menu Plus, en tete, suivie de Monuments,
  Contrat, Bourse, Echange, Profil, Communaute, Succes.

LA SIMPLIFICATION QUI COMPTE
  Il y avait deux listes : celle de la barre et celle du menu. La premiere
  n'etait meme pas utilisee par le code — elle decrivait une intention —
  et la seconde, la vraie, se tenait a jour a la main. C'est comme ca que
  le menu Plus s'etait mis a suivre un ordre different de la colonne.

  Desormais une seule liste est ecrite : celle de la barre. Le menu Plus
  est deduit — tous les autres onglets, dans l'ordre de la colonne. Les
  deux ne peuvent plus diverger, et ajouter un onglet demain le place
  automatiquement au bon endroit du menu.

CE QUE CA COUTE, PUISQU'IL FAUT LE DIRE
  La Collection est sans doute l'onglet le plus visite apres le Tirage.
  La mettre dans le menu ajoute un geste a chaque consultation. Elle reste
  atteignable depuis la carte et depuis l'album, et elle est en tete du
  menu, mais le geste existe.
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


js = lire('app.js')

js = rempl(js,
u"""const ONGLETS_BARRE = ['tirage', 'collection', 'combat', 'defense'];""",
u"""// La barre du bas tient quatre onglets plus le bouton Plus : mesure faite de
// 320 a 430 px de large, au-dela de quatre le bouton Plus passe a la ligne.
const ONGLETS_BARRE = ['tirage', 'territoire', 'combat', 'defense'];""",
u'les quatre de la barre')

js = rempl(js,
u"""// Meme ordre que la colonne de l'ordinateur, moins les quatre de la barre du
// bas : deux ordres differents pour les memes entrees, c'etait une raison de
// se tromper pour rien.
const ONGLETS_MENU = ['territoire', 'monuments', 'contrat', 'bourse', 'echange', 'profil', 'communaute', 'succes'];""",
u"""// Le menu Plus n'est plus une liste a tenir : c'est tout ce qui n'est pas dans
// la barre, dans l'ordre de la colonne. Deux listes ecrites a la main, c'etait
// deux listes qui finissaient par diverger — et c'est exactement ce qui etait
// arrive. Un onglet ajoute demain se place tout seul au bon endroit.
const ONGLETS_MENU = Array.prototype.map
  .call(document.querySelectorAll('.tab[data-tab]'), (t) => t.dataset.tab)
  .filter((id) => ONGLETS_BARRE.indexOf(id) < 0);""",
u'le menu Plus deduit de la colonne')

ecrire('app.js', js)
print(u'patch56 applique.')
