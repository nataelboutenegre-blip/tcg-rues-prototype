# patch402 (10/11/2026) : plus de traits noirs au milieu d'un territoire (remarque d'Oshannir, 10/11).
# Les contours sont simplifiés commune par commune : deux voisines n'ont pas toujours les mêmes points
# sur leur limite commune. Leurs segments ne se reconnaissaient pas (patch335 les apparie par points
# identiques) et la limite intérieure passait pour un bord de territoire : traits noirs en plein milieu.
# Mesuré sur 16, 17, 24, 79, 86, 87 : 2 680 segments sans voisine, dont environ 1 800 longent en fait une
# voisine à moins de 100 m. On les rapproche par la géométrie (trois points du segment à moins de ~150 m
# d'une autre commune) ; le voisin trouvé ainsi va dans c3, sans toucher à l'appariement exact (c2).
import sys
def rep(chemin, avant, apres, nb=1):
    t = open(chemin, encoding='utf-8').read()
    n = t.count(avant)
    if n != nb: sys.exit(f'{chemin} : {n} au lieu de {nb} pour {avant[:70]!r}')
    open(chemin, 'w', encoding='utf-8').write(t.replace(avant, apres))
A = 'app.js'

rep(A, """const TOPO = { pts: new Map(), px: [], py: [], segs: new Map(), sa: [], sb: [], c1: [], c2: [],
               communes: new Map(), segsCommune: [], deps: new Map(), version: 0 };""",
"""const TOPO = { pts: new Map(), px: [], py: [], segs: new Map(), sa: [], sb: [], c1: [], c2: [],
               communes: new Map(), segsCommune: [], deps: new Map(), version: 0,
               gx: [], gy: [], c3: [], grille: new Map() };   // patch402
// patch402 : deux voisines dont la limite n'a pas les mêmes points (contours simplifiés commune par
// commune) ne se reconnaissaient pas : leur limite passait pour un bord de territoire, d'où des traits
// noirs au milieu d'un territoire. Un segment resté seul dont trois points (au quart, au milieu, aux trois
// quarts) longent une autre commune à moins de ~150 m est une limite intérieure ; sa voisine va dans c3.
const TOPO_TOL = 0.0015, TOPO_CASE = 0.02;   // en degrés (longitude ramenée à l'échelle de la latitude)
function topoCase(x, y){ return (Math.floor(x / TOPO_CASE) + 2000) * 100000 + Math.floor(y / TOPO_CASE) + 50000; }
function topoRapprocher(debut){
  const { gx, gy, sa, sb, c1, c2, c3, grille } = TOPO;
  const cases = new Set();
  for(let s = debut; s < sa.length; s++){
    if(c2[s] !== -1) continue;
    const x1 = gx[sa[s]], y1 = gy[sa[s]], x2 = gx[sb[s]], y2 = gy[sb[s]];
    const i0 = Math.floor((Math.min(x1, x2) - TOPO_TOL) / TOPO_CASE), i1 = Math.floor((Math.max(x1, x2) + TOPO_TOL) / TOPO_CASE);
    const j0 = Math.floor((Math.min(y1, y2) - TOPO_TOL) / TOPO_CASE), j1 = Math.floor((Math.max(y1, y2) + TOPO_TOL) / TOPO_CASE);
    for(let i = i0; i <= i1; i++) for(let j = j0; j <= j1; j++){
      const k = (i + 2000) * 100000 + j + 50000;
      let l = grille.get(k);
      if(!l){ l = []; grille.set(k, l); }
      l.push(s); cases.add(k);
    }
  }
  const proche = (x, y, ci) => {
    const l = grille.get(topoCase(x, y));
    if(!l) return -1;
    let meilleur = -1, d = TOPO_TOL * TOPO_TOL;
    for(const o of l){
      if(c1[o] === ci) continue;
      const ax = gx[sa[o]], ay = gy[sa[o]], dx = gx[sb[o]] - ax, dy = gy[sb[o]] - ay, n = dx * dx + dy * dy;
      const t = n ? Math.max(0, Math.min(1, ((x - ax) * dx + (y - ay) * dy) / n)) : 0;
      const ex = x - ax - t * dx, ey = y - ay - t * dy, e = ex * ex + ey * ey;
      if(e < d){ d = e; meilleur = c1[o]; }
    }
    return meilleur;
  };
  // les segments seuls des cases touchées, anciens compris : une voisine d'un autre fichier peut arriver
  const vus = new Set();
  for(const k of cases) for(const s of grille.get(k)){
    if(vus.has(s) || c2[s] !== -1) continue;
    vus.add(s);
    const x1 = gx[sa[s]], y1 = gy[sa[s]], dx = gx[sb[s]] - x1, dy = gy[sb[s]] - y1;
    const a = proche(x1 + dx * 0.25, y1 + dy * 0.25, c1[s]);
    const m = a < 0 ? -1 : proche(x1 + dx * 0.5, y1 + dy * 0.5, c1[s]);
    const b = m < 0 ? -1 : proche(x1 + dx * 0.75, y1 + dy * 0.75, c1[s]);
    c3[s] = b < 0 ? -1 : m;
  }
}""")

rep(A, """    if(i === undefined){
      i = TOPO.px.length; TOPO.pts.set(k, i);
      const r = project(q[1], q[0]);
      TOPO.px.push(Math.round(r.x * MAP_W * 10) / 10); TOPO.py.push(Math.round(r.y * MAP_H * 10) / 10);
    }""",
"""    if(i === undefined){
      i = TOPO.px.length; TOPO.pts.set(k, i);
      const r = project(q[1], q[0]);
      TOPO.px.push(Math.round(r.x * MAP_W * 10) / 10); TOPO.py.push(Math.round(r.y * MAP_H * 10) / 10);
      TOPO.gx.push(q[0] * 0.69); TOPO.gy.push(q[1]);   // patch402
    }""")

rep(A, """  liste = [];
  const point = (q) => {""",
"""  liste = [];
  const debut = TOPO.sa.length;   // patch402
  const point = (q) => {""")

rep(A, """          mes.push(TOPO.sa.length); TOPO.sa.push(a); TOPO.sb.push(b); TOPO.c1.push(ci); TOPO.c2.push(-1);""",
"""          mes.push(TOPO.sa.length); TOPO.sa.push(a); TOPO.sb.push(b); TOPO.c1.push(ci); TOPO.c2.push(-1); TOPO.c3.push(-1);""")

rep(A, """  TOPO.deps.set(dep, liste);
  TOPO.version++;
  return liste;""",
"""  topoRapprocher(debut);   // patch402
  TOPO.deps.set(dep, liste);
  TOPO.version++;
  return liste;""")

rep(A, """      const autre = TOPO.c1[s] === ci ? TOPO.c2[s] : TOPO.c1[s];
      if(autre < 0 || proprio[autre] !== k) l.push(s);""",
"""      let autre = TOPO.c1[s] === ci ? TOPO.c2[s] : TOPO.c1[s];
      if(autre < 0) autre = TOPO.c3[s];   // patch402 : la voisine reconnue par la géométrie
      if(autre < 0 || proprio[autre] !== k) l.push(s);""")
print('patch402 OK')
