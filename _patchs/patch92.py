# -*- coding: utf-8 -*-
u"""
patch92 — « Ma France » dans la Collection Terra (saison 2, CACHÉ tant que
SAISON2 = false). Aperçu « mafrance-apercu.png » validé le 9 octobre.

- Sélecteur « Mes cartes / Ma France » sous le titre de la Collection Terra.
- Trois chiffres : % de la France, départements touchés (sur 101),
  départements complets.
- Carte en canvas, zoomable : molette, pincement, glisser, boutons + − ⌂.
  De loin, chaque département est teinté selon la part possédée ; à partir
  du zoom ×2,5, les vraies communes apparaissent, couleur de leur rareté
  (contours chargés par département, partagés avec la carte du Territoire).
  À partir de ×6, les noms des communes collectées, sans chevauchement.
- Toucher une commune : sa fiche en bas (rareté, exemplaires). De loin,
  toucher zoome sur l'endroit touché.
Rien ne change en saison 1 ni en Front.
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
assert 'terraVue' not in js, u'patch92 deja applique'

js = rempl(js, u"let terraDernier = null;           // le dernier paquet ouvert, pour le bilan\n",
           u"""let terraDernier = null;           // le dernier paquet ouvert, pour le bilan
// patch92 : Ma France en Terra
let terraVue = 'cartes';           // 'cartes' | 'france'
const MF = { k: 1, ox: 0, oy: 0, larg: 0, haut: 0, s0: 1, dpr: 1, cv: null, pointeurs: new Map(),
             bouge: 0, prevu: false, parDep: {}, bbox: null, centres: new Map() };
""", 'etat Ma France')

# --- le selecteur, et la vue France ---------------------------------------------------------
js = rempl(js, u"""  const ordre = TIERS.filter(t => tot[t.id] || parTier[t.id]);
  el.innerHTML = `
    <div class="coll-ligne-titre"><h1>Collection</h1><span class="coll-compteur"><b>${fmtNombre(terraCollection.size)}</b> / ${fmtNombre(totalFrance)} communes</span></div>
""",
           u"""  const ordre = TIERS.filter(t => tot[t.id] || parTier[t.id]);
  if(terraVue === 'france') return renderMaFranceTerra(el, totalFrance);
  el.innerHTML = `
    <div class="coll-ligne-titre"><h1>Collection</h1><span class="coll-compteur"><b>${fmtNombre(terraCollection.size)}</b> / ${fmtNombre(totalFrance)} communes</span></div>
    ${selecteurVueTerra()}
""", 'selecteur cartes')

js = rempl(js, u"""function clicCollectionTerra(e){
  const f = e.target.closest('[data-tcf]');""",
           u"""function clicCollectionTerra(e){
  const v = e.target.closest('[data-tcv]');
  if(v){ if(terraVue !== v.dataset.tcv){ terraVue = v.dataset.tcv; renderCollectionTerra(); } return; }
  const z = e.target.closest('[data-mf]');
  if(z){
    if(z.dataset.mf === 'centre'){ MF.k = 1; MF.ox = 0; MF.oy = 0; MF.bulle = null; majBulleMF(); }
    else mfZoomer(z.dataset.mf === 'plus' ? 1.8 : 1 / 1.8, MF.larg / 2, MF.haut / 2);
    mfPlanifier();
    return;
  }
  const f = e.target.closest('[data-tcf]');""", 'clics vue')

js = rempl(js, u"function renderGrilleTerra(){",
           u"""function selecteurVueTerra(){
  return `<div class="mf-vue" role="tablist" aria-label="Affichage de la collection">
    <button role="tab" data-tcv="cartes" class="${terraVue === 'cartes' ? 'on' : ''}" aria-selected="${terraVue === 'cartes'}">Mes cartes</button>
    <button role="tab" data-tcv="france" class="${terraVue === 'france' ? 'on' : ''}" aria-selected="${terraVue === 'france'}">Ma France</button></div>`;
}

// ---------- patch92 : Ma France ----------
const MF_COMMUNES = 2.5;    // a partir de ce zoom, les communes ; en dessous, les departements
const MF_NOMS = 6;          // a partir de ce zoom, les noms

function renderMaFranceTerra(el, totalFrance){
  MF.parDep = {};
  for(const e of terraCollection.values()) MF.parDep[e.dept] = (MF.parDep[e.dept] || 0) + 1;
  const touches = Object.keys(MF.parDep).filter(d => COMMUNES_PAR_DEPT[d]).length;
  const complets = Object.keys(MF.parDep).filter(d => COMMUNES_PAR_DEPT[d] && MF.parDep[d] >= COMMUNES_PAR_DEPT[d]).length;
  const nbDepts = Object.keys(COMMUNES_PAR_DEPT).length;
  const pct = totalFrance ? 100 * terraCollection.size / totalFrance : 0;
  el.innerHTML = `
    <div class="coll-ligne-titre"><h1>Collection</h1><span class="coll-compteur"><b>${fmtNombre(terraCollection.size)}</b> / ${fmtNombre(totalFrance)} communes</span></div>
    ${selecteurVueTerra()}
    <div class="mf-stats">
      <div><b>${pct < 10 ? pct.toFixed(1).replace('.', ',') : Math.round(pct)} %</b><span>de la France</span></div>
      <div><b>${touches} / ${nbDepts}</b><span>départements touchés</span></div>
      <div><b>${complets}</b><span>départements complets</span></div>
    </div>
    <div class="mf-cadre" id="mfCadre">
      <canvas id="mfCanvas" aria-label="Carte de ta collection : touche un département pour zoomer, une commune pour la voir"></canvas>
      <span class="mf-niveau" id="mfNiveau"></span>
      <div class="mf-zoom"><button data-mf="plus" aria-label="Zoomer">+</button><button data-mf="moins" aria-label="Dézoomer">−</button><button data-mf="centre" aria-label="Recentrer">⌂</button></div>
      <div class="mf-bulle" id="mfBulle" hidden></div>
    </div>
    <div class="mf-leg" id="mfLeg"></div>`;
  MF.cv = document.getElementById('mfCanvas');
  mfArmer(MF.cv);
  mfDimensionner();
  Promise.resolve(chargerDepartements()).then(() => { mfBoites(); mfPlanifier(); });
  majBulleMF();
}

function mfDimensionner(){
  const cadre = document.getElementById('mfCadre');
  if(!cadre || !MF.cv) return;
  const larg = cadre.clientWidth;
  if(larg < 40) return;
  const ratio = MAP_H / MAP_W;
  MF.larg = larg;
  MF.haut = Math.round(Math.min(larg * ratio, window.innerHeight * 0.62, larg * 1.15));
  MF.dpr = Math.min(window.devicePixelRatio || 1, 2);
  MF.cv.width = Math.round(larg * MF.dpr);
  MF.cv.height = Math.round(MF.haut * MF.dpr);
  MF.cv.style.height = MF.haut + 'px';
  // la France entiere tient dans le cadre au zoom 1
  MF.s0 = Math.min(larg / MAP_W, MF.haut / MAP_H);
  MF.baseX = (larg - MAP_W * MF.s0) / 2;
  MF.baseY = (MF.haut - MAP_H * MF.s0) / 2;
}

// boites des departements, en coordonnees de base, pour ne charger et ne
// dessiner que ce qui est a l'ecran
function mfBoites(){
  if(MF.bbox || !CONTOURS_DEPTS || typeof CONTOURS_DEPTS !== 'object') return;
  MF.bbox = {};
  for(const d in CONTOURS_DEPTS){
    let x0 = Infinity, y0 = Infinity, x1 = -Infinity, y1 = -Infinity;
    for(const anneau of CONTOURS_DEPTS[d]) for(const [lon, lat] of anneau){
      const p = project(lat, lon), x = p.x * MAP_W, y = p.y * MAP_H;
      if(x < x0) x0 = x; if(x > x1) x1 = x; if(y < y0) y0 = y; if(y > y1) y1 = y;
    }
    MF.bbox[d] = [x0, y0, x1, y1];
  }
}

function mfEchelle(){ return MF.s0 * MF.k; }
function mfVersBase(px, py){ const S = mfEchelle(); return [(px - MF.ox - MF.baseX * MF.k) / S, (py - MF.oy - MF.baseY * MF.k) / S]; }

function mfLimiter(){
  // la carte ne quitte pas le cadre
  const S = mfEchelle();
  const l = MAP_W * S, h = MAP_H * S, bx = MF.baseX * MF.k, by = MF.baseY * MF.k;
  const minX = Math.min(0, MF.larg - l) - bx, maxX = Math.max(0, MF.larg - l) - bx;
  const minY = Math.min(0, MF.haut - h) - by, maxY = Math.max(0, MF.haut - h) - by;
  if(MF.k <= 1){ MF.ox = 0; MF.oy = 0; return; }
  MF.ox = Math.min(maxX + MF.larg * 0.3, Math.max(minX - MF.larg * 0.3, MF.ox));
  MF.oy = Math.min(maxY + MF.haut * 0.3, Math.max(minY - MF.haut * 0.3, MF.oy));
}

function mfZoomer(f, px, py){
  const avant = MF.k;
  const k = Math.max(1, Math.min(60, avant * f));
  if(k === avant) return;
  // le point sous le doigt reste sous le doigt
  const [bx, by] = mfVersBase(px, py);
  MF.k = k;
  const S = mfEchelle();
  MF.ox = px - bx * S - MF.baseX * MF.k;
  MF.oy = py - by * S - MF.baseY * MF.k;
  mfLimiter();
}

function mfPlanifier(){
  if(MF.prevu) return;
  MF.prevu = true;
  requestAnimationFrame(() => { MF.prevu = false; mfDessiner(); });
}

function mfDeptsVisibles(){
  if(!MF.bbox) return [];
  const [x0, y0] = mfVersBase(0, 0), [x1, y1] = mfVersBase(MF.larg, MF.haut);
  return Object.keys(MF.bbox).filter(d => {
    const b = MF.bbox[d];
    return b[2] >= x0 && b[0] <= x1 && b[3] >= y0 && b[1] <= y1;
  });
}

function mfDessiner(){
  const cv = MF.cv;
  if(!cv || !document.body.contains(cv) || !mapBounds) return;
  const ctx = cv.getContext('2d');
  const d = MF.dpr, S = mfEchelle();
  ctx.setTransform(d, 0, 0, d, 0, 0);
  ctx.fillStyle = '#0C1A31';
  ctx.fillRect(0, 0, MF.larg, MF.haut);
  if(!CONTOURS_DEPTS || typeof CONTOURS_DEPTS !== 'object') return;
  mfBoites();
  ctx.setTransform(d * S, 0, 0, d * S, d * (MF.ox + MF.baseX * MF.k), d * (MF.oy + MF.baseY * MF.k));
  const trait = (px) => px / S;
  const niveau = document.getElementById('mfNiveau');
  const leg = document.getElementById('mfLeg');

  if(MF.k < MF_COMMUNES){
    for(const dep in CONTOURS_DEPTS){
      const p = cheminDeptCanvas(dep, CONTOURS_DEPTS[dep]);
      const tot = COMMUNES_PAR_DEPT[dep] || 1;
      const r = (MF.parDep[dep] || 0) / tot;
      ctx.fillStyle = r === 0 ? '#14294A' : `rgba(53,185,126,${(0.18 + 0.8 * Math.min(1, r * 1.6)).toFixed(3)})`;
      ctx.fill(p);
      ctx.strokeStyle = r >= 1 ? '#F0B429' : 'rgba(169,188,212,0.28)';
      ctx.lineWidth = trait(r >= 1 ? 1.6 : 0.6);
      ctx.stroke(p);
    }
    if(niveau) niveau.textContent = MF.k <= 1.01 ? 'France entière · par département' : 'Par département · zoome encore';
    if(leg) leg.innerHTML = '<span><i style="background:#14294A"></i>Rien</span><span><i style="background:rgba(53,185,126,.35)"></i>Un peu</span>'
      + '<span><i style="background:rgba(53,185,126,.98)"></i>Beaucoup</span><span><i style="background:none;box-shadow:inset 0 0 0 2px #F0B429"></i>Complet</span>';
    return;
  }

  const visibles = mfDeptsVisibles();
  const vide = new Path2D(), parTier = {};
  for(const t of TIERS) parTier[t.id] = new Path2D();
  const attente = [];
  for(const dep of visibles){
    const c = CONTOURS.get(dep);
    if(c === undefined){ attente.push(dep); }
    if(!c || c === 'erreur'){ vide.addPath(cheminDeptCanvas(dep, CONTOURS_DEPTS[dep])); continue; }
    for(const code in c){
      const p = cheminCommuneCanvas(code, c[code]);
      const e = terraCollection.get(code);
      (e ? parTier[e.tier.id] : vide).addPath(p);
    }
  }
  // les contours arrivent par departement : on redessine a chaque arrivee
  for(const dep of attente) chargerContours(dep).then(() => { if(terraVue === 'france') mfPlanifier(); });
  ctx.fillStyle = '#1A3256';
  ctx.fill(vide);
  for(const t of TIERS){
    ctx.fillStyle = COULEURS_FILTRE[t.id];
    ctx.globalAlpha = 0.92;
    ctx.fill(parTier[t.id]);
  }
  ctx.globalAlpha = 1;
  ctx.strokeStyle = 'rgba(12,26,49,0.9)';
  ctx.lineWidth = trait(MF.k > 20 ? 1 : 0.5);
  ctx.stroke(vide);
  for(const t of TIERS) ctx.stroke(parTier[t.id]);
  if(MF.bulle && MF.bulle.chemin){
    ctx.strokeStyle = '#fff';
    ctx.lineWidth = trait(2.5);
    ctx.stroke(MF.bulle.chemin);
  }
  for(const dep of visibles){
    ctx.strokeStyle = 'rgba(169,188,212,0.55)';
    ctx.lineWidth = trait(1.2);
    ctx.stroke(cheminDeptCanvas(dep, CONTOURS_DEPTS[dep]));
  }
  if(MF.k >= MF_NOMS) mfNoms(ctx, visibles);
  if(niveau) niveau.textContent = `Zoom ×${MF.k < 10 ? MF.k.toFixed(1).replace('.', ',') : Math.round(MF.k)} · communes`;
  if(leg) leg.innerHTML = TIERS.slice().reverse().map(t => `<span><i style="background:${COULEURS_FILTRE[t.id]}"></i>${t.label}</span>`).join('')
    + '<span><i style="background:#1A3256"></i>Pas encore</span>';
}

// centre d'une commune, en coordonnees de base (moyenne des points du plus grand anneau)
function mfCentre(code, poly){
  let c = MF.centres.get(code);
  if(c) return c;
  let anneau = poly[0];
  for(const a of poly) if(a.length > anneau.length) anneau = a;
  let sx = 0, sy = 0;
  for(const [lon, lat] of anneau){ const p = project(lat, lon); sx += p.x * MAP_W; sy += p.y * MAP_H; }
  c = [sx / anneau.length, sy / anneau.length];
  MF.centres.set(code, c);
  return c;
}

function mfNoms(ctx, visibles){
  const d = MF.dpr, S = mfEchelle();
  const seuil = MF.k >= 14 ? 0 : MF.k >= 9 ? 2000 : 8000;
  const liste = [];
  for(const dep of visibles){
    const c = CONTOURS.get(dep);
    if(!c || c === 'erreur') continue;
    for(const code in c){
      const e = terraCollection.get(code);
      if(e && (e.pop || 0) >= seuil) liste.push([e, c[code], code]);
    }
  }
  liste.sort((a, b) => (b[0].pop || 0) - (a[0].pop || 0));
  ctx.setTransform(d, 0, 0, d, 0, 0);
  ctx.font = '600 11px ' + getComputedStyle(document.body).getPropertyValue('--texte');
  ctx.textAlign = 'center';
  ctx.textBaseline = 'middle';
  const pris = [];
  for(const [e, poly, code] of liste.slice(0, 400)){
    const [bx, by] = mfCentre(code, poly);
    const x = bx * S + MF.ox + MF.baseX * MF.k, y = by * S + MF.oy + MF.baseY * MF.k;
    if(x < 0 || x > MF.larg || y < 0 || y > MF.haut) continue;
    const w = ctx.measureText(e.nom).width + 6, h = 14;
    const r = [x - w / 2, y - h / 2, x + w / 2, y + h / 2];
    if(r[0] < 2 || r[2] > MF.larg - 2) continue;   // pas de nom coupe au bord
    if(pris.some(q => r[0] < q[2] && r[2] > q[0] && r[1] < q[3] && r[3] > q[1])) continue;
    pris.push(r);
    ctx.fillStyle = 'rgba(5,12,24,0.75)';
    ctx.fillText(e.nom, x + 1, y + 1);
    ctx.fillStyle = '#fff';
    ctx.fillText(e.nom, x, y);
  }
}

function mfToucher(px, py){
  if(MF.k < MF_COMMUNES){ mfZoomer(3, px, py); mfPlanifier(); return; }
  const ctx = MF.cv.getContext('2d');
  const d = MF.dpr, S = mfEchelle();
  ctx.setTransform(d * S, 0, 0, d * S, d * (MF.ox + MF.baseX * MF.k), d * (MF.oy + MF.baseY * MF.k));
  for(const dep of mfDeptsVisibles()){
    const c = CONTOURS.get(dep);
    if(!c || c === 'erreur') continue;
    for(const code in c){
      const p = cheminCommuneCanvas(code, c[code]);
      if(ctx.isPointInPath(p, px * d, py * d)){
        MF.bulle = { code, dep, chemin: p };
        majBulleMF();
        mfPlanifier();
        return;
      }
    }
  }
  MF.bulle = null;
  majBulleMF();
  mfPlanifier();
}

function majBulleMF(){
  const el = document.getElementById('mfBulle');
  if(!el) return;
  if(!MF.bulle){ el.hidden = true; return; }
  const e = terraCollection.get(MF.bulle.code);
  const dep = MF.bulle.dep;
  el.hidden = false;
  el.innerHTML = e
    ? `<i class="mf-pastille ${e.tier.id}"></i><div><b>${echapperTexte(e.nom)}</b><span>${e.tier.label} · ×${e.exemplaires} · ${echapperTexte(DEPT_NAMES[dep] || dep)}</span></div>`
    : `<i class="mf-pastille vide"></i><div><b>Pas encore dans ta collection</b><span>${echapperTexte(DEPT_NAMES[dep] || dep)} · ${fmtNombre(MF.parDep[dep] || 0)} / ${fmtNombre(COMMUNES_PAR_DEPT[dep] || 0)} communes</span></div>`;
}

function mfArmer(cv){
  const pos = (ev) => { const r = cv.getBoundingClientRect(); return [ev.clientX - r.left, ev.clientY - r.top]; };
  cv.addEventListener('wheel', (ev) => {
    ev.preventDefault();
    const [x, y] = pos(ev);
    mfZoomer(Math.exp(-ev.deltaY * (ev.ctrlKey ? 0.01 : 0.0015)), x, y);
    mfPlanifier();
  }, { passive: false });
  cv.addEventListener('pointerdown', (ev) => {
    cv.setPointerCapture(ev.pointerId);
    MF.pointeurs.set(ev.pointerId, pos(ev));
    MF.bouge = 0;
  });
  cv.addEventListener('pointermove', (ev) => {
    if(!MF.pointeurs.has(ev.pointerId)) return;
    const avant = MF.pointeurs.get(ev.pointerId), apres = pos(ev);
    if(MF.pointeurs.size === 1){
      MF.ox += apres[0] - avant[0];
      MF.oy += apres[1] - avant[1];
      MF.bouge += Math.abs(apres[0] - avant[0]) + Math.abs(apres[1] - avant[1]);
      mfLimiter();
    } else if(MF.pointeurs.size === 2){
      const [a, b] = [...MF.pointeurs.entries()].map(([id, p]) => id === ev.pointerId ? apres : p);
      const [a0, b0] = [...MF.pointeurs.values()];
      const d0 = Math.hypot(a0[0] - b0[0], a0[1] - b0[1]), d1 = Math.hypot(a[0] - b[0], a[1] - b[1]);
      if(d0 > 0) mfZoomer(d1 / d0, (a[0] + b[0]) / 2, (a[1] + b[1]) / 2);
      MF.bouge += 10;
    }
    MF.pointeurs.set(ev.pointerId, apres);
    mfPlanifier();
  });
  const fin = (ev) => {
    if(!MF.pointeurs.has(ev.pointerId)) return;
    const p = MF.pointeurs.get(ev.pointerId);
    MF.pointeurs.delete(ev.pointerId);
    if(ev.type === 'pointerup' && MF.pointeurs.size === 0 && MF.bouge < 6) mfToucher(p[0], p[1]);
  };
  cv.addEventListener('pointerup', fin);
  cv.addEventListener('pointercancel', fin);
}

window.addEventListener('resize', () => {
  if(terraVue === 'france' && MF.cv && document.body.contains(MF.cv)){ mfDimensionner(); mfLimiter(); mfPlanifier(); }
});

function renderGrilleTerra(){""", 'fonctions Ma France')

ecrire('app.js', js)

css = lire('style.css')
assert 'mf-cadre' not in css, u'patch92 deja applique (css)'
css += u'''
/* =====================================================================
   patch92 — Ma France en Terra
   ===================================================================== */
.mf-vue{ display:flex; gap:4px; padding:4px; border-radius:12px; background:rgba(169,188,212,.08); border:1px solid rgba(169,188,212,.14);
  width:max-content; max-width:100%; margin:0 0 12px; }
.mf-vue button{ border:none; background:none; color:var(--brume); font:inherit; font-size:.84rem; font-weight:600; padding:7px 14px; border-radius:9px; cursor:pointer; }
.mf-vue button.on{ background:#1E5A44; color:#E8F6EE; box-shadow:inset 0 0 0 1px rgba(53,185,126,.55); }
.mf-stats{ display:flex; gap:8px; width:100%; margin:0 0 10px; }
.mf-stats div{ flex:1; background:rgba(169,188,212,.07); border:1px solid rgba(169,188,212,.14); border-radius:10px; padding:8px 10px; min-width:0; }
.mf-stats b{ display:block; color:#fff; font-size:1rem; font-variant-numeric:tabular-nums; }
.mf-stats span{ color:var(--brume); font-size:.66rem; }
.mf-cadre{ position:relative; width:100%; max-width:760px; border-radius:14px; overflow:hidden; border:1px solid rgba(169,188,212,.16); background:#0C1A31; }
.mf-cadre canvas{ display:block; width:100%; touch-action:none; cursor:grab; }
.mf-cadre canvas:active{ cursor:grabbing; }
.mf-zoom{ position:absolute; right:8px; top:8px; display:flex; flex-direction:column; gap:6px; }
.mf-zoom button{ width:34px; height:34px; border-radius:9px; border:1px solid rgba(169,188,212,.25); background:rgba(15,31,56,.9); color:#fff;
  font-size:1.1rem; font-weight:700; cursor:pointer; }
.mf-niveau{ position:absolute; left:10px; top:10px; background:rgba(15,31,56,.85); color:var(--brume); font-size:.68rem; padding:4px 8px;
  border-radius:999px; border:1px solid rgba(169,188,212,.2); pointer-events:none; }
.mf-leg{ display:flex; flex-wrap:wrap; gap:6px 12px; margin:10px 0 0; font-size:.72rem; color:var(--brume); }
.mf-leg i{ display:inline-block; width:10px; height:10px; border-radius:3px; margin-right:5px; vertical-align:-1px; }
.mf-bulle{ position:absolute; left:50%; bottom:12px; transform:translateX(-50%); display:flex; gap:10px; align-items:center; max-width:calc(100% - 24px);
  background:#122743; border:1px solid rgba(169,188,212,.25); border-radius:12px; padding:8px 12px 8px 8px; box-shadow:0 10px 30px rgba(0,0,0,.5); color:#fff; }
.mf-bulle[hidden]{ display:none; }
.mf-bulle b{ display:block; font-size:.9rem; white-space:nowrap; overflow:hidden; text-overflow:ellipsis; }
.mf-bulle span{ font-size:.7rem; color:var(--brume); }
.mf-bulle div{ min-width:0; }
.mf-pastille{ width:34px; height:34px; border-radius:8px; flex:none; background:#1A3256; }
.mf-pastille.commun{ background:var(--c-commun); } .mf-pastille.peucommun{ background:var(--c-peucommun); }
.mf-pastille.rare{ background:var(--c-rare); } .mf-pastille.epique{ background:var(--c-epique); } .mf-pastille.legendaire{ background:var(--c-legendaire); }
'''
ecrire('style.css', css)
print(u'patch92 : OK')
