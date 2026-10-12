# -*- coding: utf-8 -*-
u"""
patch119 — carte sur grand écran : légende et fiche sur les côtés (idée de Wally).

Quand la place le permet (ordinateur, écran large), la liste des joueurs
passe dans une colonne à gauche de la carte et la fiche de la commune dans
une colonne à droite : plus rien ne cache la carte. La carte prend toute la
largeur restante ; si le cadre est plus large que la France, elle est
centrée et la place en plus sert quand on zoome.
Si l'écran n'est pas assez large pour que la carte garde au moins 90 % de
sa taille d'avant, on garde l'affichage actuel (légende et fiche par-dessus).

Technique : l'échelle de la carte devient min(largeur, hauteur) du cadre au
lieu de la seule largeur (identique tant que le cadre a les proportions de
la France), et le recadrage / les départements visibles en tiennent compte.
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
assert 'placerScene' not in js, u'patch119 deja applique'

# 1. echelle : la France tient toujours entiere dans le cadre a zoom 1
js = rempl(js, u"""  if(!wrap || !MAP_W) return 1;
  return wrap.clientWidth / MAP_W;
}""", u"""  if(!wrap || !MAP_W) return 1;
  // patch119 : le cadre peut etre plus large (grand ecran) ou plus haut
  // (plein ecran) que la carte : la France doit toujours y tenir entiere
  if(!wrap.clientHeight || !MAP_H) return wrap.clientWidth / MAP_W;
  return Math.min(wrap.clientWidth / MAP_W, wrap.clientHeight / MAP_H);
}""", 'echelle')

js = rempl(js, u"""  const cw = w * mapZoom;
  const ch = (window.__mapAspectRatio ? w / window.__mapAspectRatio : h) * mapZoom;""",
          u"""  const ech = echelleCarte();   // patch119
  const cw = MAP_W * ech * mapZoom;
  const ch = MAP_H * ech * mapZoom;""", 'recadrage')

js = rempl(js, u"""  const hc = MAP_H * (w / MAP_W);
  const vus = new Set();
  const ajouter = (c) => {
    if(c.lat == null) return;
    const p = project(c.lat, c.lon);
    const x = p.x * w * mapZoom + mapPanX, y = p.y * hc * mapZoom + mapPanY;""",
          u"""  const ech = echelleCarte();   // patch119
  const vus = new Set();
  const ajouter = (c) => {
    if(c.lat == null) return;
    const p = project(c.lat, c.lon);
    const x = p.x * MAP_W * ech * mapZoom + mapPanX, y = p.y * MAP_H * ech * mapZoom + mapPanY;""", 'visibles')

# 2. taille du cadre en mode large
js = rempl(js, u"""  const availWidth = Math.min(parent.clientWidth, 1200);""", u"""  if(wrap.closest('.map-scene.large')){ tailleCarteLarge(wrap, ratio); return; }   // patch119
  const availWidth = Math.min(parent.clientWidth, 1200);""", 'taille')

# 3. legende et fiche : dans les colonnes quand la scene est large
js = rempl(js, u"""  if(!leg || !wrap || !bas) return;
  const dessous = surTelephone();""", u"""  if(!leg || !wrap || !bas) return;
  if(placerScene()) return;   // patch119 : grand ecran, legende a gauche
  const dessous = surTelephone();""", 'legende')

for nom, avant in ((u'placerPanneau', u"""function placerPanneau(el, xCss, yCss){
"""), (u'recadrerPanneau', u"""function recadrerPanneau(el){
"""), (u'poserPanneauDeplace', u"""function poserPanneauDeplace(el){
""")):
    js = rempl(js, avant, avant + u"""  if(el && el.closest('.map-cote')) return;   // patch119 : fiche dans sa colonne
""", nom)
js = rempl(js, u"""    if(!(enHaut || e.target.closest('.pc-tete')) || e.target.closest('button, a, input, select, [data-pc], [data-profil]')) return;""",
          u"""    if(el.closest('.map-cote')) return;   // patch119 : rien a deplacer dans la colonne
    if(!(enHaut || e.target.closest('.pc-tete')) || e.target.closest('button, a, input, select, [data-pc], [data-profil]')) return;""", 'glisser')

js += u"""

// ---------- patch119 : grand ecran, legende et fiche sur les cotes ----------
const SCENE_GAUCHE = 250, SCENE_DROITE = 320, SCENE_ECART = 16;
let sceneLarge = false;

// La scene large n'est retenue que si la carte y reste au moins aussi grande
// qu'en affichage classique. null = impossible a mesurer (rien a changer).
function carteLargePossible(){
  if(!canvasActif() || surTelephone() || !window.__mapAspectRatio) return false;
  const panel = document.getElementById('panel-territoire');
  const main = panel && panel.parentElement;
  if(!main || !main.clientWidth) return null;
  const cs = getComputedStyle(main);
  const dispo = Math.min(1900, main.clientWidth - parseFloat(cs.paddingLeft || 0) - parseFloat(cs.paddingRight || 0));
  const cellule = dispo - SCENE_GAUCHE - SCENE_DROITE - 2 * SCENE_ECART;
  const classique = Math.min(Math.min(dispo, 1200), window.innerHeight * 0.78 * window.__mapAspectRatio);
  // un peu plus petite qu'avant reste un gain : plus rien ne la recouvre
  return cellule >= classique * 0.9;
}

function placerScene(){
  const wrap = document.getElementById('mapWrap');
  const leg = document.getElementById('mapLegende');
  const pan = document.getElementById('mapPanneau');
  const panel = document.getElementById('panel-territoire');
  if(!wrap || !leg || !pan || !panel) return false;
  const large = carteLargePossible();
  if(large === null) return sceneLarge;
  let scene = document.getElementById('mapScene');
  if(!scene){
    if(!large) return false;
    scene = document.createElement('div');
    scene.className = 'map-scene';
    scene.id = 'mapScene';
    wrap.parentElement.insertBefore(scene, wrap);
    scene.innerHTML = `<aside class="map-cote gauche" id="mapCoteG"></aside>`;
    scene.appendChild(wrap);
    scene.insertAdjacentHTML('beforeend', `<aside class="map-cote droite" id="mapCoteD">
      <div class="map-cote-vide"><b>Aucune commune choisie</b>Clique sur une commune ou un département de la carte pour voir sa fiche ici.</div></aside>`);
  }
  const change = large !== sceneLarge;
  sceneLarge = large;
  scene.classList.toggle('large', large);
  panel.classList.toggle('carte-large', large);
  const coteD = document.getElementById('mapCoteD');
  if(large){
    if(leg.parentElement.id !== 'mapCoteG') document.getElementById('mapCoteG').appendChild(leg);
    leg.classList.remove('en-dessous');
    if(pan.parentElement !== coteD) coteD.insertBefore(pan, coteD.firstChild);
    pan.style.left = ''; pan.style.top = ''; pan.style.bottom = '';
  } else if(pan.parentElement !== wrap){
    wrap.appendChild(pan);
  }
  if(change) sizeMapWrap(window.__mapAspectRatio);
  return large;
}

// Le cadre prend la colonne du milieu ; sa hauteur reste celle d'un ecran.
function tailleCarteLarge(wrap, ratio){
  const scene = wrap.parentElement;
  const cellule = scene.clientWidth - SCENE_GAUCHE - SCENE_DROITE - 2 * SCENE_ECART;
  const haut = Math.max(320, Math.min(window.innerHeight * 0.82, cellule / ratio));
  // au-dela, ce ne serait plus que de la mer sur les cotes
  const larg = Math.min(cellule, haut * ratio * 1.6);
  wrap.style.width = Math.round(larg) + 'px';
  wrap.style.height = Math.round(haut) + 'px';
  scene.style.setProperty('--carte-h', Math.round(haut) + 'px');
  if(MODE_CANVAS){ redimensionnerCanvas(); demanderDessin(); }
  applyMapTransform();
}
"""
ecrire('app.js', js)

css = lire('style.css')
assert 'map-scene' not in css
css += u"""
/* patch119 : grand ecran, legende et fiche sur les cotes de la carte */
.map-scene:not(.large) .map-cote{ display:none; }
#panel-territoire.carte-large, #panel-territoire.carte-large .territory{ max-width:1900px; }
.map-scene.large{
  display:grid; grid-template-columns:250px minmax(0, 1fr) 320px; gap:16px; align-items:start;
}
.map-scene.large .map-wrap{ justify-self:center; max-width:none; margin:0; }
.map-cote{
  position:sticky; top:16px; max-height:var(--carte-h, 80vh); overflow-y:auto;
  scrollbar-width:thin;
}
.map-cote .map-legende{
  position:static; width:auto; max-height:none; box-shadow:none;
}
.map-cote .pc{
  position:static; width:auto; max-height:none; box-shadow:0 10px 26px rgba(0,0,0,.35);
}
.map-cote .pc::before{ display:none; }
.map-cote .pc{ padding-top:13px; }
.map-cote-vide{
  display:none; padding:18px 16px; border-radius:14px; text-align:center;
  border:1.5px dashed rgba(169,188,212,.22); color:var(--brume); font-size:.82rem; line-height:1.45;
}
.map-cote-vide b{ display:block; color:#fff; font-family:var(--titre); font-weight:800; font-size:1.1rem; margin-bottom:4px; }
.map-cote .pc[hidden] ~ .map-cote-vide{ display:block; }
"""
ecrire('style.css', css)
print(u'patch119 applique')
