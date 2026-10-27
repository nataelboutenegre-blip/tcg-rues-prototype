# -*- coding: utf-8 -*-
u"""
patch219 — l'outre-mer côté site (v1 : cartes Terra à collectionner).
Validé sur aperçu le 27/10 (écran Ma France + look des cartes).

1. Ma France : sélecteur France | Outre-mer. L'outre-mer montre les 5 DOM côte
   à côte, chacun à son échelle (DA « lagon »), communes coloriées par rareté si
   collectionnées ; ⤢ agrandit un territoire (noms affichés) ; toucher une
   commune ouvre une bulle, toucher la bulle ouvre la carte.
2. Cartes DOM (reconnues au code INSEE 97xxx/98xxx) : illustration lagon,
   badge « ★ Outre-mer », liseré blanc/turquoise/corail, « Rang outre-mer ».
   Grande carte, mini-carte et fiche (qui reprend la mini-carte).
3. Compteurs : la progression et « X / 34 739 » se comptent en métropole ;
   l'outre-mer a son compteur à part (« · n / 129 outre-mer »).
   (côté serveur, totaux_paliers est déjà métropole : s2-34.)
4. Recherche : « 74 » ne trouve plus La Réunion (974) — un code d'outre-mer se
   tape par le début ; « Réunion » sans l'article est reconnu comme département.
5. Règles : une phrase sur le numéro « / 129 ».
+ contours/971.json … 976.json (ajoutés à part, pas de changement de CONTOURS_V :
  ce sont des adresses nouvelles, la métropole n'est pas re-téléchargée).

Ordre : s2-34 et s2-36 passés -> ce patch pushé -> s2-35 (chargement des DOM).
Sans DOM en base, ce patch ne change rien de visible hormis le sélecteur.
"""
import io, os
ICI = os.path.dirname(os.path.abspath(__file__))
BASE = os.path.dirname(ICI) if os.path.basename(ICI) == '_patchs' else ICI
def lire(n):
    with io.open(os.path.join(BASE, n), encoding='utf-8') as f: return f.read()
def ecrire(n, s):
    with io.open(os.path.join(BASE, n), 'w', encoding='utf-8') as f: f.write(s)
def rep(s, a, b, n=1):
    c = s.count(a); assert c == n, ('MATCH', a[:70], 'trouve', c, 'attendu', n); return s.replace(a, b)

HAUT = r'''
// patch219 : l'outre-mer — un set à part (rareté propre, numéros « / 129 »), qui ne se
// mélange ni aux compteurs ni à la carte de la métropole. 97x = DOM ; 98x = Pacifique (plus tard).
// Le code INSEE suffit à reconnaître une carte : 97xxx / 98xxx, jamais en métropole.
const estOutremer = (dep) => /^9[78]/.test(String(dep || ''));
const estOutremerCode = (code) => /^9[78]\d/.test(String(code || ''));
const OM_TERR = [
  { dep: '971', nom: 'Guadeloupe', n: 32 }, { dep: '972', nom: 'Martinique', n: 34 },
  { dep: '973', nom: 'Guyane', n: 22 }, { dep: '974', nom: 'La Réunion', n: 24 },
  { dep: '976', nom: 'Mayotte', n: 17 },
];
const OM_TOTAL = OM_TERR.reduce((s, t) => s + t.n, 0);   // 129
let mfZone = 'france';            // Ma France : 'france' | 'outremer'
const OM = { focus: null, tuiles: new Map(), bulle: null };
const OM_BADGE = '<span class="om-badge" title="Commune d’outre-mer">★ Outre-mer</span>';
const OM_BADGE_MINI = '<span class="om-badge" title="Commune d’outre-mer">★</span>';'''
BLOC = r'''// en-tête de la collection : la métropole sur 34 739, l'outre-mer à part sur 129
function collectionMetro(){
  let n = 0;
  for(const e of terraCollection.values()) if(!estOutremer(e.dept)) n++;
  return n;
}
function compteurCollectionHtml(totalFrance){
  const om = collectionOutremer().n;
  return `<span class="coll-compteur"><b>${fmtNombre(collectionMetro())}</b> / ${fmtNombre(totalFrance)} communes${om ? ` <span class="om-compteur">· <b>${fmtNombre(om)}</b> / ${OM_TOTAL} outre-mer</span>` : ''}</span>`;
}

// ---------- patch219 : l'outre-mer dans Ma France ----------
// Ma France gagne un sélecteur France | Outre-mer ; l'outre-mer montre les 5
// territoires côte à côte, chacun à son échelle, dans la DA « lagon ».
function selecteurZoneMF(){
  const b = (id, nom) => `<button data-mfz="${id}" class="${mfZone === id ? 'on' : ''}" aria-pressed="${mfZone === id}">${nom}</button>`;
  return `<div class="mf-zone ${mfZone}" role="group" aria-label="Quelle carte">${b('france', 'France')}${b('outremer', 'Outre-mer')}</div>`;
}

function collectionOutremer(){
  const parDep = {};
  let n = 0;
  for(const e of terraCollection.values()){
    if(!estOutremer(e.dept)) continue;
    parDep[e.dept] = (parDep[e.dept] || 0) + 1;
    n++;
  }
  return { parDep, n };
}

function renderOutremerTerra(el){
  const { parDep, n } = collectionOutremer();
  const touches = OM_TERR.filter(t => parDep[t.dep]).length;
  const complets = OM_TERR.filter(t => (parDep[t.dep] || 0) >= t.n).length;
  const focus = OM_TERR.find(t => t.dep === OM.focus);
  const tuile = (t) => `
    <div class="om-tuile${focus ? ' grande' : ''}" data-omdep="${t.dep}">
      <span class="om-nom">${t.nom}</span>
      <span class="om-nb">${fmtNombre(parDep[t.dep] || 0)} / ${t.n} communes${(parDep[t.dep] || 0) >= t.n ? ' ✓' : ''}</span>
      <span class="om-code" aria-hidden="true">${t.dep}</span>
      ${focus ? '' : `<button class="om-agrandir" data-omfocus="${t.dep}" aria-label="Agrandir ${t.nom}">⤢</button>`}
      <canvas aria-label="${t.nom} : touche une commune pour la voir"></canvas>
      <div class="mf-bulle om-bulle" hidden></div>
    </div>`;
  el.innerHTML = `
    <div class="coll-ligne-titre"><h1>Collection</h1><span class="coll-compteur"><b>${fmtNombre(n)}</b> / ${OM_TOTAL} communes d'outre-mer</span></div>
    ${selecteurVueTerra()}
    <div class="mf-stats om">
      <div><b>${fmtNombre(n)} / ${OM_TOTAL}</b><span>communes d'outre-mer</span></div>
      <div><b>${touches} / ${OM_TERR.length}</b><span>territoires touchés</span></div>
      <div><b>${complets}</b><span>territoire${complets > 1 ? 's' : ''} complet${complets > 1 ? 's' : ''}</span></div>
    </div>
    ${selecteurZoneMF()}
    ${focus ? `<button class="om-retour" data-omfocus="">← Les 5 territoires</button>` : ''}
    <div class="om-grille${focus ? ' focus' : ''}">${(focus ? [focus] : OM_TERR).map(tuile).join('')}</div>
    <div class="mf-leg">${TIERS.slice().reverse().map(t => `<span><i style="background:${COULEURS_FILTRE[t.id]}"></i>${t.label}</span>`).join('')}<span><i class="om-vide"></i>Pas encore</span></div>`;
  OM.tuiles.clear();
  OM.bulle = null;
  for(const div of el.querySelectorAll('.om-tuile')){
    const dep = div.dataset.omdep;
    const tu = { div, cv: div.querySelector('canvas'), chemins: [] };
    OM.tuiles.set(dep, tu);
    chargerContours(dep).then(() => omDessiner(dep));
  }
}

// projection propre à chaque territoire : équirectangulaire corrigée de la
// latitude, ajustée dans la tuile
function omProjection(contours, larg, haut, marge, entete){
  let x0 = Infinity, y0 = Infinity, x1 = -Infinity, y1 = -Infinity, sl = 0, nl = 0;
  for(const code in contours) for(const anneau of contours[code]) for(const [lon, lat] of anneau){
    if(lon < x0) x0 = lon; if(lon > x1) x1 = lon; if(lat < y0) y0 = lat; if(lat > y1) y1 = lat;
    sl += lat; nl++;
  }
  const kx = Math.cos((sl / nl) * Math.PI / 180);
  const w = (x1 - x0) * kx, h = y1 - y0;
  // le haut de la tuile porte le nom et le compteur : on dessine en dessous
  const s = Math.min((larg - 2 * marge) / w, (haut - entete - 2 * marge) / h);
  const ox = (larg - w * s) / 2, oy = entete + (haut - entete - h * s) / 2;
  return (lon, lat) => [ox + (lon - x0) * kx * s, oy + (y1 - lat) * s];
}

function omDessiner(dep){
  const tu = OM.tuiles.get(dep);
  const contours = CONTOURS.get(dep);
  if(!tu || !document.body.contains(tu.cv)) return;
  const cv = tu.cv, larg = cv.clientWidth;
  if(larg < 40) return;
  const grand = tu.div.classList.contains('grande');
  const haut = Math.round(grand ? Math.min(larg * 0.9, window.innerHeight * 0.66) : larg * 1.05);
  const dpr = Math.min(window.devicePixelRatio || 1, 2);
  cv.width = Math.round(larg * dpr); cv.height = Math.round(haut * dpr); cv.style.height = haut + 'px';
  const ctx = cv.getContext('2d');
  ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
  ctx.clearRect(0, 0, larg, haut);
  // les fonds marins : des courbes de niveau autour de l'île
  for(let i = 8; i >= 1; i--){
    ctx.strokeStyle = `rgba(44,198,201,${(0.04 + i * 0.012).toFixed(3)})`;
    ctx.lineWidth = 1;
    ctx.beginPath();
    ctx.ellipse(larg / 2, haut / 2 + 20, larg * 0.075 * i, haut * 0.07 * i, 0, 0, Math.PI * 2);
    ctx.stroke();
  }
  if(!contours || contours === 'erreur'){ tu.chemins = []; return; }
  const P = omProjection(contours, larg, haut, grand ? 18 : 10, grand ? 40 : 46);
  tu.P = P;
  tu.chemins = [];
  for(const code in contours){
    const p = new Path2D();
    for(const anneau of contours[code]){
      anneau.forEach(([lon, lat], i) => { const [x, y] = P(lon, lat); i ? p.lineTo(x, y) : p.moveTo(x, y); });
      p.closePath();
    }
    tu.chemins.push([code, p]);
    const e = terraCollection.get(code);
    ctx.fillStyle = e ? COULEURS_FILTRE[e.tier.id] : '#14454E';
    ctx.globalAlpha = e ? 0.95 : 1;
    ctx.fill(p);
    ctx.globalAlpha = 1;
    ctx.strokeStyle = e ? 'rgba(4,30,36,.85)' : 'rgba(44,198,201,.38)';
    ctx.lineWidth = grand ? 1.1 : 0.8;
    ctx.stroke(p);
  }
  if(OM.bulle && OM.bulle.dep === dep){
    const c = tu.chemins.find(([code]) => code === OM.bulle.code);
    if(c){ ctx.strokeStyle = '#fff'; ctx.lineWidth = 2.2; ctx.stroke(c[1]); }
  }
  if(grand) omNoms(ctx, tu, contours, larg, haut);
}

// en grand : le nom des communes de la collection, sans chevauchement
function omNoms(ctx, tu, contours, larg, haut){
  const liste = [];
  for(const code in contours){ const e = terraCollection.get(code); if(e) liste.push([e, contours[code]]); }
  liste.sort((a, b) => (b[0].pop || 0) - (a[0].pop || 0));
  ctx.font = '600 11px ' + getComputedStyle(document.body).getPropertyValue('--texte');
  ctx.textAlign = 'center'; ctx.textBaseline = 'middle';
  const pris = [];
  for(const [e, poly] of liste){
    let anneau = poly[0]; for(const a of poly) if(a.length > anneau.length) anneau = a;
    let sx = 0, sy = 0; for(const [lon, lat] of anneau){ const [x, y] = tu.P(lon, lat); sx += x; sy += y; }
    const x = sx / anneau.length, y = sy / anneau.length;
    const w = ctx.measureText(e.nom).width + 6;
    const r = [x - w / 2, y - 7, x + w / 2, y + 7];
    if(r[0] < 2 || r[2] > larg - 2 || r[1] < 2 || r[3] > haut - 2) continue;
    if(pris.some(q => r[0] < q[2] && r[2] > q[0] && r[1] < q[3] && r[3] > q[1])) continue;
    pris.push(r);
    ctx.fillStyle = 'rgba(2,14,18,.8)'; ctx.fillText(e.nom, x + 1, y + 1);
    ctx.fillStyle = '#fff'; ctx.fillText(e.nom, x, y);
  }
}

function omToucher(dep, px, py){
  const tu = OM.tuiles.get(dep);
  if(!tu) return;
  const ctx = tu.cv.getContext('2d');
  const dpr = tu.cv.width / tu.cv.clientWidth;
  ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
  const avant = OM.bulle && OM.bulle.dep;
  const trouve = tu.chemins.find(([, p]) => ctx.isPointInPath(p, px * dpr, py * dpr));
  OM.bulle = trouve ? { dep, code: trouve[0] } : null;
  if(avant && avant !== dep) omDessiner(avant);
  omDessiner(dep);
  for(const [d, t] of OM.tuiles){
    const b = t.div.querySelector('.om-bulle');
    if(!OM.bulle || d !== OM.bulle.dep){ b.hidden = true; continue; }
    const e = terraCollection.get(OM.bulle.code);
    const terr = OM_TERR.find(x => x.dep === d);
    b.hidden = false;
    b.innerHTML = e
      ? `<i class="mf-pastille ${e.tier.id}"></i><div><b>${echapperTexte(e.nom)}</b><span>${e.tier.label} · ×${e.exemplaires} · n° ${e.rank} / ${e.tierSize}</span></div>`
      : `<i class="mf-pastille vide"></i><div><b>Pas encore dans ta collection</b><span>${echapperTexte(terr.nom)} · tire-la dans un paquet</span></div>`;
    if(e) b.dataset.tcode = e.code; else delete b.dataset.tcode;
  }
}

function clicOutremer(e){
  const z = e.target.closest('[data-mfz]');
  if(z){ if(mfZone !== z.dataset.mfz){ mfZone = z.dataset.mfz; OM.focus = null; renderCollectionTerra(); } return true; }
  const f = e.target.closest('[data-omfocus]');
  if(f){ OM.focus = f.dataset.omfocus || null; renderCollectionTerra(); return true; }
  const cv = e.target.closest('.om-tuile canvas');
  if(cv){
    const r = cv.getBoundingClientRect();
    omToucher(cv.parentElement.dataset.omdep, e.clientX - r.left, e.clientY - r.top);
    return true;
  }
  return false;
}

// l'illustration : un lagon, des fonds marins en courbes, une île à l'épingle
// de la couleur de la rareté. Stable pour une commune donnée.
function artLagonSvg(code, tierId, w, h, id){
  const [clair, fonce] = TEINTES_CARTE[tierId];
  const rnd = aleatoireStable(hashTexte('om' + code));
  const cx = w * (0.3 + 0.4 * rnd()), cy = h * (0.38 + 0.24 * rnd());
  const ang = Math.round(rnd() * 50 - 25);
  let anneaux = '';
  for(let i = 1; i <= 8; i++){
    anneaux += `<ellipse cx="${cx.toFixed(1)}" cy="${cy.toFixed(1)}" rx="${(w * 0.075 * i).toFixed(1)}" ry="${(h * 0.1 * i).toFixed(1)}"`
      + ` transform="rotate(${ang} ${cx.toFixed(1)} ${cy.toFixed(1)})" fill="none" stroke="rgba(191,244,245,${(0.34 - i * 0.03).toFixed(2)})" stroke-width="1"/>`;
  }
  const ri = Math.min(w, h) * 0.11;
  return `<svg viewBox="0 0 ${w} ${h}" preserveAspectRatio="xMidYMid slice" aria-hidden="true">
    <defs><radialGradient id="${id}" cx="${(cx / w * 100).toFixed(0)}%" cy="${(cy / h * 100).toFixed(0)}%" r="90%">
      <stop offset="0%" stop-color="#7FE7E4"/><stop offset="38%" stop-color="#1A8C96"/><stop offset="100%" stop-color="#06252E"/></radialGradient></defs>
    <rect width="${w}" height="${h}" fill="url(#${id})"/>
    ${anneaux}
    <ellipse cx="${cx.toFixed(1)}" cy="${cy.toFixed(1)}" rx="${(ri * 1.5).toFixed(1)}" ry="${ri.toFixed(1)}" transform="rotate(${ang} ${cx.toFixed(1)} ${cy.toFixed(1)})" fill="#F3E2B7" opacity=".92"/>
    <ellipse cx="${cx.toFixed(1)}" cy="${cy.toFixed(1)}" rx="${(ri * 1.05).toFixed(1)}" ry="${(ri * 0.68).toFixed(1)}" transform="rotate(${ang} ${cx.toFixed(1)} ${cy.toFixed(1)})" fill="${clair}"/>
    <circle cx="${cx.toFixed(1)}" cy="${cy.toFixed(1)}" r="${(ri * 0.42).toFixed(1)}" fill="#fff" stroke="${fonce}" stroke-width="2"/>
  </svg>`;
}

'''
CSS = r'''/* =====================================================================
   patch219 — l'outre-mer dans Ma France (DA « lagon »)
   ===================================================================== */
.mf-zone{ display:flex; gap:4px; padding:4px; border-radius:999px; width:max-content; max-width:100%; margin:0 0 10px;
  background:rgba(0,0,0,.28); border:1px solid rgba(169,188,212,.16); }
.mf-zone button{ border:none; background:none; color:var(--brume); font:inherit; font-size:.84rem; font-weight:700; padding:7px 16px;
  border-radius:999px; cursor:pointer; }
.mf-zone.france button.on{ background:#1E5A44; color:#E8F6EE; box-shadow:inset 0 0 0 1px rgba(53,185,126,.55); }
.mf-zone.outremer button.on{ background:#2CC6C9; color:#04252A; }
.mf-stats.om div{ background:rgba(44,198,201,.07); border-color:rgba(44,198,201,.22); }
.om-grille{ display:grid; grid-template-columns:repeat(auto-fill, minmax(150px, 1fr)); gap:10px; width:100%; max-width:760px; }
.om-grille.focus{ grid-template-columns:1fr; }
.om-tuile{ position:relative; border-radius:14px; overflow:hidden; border:1px solid rgba(44,198,201,.3);
  background:radial-gradient(130% 100% at 50% 0%, #0A3942, #06252E 70%); }
.om-tuile canvas{ display:block; width:100%; touch-action:manipulation; cursor:pointer; }
.om-nom{ position:absolute; left:11px; top:9px; font-weight:800; font-size:.92rem; color:#fff; text-shadow:0 1px 6px rgba(0,0,0,.6);
  pointer-events:none; }
.om-nb{ position:absolute; left:11px; top:29px; font-size:.7rem; font-weight:700; color:#2CC6C9; pointer-events:none; }
.om-code{ display:none; }
.om-tuile.grande .om-code{ display:block; position:absolute; right:12px; top:6px; font-size:2rem; font-weight:900; color:rgba(255,255,255,.1); pointer-events:none; }
.om-agrandir{ position:absolute; right:7px; top:7px; width:30px; height:30px; border-radius:9px; border:1px solid rgba(44,198,201,.35);
  background:rgba(6,37,46,.85); color:#fff; font-size:1rem; cursor:pointer; }
.om-retour{ display:block; margin:0 0 10px; border:1px solid rgba(44,198,201,.35); background:rgba(44,198,201,.1); color:#BFF4F5;
  font:inherit; font-size:.8rem; font-weight:700; padding:6px 12px; border-radius:999px; cursor:pointer; }
.om-bulle{ background:#0B3540; border-color:rgba(44,198,201,.4); bottom:8px; left:8px; right:8px; transform:none; max-width:none; }
.om-bulle[data-tcode]{ cursor:pointer; }
.mf-pastille.vide{ background:#14454E; box-shadow:inset 0 0 0 1px rgba(44,198,201,.5); }
.mf-leg .om-vide{ background:#14454E; box-shadow:inset 0 0 0 1px rgba(44,198,201,.5); }

/* patch219 — la carte d'une commune d'outre-mer */
.om-badge{ position:absolute; left:6px; top:6px; z-index:1; font-size:.58rem; font-weight:800; letter-spacing:.06em; text-transform:uppercase;
  color:#04252A; background:#F3E2B7; padding:2px 7px; border-radius:999px; box-shadow:0 2px 6px rgba(0,0,0,.25); }
.mini .om-badge{ left:4px; top:4px; font-size:.6rem; padding:1px 5px; letter-spacing:0; }
.card.outremer .carte-lisere span:nth-child(1), .mini.outremer .mini-lisere span:nth-child(1){ background:#fff; }
.card.outremer .carte-lisere span:nth-child(2), .mini.outremer .mini-lisere span:nth-child(2){ background:#2CC6C9; }
.card.outremer .carte-lisere span:nth-child(3), .mini.outremer .mini-lisere span:nth-child(3){ background:#FF7A59; }
.card.outremer .carte-dept, .mini.outremer .mini-dept{ color:rgba(255,255,255,.34); }
.om-compteur{ color:#2CC6C9; font-weight:600; }
'''

js = lire('app.js')
assert 'patch219' not in js

# 0. constantes de l'outre-mer, en tête (utilisées au rendu des cartes)
js = rep(js, r"""const METRO_DEPT_RE = /^(0[1-9]|[1-8][0-9]|9[0-5]|2A|2B)$/;""",
  r"""const METRO_DEPT_RE = /^(0[1-9]|[1-8][0-9]|9[0-5]|2A|2B)$/;""" + HAUT)

# 1. illustration lagon (grande carte et mini-carte)
js = rep(js, r"""function carteArtSvg(code, tierId){
""", r"""function carteArtSvg(code, tierId){
  if(estOutremerCode(code)) return artLagonSvg(code, tierId, 200, 120, 'cg' + code);   // patch219
""")
js = rep(js, r"""function miniArtGabarit(code, tierId, cle){
""", r"""function miniArtGabarit(code, tierId, cle){
  if(estOutremerCode(code)){ const s = artLagonSvg(code, tierId, 160, 100, '__MGID__'); miniArtCache.set(cle, s); return s; }   // patch219
""")

# 2. grande carte : classe, badge, rang
js = rep(js, r"""wrap.className = 'card ' + draw.tier.id + (mon ? ' a-monument' : '') + (draw.aurore ? ' aurore' : '');""",
  r"""wrap.className = 'card ' + draw.tier.id + (mon ? ' a-monument' : '') + (draw.aurore ? ' aurore' : '') + (estOutremerCode(draw.code) ? ' outremer' : '');   // patch219""")
js = rep(js, r"""<div class="carte-art">${carteArtSvg(draw.code, draw.tier.id)}""",
  r"""<div class="carte-art">${estOutremerCode(draw.code) ? OM_BADGE : ''}${carteArtSvg(draw.code, draw.tier.id)}""")
js = rep(js, r"""<div><span>Rang</span><b>${draw.rank.toLocaleString('fr-FR')}</b></div>""",
  r"""<div><span>${estOutremerCode(draw.code) ? 'Rang outre-mer' : 'Rang'}</span><b>${draw.rank.toLocaleString('fr-FR')}</b></div>""")

# 3. mini-carte (collection, bilan de paquet, fiche)
js = rep(js, r"""return `<div class="mini ${e.tier.id}${au ? ' aurore' : ''}""",
  r"""return `<div class="mini ${e.tier.id}${au ? ' aurore' : ''}${estOutremerCode(e.code) ? ' outremer' : ''}""")
js = rep(js, r"""<div class="mini-art">${e.photo ?""",
  r"""<div class="mini-art">${estOutremerCode(e.code) ? OM_BADGE_MINI : ''}${e.photo ?""")

# 4. recherche
js = rep(js, r"""      || String(dept).toLowerCase().includes(recherche)
""", r"""      // patch219 : « 74 » ne doit pas trouver La Réunion (974) — un code d'outre-mer se tape par le début
      || (String(dept).length > 2 ? String(dept).toLowerCase().startsWith(recherche) : String(dept).toLowerCase().includes(recherche))
""")
js = rep(js, r"""  const exact = codes.find(c => nu(DEPT_NAMES[c]) === t);
  if(exact) return exact;
  const debuts = codes.filter(c => nu(DEPT_NAMES[c]).startsWith(t));""",
  r"""  // patch219 : « Réunion » sans l'article trouve La Réunion
  const noms = (c) => { const n = DEPT_NAMES[c], s = n.replace(/^(la|le|les|l['’])\s*/i, ''); return s !== n ? [nu(n), nu(s)] : [nu(n)]; };
  const exact = codes.find(c => noms(c).includes(t));
  if(exact) return exact;
  const debuts = codes.filter(c => noms(c).some(x => x.startsWith(t)));""")

# 5. compteurs de la collection : métropole d'un côté, outre-mer de l'autre
js = rep(js, r"""<span class="coll-compteur"><b>${fmtNombre(terraCollection.size)}</b> / ${fmtNombre(totalFrance)} communes</span>""",
  r"""${compteurCollectionHtml(totalFrance)}""", 2)
js = rep(js, r"""  for(const e of terraCollection.values()) parTier[e.tier.id] = (parTier[e.tier.id] || 0) + 1;
""", r"""  for(const e of terraCollection.values()) parTier[e.tier.id] = (parTier[e.tier.id] || 0) + 1;
  // patch219 : la progression par rareté se compte en métropole (les totaux du serveur aussi)
  const parTierM = {};
  for(const e of terraCollection.values()) if(!estOutremer(e.dept)) parTierM[e.tier.id] = (parTierM[e.tier.id] || 0) + 1;
""")
js = rep(js, r"""      const n = parTier[t.id] || 0, total""", r"""      const n = parTierM[t.id] || 0, total""")

# 6. Ma France : sélecteur, branche outre-mer, pourcentage en métropole
js = rep(js, r"""function renderMaFranceTerra(el, totalFrance){
""", r"""function renderMaFranceTerra(el, totalFrance){
  if(mfZone === 'outremer') return renderOutremerTerra(el);   // patch219
""")
js = rep(js, r"""  const pct = totalFrance ? 100 * terraCollection.size / totalFrance : 0;""",
  r"""  const pct = totalFrance ? 100 * collectionMetro() / totalFrance : 0;   // patch219""")
js = rep(js, r"""    <div class="mf-cadre" id="mfCadre">""", r"""    ${selecteurZoneMF()}
    <div class="mf-cadre" id="mfCadre">""")
js = rep(js, r"""  if(clicCollections(e)) return;   // patch112
""", r"""  if(clicCollections(e)) return;   // patch112
  if(clicOutremer(e)) return;   // patch219
""")
js = rep(js, r"""window.addEventListener('resize', () => {
  if(terraVue === 'france' && MF.cv && document.body.contains(MF.cv)){ mfDimensionner(); mfLimiter(); mfPlanifier(); }
});
""", BLOC + r"""window.addEventListener('resize', () => {
  if(terraVue === 'france' && MF.cv && document.body.contains(MF.cv)){ mfDimensionner(); mfLimiter(); mfPlanifier(); }
  if(terraVue === 'france' && mfZone === 'outremer') for(const dep of OM.tuiles.keys()) omDessiner(dep);   // patch219
});
""")
ecrire('app.js', js)

# 7. style
css = lire('style.css')
assert 'patch219' not in css
ecrire('style.css', css.rstrip('\n') + '\n\n' + CSS)

# 8. règles
html = lire('index.html')
html = rep(html, r"""est son rang parmi les communes de sa rareté, de la plus peuplée à la moins peuplée.</p>""",
  r"""est son rang parmi les communes de sa rareté, de la plus peuplée à la moins peuplée. Les communes d'outre-mer forment un set à part : leur numéro, par exemple <b>n° 3 / 129</b>, est leur rang parmi les 129 communes d'outre-mer.</p>""")
ecrire('index.html', html)
print('patch219 OK')
