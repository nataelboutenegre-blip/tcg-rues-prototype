# -*- coding: utf-8 -*-
u"""
patch117 — carte du territoire : un bug et une idée (LeoLesel, Wally).

1. Bug : « Proposer un échange » depuis la carte, puis retour sur la carte :
   elle est vide, « zoomée loin hors de la France ». Sur téléphone, le
   changement d'onglet fait défiler la page, la barre d'adresse se replie et
   le navigateur envoie un « resize » pendant que la carte est cachée. La
   carte mesurait alors 0 × 0 px et le recadrage remettait le déplacement à
   (0, 0) en gardant le zoom : on retombait sur le coin en haut à gauche,
   en pleine mer. On ne recadre plus une carte cachée.

2. Idée de LeoLesel : sur téléphone, dès qu'on zoome, la carte passe en
   plein écran (la barre d'onglets du bas reste visible). Bouton « Réduire »
   en haut à droite ; revenir au zoom de départ la réduit aussi. Le point
   regardé reste au centre au passage.
"""
import io, os

ICI = os.path.dirname(os.path.abspath(__file__))
BASE = os.path.dirname(ICI) if os.path.basename(ICI) == '_patchs' else ICI

def lire(n):
    with io.open(os.path.join(BASE, n), encoding='utf-8') as f:
        return f.read()

def ecrire(n, s):
    with io.open(os.path.join(BASE, n), 'w', encoding='utf-8') as f:
        f.write(s)

def rempl(src, avant, apres, etiquette, n_attendu=1):
    n = src.count(avant)
    assert n == n_attendu, u'%s : %d occurrences (attendu %d)' % (etiquette, n, n_attendu)
    return src.replace(avant, apres)

js = lire('app.js')
assert 'entrerPleinEcran' not in js, u'patch117 deja applique'

# 1. une carte cachee ne se redimensionne pas et ne se recadre pas
js = rempl(js, u"""  const parent = wrap.parentElement;
  const availWidth = Math.min(parent.clientWidth, 1200);""", u"""  const parent = wrap.parentElement;
  // onglet cache : rien a mesurer. L'ouverture de l'onglet rappelle sizeMapWrap.
  if(!parent.clientWidth) return;
  if(wrap.classList.contains('plein-ecran')){
    if(MODE_CANVAS){ redimensionnerCanvas(); demanderDessin(); }
    applyMapTransform();
    return;
  }
  const availWidth = Math.min(parent.clientWidth, 1200);""", 'sizeMapWrap')

js = rempl(js, u"""  const w = wrap.clientWidth, h = wrap.clientHeight;
  mapPanX = Math.min(0, Math.max(w - w * mapZoom, mapPanX));
  mapPanY = Math.min(0, Math.max(h - h * mapZoom, mapPanY));""", u"""  const w = wrap.clientWidth, h = wrap.clientHeight;
  // patch117 : carte cachee (0 x 0) -> on ne touche a rien, sinon le
  // deplacement retombait a (0, 0) avec le zoom garde : en pleine mer
  if(!w || !h) return;
  // en plein ecran le cadre est plus haut que la carte : on borne sur la
  // vraie hauteur de la carte, et on la centre si elle est plus petite
  const cw = w * mapZoom;
  const ch = (window.__mapAspectRatio ? w / window.__mapAspectRatio : h) * mapZoom;
  mapPanX = cw > w ? Math.min(0, Math.max(w - cw, mapPanX)) : (w - cw) / 2;
  mapPanY = ch > h ? Math.min(0, Math.max(h - ch, mapPanY)) : (h - ch) / 2;""", 'clampMapPan')

js = rempl(js, u"""  if(!cv || !wrap || !CV.ctx) return;
  // au-dela de 2 le gain est invisible et le cout de remplissage double""", u"""  if(!cv || !wrap || !CV.ctx) return;
  if(!wrap.clientWidth || !wrap.clientHeight) return;   // patch117 : carte cachee
  // au-dela de 2 le gain est invisible et le cout de remplissage double""", 'canvas')

# 2. plein ecran : a la fin d'un geste, et en changeant d'onglet
js = rempl(js, u"""    } else if(e.touches.length === 0){
      touchPinch = null;
      mapDragging = false;
    }
  });
}""", u"""    } else if(e.touches.length === 0){
      touchPinch = null;
      mapDragging = false;
      majPleinEcran();   // patch117
    }
  });
}""", 'fin du geste')
js = rempl(js, u"""    if(tab.dataset.tab === 'territoire') sizeMapWrap(window.__mapAspectRatio);""",
          u"""    if(tab.dataset.tab !== 'territoire') quitterPleinEcran();   // patch117
    if(tab.dataset.tab === 'territoire') sizeMapWrap(window.__mapAspectRatio);""", 'onglet')

# le bouton Reduire, dans le cadre de la carte
h = lire('index.html')
h = rempl(h, u"""          <div class="map-legende" id="mapLegende"></div>
        </div>""", u"""          <div class="map-legende" id="mapLegende"></div>
          <button type="button" class="map-reduire" id="mapReduire" aria-label="Réduire la carte">
            <svg viewBox="0 0 24 24" width="16" height="16" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"><path d="M9 4v5H4M15 4v5h5M9 20v-5H4M15 20v-5h5"/></svg>
            Réduire</button>
        </div>""", 'bouton')
ecrire('index.html', h)

js += u"""

// ---------- patch117 : la carte en plein ecran sur telephone ----------
// Idee de LeoLesel : des qu'on zoome, la carte prend tout l'ecran, sauf la
// barre d'onglets du bas. Seulement sur telephone et en mode canvas (le mode
// SVG de secours garde le cadre fixe).
const PLEIN_ECRAN_SEUIL = 1.15;
const pleinEcranPossible = () => canvasActif() && window.matchMedia('(max-width: 720px)').matches;
const carteEnPleinEcran = () => {
  const w = document.getElementById('mapWrap');
  return !!(w && w.classList.contains('plein-ecran'));
};

// change le cadre en gardant au centre le point qu'on regardait
function recadrerCarte(changer){
  const wrap = document.getElementById('mapWrap');
  if(!wrap) return;
  const ech = echelleCarte() * mapZoom;
  const cx = (wrap.clientWidth / 2 - mapPanX) / ech, cy = (wrap.clientHeight / 2 - mapPanY) / ech;
  changer(wrap);
  redimensionnerCanvas();
  const ech2 = echelleCarte() * mapZoom;
  mapPanX = wrap.clientWidth / 2 - cx * ech2;
  mapPanY = wrap.clientHeight / 2 - cy * ech2;
  applyMapTransform();
  demanderDessin();
}

function entrerPleinEcran(){
  if(carteEnPleinEcran() || !pleinEcranPossible()) return;
  const barre = document.querySelector('.sidebar');
  const bas = barre ? Math.max(0, window.innerHeight - barre.getBoundingClientRect().top) : 0;
  recadrerCarte((wrap) => {
    wrap.style.setProperty('--carte-bas', bas + 'px');
    wrap.classList.add('plein-ecran');
    document.body.classList.add('carte-plein-ecran');
  });
}

function quitterPleinEcran(){
  if(!carteEnPleinEcran()) return;
  recadrerCarte((wrap) => {
    wrap.classList.remove('plein-ecran');
    document.body.classList.remove('carte-plein-ecran');
  });
  sizeMapWrap(window.__mapAspectRatio);
}

// a la fin d'un geste : on zoome -> plein ecran ; revenu au depart -> on reduit
function majPleinEcran(){
  if(!carteEnPleinEcran() && mapZoom > PLEIN_ECRAN_SEUIL) entrerPleinEcran();
  else if(carteEnPleinEcran() && mapZoom <= MAP_ZOOM_MIN + 0.01) quitterPleinEcran();
}

document.getElementById('mapReduire').addEventListener('click', (e) => {
  e.stopPropagation();
  mapZoom = MAP_ZOOM_MIN;
  quitterPleinEcran();
  renderMapOverlay();
});
// le bouton ne doit pas lancer un deplacement de la carte
['mousedown', 'touchstart'].forEach(t => document.getElementById('mapReduire')
  .addEventListener(t, (e) => e.stopPropagation(), { passive: true }));
"""
ecrire('app.js', js)

css = lire('style.css')
assert 'plein-ecran' not in css
css += u"""
/* patch117 : la carte en plein ecran sur telephone (barre d'onglets visible) */
.map-reduire{ display:none; }
@media (max-width: 720px){
  .map-wrap.plein-ecran{
    position:fixed; left:0; right:0; top:0; bottom:var(--carte-bas, 0px);
    width:auto !important; height:auto !important; max-width:none; margin:0;
    border:0; border-radius:0; box-shadow:none; z-index:39;
  }
  body.carte-plein-ecran{ overflow:hidden; }
  .map-wrap.plein-ecran .map-reduire{
    display:flex; align-items:center; gap:6px;
    position:absolute; z-index:9; right:12px; top:calc(12px + env(safe-area-inset-top, 0px));
    font:inherit; font-size:.8rem; font-weight:600; color:#fff;
    padding:8px 12px; border-radius:999px; cursor:pointer;
    background:rgba(10,22,40,.82); border:1px solid rgba(169,188,212,.3);
    -webkit-backdrop-filter:blur(8px); backdrop-filter:blur(8px);
    box-shadow:0 6px 16px rgba(0,0,0,.4);
  }
}
"""
ecrire('style.css', css)
print(u'patch117 applique')
