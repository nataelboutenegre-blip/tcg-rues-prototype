# patch530 : (1) la règle sur la carte (idée de Saaslil) ; (2) en S3, les 3 ronds de l'ancienne série
# laissent place à un badge « en cours » quand j'ai déjà un siège sur la commune (Arkhannou, Saaslil).
import os, sys, json
R = sys.argv[1] if len(sys.argv) > 1 else '.'
def rep(f, a, b, n=1):
    p = os.path.join(R, f); t = open(p, encoding='utf-8').read()
    if t.count(a) != n:
        if b in t: print(f'{f} : déjà fait'); return
        raise SystemExit(f'{f} : {t.count(a)} occurrence(s) pour {a[:80]!r}')
    open(p, 'w', encoding='utf-8').write(t.replace(a, b)); print(f'{f} : ok')

# ---- 1. la règle ----
rep('app.js', "  majEchelle();   // patch394\n", "  majEchelle();   // patch394\n  rgMaj();   // patch530 : la règle suit la carte\n")
rep('app.js', "    if(SAISON2 && bfxToucher(x, y)) return;   // patch377",
              "    if(RG.actif){ rgAjouter(x, y); return; }   // patch530 : en mode règle, un toucher pose un point\n    if(SAISON2 && bfxToucher(x, y)) return;   // patch377")
rep('app.js', "function applyMapTransform(){", r"""// ---------- patch530 : la règle (idée de Saaslil) ----------
// Les points sont gardés en unités de carte ; la distance se calcule à vol d'oiseau (haversine).
const RG = { actif: false, pts: [], glisse: null };
const RG_MAX = 20;
function rgLatLon(p){
  return { lon: mapBounds.lonMin + p.x / MAP_W * (mapBounds.lonMax - mapBounds.lonMin),
           lat: mapBounds.latMax - p.y / MAP_H * (mapBounds.latMax - mapBounds.latMin) };
}
function rgKm(a, b){
  const A = rgLatLon(a), B = rgLatLon(b), r = Math.PI / 180;
  const h = Math.sin((B.lat - A.lat) * r / 2) ** 2 + Math.cos(A.lat * r) * Math.cos(B.lat * r) * Math.sin((B.lon - A.lon) * r / 2) ** 2;
  return 2 * 6371 * Math.asin(Math.min(1, Math.sqrt(h)));
}
function rgTxt(km){ return (km < 10 ? km.toFixed(1).replace('.', ',') : Math.round(km).toLocaleString('fr-FR')) + ' km'; }
function rgInit(){
  const wrap = document.getElementById('mapWrap');
  if(!wrap || document.getElementById('mapRegle')) return !!wrap;
  const garder = (el) => ['mousedown', 'touchstart', 'pointerdown', 'wheel'].forEach(t => el.addEventListener(t, (e) => e.stopPropagation(), { passive: true }));
  const b = document.createElement('button');
  b.type = 'button'; b.id = 'mapRegleBtn'; b.className = 'map-regle-btn'; b.textContent = '📏 Mesurer';
  b.setAttribute('aria-pressed', 'false');
  b.addEventListener('click', (e) => { e.stopPropagation(); rgBasculer(); });
  garder(b);
  const bd = document.createElement('div');
  bd.id = 'mapRegleBandeau'; bd.className = 'map-regle-bandeau'; bd.hidden = true;
  bd.innerHTML = '<span id="mapRegleTotal"></span><button type="button" data-rg="effacer">Effacer</button><button type="button" data-rg="fermer" aria-label="Fermer la règle">✕</button>';
  bd.addEventListener('click', (e) => {
    e.stopPropagation();
    const q = e.target.closest('[data-rg]');
    if(!q) return;
    if(q.dataset.rg === 'effacer'){ RG.pts = []; rgMaj(); } else rgBasculer(false);
  });
  garder(bd);
  const svg = document.createElementNS('http://www.w3.org/2000/svg', 'svg');
  svg.id = 'mapRegle'; svg.setAttribute('class', 'map-regle'); svg.setAttribute('aria-hidden', 'true');
  // un point se glisse pour le déplacer ; touché sans bouger, il s'enlève
  const surPoint = (e) => e.target.closest && e.target.closest('[data-rg-i]');
  ['mousedown', 'touchstart'].forEach(t => svg.addEventListener(t, (e) => { if(surPoint(e)) e.stopPropagation(); }, { passive: true }));
  svg.addEventListener('pointerdown', (e) => {
    const c = surPoint(e);
    if(!c) return;
    e.stopPropagation(); e.preventDefault();
    RG.glisse = { i: Number(c.dataset.rgI), id: e.pointerId, x0: e.clientX, y0: e.clientY, bouge: false };
    try { svg.setPointerCapture(e.pointerId); } catch(err){}
  });
  svg.addEventListener('pointermove', (e) => {
    const g = RG.glisse;
    if(!g || g.id !== e.pointerId) return;
    if(!g.bouge && Math.hypot(e.clientX - g.x0, e.clientY - g.y0) < 5) return;
    g.bouge = true;
    const r = wrap.getBoundingClientRect();
    RG.pts[g.i] = ecranVersCarte(e.clientX - r.left, e.clientY - r.top);
    rgMaj();
  });
  const fin = (e) => {
    const g = RG.glisse;
    if(!g || g.id !== e.pointerId) return;
    RG.glisse = null;
    if(!g.bouge && e.type === 'pointerup'){ RG.pts.splice(g.i, 1); rgMaj(); }
  };
  svg.addEventListener('pointerup', fin);
  svg.addEventListener('pointercancel', fin);
  wrap.append(svg, bd, b);
  return true;
}
function rgBasculer(v){
  RG.actif = v === undefined ? !RG.actif : !!v;
  RG.pts = []; RG.glisse = null;
  const wrap = document.getElementById('mapWrap');
  if(wrap) wrap.classList.toggle('regle-on', RG.actif);
  const b = document.getElementById('mapRegleBtn');
  if(b){ b.classList.toggle('on', RG.actif); b.setAttribute('aria-pressed', String(RG.actif)); }
  if(RG.actif && typeof fermerPanneau === 'function') fermerPanneau();
  rgMaj();
}
function rgAjouter(x, y){
  if(RG.pts.length >= RG_MAX) return;
  RG.pts.push(ecranVersCarte(x, y));
  rgMaj();
}
function rgMaj(){
  if(!mapBounds || !MAP_W || !rgInit()) return;
  const b = document.getElementById('mapRegleBtn');
  const bd = document.getElementById('mapRegleBandeau');
  const svg = document.getElementById('mapRegle');
  const dispo = typeof canvasActif === 'function' && !!canvasActif();
  b.hidden = !dispo;
  if(!dispo && RG.actif){ RG.actif = false; RG.pts = []; }
  bd.hidden = !RG.actif;
  if(!RG.actif){ svg.innerHTML = ''; return; }
  const s = echelleCarte() * mapZoom;
  const P = RG.pts.map(p => [mapPanX + p.x * s, mapPanY + p.y * s]);
  let total = 0, etiquettes = '';
  for(let i = 1; i < RG.pts.length; i++){
    const km = rgKm(RG.pts[i - 1], RG.pts[i]); total += km;
    const [x1, y1] = P[i - 1], [x2, y2] = P[i];
    if(Math.hypot(x2 - x1, y2 - y1) < 46 || RG.pts.length < 3) continue;   // une seule distance : elle est dans le bandeau
    const t = rgTxt(km), w = t.length * 6.4 + 14, mx = (x1 + x2) / 2, my = (y1 + y2) / 2;
    etiquettes += `<g class="rg-et"><rect x="${(mx - w / 2).toFixed(1)}" y="${(my - 10).toFixed(1)}" width="${w.toFixed(1)}" height="20" rx="10"/><text x="${mx.toFixed(1)}" y="${(my + 4).toFixed(1)}">${t}</text></g>`;
  }
  const ligne = P.length > 1 ? `<polyline class="rg-l" points="${P.map(p => p[0].toFixed(1) + ',' + p[1].toFixed(1)).join(' ')}"/>` : '';
  const points = P.map(([x, y], i) => `<g data-rg-i="${i}" class="rg-h"><circle class="rg-zone" cx="${x.toFixed(1)}" cy="${y.toFixed(1)}" r="18"/><circle class="rg-p" cx="${x.toFixed(1)}" cy="${y.toFixed(1)}" r="7"/></g>`).join('');
  svg.innerHTML = ligne + etiquettes + points;
  const tt = document.getElementById('mapRegleTotal');
  tt.innerHTML = RG.pts.length === 0 ? '📏 Touche la carte pour poser un point'
    : RG.pts.length === 1 ? '📏 Pose un deuxième point'
    : `📏 <b>${rgTxt(total)}</b>${RG.pts.length > 2 ? ` <small>· ${RG.pts.length - 1} étapes</small>` : ''}`;
}

function applyMapTransform(){""")
rep('style.css', ".map-echelle[hidden], .map-wrap.outremer .map-echelle, .map-wrap.panneau-ouvert .map-echelle{ display:none; }",
""".map-echelle[hidden], .map-wrap.outremer .map-echelle, .map-wrap.panneau-ouvert .map-echelle{ display:none; }
/* patch530 : la règle */
.map-regle{ position:absolute; left:0; top:0; width:100%; height:100%; z-index:3; pointer-events:none; overflow:visible; }
.map-regle .rg-l{ fill:none; stroke:#F0B429; stroke-width:2.5; stroke-dasharray:7 5; stroke-linecap:round; filter:drop-shadow(0 1px 1px rgba(7,17,31,.8)); }
.map-regle .rg-h{ pointer-events:all; cursor:grab; touch-action:none; }
.map-regle .rg-zone{ fill:transparent; }
.map-regle .rg-p{ fill:#0B1830; stroke:#F0B429; stroke-width:2.5; }
.map-regle .rg-et rect{ fill:rgba(11,24,48,.92); stroke:#F0B429; stroke-width:1; }
.map-regle .rg-et text{ fill:#F6D77A; font:700 11px var(--texte); text-anchor:middle; }
.map-regle-btn{ position:absolute; z-index:4; right:10px; bottom:10px; background:rgba(11,24,48,.92); color:#F6D77A;
  border:1px solid rgba(240,180,41,.65); border-radius:9px; padding:6px 10px; font:700 .74rem var(--texte); cursor:pointer; }
.map-regle-btn.on{ background:#F0B429; color:#13233B; border-color:#F0B429; }
.map-regle-btn[hidden], .map-wrap.outremer .map-regle-btn{ display:none; }
.map-wrap.panneau-ouvert:not(.regle-on) .map-regle-btn{ display:none; }
.map-wrap.plein-ecran .map-regle-btn{ bottom:calc(10px + env(safe-area-inset-bottom, 0px)); }
.map-regle-bandeau{ position:absolute; z-index:4; top:10px; right:10px; max-width:calc(100% - 20px); display:flex; align-items:center; gap:6px;
  background:rgba(11,24,48,.95); border:1px solid #F0B429; border-radius:10px; padding:5px 6px 5px 10px; color:#F6D77A; font-size:.8rem; }
.map-regle-bandeau[hidden]{ display:none; }
.map-regle-bandeau > span{ flex:1; min-width:0; white-space:nowrap; overflow:hidden; text-overflow:ellipsis; }
.map-regle-bandeau b{ color:#FFE6A0; font-size:.92rem; }
.map-regle-bandeau small{ color:#C9B67A; }
.map-regle-bandeau button{ flex:none; background:transparent; border:1px solid rgba(240,180,41,.5); color:#F6D77A; border-radius:7px; padding:3px 8px; font:600 .72rem var(--texte); cursor:pointer; }
.map-wrap.regle-on #mapCanvas{ cursor:crosshair; }""")

# ---- 2. les ronds → « en cours » ----
rep('app.js', """<span class="ca-serie" title="Ta série : ${victoires} / 3">${serie}</span>""",
"""${SIEGE ? (sgEnCours(c.commune_code) ? '<span class="ca-encours">en cours</span>' : '') : `<span class="ca-serie" title="Ta série : ${victoires} / 3">${serie}</span>`}""")
rep('app.js', "function sgSuffit(v){ return !!(v && v.en_cours && v.suffit); }   // patch528",
"""function sgSuffit(v){ return !!(v && v.en_cours && v.suffit); }   // patch528
function sgEnCours(code){   // patch530 : j'ai déjà un siège sur cette commune
  const v = sgEstLu(code);
  return !!(v && v.en_cours) || (Array.isArray(sgMes) && sgMes.some(s => String(s.commune) === String(code)));
}""")
rep('app.js', "  art.classList.toggle('ca-ok', ok);\n",
"""  art.classList.toggle('ca-ok', ok);
  const qui = art.querySelector('.ca-qui');   // patch530 : le badge arrive avec l'estimation
  if(qui && v && v.en_cours && !qui.querySelector('.ca-encours')) qui.insertAdjacentHTML('beforeend', '<span class="ca-encours">en cours</span>');
""")
rep('style.css', ".mfo-l .dep{ margin-left:5px; vertical-align:1px; }   /* patch529 */",
""".mfo-l .dep{ margin-left:5px; vertical-align:1px; }   /* patch529 */
.ca-encours{ margin-left:auto; flex:none; background:var(--c-rouge, #E5484D); color:#fff; font-size:.62rem; font-weight:700; padding:1px 7px; border-radius:999px; }   /* patch530 */""")

p = os.path.join(R, 'data', 'nouveautes.json'); d = json.load(open(p, encoding='utf-8'))
e = d[0]; assert e['date'] == '2026-11-24'
for l in ["📏 Carte : un bouton « Mesurer » pour mesurer les distances à vol d'oiseau. Touche la carte pour poser des points, glisse-les pour les déplacer, touche un point pour l'enlever (merci Saaslil).",
          "⚔️ Attaquer : les 3 petits ronds de l'ancien système disparaissent. À la place, un badge « en cours » quand tu as déjà un siège sur la commune (merci Arkhannou et Saaslil)."]:
    if l not in e['nouveautes']: e['nouveautes'].insert(0, l)
json.dump(d, open(p, 'w', encoding='utf-8'), ensure_ascii=False, indent=2); print('nouveautes.json : ok')
