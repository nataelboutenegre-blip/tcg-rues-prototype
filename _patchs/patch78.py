# -*- coding: utf-8 -*-
u"""
patch78 — Radar : zoom sur la carte (classé et entraînement).

- Ordinateur : la molette ou le trackpad (défilement à deux doigts,
  pincement, y compris sur Safari) zoome autour du curseur ; carte
  zoomée, on la fait glisser à la souris ou au trackpad (cliquer-glisser).
- Téléphone et ordinateur : boutons + / − / recentrer dans le coin de la
  carte. Le zoom par bouton se fait autour du point posé s'il y en a un.
  Carte zoomée : on la fait glisser au doigt.
- Un glissement ne pose pas de point (seul un clic ou un tap le fait).
- Fond de carte en canvas sous le SVG : les limites des départements
  apparaissent dès qu'on zoome, celles des communes à partir d'un zoom x2,5
  (mêmes fichiers contours/ que la carte Territoire, même cache). Le SVG
  ne garde que le trait de côte, les points et les clics.
- Chaque nouvelle commune repart de la vue entière (ou de la région à
  l'entraînement). Les points gardent leur taille à l'écran.
Aucun changement serveur : le serveur ne reçoit que la position du point.
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

def rempl(src, avant, apres, etiquette):
    n = src.count(avant)
    assert n == 1, u'%s : %d occurrences (attendu 1)' % (etiquette, n)
    return src.replace(avant, apres)

h = lire('index.html')
h = rempl(h,
u'''        <div class="rd-carte"><svg id="rdCarte" role="img" aria-label="Carte de France : clique pour placer la commune"></svg></div>''',
u'''        <div class="rd-carte"><canvas id="rdFond" aria-hidden="true"></canvas><svg id="rdCarte" role="img" aria-label="Carte de France : clique pour placer la commune"></svg>
          <div class="rd-zoom-btns" role="group" aria-label="Zoom de la carte">
            <button type="button" data-zoom="plus" aria-label="Zoomer">+</button>
            <button type="button" data-zoom="moins" aria-label="Dézoomer">−</button>
            <button type="button" data-zoom="raz" aria-label="Revoir toute la carte" hidden>⤢</button>
          </div></div>''', 'boutons zoom')
ecrire('index.html', h)

js = lire('app.js')
# la vue dessinée tient compte du zoom ; on garde ce qui est dessiné pour redessiner
js = rempl(js,
u'''function radarDessiner(manche){
  const svg = document.getElementById('rdCarte');
  if(!svg || !radarAssurerBornes()) return;
  const contour = FRANCE_OUTLINE || cdjContour;
  const vue = radarModeEntr && entr.vue ? entr.vue : null;
  svg.setAttribute('viewBox', vue ? `${vue.x} ${vue.y} ${vue.w} ${vue.h}` : `0 0 ${cdjBornes.w.toFixed(2)} ${cdjBornes.h.toFixed(2)}`);
  svg.classList.toggle('rd-zoom', !!vue);
  const ray = (vue ? vue.w : cdjBornes.w) / 80;''',
u'''function radarDessiner(manche){
  const svg = document.getElementById('rdCarte');
  if(!svg || !radarAssurerBornes()) return;
  radarDessinCourant = manche || null;
  const contour = FRANCE_OUTLINE || cdjContour;
  const vue = radarModeEntr && entr.vue ? entr.vue : null;
  const v = radarVueCourante();
  svg.setAttribute('viewBox', `${v.x.toFixed(3)} ${v.y.toFixed(3)} ${v.w.toFixed(3)} ${v.h.toFixed(3)}`);
  svg.classList.toggle('rd-zoom', !!vue);
  svg.classList.toggle('rd-zoome', radarZoom.k > 1);
  const raz = document.querySelector('.rd-zoom-btns [data-zoom="raz"]');
  if(raz) raz.hidden = radarZoom.k <= 1;
  const ray = v.w / 80;''', 'radarDessiner zoom')

js = rempl(js,
u'''document.getElementById('rdCarte').addEventListener('click', (e) => {
  if(radarRevele || radarEnvoi || !cdjBornes) return;''',
u'''// ----- zoom de la carte Radar (patch78) -----
let radarZoom = { k: 1, cx: null, cy: null };
let radarDessinCourant = null, radarGeste = null, radarGlisse = false, radarGesteSafari = null;
const RADAR_ZOOM_MAX = 8;
function radarVueBase(){
  const vue = radarModeEntr && entr.vue ? entr.vue : null;
  return vue ? { x: vue.x, y: vue.y, w: vue.w, h: vue.h } : { x: 0, y: 0, w: cdjBornes.w, h: cdjBornes.h };
}
function radarVueCourante(){
  const b = radarVueBase(), k = radarZoom.k;
  if(k <= 1) return b;
  const w = b.w / k, h = b.h / k;
  let cx = radarZoom.cx == null ? b.x + b.w / 2 : radarZoom.cx;
  let cy = radarZoom.cy == null ? b.y + b.h / 2 : radarZoom.cy;
  cx = Math.min(Math.max(cx, b.x + w / 2), b.x + b.w - w / 2);
  cy = Math.min(Math.max(cy, b.y + h / 2), b.y + b.h - h / 2);
  radarZoom.cx = cx; radarZoom.cy = cy;
  return { x: cx - w / 2, y: cy - h / 2, w, h };
}
function radarZoomRaz(){ radarZoom = { k: 1, cx: null, cy: null }; }
// facteur f autour du point (px, py) de la carte, qui reste sous le curseur
function radarZoomer(f, px, py){
  if(!cdjBornes) return;
  const b = radarVueBase(), v0 = radarVueCourante();
  const k = Math.min(RADAR_ZOOM_MAX, Math.max(1, radarZoom.k * f));
  if(k === radarZoom.k) return;
  if(px == null){ px = v0.x + v0.w / 2; py = v0.y + v0.h / 2; }
  const rx = (px - v0.x) / v0.w, ry = (py - v0.y) / v0.h;
  const w = b.w / k, h = b.h / k;
  radarZoom = { k, cx: px - rx * w + w / 2, cy: py - ry * h + h / 2 };
  if(k === 1) radarZoomRaz();
  radarDessiner(radarDessinCourant);
}
function radarPointCarte(e){
  const svg = document.getElementById('rdCarte'), pt = svg.createSVGPoint();
  pt.x = e.clientX; pt.y = e.clientY;
  return pt.matrixTransform(svg.getScreenCTM().inverse());
}
(function(){
  const svg = document.getElementById('rdCarte');
  // molette, défilement à deux doigts et pincement du trackpad (Chrome,
  // Firefox : ctrlKey). Le facteur suit l'amplitude : un cran de molette
  // zoome franchement, un trackpad zoome en douceur.
  svg.addEventListener('wheel', (e) => {
    if(!cdjBornes || document.getElementById('rdManche').hidden) return;
    e.preventDefault();
    if(e.ctrlKey && radarGesteSafari != null) return;   // Safari envoie déjà le geste
    const d = e.deltaY * (e.deltaMode === 1 ? 33 : e.deltaMode === 2 ? 400 : 1);
    const f = Math.exp(-d * (e.ctrlKey ? 0.012 : 0.0025));
    const q = radarPointCarte(e);
    radarZoomer(Math.min(1.6, Math.max(1 / 1.6, f)), q.x, q.y);
  }, { passive: false });
  // pincement sur Safari (trackpad du Mac, iPhone, iPad)
  svg.addEventListener('gesturestart', (e) => { e.preventDefault(); radarGesteSafari = 1; });
  svg.addEventListener('gesturechange', (e) => {
    e.preventDefault();
    if(radarGesteSafari == null || !cdjBornes) return;
    const f = e.scale / radarGesteSafari; radarGesteSafari = e.scale;
    const q = radarPointCarte(e);
    radarZoomer(f, q.x, q.y);
  });
  svg.addEventListener('gestureend', (e) => { e.preventDefault(); radarGesteSafari = null; });
  svg.addEventListener('pointerdown', (e) => {
    // un glissement au doigt ne produit pas toujours de clic : chaque geste repart à zéro
    radarGlisse = false;
    if(radarZoom.k <= 1 || (e.pointerType === 'mouse' && e.button !== 0)) return;
    radarGeste = { id: e.pointerId, x: e.clientX, y: e.clientY, cx: radarZoom.cx, cy: radarZoom.cy, bouge: false };
  });
  svg.addEventListener('pointermove', (e) => {
    const g = radarGeste; if(!g || g.id !== e.pointerId) return;
    const dx = e.clientX - g.x, dy = e.clientY - g.y;
    if(!g.bouge && Math.hypot(dx, dy) < 6) return;
    if(!g.bouge){ g.bouge = true; try { svg.setPointerCapture(e.pointerId); } catch(err){} }
    const m = svg.getScreenCTM();
    radarZoom.cx = g.cx - dx / m.a; radarZoom.cy = g.cy - dy / m.d;
    radarDessiner(radarDessinCourant);
  });
  const fin = (e) => { const g = radarGeste; if(!g || g.id !== e.pointerId) return; if(g.bouge) radarGlisse = true; radarGeste = null; };
  svg.addEventListener('pointerup', fin);
  svg.addEventListener('pointercancel', fin);
  document.querySelector('.rd-zoom-btns').addEventListener('click', (e) => {
    const b = e.target.closest('[data-zoom]'); if(!b || !cdjBornes) return;
    if(b.dataset.zoom === 'raz'){ radarZoomRaz(); radarDessiner(radarDessinCourant); return; }
    // autour du point posé s'il y en a un, sinon au centre
    let px = null, py = null;
    if(radarPin && !radarRevele){ [px, py] = cdjPx(+radarPin[0], +radarPin[1]).map(Number); }
    radarZoomer(b.dataset.zoom === 'plus' ? 1.6 : 1 / 1.6, px, py);
  });
})();

document.getElementById('rdCarte').addEventListener('click', (e) => {
  // la fin d'un glissement n'est pas un clic
  if(radarGlisse){ radarGlisse = false; return; }
  if(radarRevele || radarEnvoi || !cdjBornes) return;''', 'gestes')

# chaque nouvelle commune repart de la vue entière
js = rempl(js,
u'''  radarPin = null; radarRevele = false; radarEnvoi = false;
  radarMontrer('rdManche');
  const n = data.manche;''',
u'''  radarPin = null; radarRevele = false; radarEnvoi = false;
  radarZoomRaz();
  radarMontrer('rdManche');
  const n = data.manche;''', 'raz duel')
js = rempl(js,
u'''  radarPin = null; radarRevele = false; radarEnvoi = false;
  radarMontrer('rdManche');
  document.getElementById('rdNum').textContent = `Commune ${n + 1} sur ${ENTR_MANCHES} · entraînement`;''',
u'''  radarPin = null; radarRevele = false; radarEnvoi = false;
  radarZoomRaz();
  radarMontrer('rdManche');
  document.getElementById('rdNum').textContent = `Commune ${n + 1} sur ${ENTR_MANCHES} · entraînement`;''', 'raz entr')
# l'aide rappelle le zoom sur ordinateur
AIDE_AVANT = u'''document.getElementById('rdVerdict').innerHTML = '<span>Clique sur la carte, puis valide.</span>';'''
assert js.count(AIDE_AVANT) == 2, js.count(AIDE_AVANT)
js = js.replace(AIDE_AVANT, u'''document.getElementById('rdVerdict').innerHTML = `<span>Clique sur la carte, puis valide.${RADAR_SOURIS ? ' La molette zoome.' : ''}</span>`;''')
js = rempl(js, u'''const ENTR_MANCHES = 5,''', u'''const RADAR_SOURIS = window.matchMedia && matchMedia('(hover: hover) and (pointer: fine)').matches;
const ENTR_MANCHES = 5,''', 'souris')

# le fond de carte passe dans un canvas sous le SVG : France, départements
# (dès qu'on zoome), communes (zoom fort). Le SVG ne garde que le trait de
# côte, les points et les clics.
js = rempl(js,
u"""  if(vue && entr.depsPath) h += `<path class="rd-dep" d="${entr.depsPath}"/>`;
  if(manche){
    const [cx, cy] = cdjPx(+manche.lon, +manche.lat);""",
u"""  radarDessinerFond(v, !!vue);
  if(manche){
    const [cx, cy] = cdjPx(+manche.lon, +manche.lat);""", 'fond canvas')
js = rempl(js,
u"""function radarZoomRaz(){ radarZoom = { k: 1, cx: null, cy: null }; }""",
u"""function radarZoomRaz(){ radarZoom = { k: 1, cx: null, cy: null }; }

// ----- fond de la carte Radar en canvas (patch78) -----
const RADAR_SEUIL_COMMUNES = 2.5;          // zoom à partir duquel on dessine les communes
let radarFrance = null;                     // contour du pays (Path2D, unités de carte)
let radarDeps = null, radarDepsTrait = null, radarDepsEnCours = false;   // { code: [x0, y0, x1, y1] }
const radarCommunes = new Map(), radarCommunesEnCours = new Set();       // dep -> Path2D
function radarRedessiner(){ if(!document.getElementById('rdManche').hidden) radarDessiner(radarDessinCourant); }
function radarCheminAnneaux(anneaux, p){
  for(const a of anneaux){ a.forEach(([lo, la], i) => { const [X, Y] = cdjPx(lo, la).map(Number); i ? p.lineTo(X, Y) : p.moveTo(X, Y); }); p.closePath(); }
  return p;
}
async function radarChargerDeps(){
  if(radarDeps || radarDepsEnCours) return;
  radarDepsEnCours = true;
  try{
    const deps = await (await fetch('contours-departements.json', { cache: 'force-cache' })).json();
    const trait = new Path2D(), bornes = {};
    for(const [code, polys] of Object.entries(deps)){
      if(code.length !== 2) continue;   // métropole et Corse
      const anneaux = polys.map(poly => typeof poly[0][0] === 'number' ? poly : poly[0]);
      radarCheminAnneaux(anneaux, trait);
      let x0 = 1e9, y0 = 1e9, x1 = -1e9, y1 = -1e9;
      for(const a of anneaux) for(const [lo, la] of a){ const [X, Y] = cdjPx(lo, la).map(Number); x0 = Math.min(x0, X); x1 = Math.max(x1, X); y0 = Math.min(y0, Y); y1 = Math.max(y1, Y); }
      bornes[code] = [x0, y0, x1, y1];
    }
    radarDeps = bornes; radarDepsTrait = trait;
    radarRedessiner();
  } catch(e){ radarDepsEnCours = false; }
}
// les mêmes fichiers que la carte Territoire, et le même cache (CONTOURS)
async function radarChargerCommunes(dep){
  if(radarCommunes.has(dep) || radarCommunesEnCours.has(dep)) return;
  radarCommunesEnCours.add(dep);
  try{
    let data = CONTOURS.get(dep);
    if(!data || data === 'erreur'){
      const r = await fetch(`contours/${dep}.json`, { cache: 'force-cache' });
      if(!r.ok) throw new Error('contours');
      data = await r.json();
      if(!CONTOURS.get(dep)) CONTOURS.set(dep, data);
    }
    const p = new Path2D();
    for(const anneaux of Object.values(data)) radarCheminAnneaux(anneaux, p);
    radarCommunes.set(dep, p);
    radarRedessiner();
  } catch(e){} finally { radarCommunesEnCours.delete(dep); }
}
function radarDessinerFond(v, region){
  const svg = document.getElementById('rdCarte'), cv = document.getElementById('rdFond');
  if(!cv || !svg) return;
  const rs = svg.getBoundingClientRect(), parent = cv.parentElement, rp = parent.getBoundingClientRect();
  const W = rs.width, H = rs.height;
  if(!W || !H) return;
  const dpr = Math.min(2, window.devicePixelRatio || 1);
  cv.style.left = (rs.left - rp.left - parent.clientLeft) + 'px';
  cv.style.top = (rs.top - rp.top - parent.clientTop) + 'px';
  cv.style.width = W + 'px'; cv.style.height = H + 'px';
  if(cv.width !== Math.round(W * dpr) || cv.height !== Math.round(H * dpr)){ cv.width = Math.round(W * dpr); cv.height = Math.round(H * dpr); }
  const x = cv.getContext('2d');
  x.setTransform(1, 0, 0, 1, 0, 0); x.clearRect(0, 0, cv.width, cv.height);
  // même cadrage que le SVG (preserveAspectRatio « meet »)
  const s = Math.min(W / v.w, H / v.h), ox = (W - v.w * s) / 2, oy = (H - v.h * s) / 2;
  x.setTransform(dpr * s, 0, 0, dpr * s, dpr * (ox - v.x * s), dpr * (oy - v.y * s));
  const px = 1 / s;   // un pixel d'écran, en unités de carte
  if(!radarFrance) radarFrance = radarCheminAnneaux(FRANCE_OUTLINE || cdjContour, new Path2D());
  x.fillStyle = region ? '#172D4C' : '#1F3A60'; x.fill(radarFrance);
  if(region && entr.depsPath){
    if(entr.depsP2DSrc !== entr.depsPath){ entr.depsP2D = new Path2D(entr.depsPath); entr.depsP2DSrc = entr.depsPath; }
    x.fillStyle = '#22416B'; x.fill(entr.depsP2D);
  }
  const k = radarZoom.k;
  if(k > 1 || region){
    if(!radarDeps){ radarChargerDeps(); return; }
    x.save(); x.clip(radarFrance);
    // les communes des départements visibles, à fort zoom
    if(k >= RADAR_SEUIL_COMMUNES){
      x.lineWidth = 0.7 * px; x.strokeStyle = `rgba(169,188,212,${Math.min(0.3, 0.12 + (k - RADAR_SEUIL_COMMUNES) * 0.12).toFixed(3)})`;
      for(const [dep, b] of Object.entries(radarDeps)){
        if(b[2] < v.x || b[0] > v.x + v.w || b[3] < v.y || b[1] > v.y + v.h) continue;
        const p = radarCommunes.get(dep);
        if(p) x.stroke(p); else radarChargerCommunes(dep);
      }
    }
    x.lineWidth = 1.1 * px; x.strokeStyle = `rgba(169,188,212,${region ? 0.55 : Math.min(0.55, (k - 1) * 0.5).toFixed(3)})`;
    x.stroke(radarDepsTrait);
    x.restore();
  }
}
window.addEventListener('resize', () => radarRedessiner());""", 'fond canvas fonctions')

ecrire('app.js', js)

css = lire('style.css')
MARQUE = u'/* ---------- Radar : zoom (patch78) ---------- */'
assert MARQUE not in css, u'patch78 déjà passé'
css = css.rstrip('\n') + u'\n\n' + MARQUE + u'''
.rd-carte{ position:relative; }
.rd-carte svg.rd-zoome{ touch-action:none; cursor:grab; }
.rd-carte svg.rd-zoome:active{ cursor:grabbing; }
.rd-zoom-btns{ position:absolute; right:12px; top:12px; display:flex; flex-direction:column; gap:6px; z-index:2; }
.rd-zoom-btns button{ width:40px; height:40px; border-radius:10px; border:1px solid rgba(169,188,212,.35);
  background: rgba(11,24,48,.85); color:#fff; font:700 22px/1 var(--texte); cursor:pointer; display:grid; place-items:center; }
.rd-zoom-btns button:hover{ border-color: var(--c-legendaire); color: var(--c-legendaire); }
.rd-zoom-btns button[hidden]{ display:none; }
.rd-zoom-btns [data-zoom="raz"]{ font-size:18px; }
#rdFond{ position:absolute; left:0; top:0; pointer-events:none; z-index:0; }
#rdCarte{ position:relative; z-index:1; }
#rdCarte .cdj-fr{ fill:none; }
'''
ecrire('style.css', css)
print(u'patch78 : OK')
