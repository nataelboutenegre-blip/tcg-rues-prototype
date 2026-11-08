# patch377 (8/11/2026) : l'impact de la bombe sur la carte Territoire.
# Aperçu validé par Nataël le 5/11 à 14 h 53 (« c'est parfait ! ») :
# https://claude.ai/artifact/Wue8jQNB3iTDF4RuUCb6wk — demandé le 8/11 à 15 h 02.
#   - la bannière d'une bombe gagne « Voir › » : la carte glisse jusqu'à la zone,
#     viseur, flash, deux ondes de choc jusqu'au rayon, la zone rougit, les
#     garnisons soufflées éclatent (la tienne en or, s2-119), tremblement, puis
#     le cercle en pointillés habituel ;
#   - une fois par bombe et par joueur, l'impact se rejoue tout seul quand la
#     zone est assez grande à l'écran ; toucher l'étiquette « 💥 +15 % » le rejoue ;
#   - « réduire les animations » : la carte va sur la zone, sans effet ;
#   - un calque à part au-dessus de la carte (rien n'est redessiné en plus) ;
#     toucher la carte pendant l'animation l'arrête.
import pathlib

def rep(s, avant, apres, n=1):
    c = s.count(avant)
    assert c == n, f'{c} fois au lieu de {n} : {avant[:80]!r}'
    return s.replace(avant, apres)

F = pathlib.Path('app.js'); s = F.read_text(encoding='utf-8')
assert 'patch377' not in s, 'patch377 déjà appliqué'

# ---------- la bannière : « Voir › » ----------
s = rep(s, """    : `<span class="gc-ico">💥</span><span class="gc-tx"><b><em>${echapperTexte(a.lanceur_pseudo || 'Un joueur')}</em> a lâché une bombe sur ${echapperTexte(a.cible_nom || '')}</b><small>${perte ? `Tu y perds ${[a.mes_garnisons ? a.mes_garnisons + ' garnison' + (a.mes_garnisons > 1 ? 's' : '') : '', a.mes_forteresses ? a.mes_forteresses + ' forteresse' + (a.mes_forteresses > 1 ? 's' : '') : ''].filter(Boolean).join(' et ')} · ` : ''}+${btReglage('bombe_bonus', 15)} % en attaque dans la zone pendant 24 h</small></span>`;
  el.addEventListener('click', () => el.remove());""",
"""    : `<span class="gc-ico">💥</span><span class="gc-tx"><b><em>${echapperTexte(a.lanceur_pseudo || 'Un joueur')}</em> a lâché une bombe sur ${echapperTexte(a.cible_nom || '')}</b><small>${perte ? `Tu y perds ${[a.mes_garnisons ? a.mes_garnisons + ' garnison' + (a.mes_garnisons > 1 ? 's' : '') : '', a.mes_forteresses ? a.mes_forteresses + ' forteresse' + (a.mes_forteresses > 1 ? 's' : '') : ''].filter(Boolean).join(' et ')} · ` : ''}+${btReglage('bombe_bonus', 15)} % en attaque dans la zone pendant 24 h</small></span>`
      + (a.etat === 'active' && MODE_CANVAS ? '<button type="button" class="gc-voir">Voir ›</button>' : '');   // patch377
  el.addEventListener('click', (e) => { if(e.target.closest('.gc-voir')) bfxVoir(a.id); el.remove(); });""")

# ---------- la zone bombardée : cachée sur la carte pendant son animation ----------
s = rep(s, """  for(const z of BOMBES_ZONES){
    if(z.lat == null || new Date(z.fin).getTime() < Date.now()) continue;
    const p = project(z.lat, z.lon);""",
"""  for(const z of BOMBES_ZONES){
    if(z.lat == null || new Date(z.fin).getTime() < Date.now()) continue;
    if(BFX && BFX.cache && BFX.z.id === z.id) continue;   // patch377 : l'animation la dessine
    const p = project(z.lat, z.lon);""")
s = rep(s, """// ---------- la mallette de frappe ----------
let ML = null;""",
"""// ---------- patch377 : l'impact de la bombe sur la carte (aperçu validé le 5/11) ----------
let BFX = null;
const BFX_CLE = 'tf-bombes-anim';
function bfxVues(){ try{ const v = JSON.parse(localStorage.getItem(BFX_CLE) || '[]'); return new Set(Array.isArray(v) ? v : []); }catch(e){ return new Set(); } }
function bfxNoter(id){ try{ const v = [...bfxVues()].filter(x => x !== id); v.unshift(id); localStorage.setItem(BFX_CLE, JSON.stringify(v.slice(0, 40))); }catch(e){} }
const bfxEase = (t) => t < 0 ? 0 : t > 1 ? 1 : 1 - Math.pow(1 - t, 3);
const bfxEaseIO = (t) => t < 0 ? 0 : t > 1 ? 1 : t < .5 ? 4 * t * t * t : 1 - Math.pow(-2 * t + 2, 3) / 2;
const bfxBorne = (t) => Math.max(0, Math.min(1, t));
const bfxLerp = (a, b, t) => a + (b - a) * t;
function bfxGeo(z){
  const { latMin, latMax, lonMin, lonMax } = mapBounds;
  const p = project(z.lat, z.lon);
  return { cx: p.x * MAP_W, cy: p.y * MAP_H,
           ry: z.rayon_km / 111.19 / (latMax - latMin) * MAP_H,
           rx: z.rayon_km / (111.19 * Math.cos(z.lat * Math.PI / 180)) / (lonMax - lonMin) * MAP_W };
}
function bfxCalque(){
  const wrap = document.getElementById('mapWrap');
  if(!wrap || !wrap.clientWidth) return null;
  let cv = document.getElementById('mapBombeFx');
  if(!cv){ cv = document.createElement('canvas'); cv.id = 'mapBombeFx'; cv.className = 'map-bombe-fx'; cv.setAttribute('aria-hidden', 'true'); wrap.appendChild(cv); }
  const dpr = Math.min(window.devicePixelRatio || 1, 2), w = wrap.clientWidth, h = wrap.clientHeight;
  if(cv.width !== Math.round(w * dpr) || cv.height !== Math.round(h * dpr)){ cv.width = Math.round(w * dpr); cv.height = Math.round(h * dpr); }
  return { cv, ctx: cv.getContext('2d'), dpr, w, h };
}
function bfxArreter(){
  if(!BFX) return;
  cancelAnimationFrame(BFX.raf);
  const c = document.getElementById('mapBombeFx');
  if(c) c.getContext('2d').clearRect(0, 0, c.width, c.height);
  const m = document.getElementById('mapCanvas'); if(m) m.style.transform = '';
  BFX = null;
  demanderDessin();
}
// la bannière : aller sur la carte, puis jouer
function bfxVoir(id){
  const jouer = () => { const z = (BOMBES_ZONES || []).find(x => x.id === id); if(z) bfxJouer(z, true); };
  const wrap = document.getElementById('mapWrap');
  if(wrap && wrap.clientWidth && modeJeu === 'front') jouer();
  else ncAller('front', 'territoire', () => setTimeout(jouer, 350));
}
// les garnisons soufflées (s2-119) : position et « à moi »
async function bfxTouchees(z){
  if(z._touchees) return z._touchees;
  let L = [];
  try{ const { data, error } = await sb.rpc('bombe_touchees', { p_id: z.id }); if(!error && Array.isArray(data)) L = data; }catch(e){}
  z._touchees = L.map(t => { const c = collectionMap.get(t.c) || othersMap.get(t.c); if(!c || c.lat == null) return null; const p = project(c.lat, c.lon); return { x: p.x * MAP_W, y: p.y * MAP_H, moi: !!t.moi }; }).filter(Boolean);
  return z._touchees;
}
async function bfxJouer(z, camera){
  if(!z || z.lat == null || !mapBounds || !canvasActif()) return;
  bfxArreter();
  const wrap = document.getElementById('mapWrap');
  if(!wrap || !wrap.clientWidth) return;
  fermerPanneau();
  bfxNoter(z.id);
  if(camera){   // sur téléphone, la carte passe en plein écran ; ailleurs, on la ramène dans l'écran
    if(typeof pleinEcranPossible === 'function' && pleinEcranPossible()) entrerPleinEcran();
    else { const r = wrap.getBoundingClientRect(); if(r.top < 0 || r.bottom > window.innerHeight) wrap.scrollIntoView({ block: 'center' }); }
  }
  const g = bfxGeo(z), W = wrap.clientWidth, H = wrap.clientHeight, ech = echelleCarte();
  const Z0 = mapZoom, c0 = [(W / 2 - mapPanX) / (ech * Z0), (H / 2 - mapPanY) / (ech * Z0)];
  const Z1 = Math.min(zoomMaxCarte(), Math.max(MAP_ZOOM_MIN, 0.62 * Math.min(W, H) / (2 * Math.max(g.rx, g.ry) * ech)));
  const reduit = window.matchMedia && window.matchMedia('(prefers-reduced-motion: reduce)').matches;
  if(reduit){
    if(camera){ mapZoom = Z1; mapPanX = W / 2 - g.cx * ech * Z1; mapPanY = H / 2 - g.cy * ech * Z1; applyMapTransform(); renderMapOverlay(); }
    return;
  }
  const touchees = await bfxTouchees(z);
  BFX = { z, g, camera: !!camera, Z0, Z1, c0, t0: performance.now(), cache: true, touchees, raf: 0 };
  // une image nette sans la zone : c'est elle qu'on agrandit pendant le glissement
  CV.geste = false; dessinerCanvas();
  BFX.t0 = performance.now();
  BFX.raf = requestAnimationFrame(bfxImage);
}
function bfxImage(now){
  const B = BFX; if(!B) return;
  const t = (now - B.t0) / 1000;
  const wrap = document.getElementById('mapWrap'), ech = echelleCarte();
  if(!wrap || !wrap.clientWidth){ bfxArreter(); return; }
  const W = wrap.clientWidth, H = wrap.clientHeight;
  // 1. la carte glisse jusqu'à la zone (1,3 s)
  const tImpact = B.camera ? 1.95 : 0.7;
  if(B.camera && !B.camFini){
    const k = bfxEaseIO(Math.min(1, t / 1.3));
    mapZoom = B.Z0 * Math.pow(B.Z1 / B.Z0, k);
    const cx = bfxLerp(B.c0[0], B.g.cx, k), cy = bfxLerp(B.c0[1], B.g.cy, k);
    mapPanX = W / 2 - cx * ech * mapZoom; mapPanY = H / 2 - cy * ech * mapZoom;
    applyMapTransform();
    if(k >= 1){ B.camFini = true; renderMapOverlay(); }
  }
  const ti = t - tImpact;
  const st = {
    viseur: bfxBorne((t - (tImpact - .65)) / .65),
    flash: ti > 0 ? Math.max(0, 1 - ti / .45) : 0,
    ondes: [ti / 1.1, (ti - .28) / 1.1],
    rouge: ti > 0 ? (ti < .25 ? ti / .25 : Math.max(.22, 1 - (ti - .25) / 1.4)) : 0,
    eclat: ti < .15 ? 0 : (ti - .15) / .7,
    zone: bfxBorne((ti - 1.0) / .6),
    dx: ti > 0 && ti < .35 ? Math.sin(ti * 90) * 3 * (1 - ti / .35) : 0,
    dy: ti > 0 && ti < .35 ? Math.cos(ti * 70) * 2 * (1 - ti / .35) : 0
  };
  if(ti > 1.6) st.rouge = .22 * Math.max(0, 1 - (ti - 1.6) / .8);
  const m = document.getElementById('mapCanvas');
  if(m) m.style.transform = st.dx || st.dy ? `translate(${st.dx.toFixed(2)}px, ${st.dy.toFixed(2)}px)` : '';
  // la zone réapparaît sur la carte elle-même à la fin du fondu
  if(B.cache && ti > 1.6){ B.cache = false; demanderDessin(); }
  bfxDessiner(B, st);
  if(ti > 2.5){ bfxArreter(); setTimeout(bfxAuto, 500); return; }   // plusieurs bombes : la suivante, si elle est à l'écran
  B.raf = requestAnimationFrame(bfxImage);
}
function bfxDessiner(B, st){
  const L = bfxCalque(); if(!L) return;
  const { ctx, dpr, w, h } = L, ech = echelleCarte(), s = ech * mapZoom, lw = 1 / s;
  ctx.setTransform(1, 0, 0, 1, 0, 0); ctx.clearRect(0, 0, L.cv.width, L.cv.height);
  ctx.setTransform(dpr * s, 0, 0, dpr * s, dpr * (mapPanX + st.dx), dpr * (mapPanY + st.dy));
  const { cx, cy, rx, ry } = B.g;
  const ellipse = (k) => { ctx.beginPath(); ctx.ellipse(cx, cy, rx * k, ry * k, 0, 0, Math.PI * 2); };
  // la zone rougit (sur la terre seulement)
  if(st.rouge > 0){
    ctx.save();
    const fond = typeof cheminsDuFond === 'function' ? cheminsDuFond() : null;
    if(fond && fond.terre) ctx.clip(fond.terre);
    ctx.translate(cx, cy); ctx.scale(rx / ry, 1);
    const gr = ctx.createRadialGradient(0, 0, 0, 0, 0, ry);
    gr.addColorStop(0, `rgba(255,70,60,${(.75 * st.rouge).toFixed(3)})`); gr.addColorStop(1, `rgba(255,70,60,${(.75 * st.rouge * .65).toFixed(3)})`);
    ctx.fillStyle = gr; ctx.beginPath(); ctx.arc(0, 0, ry, 0, Math.PI * 2); ctx.fill();
    ctx.restore();
  }
  // le cercle d'aujourd'hui, en fondu (la carte le reprend ensuite)
  if(B.cache && st.zone > 0){
    ctx.globalAlpha = st.zone; ellipse(1);
    ctx.fillStyle = 'rgba(229,72,77,0.15)'; ctx.fill();
    ctx.setLineDash([6 * lw, 4 * lw]); ctx.strokeStyle = 'rgba(255,90,82,0.95)'; ctx.lineWidth = 1.8 * lw; ctx.stroke(); ctx.setLineDash([]);
    ctx.globalAlpha = 1;
  }
  // les garnisons soufflées
  const tG = 7 * lw;
  const bouclier = (x, y, coul, alpha, sc) => {
    ctx.save(); ctx.translate(x, y); ctx.scale(sc, sc); ctx.globalAlpha = alpha;
    ctx.beginPath(); ctx.moveTo(0, -tG); ctx.lineTo(tG * .85, -tG * .6); ctx.lineTo(tG * .7, tG * .35); ctx.lineTo(0, tG); ctx.lineTo(-tG * .7, tG * .35); ctx.lineTo(-tG * .85, -tG * .6); ctx.closePath();
    ctx.fillStyle = coul; ctx.fill(); ctx.strokeStyle = '#07111F'; ctx.lineWidth = tG * .22; ctx.stroke();
    ctx.restore();
  };
  for(const g of B.touchees || []){
    const e = st.eclat, coul = g.moi ? '#F0B429' : '#DCE6F2';
    if(e <= 0) bouclier(g.x, g.y, coul, 1, 1);
    else if(e < 1){
      bouclier(g.x, g.y, coul, 1 - e, 1 + e * 1.2);
      for(let i = 0; i < 7; i++){
        const a = i / 7 * Math.PI * 2 + g.x * 40, d = tG * (1 + e * 4.5);
        ctx.beginPath(); ctx.arc(g.x + Math.cos(a) * d, g.y + Math.sin(a) * d, tG * .22 * (1 - e), 0, Math.PI * 2);
        ctx.fillStyle = g.moi ? `rgba(240,180,41,${1 - e})` : `rgba(255,170,150,${1 - e})`; ctx.fill();
      }
    }
  }
  // les ondes de choc
  for(const o of st.ondes){
    if(o <= 0 || o >= 1) continue;
    ellipse(bfxEase(o) * 1.02);
    ctx.strokeStyle = `rgba(255,${Math.round(bfxLerp(240, 90, o))},${Math.round(bfxLerp(220, 80, o))},${(1 - o).toFixed(3)})`;
    ctx.lineWidth = bfxLerp(6, 1.5, o) * lw; ctx.stroke();
  }
  // l'éclair
  if(st.flash > 0){
    ctx.save(); ctx.translate(cx, cy); ctx.scale(rx / ry, 1);
    const gr = ctx.createRadialGradient(0, 0, 0, 0, 0, ry * .9);
    gr.addColorStop(0, `rgba(255,255,255,${st.flash})`); gr.addColorStop(.35, `rgba(255,190,150,${st.flash * .7})`); gr.addColorStop(1, 'rgba(255,90,82,0)');
    ctx.fillStyle = gr; ctx.beginPath(); ctx.arc(0, 0, ry * .9, 0, Math.PI * 2); ctx.fill();
    ctx.restore();
  }
  // le viseur
  if(st.viseur > 0 && st.viseur < 1){
    const v = st.viseur, rr = ry * bfxLerp(1.6, .18, bfxEase(v));
    ctx.save(); ctx.translate(cx, cy); ctx.rotate(v * 1.2);
    ctx.strokeStyle = `rgba(255,90,82,${Math.min(1, v * 3).toFixed(3)})`; ctx.lineWidth = 2 * lw;
    ctx.beginPath(); ctx.arc(0, 0, rr, 0, Math.PI * 2); ctx.stroke();
    for(let i = 0; i < 4; i++){ ctx.rotate(Math.PI / 2); ctx.beginPath(); ctx.moveTo(rr * .55, 0); ctx.lineTo(rr * 1.35, 0); ctx.stroke(); }
    ctx.restore();
  }
}
// une fois par bombe : l'impact se joue quand la zone est bien visible à l'écran
function bfxAuto(){
  if(BFX || !canvasActif() || !mapBounds || !(BOMBES_ZONES || []).length) return;
  const wrap = document.getElementById('mapWrap');
  if(!wrap || !wrap.clientWidth || modeJeu !== 'front') return;
  const vues = bfxVues(), ech = echelleCarte(), W = wrap.clientWidth, H = wrap.clientHeight;
  for(const z of BOMBES_ZONES){
    if(z.lat == null || vues.has(z.id) || new Date(z.fin).getTime() < Date.now()) continue;
    const g = bfxGeo(z), x = g.cx * ech * mapZoom + mapPanX, y = g.cy * ech * mapZoom + mapPanY, r = g.ry * ech * mapZoom;
    if(r >= 22 && x > 0 && x < W && y > 0 && y < H){ bfxJouer(z, false); return; }
  }
}
// toucher l'étiquette « 💥 +15 % · Commune » rejoue l'impact
let bfxMesure = null;
function bfxToucher(x, y){
  if(!mapBounds || !(BOMBES_ZONES || []).length) return false;
  const ech = echelleCarte(), s = ech * mapZoom;
  if(!bfxMesure) bfxMesure = document.createElement('canvas').getContext('2d');
  bfxMesure.font = '600 11px "Instrument Sans", system-ui, sans-serif';
  for(const z of BOMBES_ZONES){
    if(z.lat == null || new Date(z.fin).getTime() < Date.now()) continue;
    const g = bfxGeo(z), px = g.cx * s + mapPanX, haut = (g.cy - g.ry) * s + mapPanY - 6 - 18.7;
    const larg = bfxMesure.measureText(`💥 +${btReglage('bombe_bonus', 15)} % · ${z.cible_nom || ''}`).width + 13.2;
    if(Math.abs(x - px) <= larg / 2 + 6 && y >= haut - 6 && y <= haut + 18.7 + 6){ bfxJouer(z, false); return true; }
  }
  return false;
}

// ---------- la mallette de frappe ----------
let ML = null;""")

# déclencheurs : fin d'un geste, arrivée des zones, toucher la carte
s = rep(s, """  CV.finGeste = setTimeout(() => { CV.geste = false; demanderDessin(); }, 160);""",
           """  CV.finGeste = setTimeout(() => { CV.geste = false; demanderDessin(); if(!BFX && typeof bfxAuto === 'function') bfxAuto(); }, 160);   // patch377""")
s = rep(s, """    BOMBES_ALERTES = al && !al.error && Array.isArray(al.data) ? al.data : [];
    bombesAnnoncer();""",
"""    BOMBES_ALERTES = al && !al.error && Array.isArray(al.data) ? al.data : [];
    bombesAnnoncer();
    setTimeout(bfxAuto, 900);   // patch377""")
s = rep(s, """    if(bouge > 6) return;
    const rect = cv.getBoundingClientRect();
    const x = e.clientX - rect.left, y = e.clientY - rect.top;
    if(vueDepartements()){""",
"""    if(bouge > 6) return;
    const rect = cv.getBoundingClientRect();
    const x = e.clientX - rect.left, y = e.clientY - rect.top;
    if(SAISON2 && bfxToucher(x, y)) return;   // patch377 : rejouer l'impact
    if(vueDepartements()){""")
s = rep(s, """  cv.addEventListener('pointerdown', (e) => { depart = { x: e.clientX, y: e.clientY }; });""",
           """  cv.addEventListener('pointerdown', (e) => { depart = { x: e.clientX, y: e.clientY }; if(BFX) bfxArreter(); });   // patch377 : toucher arrête l'animation""")
F.write_text(s, encoding='utf-8')

C = pathlib.Path('style.css'); c = C.read_text(encoding='utf-8')
assert 'patch377' not in c
c += """
/* patch377 : l'impact de la bombe sur la carte */
.map-bombe-fx{ position:absolute; inset:0; width:100%; height:100%; pointer-events:none; z-index:2; }
.map-wrap:not(.en-canvas) .map-bombe-fx{ display:none; }
.gc-voir{ flex:none; margin-left:auto; border:0; border-radius:999px; padding:8px 14px; cursor:pointer;
  font:600 .85rem/1 'Instrument Sans', sans-serif; color:#2A0E10; background:#FF9C95; box-shadow:0 2px 8px rgba(0,0,0,.35); }
.gc-voir:active{ transform:translateY(1px); }
"""
C.write_text(c, encoding='utf-8')
print('patch377 ok')
