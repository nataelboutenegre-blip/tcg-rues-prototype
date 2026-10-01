# -*- coding: utf-8 -*-
u"""
patch50 — Les deux gênes signalées par Oshannir sur iPhone.

1. LE MENU « PLUS » QU'ON N'ARRIVE PAS A FERMER

   Il se ferme en realite de deux façons : en touchant a cote, et en
   retouchant le bouton Plus. Mais la petite barre en haut de la feuille
   ressemble a une poignee, donc le geste naturel est de la tirer vers le
   bas — et ce geste-la ne faisait rien. Pire : il declenchait le
   « tirer pour rafraichir » de Safari, qui recharge la page.

   Trois corrections :
     - la poignee devient un vrai bouton de fermeture, touchable
     - un glissement vers le bas ferme la feuille, en la suivant du doigt
     - overscroll-behavior: contain empeche le geste d'atteindre la page

2. LE ZOOM AUTOMATIQUE QUAND ON TOUCHE UN CHAMP

   iOS zoome tout seul sur un champ de saisie dont le texte fait moins de
   16 px. Le jeu en a treize sous ce seuil : 14,4 px pour les recherches,
   15,2 px pour la connexion. D'ou le zoom involontaire a chaque recherche,
   et le dezoom a faire a la main ensuite.

   Oshannir propose de bloquer le zoom. Je ne le fais pas, pour deux
   raisons : iOS ignore user-scalable=no depuis 2016, donc ca ne marcherait
   pas ; et empecher de zoomer est une barriere pour qui a besoin
   d'agrandir. La seule vraie correction est de passer les champs a 16 px
   sur telephone, ce qui enleve a iOS la raison de zoomer.

   La regle vise les types de champ et non des classes : un champ ajoute
   plus tard sera couvert sans qu'on y pense.
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
#  index.html — la poignee devient un bouton
# ===========================================================================
html = lire('index.html')
html = rempl(html,
u"""  <div class="feuille-poignee"></div>""",
u"""  <button type="button" class="feuille-poignee" id="feuilleFermer" aria-label="Fermer le menu"><span></span></button>""",
u'poignee cliquable')
ecrire('index.html', html)


# ===========================================================================
#  app.js — le bouton et le glissement
# ===========================================================================
js = lire('app.js')
js = rempl(js,
u"""document.getElementById('voileMenu').addEventListener('click', () => ouvrirMenuPlus(false));""",
u"""document.getElementById('voileMenu').addEventListener('click', () => ouvrirMenuPlus(false));

// La poignee ressemblait a quelque chose qu'on tire : elle le fait maintenant.
// glisse = true pendant le court instant qui suit un vrai glissement : sans
// ca, relacher le doigt apres avoir tire de 20 px declenche aussi le clic du
// bouton, et la feuille se ferme alors qu'on ne l'a pas assez tiree.
let feuilleGlissee = false;
document.getElementById('feuilleFermer').addEventListener('click', () => {
  if(feuilleGlissee) return;
  ouvrirMenuPlus(false);
});

// Glisser la feuille vers le bas la referme. Elle suit le doigt pendant le
// geste, sinon on ne sait pas si on a bien attrape quelque chose.
(function glisserFeuille(){
  const feuille = document.getElementById('feuillePlus');
  if(!feuille) return;
  let depart = null, decalage = 0;
  const FERMETURE = 60;            // px au-dela desquels on considere que c'est ferme

  feuille.addEventListener('pointerdown', (e) => {
    if(e.target.closest('.fp-item')) return;   // un appui sur une ligne reste un appui
    depart = e.clientY; decalage = 0;
    feuille.style.transition = 'none';
  });
  feuille.addEventListener('pointermove', (e) => {
    if(depart === null) return;
    decalage = Math.max(0, e.clientY - depart);
    feuille.style.transform = 'translateY(' + decalage + 'px)';
  });
  const relacher = () => {
    if(depart === null) return;
    depart = null;
    feuille.style.transition = '';
    feuille.style.transform = '';
    feuilleGlissee = decalage > 10;
    setTimeout(() => { feuilleGlissee = false; }, 50);
    if(decalage > FERMETURE) ouvrirMenuPlus(false);
  };
  feuille.addEventListener('pointerup', relacher);
  feuille.addEventListener('pointercancel', relacher);
  feuille.addEventListener('pointerleave', relacher);
})();""",
u'fermeture par la poignee et par glissement')
ecrire('app.js', js)


# ===========================================================================
#  style.css
# ===========================================================================
css = lire('style.css')

css = rempl(css,
u"""  .feuille-poignee{ width:38px; height:4px; border-radius:2px; background:rgba(169,188,212,0.3); margin:2px auto 10px; }""",
u"""  /* La poignee est un bouton : la barre reste fine a l'oeil, mais la zone
     touchable fait 34 px de haut sur toute la largeur. */
  .feuille-poignee{
    display:block; width:100%; height:34px; margin:-6px 0 2px;
    padding:0; border:0; background:none; cursor:pointer;
  }
  .feuille-poignee span{
    display:block; width:38px; height:4px; margin:15px auto 0;
    border-radius:2px; background:rgba(169,188,212,0.3);
  }
  .feuille-poignee:active span{ background:rgba(169,188,212,0.55); }""",
u'poignee touchable')

css = rempl(css,
u"""    transform: translateY(102%);
    transition: transform .22s cubic-bezier(.2,.8,.3,1);
  }""",
u"""    transform: translateY(102%);
    transition: transform .22s cubic-bezier(.2,.8,.3,1);
    touch-action: none;
    /* sans ca, tirer la feuille vers le bas declenche le « tirer pour
       rafraichir » de Safari : le geste qu'on fait pour la fermer
       rechargeait la page */
    overscroll-behavior: contain;
  }""",
u'le geste ne traverse plus vers la page')

css = rempl(css,
u"""  .voile-menu.ouvert{ opacity:1; }""",
u"""  .voile-menu.ouvert{ opacity:1; }
  .voile-menu{ overscroll-behavior: contain; touch-action: none; }""",
u'voile sans rebond')

# --- le zoom d'iOS -----------------------------------------------------------
css += (
u"""
  /* ---------- Le zoom automatique d'iOS ----------
     Safari zoome tout seul sur un champ dont le texte fait moins de 16 px,
     et il garde ce zoom ensuite, y compris au retour sur le site. C'est ce
     qui obligeait a pincer pour revenir a une vue normale apres chaque
     recherche. On vise les TYPES de champ et non des classes : un champ
     ajoute plus tard sera couvert sans qu'on ait a y penser.
     Bloquer le zoom aurait ete plus simple, mais iOS ignore
     user-scalable=no depuis 2016, et empecher d'agrandir gene ceux qui en
     ont besoin. */
  @media (max-width: 860px){
    input[type="text"], input[type="search"], input[type="email"],
    input[type="password"], input[type="number"], input[type="tel"],
    input[type="url"], select, textarea{ font-size:16px; }
  }
""")

ecrire('style.css', css)
print(u'patch50 applique.')
