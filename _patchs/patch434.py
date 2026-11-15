# patch434 (15/11/2026) : deux retours de joueurs.
#  - Arkhannou : un département choisi dans le cartouche « Paris et petite couronne » restait en gras
#    quand on en choisissait un autre sur la grande carte (ou une commune) : le cartouche suit maintenant.
#  - Bonjean : la carte Outre-mer du Front ne montrait ni les bâtiments (dont les Centres de recherche
#    dévoilés) ni les zones de bombe : elle les dessine maintenant, comme la carte de France.
import sys
def rep(chemin, avant, apres, nb=1):
    t = open(chemin, encoding='utf-8').read()
    n = t.count(avant)
    if n != nb: sys.exit(f'{chemin} : {n} au lieu de {nb} pour {avant[:70]!r}')
    open(chemin, 'w', encoding='utf-8').write(t.replace(avant, apres))
A = 'app.js'
if 'patch434' in open(A, encoding='utf-8').read(): sys.exit('déjà appliqué')

# 1. le cartouche suit le département ouvert
rep(A, """  panneauCommune = null;
  panneauDept = dep;
  panneauAncre = { x: xCss, y: yCss };
""", """  panneauCommune = null;
  panneauDept = dep;
  panneauAncre = { x: xCss, y: yCss };
  idfSurligner();   // patch434 : le cartouche suit (Arkhannou)
""")
rep(A, """  panneauCommune = code;
  panneauDept = null;
  if(typeof xCss === 'number' && typeof yCss === 'number'){""", """  panneauCommune = code;
  panneauDept = null;
  idfSurligner();   // patch434
  if(typeof xCss === 'number' && typeof yCss === 'number'){""")

# 2. outre-mer : bombes et bâtiments
rep(A, """  if(OMF.bulle && OMF.bulle.dep === dep){
    const c = tu.chemins.find(([code]) => code === OMF.bulle.code);
    if(c){ ctx.strokeStyle = '#fff'; ctx.lineWidth = 2.4; ctx.stroke(c[1]); }
  }
}
""", """  if(SAISON2) omfBombesBatiments(ctx, contours, P, larg, haut, grand);   // patch434 (Bonjean)
  if(OMF.bulle && OMF.bulle.dep === dep){
    const c = tu.chemins.find(([code]) => code === OMF.bulle.code);
    if(c){ ctx.strokeStyle = '#fff'; ctx.lineWidth = 2.4; ctx.stroke(c[1]); }
  }
}

// patch434 : sur une tuile d'outre-mer, les zones de bombe en cours puis les bâtiments visibles,
// avec les mêmes couleurs et les mêmes pastilles que sur la carte de France
function omfBombesBatiments(ctx, contours, P, larg, haut, grand){
  const maintenant = Date.now();
  for(const z of (BOMBES_ZONES || [])){
    if(z.lat == null || z.lon == null || new Date(z.fin).getTime() < maintenant) continue;
    const lat = Number(z.lat), lon = Number(z.lon), rk = Number(z.rayon_km) || 0;
    const [cx, cy] = P(lon, lat);
    const [, yh] = P(lon, lat + rk / 111.19);
    const [xd] = P(lon + rk / (111.19 * Math.cos(lat * Math.PI / 180)), lat);
    const rx = Math.abs(xd - cx), ry = Math.abs(cy - yh);
    if(!(rx > 0) || cx + rx < 0 || cx - rx > larg || cy + ry < 0 || cy - ry > haut) continue;
    ctx.save();
    ctx.beginPath(); ctx.ellipse(cx, cy, rx, ry, 0, 0, Math.PI * 2);
    ctx.fillStyle = 'rgba(229,72,77,0.15)'; ctx.fill();
    ctx.setLineDash([5, 3.5]); ctx.strokeStyle = 'rgba(255,90,82,0.95)'; ctx.lineWidth = 1.6; ctx.stroke(); ctx.setLineDash([]);
    const f = grand ? 11 : 10;
    const txt = grand ? `💥 +${btReglage('bombe_bonus', 15)} % · ${formatDuree(new Date(z.fin).getTime() - maintenant)}` : '💥';
    ctx.font = `600 ${f}px "Instrument Sans", system-ui, sans-serif`;
    const w = grand ? ctx.measureText(txt).width + f * 1.2 : f * 1.9, h = f * 1.8;
    const y = Math.max(2, cy - ry - h - 3);
    ctx.fillStyle = 'rgba(229,72,77,0.92)';
    ctx.beginPath(); if(ctx.roundRect) ctx.roundRect(cx - w / 2, y, w, h, h / 2); else ctx.rect(cx - w / 2, y, w, h); ctx.fill();
    ctx.fillStyle = '#fff'; ctx.textAlign = 'center'; ctx.textBaseline = 'middle';
    ctx.fillText(txt, cx, y + h / 2 + 0.5);
    ctx.restore();
  }
  if(!BT_TRACES || !BATIMENTS_CARTE.size || (typeof CALQUES !== 'undefined' && CALQUES.batiments === false)) return;
  const r = grand ? 9 : 6.5;
  for(const code in contours){
    const bt = BATIMENTS_CARTE.get(String(code));
    if(!bt) continue;
    const types = ['fonderie', 'forteresse', 'centre', 'banque', 'radar'].filter(t => bt[t] && BT_TRACES[t]);
    if(!types.length) continue;
    let anneau = contours[code][0];
    for(const a of contours[code]) if(a.length > anneau.length) anneau = a;
    let sx = 0, sy = 0;
    for(const [lo, la] of anneau){ const [x, y] = P(lo, la); sx += x; sy += y; }
    const x0 = sx / anneau.length, y0 = sy / anneau.length;
    types.forEach((t, i) => {
      const cx = x0 + (i - (types.length - 1) / 2) * (2 * r + 2), cy = y0;
      ctx.save();
      ctx.globalAlpha = bt[t].pret ? 1 : 0.65;
      ctx.beginPath(); ctx.arc(cx, cy, r, 0, Math.PI * 2);
      ctx.shadowColor = t === 'centre' ? 'rgba(255,90,82,.7)' : t === 'radar' ? 'rgba(110,195,240,.75)' : 'rgba(255,150,60,.75)'; ctx.shadowBlur = 8;
      ctx.fillStyle = '#3A220F'; ctx.fill(); ctx.shadowBlur = 0;
      ctx.lineWidth = grand ? 2.2 : 1.8;
      ctx.strokeStyle = bt[t].moi ? '#F0B429' : t === 'centre' ? '#FF6B63' : t === 'radar' ? '#6EC3F0' : '#FFB347';
      if(!bt[t].pret) ctx.setLineDash([2.2, 1.6]);
      ctx.stroke(); ctx.setLineDash([]);
      const k = r / 14;
      ctx.translate(cx - 12 * k, cy - 12 * k); ctx.scale(k, k);
      ctx.strokeStyle = '#FFE0B8'; ctx.fillStyle = '#FFE0B8'; ctx.lineWidth = 2.1; ctx.lineJoin = 'round'; ctx.lineCap = 'round';
      ctx.stroke(BT_TRACES[t][0]); if(BT_TRACES[t][1]) ctx.fill(BT_TRACES[t][1]);
      ctx.restore();
    });
  }
}
""")
# les bâtiments et les bombes arrivent après le premier dessin : on redessine l'outre-mer
rep(A, """    BATIMENTS_CARTE = carte;
    majMiniBt();   // patch397""", """    BATIMENTS_CARTE = carte;
    if(typeof omfRafraichir === 'function') omfRafraichir();   // patch434
    majMiniBt();   // patch397""")
print('patch434 OK')
