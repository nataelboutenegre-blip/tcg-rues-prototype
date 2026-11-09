# patch394 (10/11/2026) : une échelle de distance sur la carte (zintox, 9/11).
import sys
def rep(chemin, avant, apres, nb=1):
    t = open(chemin, encoding='utf-8').read()
    n = t.count(avant)
    if n != nb: sys.exit(f'{chemin} : {n} au lieu de {nb} pour {avant[:70]!r}')
    open(chemin, 'w', encoding='utf-8').write(t.replace(avant, apres))
A = 'app.js'
rep(A, """function applyMapTransform(){
  clampMapPan();
""", """// patch394 : l'échelle de distance, en bas à gauche de la carte (zintox, 9/11)
const ECH_PAS = [1, 2, 5, 10, 20, 25, 50, 100, 200, 250, 500];
let echelleKm = 0, echellePx = 0;
function majEchelle(){
  const wrap = document.getElementById('mapWrap');
  if(!wrap || !mapBounds || !MAP_H) return;
  let el = document.getElementById('mapEchelle');
  if(!el){
    el = document.createElement('div');
    el.id = 'mapEchelle'; el.className = 'map-echelle'; el.setAttribute('aria-hidden', 'true');
    el.innerHTML = '<span></span><i></i>';
    wrap.appendChild(el);
  }
  // la carte garde les proportions réelles à la latitude moyenne : 1 degré de latitude = 111,19 km
  const kmParPx = (mapBounds.latMax - mapBounds.latMin) * 111.19 / (MAP_H * echelleCarte() * mapZoom);
  if(!isFinite(kmParPx) || kmParPx <= 0){ el.hidden = true; return; }
  let km = ECH_PAS[0];
  for(const k of ECH_PAS) if(k / kmParPx <= 90) km = k;
  const px = Math.max(8, Math.round(km / kmParPx));
  el.hidden = false;
  if(km !== echelleKm || px !== echellePx){
    echelleKm = km; echellePx = px;
    el.firstChild.textContent = km + '\\u00a0km';
    el.lastChild.style.width = px + 'px';
  }
}
function applyMapTransform(){
  clampMapPan();
  majEchelle();   // patch394
""")
rep('style.css', ".as-jgarn{ font-size:.7rem; color: var(--brume); margin:4px 0 0; }   /* patch393 */",
""".as-jgarn{ font-size:.7rem; color: var(--brume); margin:4px 0 0; }   /* patch393 */
/* patch394 : l'échelle de distance */
.map-echelle{ position:absolute; z-index:2; left:10px; bottom:10px; pointer-events:none;
  display:flex; flex-direction:column; align-items:flex-start; gap:3px;
  color:#E0ECFA; font-size:.68rem; font-weight:700; letter-spacing:.02em; line-height:1;
  text-shadow:0 1px 2px rgba(7,17,31,.95), 0 0 4px rgba(7,17,31,.9); }
.map-echelle i{ display:block; height:5px; border:2px solid rgba(224,236,250,.92); border-top:0;
  box-shadow:0 1px 2px rgba(7,17,31,.7); }
.map-echelle[hidden], .map-wrap.outremer .map-echelle, .map-wrap.panneau-ouvert .map-echelle{ display:none; }
.map-wrap.plein-ecran .map-echelle{ bottom:calc(10px + env(safe-area-inset-bottom, 0px)); }""")
print('patch394 ok')
