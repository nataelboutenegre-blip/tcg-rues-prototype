# -*- coding: utf-8 -*-
u"""
patch48 — L'onglet Combat s'affiche par lots.

LE PROBLEME MESURE
  4 870 cibles, 30 elements HTML par carte, soit 148 022 elements fabriques
  d'un coup. 5,7 secondes sur une machine rapide, sans reseau. Et c'est
  refait ENTIEREMENT a chaque changement de filtre : un clic sur « Rare »,
  5,7 secondes de plus.

  La trace d'Oshannir montrait son DOM passant de 138 729 a 178 808 noeuds
  pendant son blocage de 26 secondes. C'etait ca.

CE QUE J'AI CHOISI, ET POURQUOI PAS CE QUE J'AVAIS ANNONCE
  J'avais decrit le recyclage de cartes : garder cinquante cartes et
  reecrire leur contenu au defilement. C'est la solution la plus pure, et
  c'est aussi la plus fragile ici : la grille est en « auto-fill », le
  nombre de colonnes change avec la largeur, et la hauteur d'une carte
  depend de la longueur du nom et de la presence d'une ligne de distance.
  Un recyclage mal cale sur des hauteurs variables donne des sauts de
  defilement — un bug beaucoup plus desagreable que la lenteur qu'il
  corrige.

  J'ai donc pris l'affichage par lots : on fabrique 60 cartes, et on ajoute
  les 60 suivantes quand le joueur approche du bas. Pas de calcul de
  hauteur, pas de saut possible, et le gain est le meme dans l'usage reel —
  personne ne fait defiler 4 870 cibles, on tape un nom ou on filtre.

  La difference honnete : un joueur qui defilerait vraiment jusqu'en bas
  reconstruirait les 4 870 cartes. Mais par paquets de 60, jamais en un
  bloc de 5,7 secondes.

DEUX DETAILS QUI COMPTENT
  - Un changement de filtre repart du premier lot. Un rafraichissement
    automatique (toutes les 30 s) garde le nombre de cartes deja affichees,
    sinon le joueur perdrait sa place toutes les demi-minutes.
  - Les boutons « Attaquer » passent par une delegation sur document : les
    cartes ajoutees sont cliquables sans rien rebrancher.

LE MECANISME EST GENERIQUE
  afficherParLots() servira pour la Collection (38 491 elements chez
  Maroli) et la Bourse (14 663) sans etre reecrit.
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


# ===========================================================================
#  app.js
# ===========================================================================
js = lire('app.js')

# --- 1. le mecanisme, pose a cote du rendu differe -------------------------
js = rempl(js,
u"""function renderCollection(){
  if(rendreALOuverture('collection', renderCollection)) return;""",
u"""// ---------- Affichage par lots ----------
// Une grille de milliers de cartes se fabrique par paquets : le premier lot
// tout de suite, les suivants quand le joueur approche du bas. On ne calcule
// aucune hauteur, donc aucun saut de defilement possible.
const LOT_DEFAUT = 60;
const ETATS_LOTS = new Map();          // id de la grille -> etat

function afficherParLots(grid, elements, fabriquer, signature, lot){
  lot = lot || LOT_DEFAUT;
  let etat = ETATS_LOTS.get(grid.id);
  if(!etat){ etat = { signature: null, affiches: 0, obs: null }; ETATS_LOTS.set(grid.id, etat); }
  if(etat.obs){ etat.obs.disconnect(); etat.obs = null; }

  // filtre change => on repart du debut ; simple rafraichissement => on garde
  // le nombre de cartes deja affichees, sinon le joueur perd sa place
  if(signature !== etat.signature){ etat.signature = signature; etat.affiches = 0; }
  const premier = Math.min(elements.length, Math.max(lot, etat.affiches));
  etat.affiches = premier;

  grid.innerHTML = elements.slice(0, premier).map(fabriquer).join('')
    + (premier < elements.length ? '<div class="lot-suite" aria-hidden="true"></div>' : '');

  const armer = () => {
    const sentinelle = grid.querySelector('.lot-suite');
    if(!sentinelle || !('IntersectionObserver' in window)) return;
    etat.obs = new IntersectionObserver((entrees) => {
      if(!entrees.some(x => x.isIntersecting)) return;
      if(etat.obs){ etat.obs.disconnect(); etat.obs = null; }
      ajouterUnLot();
    }, { rootMargin: '800px 0px' });
    etat.obs.observe(sentinelle);
  };

  const ajouterUnLot = () => {
    const sentinelle = grid.querySelector('.lot-suite');
    if(!sentinelle) return;
    const fin = Math.min(elements.length, etat.affiches + lot);
    sentinelle.insertAdjacentHTML('beforebegin',
      elements.slice(etat.affiches, fin).map(fabriquer).join(''));
    etat.affiches = fin;
    if(fin >= elements.length){ sentinelle.remove(); return; }
    armer();
  };

  // sans IntersectionObserver (tres vieux navigateur) on affiche tout :
  // lent, mais complet. Mieux vaut lent que tronque.
  if(!('IntersectionObserver' in window)){
    while(etat.affiches < elements.length) ajouterUnLot();
    return;
  }
  armer();
}

function renderCollection(){
  if(rendreALOuverture('collection', renderCollection)) return;""",
u'mecanisme afficherParLots')

# --- 2. la grille du Combat l'utilise --------------------------------------
js = rempl(js,
u"""  grid.innerHTML = cibles.map(c => {
    const commune = c.communes;""",
u"""  const carteCible = (c) => {
    const commune = c.communes;""",
u'la fabrique d une carte cible')

js = rempl(js,
u"""          <button class="cible-attaquer" data-action="attaquer" data-code="${c.commune_code}" ${disabled ? 'disabled' : ''}>Attaquer <b>${cout} pts</b><i>${vrai ? vrai.chances + ' %' : '…'}</i></button>
        </div>
      </article>`;
  }).join('');
}""",
u"""          <button class="cible-attaquer" data-action="attaquer" data-code="${c.commune_code}" ${disabled ? 'disabled' : ''}>Attaquer <b>${cout} pts</b><i>${vrai ? vrai.chances + ' %' : '…'}</i></button>
        </div>
      </article>`;
  };

  // la signature dit si c'est un nouveau filtrage ou un simple rafraichissement
  const signature = [combatFilterTier, searchText, combatProximite,
                     combatRayonKm, combatEnCours, cibles.length].join('|');
  afficherParLots(grid, cibles, carteCible, signature);
}""",
u'appel a afficherParLots pour le Combat')

ecrire('app.js', js)


# ===========================================================================
#  style.css
# ===========================================================================
css = lire('style.css')

css = rempl(css,
u"""  .cibles-grille > .collection-empty{ grid-column: 1 / -1; }""",
u"""  .cibles-grille > .collection-empty{ grid-column: 1 / -1; }
  /* Le reperage du bas de liste : invisible, il occupe toute la largeur de
     la grille pour que le navigateur sache quand on en approche. */
  .lot-suite{ grid-column: 1 / -1; height:1px; }""",
u'style de la sentinelle de lot')

ecrire('style.css', css)

print(u'patch48 applique.')
