# patch373 (8/11/2026) : cartouche « Paris et petite couronne » sur la carte
# Territoire (idée d'Arkhannou sur Discord).
#
# Vue de la France entière, Paris et les Hauts-de-Seine, la Seine-Saint-Denis et
# le Val-de-Marne font quelques pixels : impossible de les toucher pour lire les
# pourcentages. Un encart dans un coin les montre en grand, colorés comme sur la
# carte (le joueur en tête de chaque département) ; toucher un département ouvre
# sa fiche habituelle (parts de chaque joueur, libres, « Zoomer ici »).
#   - visible seulement en vue par départements (comme la carte elle-même) ;
#   - en haut à gauche, ou en haut à droite quand la légende occupe ce coin ;
#   - les quatre départements de la grande couronne en fond, pour se repérer.
import pathlib

def rep(s, avant, apres, n=1):
    c = s.count(avant)
    assert c == n, f'{c} fois au lieu de {n} : {avant[:80]!r}'
    return s.replace(avant, apres)

F = pathlib.Path('app.js'); s = F.read_text(encoding='utf-8')
assert 'patch373' not in s, 'patch373 déjà appliqué'

# ---------- le cartouche ----------
s = rep(s, """function vueDepartements(){
  return mapZoom < SEUIL_CONTOURS && CONTOURS_DEPTS && typeof CONTOURS_DEPTS === 'object';
}""",
"""function vueDepartements(){
  return mapZoom < SEUIL_CONTOURS && CONTOURS_DEPTS && typeof CONTOURS_DEPTS === 'object';
}

// ---------- patch373 : cartouche « Paris et petite couronne » (idée d'Arkhannou) ----------
const IDF_PC = ['75', '92', '93', '94'];
const IDF_FOND = ['77', '78', '91', '95'];
// où écrire le numéro : un point bien à l'intérieur (les Hauts-de-Seine sont un croissant)
const IDF_ETIQ = { '75': [48.858, 2.345], '92': [48.885, 2.205], '93': [48.915, 2.47], '94': [48.78, 2.47] };
let idfTimer = null, idfSignature = '', idfGeo = null;
function idfPlanifier(){ clearTimeout(idfTimer); idfTimer = setTimeout(idfMaj, 150); }
function idfGeometrie(){
  if(idfGeo) return idfGeo;
  if(!CONTOURS_DEPTS || typeof CONTOURS_DEPTS !== 'object' || !IDF_PC.every(d => CONTOURS_DEPTS[d])) return null;
  const pt = (lat, lon) => { const p = project(lat, lon); return [p.x * MAP_W, p.y * MAP_H]; };
  let x0 = 1e9, y0 = 1e9, x1 = -1e9, y1 = -1e9;
  const chemins = {};
  for(const dep of IDF_PC.concat(IDF_FOND)){
    const polys = CONTOURS_DEPTS[dep];
    if(!polys) continue;
    let d = '';
    for(const poly of polys){
      const anneau = typeof poly[0][0] === 'number' ? poly : poly[0];
      d += 'M' + anneau.map(([lon, lat]) => {
        const [x, y] = pt(lat, lon);
        if(IDF_PC.includes(dep)){ x0 = Math.min(x0, x); x1 = Math.max(x1, x); y0 = Math.min(y0, y); y1 = Math.max(y1, y); }
        return x.toFixed(2) + ',' + y.toFixed(2);
      }).join('L') + 'Z';
    }
    chemins[dep] = d;
  }
  const m = Math.max(x1 - x0, y1 - y0) * 0.06;
  const vb = { x: x0 - m, y: y0 - m, w: x1 - x0 + 2 * m, h: y1 - y0 + 2 * m };
  const etiq = {};
  for(const dep of IDF_PC) etiq[dep] = pt(IDF_ETIQ[dep][0], IDF_ETIQ[dep][1]);
  idfGeo = { vb, chemins, etiq };
  return idfGeo;
}
// la même couleur que la carte : le joueur en tête du département
function idfCouleurs(){
  const r = CV.reperage;
  const res = {};
  if(!r) return res;
  const compte = {};
  for(const c of r.liste){
    if(!IDF_ETIQ[c.dept]) continue;
    const m = compte[c.dept] || (compte[c.dept] = new Map());
    m.set(c.joueur, (m.get(c.joueur) || 0) + 1);
  }
  for(const dep in compte){
    let meilleur = null, n = 0, total = 0;
    for(const [j, v] of compte[dep]){ total += v; if(v > n){ n = v; meilleur = j; } }
    const jo = r.joueurs.get(meilleur);
    if(!jo) continue;
    const force = (0.3 + 0.55 * (n / total)) * (jo.moi ? 1 : 0.8);
    res[dep] = { couleur: jo.couleur, alpha: opaciteJoueur(meilleur, force) };
  }
  return res;
}
function idfElement(){
  let el = document.getElementById('mapIdf');
  if(el) return el;
  const wrap = document.getElementById('mapWrap');
  if(!wrap) return null;
  el = document.createElement('div');
  el.className = 'map-idf'; el.id = 'mapIdf'; el.hidden = true;
  el.setAttribute('role', 'group'); el.setAttribute('aria-label', 'Paris et petite couronne');
  wrap.appendChild(el);
  // un geste commencé ici n'est pas un déplacement de la carte
  el.addEventListener('mousedown', (e) => e.stopPropagation());
  el.addEventListener('pointerup', (e) => {
    const g = e.target.closest('[data-idf]');
    if(!g) return;
    const r = wrap.getBoundingClientRect();
    ouvrirPanneauDept(g.dataset.idf, e.clientX - r.left, e.clientY - r.top);
    if(e.pointerType !== 'mouse') panneauOuvertAuDoigt = performance.now();
    idfSurligner();
  });
  return el;
}
function idfSurligner(){
  const el = document.getElementById('mapIdf');
  if(!el) return;
  el.querySelectorAll('[data-idf]').forEach(g => g.classList.toggle('on', g.dataset.idf === panneauDept));
}
function idfVisibilite(){
  const el = document.getElementById('mapIdf');
  if(!el) return;
  const voir = !!(el.dataset.pret && vueDepartements());
  if(el.hidden === voir) el.hidden = !voir;
}
function idfMaj(){
  const geo = idfGeometrie();
  const el = geo && idfElement();
  if(!el) return;
  const wrap = document.getElementById('mapWrap'), leg = document.getElementById('mapLegende');
  el.classList.toggle('droite', !!(leg && leg.parentElement === wrap && leg.innerHTML));
  const coul = idfCouleurs();
  const sig = JSON.stringify(coul);
  if(sig !== idfSignature || !el.dataset.pret){
    idfSignature = sig;
    const { vb, chemins, etiq } = geo;
    const fs = vb.w * 0.085;
    const fond = IDF_FOND.filter(d => chemins[d]).map(d => `<path class="idf-ctx" d="${chemins[d]}"/>`).join('');
    const deps = IDF_PC.map(d => {
      const c = coul[d];
      return `<g class="idf-dep${d === panneauDept ? ' on' : ''}" data-idf="${d}"><title>${echapperHtml(DEPT_NAMES[d] || d)}</title>`
        + `<path class="idf-fond" d="${chemins[d]}"/>`
        + (c ? `<path d="${chemins[d]}" fill="${c.couleur}" fill-opacity="${c.alpha.toFixed(3)}"/>` : '')
        + `<path class="idf-trait" d="${chemins[d]}"/></g>`;
    }).join('');
    const nums = IDF_PC.map(d => `<text x="${etiq[d][0].toFixed(2)}" y="${etiq[d][1].toFixed(2)}" font-size="${(d === '75' ? fs * 0.82 : fs).toFixed(2)}" stroke-width="${(fs * 0.2).toFixed(2)}">${d}</text>`).join('');
    el.innerHTML = `<span class="idf-titre"><span class="idf-l">Paris et petite couronne</span><span class="idf-c">Petite couronne</span></span>`
      + `<svg viewBox="${vb.x.toFixed(2)} ${vb.y.toFixed(2)} ${vb.w.toFixed(2)} ${vb.h.toFixed(2)}" aria-hidden="true">${fond}${deps}${nums}</svg>`;
    el.dataset.pret = '1';
  }
  idfVisibilite();
}""")

# mises à jour : données, couleurs, zoom, légende, fiche
s = rep(s, """  if(rendreALOuverture('territoire', renderMapOverlay)) return;
  omfRafraichir();   // patch220""",
"""  if(rendreALOuverture('territoire', renderMapOverlay)) return;
  omfRafraichir();   // patch220
  idfPlanifier();   // patch373""")
s = rep(s, """  majReperage(CV.donnees.liste, CV.donnees.joueurs);
  return CV.donnees;""",
"""  majReperage(CV.donnees.liste, CV.donnees.joueurs);
  idfPlanifier();   // patch373 : les couleurs du cartouche
  return CV.donnees;""")
s = rep(s, """function applyMapTransform(){
  clampMapPan();""",
"""function applyMapTransform(){
  clampMapPan();
  idfVisibilite();   // patch373""")
s = rep(s, "  if(placerScene()) return;   // patch119 : grand ecran, legende a gauche",
"""  idfPlanifier();   // patch373 : le cartouche change de coin avec la légende
  if(placerScene()) return;   // patch119 : grand ecran, legende a gauche""")
s = rep(s, """  panneauCommune = null;
  panneauDept = null;
  panneauAncre = null;
  panneauDeplace = null;
}""",
"""  panneauCommune = null;
  panneauDept = null;
  panneauAncre = null;
  panneauDeplace = null;
  idfSurligner();   // patch373
}""")
s = rep(s, "  const gesteHorsCarte = (e) => !!(e.target && e.target.closest && e.target.closest('#mapPanneau, #mapLegende'));",
           "  const gesteHorsCarte = (e) => !!(e.target && e.target.closest && e.target.closest('#mapPanneau, #mapLegende, #mapIdf'));   // patch373 : le cartouche")
F.write_text(s, encoding='utf-8')

C = pathlib.Path('style.css'); c = C.read_text(encoding='utf-8')
assert 'patch373' not in c
c += """
/* patch373 : cartouche Paris et petite couronne */
.map-idf{ position:absolute; z-index:3; left:12px; top:12px; width:150px; padding:7px 7px 5px;
  background:rgba(10,22,40,.92); border:1px solid rgba(169,188,212,.22); border-radius:12px;
  box-shadow:0 6px 16px rgba(0,0,0,.35); touch-action:none; }
.map-idf.droite{ left:auto; right:12px; }
.map-idf[hidden]{ display:none; }
.map-idf .idf-titre{ display:block; margin:0 2px 4px; font-size:.64rem; font-weight:600; line-height:1.2; color:#A9BCD4; white-space:nowrap; }
.map-idf .idf-c{ display:none; }
.map-idf svg{ display:block; width:100%; height:auto; overflow:hidden; border-radius:7px; background:#0E2140; }
.map-idf .idf-ctx{ fill:#172F52; stroke:rgba(169,188,212,.22); stroke-width:.8; vector-effect:non-scaling-stroke; }
.map-idf .idf-dep{ cursor:pointer; }
.map-idf .idf-fond{ fill:#20406A; }
.map-idf .idf-trait{ fill:none; stroke:rgba(214,230,246,.55); stroke-width:1; vector-effect:non-scaling-stroke; pointer-events:none; }
.map-idf .idf-dep:hover .idf-trait{ stroke:rgba(255,255,255,.85); stroke-width:1.5; }
.map-idf .idf-dep.on .idf-trait{ stroke:#fff; stroke-width:2.2; }
.map-idf text{ font-family:var(--titre); font-weight:800; fill:#fff; text-anchor:middle; dominant-baseline:central;
  paint-order:stroke; stroke:rgba(5,12,24,.85); stroke-linejoin:round; pointer-events:none; }
.map-wrap.outremer .map-idf{ display:none !important; }
@media (max-width: 720px){
  .map-idf{ left:8px; top:8px; width:92px; padding:5px 5px 4px; border-radius:10px; }
  .map-idf.droite{ right:8px; }
  .map-idf .idf-titre{ font-size:.56rem; margin-bottom:3px; }
  .map-idf .idf-l{ display:none; }
  .map-idf .idf-c{ display:inline; }
  .map-wrap.plein-ecran .map-idf{ top:calc(8px + env(safe-area-inset-top, 0px)); }
}
"""
C.write_text(c, encoding='utf-8')
print('patch373 ok')
