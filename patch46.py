# -*- coding: utf-8 -*-
u"""
patch46 — 37 000 elements invisibles retires de la page.

CE QUE J'AI TROUVE
  La carte existe en deux versions dans le code : une en SVG, l'ancienne,
  et une en canvas, la nouvelle. Le canvas est actif par defaut (MODE_CANVAS,
  qu'on ne desactive qu'avec ?svg dans l'adresse).

  Mais le canvas ne s'initialise qu'apres le chargement de
  data/france-outline.json. Tous les renderMapOverlay() qui arrivent AVANT
  ce chargement trouvent CV.ctx encore vide, ne passent donc pas par le
  raccourci canvas, et dessinent la carte en SVG. Une fois le canvas pret,
  il se dessine par-dessus — mais les 37 000 elements SVG restent dans la
  page pour toujours.

LA PREUVE
  J'ai vide les quatre groupes SVG a chaud sur la page d'Oshannir, puis
  compare les deux captures pixel par pixel :

      elements : 67 823 -> 30 942
      pixels differents : 0 sur 2 249 744

  Zero. Pas un pixel. Ces elements ne sont pas juste redondants, ils sont
  invisibles. Chaque joueur les paie a chaque interaction.

CE QUE FAIT CE CORRECTIF
  Une ligne de garde : quand le mode canvas est en service, on ne dessine
  plus jamais le SVG. Si le canvas devait echouer (contexte 2d refuse par
  le navigateur), un drapeau fait repasser la carte en SVG comme avant.

CE QUE CA NE CORRIGE PAS
  Les onglets construits d'avance : la Collection de Maroli fait a elle
  seule 38 000 elements. C'est le second chantier, separe.
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

# --- 1. un drapeau : le canvas a-t-il echoue ? ------------------------------
js = rempl(js,
u"""const MODE_CANVAS = !new URLSearchParams(location.search).has('svg');""",
u"""const MODE_CANVAS = !new URLSearchParams(location.search).has('svg');
// Passe a true si le navigateur refuse un contexte 2d. C'est la seule
// situation ou la carte SVG doit reprendre la main.
let CANVAS_HS = false;""",
u'drapeau CANVAS_HS')

# --- 2. le detecter a l'initialisation --------------------------------------
js = rempl(js,
u"""  wrap.classList.add('en-canvas');
  CV.ctx = cv.getContext('2d');
  redimensionnerCanvas();""",
u"""  wrap.classList.add('en-canvas');
  CV.ctx = cv.getContext('2d');
  if(!CV.ctx){ CANVAS_HS = true; wrap.classList.remove('en-canvas'); renderMapOverlay(); return; }
  redimensionnerCanvas();""",
u'repli si le contexte 2d est refuse')

# --- 3. la garde ------------------------------------------------------------
js = rempl(js,
u"""    demanderDessin();
    return;
  }
  // plusieurs appels rapproches (cartes retournees une par une) = un seul dessin
  if(carteRenduPlanifie) return;""",
u"""    demanderDessin();
    return;
  }
  // Le canvas est en service mais pas encore initialise : il attend
  // data/france-outline.json. Surtout NE PAS dessiner le SVG en attendant.
  // Il serait recouvert par le canvas des qu'il est pret, donc invisible,
  // mais resterait dans la page : 37 000 elements payes par tous les
  // joueurs a chaque interaction, pour rien. Mesure a l'appui : les vider
  // a chaud ne change pas un seul pixel sur 2,2 millions.
  if(MODE_CANVAS && !CANVAS_HS) return;
  // plusieurs appels rapproches (cartes retournees une par une) = un seul dessin
  if(carteRenduPlanifie) return;""",
u'garde contre le dessin SVG inutile')

ecrire('app.js', js)
print(u'patch46 applique.')
