# patch540 (Arkhannou) : le blason d'un département complet sur la carte « Ma France », dans la bulle
# et dans la liste « Département par département » ; crédits dans credits-blasons.html.
import os, sys
R = sys.argv[1] if len(sys.argv) > 1 else '.'
def rep(f, a, b, n=1):
    p = os.path.join(R, f); t = open(p, encoding='utf-8').read()
    if t.count(a) != n:
        if b in t: print(f'{f} : déjà fait'); return
        raise SystemExit(f'{f} : {t.count(a)} occurrence(s) pour {a[:80]!r}')
    open(p, 'w', encoding='utf-8').write(t.replace(a, b)); print(f'{f} : ok')

# chargement des crédits et des images
rep('app.js', "// ---------- patch92 : Ma France ----------\n", """// ---------- patch92 : Ma France ----------
// patch540 : blasons des départements complets (blasons/<code>.webp, crédits dans data/blasons.json)
let BL_DEP = null, blDepPromesse = null;
const BL_DEP_IMG = new Map();
function blDepCharger(){
  if(!blDepPromesse) blDepPromesse = fetch('data/blasons.json?v=1').then(r => r.ok ? r.json() : {}).catch(() => ({})).then(d => { BL_DEP = d || {}; return BL_DEP; });
  return blDepPromesse;
}
function blDepImg(dep){
  if(!BL_DEP || !BL_DEP[dep]) return null;
  let im = BL_DEP_IMG.get(dep);
  if(!im){ im = new Image(); im.onload = () => mfPlanifier(); im.src = 'blasons/' + encodeURIComponent(dep) + '.webp'; BL_DEP_IMG.set(dep, im); }
  return im.complete && im.naturalWidth ? im : null;
}
function mfComplet(dep){ const t = COMMUNES_PAR_DEPT[dep]; return !!t && (MF.parDep[dep] || 0) >= t; }
""")
rep('app.js', """  mfListeArmer(el);   // patch441
  MF.cv = document.getElementById('mfCanvas');""", """  mfListeArmer(el);   // patch441
  blDepCharger().then(() => {   // patch540 : la liste reçoit ses blasons
    const d = el.querySelector('.mfl');
    if(!d || !document.body.contains(d)) return;
    const neuf = document.createElement('div'); neuf.innerHTML = mfListeHtml();
    d.replaceWith(neuf.firstElementChild); mfListeArmer(el); mfPlanifier();
  });
  MF.cv = document.getElementById('mfCanvas');""")

# liste
rep('app.js', """        <span class="mfl-c">${x.d}</span><span class="mfl-nom">${echapperTexte(x.nom)}</span>""",
              """        <span class="mfl-c">${x.d}</span><span class="mfl-nom">${ok && BL_DEP && BL_DEP[x.d] ? `<img class="mfl-bl" src="blasons/${encodeURIComponent(x.d)}.webp" alt="" loading="lazy">` : ''}${echapperTexte(x.nom)}</span>""")
rep('app.js', """    }).join('')}</ol>
  </details>`;""", """    }).join('')}</ol>
    <p class="mfl-cr">Un département complet affiche son blason sur ta carte · <a href="credits-blasons.html" target="_blank" rel="noopener">crédits des blasons</a></p>
  </details>`;""")

# centre de chaque département (moyenne du plus grand anneau)
rep('app.js', """  MF.bbox = {};
  for(const d in CONTOURS_DEPTS){""", """  MF.bbox = {}; MF.ctr = {};   // patch540 : MF.ctr, centre pour le blason
  for(const d in CONTOURS_DEPTS){
    let grand = CONTOURS_DEPTS[d][0] || [];
    for(const a of CONTOURS_DEPTS[d]) if(a.length > grand.length) grand = a;
    let sx = 0, sy = 0;
    for(const [lon, lat] of grand){ const p = project(lat, lon); sx += p.x * MAP_W; sy += p.y * MAP_H; }
    if(grand.length) MF.ctr[d] = [sx / grand.length, sy / grand.length];""")

# dessin à l'échelle des départements
rep('app.js', """    if(niveau) niveau.textContent = MF.k <= 1.01 ? 'France entière · par département' : 'Par département · zoome encore';""",
"""    // patch540 : le blason des départements complets, au centre
    if(BL_DEP) for(const dep in CONTOURS_DEPTS){
      if(!mfComplet(dep) || !MF.ctr || !MF.ctr[dep]) continue;
      const im = blDepImg(dep), b = MF.bbox[dep];
      if(!im || !b) continue;
      const hpx = Math.max(16, Math.min(46, 0.55 * Math.min(b[2] - b[0], b[3] - b[1]) * S));
      const h = hpx / S, w = h * im.naturalWidth / im.naturalHeight, [cx, cy] = MF.ctr[dep];
      ctx.save();
      ctx.shadowColor = 'rgba(0,0,0,0.55)'; ctx.shadowBlur = 4 * d; ctx.shadowOffsetY = d;
      ctx.drawImage(im, cx - w / 2, cy - h / 2, w, h);
      ctx.restore();
    }
    if(niveau) niveau.textContent = MF.k <= 1.01 ? 'France entière · par département' : 'Par département · zoome encore';""")

# toucher un département complet : sa bulle de blason, puis le zoom comme avant
rep('app.js', """  if(MF.k < MF_COMMUNES){ mfZoomer(3, px, py); mfPlanifier(); return; }
  const ctx = MF.cv.getContext('2d');
  const d = MF.dpr, S = mfEchelle();
  ctx.setTransform(d * S, 0, 0, d * S, d * (MF.ox + MF.baseX * MF.k), d * (MF.oy + MF.baseY * MF.k));""",
"""  const ctx = MF.cv.getContext('2d');
  const d = MF.dpr, S = mfEchelle();
  ctx.setTransform(d * S, 0, 0, d * S, d * (MF.ox + MF.baseX * MF.k), d * (MF.oy + MF.baseY * MF.k));
  if(MF.k < MF_COMMUNES){
    MF.bulle = null;   // patch540
    if(BL_DEP) for(const dep in CONTOURS_DEPTS)
      if(mfComplet(dep) && BL_DEP[dep] && ctx.isPointInPath(cheminDeptCanvas(dep, CONTOURS_DEPTS[dep]), px * d, py * d)){ MF.bulle = { blason: dep }; break; }
    majBulleMF();
    mfZoomer(3, px, py); mfPlanifier(); return;
  }""")
rep('app.js', """  MF.dernierZoom = performance.now();
  mfLimiter();
  MF.bulle = null; majBulleMF();""", """  MF.dernierZoom = performance.now();
  mfLimiter();
  MF.bulle = BL_DEP && BL_DEP[dep] && mfComplet(dep) ? { blason: dep } : null; majBulleMF();   // patch540""")

rep('app.js', """  if(!MF.bulle){ el.hidden = true; return; }
  const e = terraCollection.get(MF.bulle.code);""", """  if(!MF.bulle){ el.hidden = true; return; }
  if(MF.bulle.blason){   // patch540
    const dep = MF.bulle.blason, c = (BL_DEP && BL_DEP[dep]) || {};
    el.hidden = false;
    el.innerHTML = `<img class="mf-bl" src="blasons/${encodeURIComponent(dep)}.webp" alt="Blason : ${echapperTexte(DEPT_NAMES[dep] || dep)}"><div><b>${echapperTexte(DEPT_NAMES[dep] || dep)} · complet ✓</b>`
      + `<span>${fmtNombre(MF.parDep[dep] || 0)} / ${fmtNombre(COMMUNES_PAR_DEPT[dep] || 0)} communes</span>`
      + `<small>Blason : ${c.a ? echapperTexte(c.a) + ', ' : ''}${echapperTexte(c.l || '')} · <a href="${echapperTexte(c.p || 'credits-blasons.html')}" target="_blank" rel="noopener">Wikimédia Commons</a></small></div>`;
    return;
  }
  const e = terraCollection.get(MF.bulle.code);""")

rep('style.css', ".mf-bulle[hidden]{ display:none; }", """.mf-bulle[hidden]{ display:none; }
.mf-bulle img.mf-bl{ width:44px; height:auto; flex:none; filter:drop-shadow(0 2px 3px rgba(0,0,0,.5)); }   /* patch540 */
.mf-bulle small{ display:block; font-size:.64rem; color:var(--brume); margin-top:2px; }
.mf-bulle small a{ color:inherit; }
.mfl-bl{ width:15px; height:auto; vertical-align:-3px; margin-right:6px; }
.mfl-cr{ font-size:.7rem; color:var(--brume); margin:8px 4px 2px; }
.mfl-cr a{ color:inherit; }""")
