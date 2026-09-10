// --- Connexion Supabase ---
const SUPABASE_URL = 'https://yzcgroprydxhbwaufkdu.supabase.co';
const SUPABASE_ANON_KEY = 'sb_publishable_s829mEa2YUPWr9DOks2FTg_k9gpTQTA';
const sb = window.supabase.createClient(SUPABASE_URL, SUPABASE_ANON_KEY);
const CURRENT_SEASON = 'saison-1';

const TIERS = [
  {id:'legendaire', label:'Légendaire', color:'#B0862C', target:0.83},
  {id:'rare', label:'Rare', color:'#2A5FA8', target:11.40},
  {id:'peucommun', label:'Peu commun', color:'#2E7D5B', target:36.85},
  {id:'commun', label:'Commun', color:'#7C8798', target:50.92},
];
const DEPT_NAMES = {"01":"Ain","02":"Aisne","03":"Allier","04":"Alpes-de-Haute-Provence","05":"Hautes-Alpes","06":"Alpes-Maritimes","07":"Ardèche","08":"Ardennes","09":"Ariège","10":"Aube","11":"Aude","12":"Aveyron","13":"Bouches-du-Rhône","14":"Calvados","15":"Cantal","16":"Charente","17":"Charente-Maritime","18":"Cher","19":"Corrèze","21":"Côte-d'Or","22":"Côtes-d'Armor","23":"Creuse","24":"Dordogne","25":"Doubs","26":"Drôme","27":"Eure","28":"Eure-et-Loir","29":"Finistère","2A":"Corse-du-Sud","2B":"Haute-Corse","30":"Gard","31":"Haute-Garonne","32":"Gers","33":"Gironde","34":"Hérault","35":"Ille-et-Vilaine","36":"Indre","37":"Indre-et-Loire","38":"Isère","39":"Jura","40":"Landes","41":"Loir-et-Cher","42":"Loire","43":"Haute-Loire","44":"Loire-Atlantique","45":"Loiret","46":"Lot","47":"Lot-et-Garonne","48":"Lozère","49":"Maine-et-Loire","50":"Manche","51":"Marne","52":"Haute-Marne","53":"Mayenne","54":"Meurthe-et-Moselle","55":"Meuse","56":"Morbihan","57":"Moselle","58":"Nièvre","59":"Nord","60":"Oise","61":"Orne","62":"Pas-de-Calais","63":"Puy-de-Dôme","64":"Pyrénées-Atlantiques","65":"Hautes-Pyrénées","66":"Pyrénées-Orientales","67":"Bas-Rhin","68":"Haut-Rhin","69":"Rhône","70":"Haute-Saône","71":"Saône-et-Loire","72":"Sarthe","73":"Savoie","74":"Haute-Savoie","75":"Paris","76":"Seine-Maritime","77":"Seine-et-Marne","78":"Yvelines","79":"Deux-Sèvres","80":"Somme","81":"Tarn","82":"Tarn-et-Garonne","83":"Var","84":"Vaucluse","85":"Vendée","86":"Vienne","87":"Haute-Vienne","88":"Vosges","89":"Yonne","90":"Territoire de Belfort","91":"Essonne","92":"Hauts-de-Seine","93":"Seine-Saint-Denis","94":"Val-de-Marne","95":"Val-d'Oise"};
const METRO_DEPT_RE = /^(0[1-9]|[1-8][0-9]|9[0-5]|2A|2B)$/;

const OPPONENT_COLORS = ['#C8313A','#8E44AD','#E67E22','#16A085','#D4406A','#6B4226','#7F8C00','#4A4E69'];

function colorForPlayer(id){
  let hash = 0;
  for(let i = 0; i < id.length; i++){
    hash = (hash * 31 + id.charCodeAt(i)) >>> 0;
  }
  return OPPONENT_COLORS[hash % OPPONENT_COLORS.length];
}

// ---------- Direction artistique : courbes de niveau ----------
const REDUCED_MOTION = window.matchMedia('(prefers-reduced-motion: reduce)').matches;

// Meme texte = meme nombre, donc meme commune = meme dessin a chaque fois
function hashTexte(str){
  let h = 2166136261;
  for(const ch of str){ h ^= ch.charCodeAt(0); h = Math.imul(h, 16777619); }
  return h >>> 0;
}
function aleatoireStable(a){
  return function(){
    a |= 0; a = a + 0x6D2B79F5 | 0;
    let t = Math.imul(a ^ a >>> 15, 1 | a);
    t = t + Math.imul(t ^ t >>> 7, 61 | t) ^ t;
    return ((t ^ t >>> 14) >>> 0) / 4294967296;
  };
}
function courbesDeNiveau(seed, w, h, anneaux){
  const rnd = aleatoireStable(seed);
  const cx = w * (0.3 + rnd() * 0.4), cy = h * (0.3 + rnd() * 0.4);
  const k1 = 2 + Math.floor(rnd() * 3), k2 = 3 + Math.floor(rnd() * 4);
  const p1 = rnd() * 6.28, p2 = rnd() * 6.28;
  const a1 = 0.08 + rnd() * 0.12, a2 = 0.04 + rnd() * 0.08;
  const pas = Math.max(w, h) / anneaux * 0.95;
  let d = '';
  for(let i = 1; i <= anneaux; i++){
    const r = i * pas;
    const pts = [];
    for(let k = 0; k < 90; k++){
      const t = k / 90 * Math.PI * 2;
      const rr = r * (1 + a1 * Math.sin(k1 * t + p1 + i * 0.35) + a2 * Math.sin(k2 * t + p2 - i * 0.2));
      pts.push((cx + rr * Math.cos(t)).toFixed(1) + ',' + (cy + rr * Math.sin(t) * 0.82).toFixed(1));
    }
    d += 'M' + pts.join('L') + 'Z';
  }
  return { d, cx, cy };
}

const TEINTES_CARTE = {
  commun:     ['#8D9AAE', '#5F6C80'],
  peucommun:  ['#35B97E', '#16734C'],
  rare:       ['#4E92FF', '#1D4FB8'],
  legendaire: ['#F7C548', '#B7791F'],
};

function carteArtSvg(code, tierId){
  const [clair, fonce] = TEINTES_CARTE[tierId];
  const id = 'cg' + code;
  const { d, cx, cy } = courbesDeNiveau(hashTexte(String(code)), 200, 120, 9);
  return `
    <svg viewBox="0 0 200 120" preserveAspectRatio="xMidYMid slice" aria-hidden="true">
      <defs>
        <radialGradient id="${id}" cx="${(cx / 200 * 100).toFixed(0)}%" cy="${(cy / 120 * 100).toFixed(0)}%" r="85%">
          <stop offset="0%" stop-color="${clair}"/>
          <stop offset="100%" stop-color="${fonce}"/>
        </radialGradient>
      </defs>
      <rect width="200" height="120" fill="url(#${id})"/>
      <path d="${d}" fill="none" stroke="rgba(255,255,255,0.38)" stroke-width="1"/>
      <circle cx="${cx.toFixed(1)}" cy="${cy.toFixed(1)}" r="5" fill="#fff" stroke="${fonce}" stroke-width="2.5"/>
    </svg>`;
}

function dessinerFondTopo(){
  const svg = document.getElementById('fondTopo');
  if(!svg) return;
  const w = 1600, h = 1000;
  svg.setAttribute('viewBox', `0 0 ${w} ${h}`);
  svg.setAttribute('preserveAspectRatio', 'xMidYMid slice');
  const a = courbesDeNiveau(hashTexte('fond-a'), w * 0.9, h * 1.1, 16);
  const b = courbesDeNiveau(hashTexte('fond-b'), w * 0.8, h * 0.9, 12);
  svg.innerHTML = `
    <path d="${a.d}" fill="none" stroke="rgba(169,188,212,0.07)" stroke-width="1.2"/>
    <path d="${b.d}" transform="translate(${w * 0.55} ${h * 0.35})" fill="none" stroke="rgba(169,188,212,0.06)" stroke-width="1.2"/>`;
}
dessinerFondTopo();

let FRANCE_OUTLINE = null;
let mapBounds = null;
let collectionMap = new Map();
let othersMap = new Map();
let session = {commun:0, peucommun:0, rare:0, legendaire:0, total:0};

// ---------- Authentification ----------
function showAuth(msg){
  document.getElementById('authScreen').style.display = 'flex';
  document.getElementById('gameScreen').style.display = 'none';
  if(msg) document.getElementById('authMsg').textContent = msg;
}

async function showGame(session_){
  document.getElementById('authScreen').style.display = 'none';
  document.getElementById('gameScreen').style.display = 'flex';
  document.getElementById('whoami').textContent = session_.user.email;
  await loadOutline();
  await loadMyCollection();
  await loadOthersPossessions();
  await loadPackStatus();
}

async function initAuth(){
  const { data: { session: s } } = await sb.auth.getSession();
  if(s) showGame(s); else showAuth();
  sb.auth.onAuthStateChange((event, s2) => {
    if(s2) showGame(s2); else showAuth();
  });
}

document.getElementById('loginBtn').addEventListener('click', async () => {
  const email = document.getElementById('authEmail').value.trim();
  const password = document.getElementById('authPassword').value;
  const { error } = await sb.auth.signInWithPassword({ email, password });
  if(error) showAuth(error.message);
});

document.getElementById('signupBtn').addEventListener('click', async () => {
  const email = document.getElementById('authEmail').value.trim();
  const password = document.getElementById('authPassword').value;
  const pseudo = document.getElementById('authPseudo').value.trim();
  const { error } = await sb.auth.signUp({ email, password, options: { data: { pseudo } } });
  if(error) showAuth(error.message);
  else showAuth('Compte créé — connecte-toi maintenant.');
});

document.getElementById('logoutBtn').addEventListener('click', async () => {
  await sb.auth.signOut();
});
document.getElementById('logoutBtnMobile').addEventListener('click', async () => {
  await sb.auth.signOut();
});

// ---------- Carte (contour reel + points) ----------
async function loadOutline(){
  if(FRANCE_OUTLINE) return;
  const res = await fetch('data/france-outline.json');
  FRANCE_OUTLINE = await res.json();
  computeMapBounds();
  renderFranceOutline();
}

function computeMapBounds(){
  let latMin=90, latMax=-90, lonMin=180, lonMax=-180;
  for(const ring of FRANCE_OUTLINE){
    for(const [lon, lat] of ring){
      if(lat<latMin) latMin=lat;
      if(lat>latMax) latMax=lat;
      if(lon<lonMin) lonMin=lon;
      if(lon>lonMax) lonMax=lon;
    }
  }
  // marge respirante tout autour (meme proportion sur les 4 cotes,
  // continent et Corse gardent leur position relative exacte)
  const pad = 0.04;
  const latPad = (latMax - latMin) * pad;
  const lonPad = (lonMax - lonMin) * pad;
  latMin -= latPad; latMax += latPad;
  lonMin -= lonPad; lonMax += lonPad;

  mapBounds = {latMin, latMax, lonMin, lonMax};
  const meanLat = (latMin + latMax) / 2;
  const lonSpanCorrected = (lonMax - lonMin) * Math.cos(meanLat * Math.PI / 180);
  const latSpan = latMax - latMin;
  const ratio = lonSpanCorrected / latSpan;
  window.__mapAspectRatio = ratio;
  sizeMapWrap(ratio);
  window.addEventListener('resize', () => sizeMapWrap(ratio));
}

function sizeMapWrap(ratio){
  const wrap = document.getElementById('mapWrap');
  if(!wrap || !ratio) return;
  const parent = wrap.parentElement;
  const availWidth = Math.min(parent.clientWidth, 1200);
  const availHeightPx = window.innerHeight * 0.78;
  const widthFromHeight = availHeightPx * ratio;
  const finalWidth = Math.min(availWidth, widthFromHeight);
  wrap.style.width = finalWidth + 'px';
  wrap.style.height = (finalWidth / ratio) + 'px';
  applyMapTransform();
}

function project(lat, lon){
  const {latMin, latMax, lonMin, lonMax} = mapBounds;
  const x = (lon - lonMin) / (lonMax - lonMin);
  const y = (latMax - lat) / (latMax - latMin);
  return {x, y};
}

function renderFranceOutline(){
  const group = document.getElementById('franceOutlineGroup');
  if(!group || !mapBounds) return;
  group.innerHTML = '';
  for(const ring of FRANCE_OUTLINE){
    const pts = ring.map(([lon, lat]) => {
      const p = project(lat, lon);
      return (p.x*1000).toFixed(1) + ',' + (p.y*1000).toFixed(1);
    }).join(' ');
    const poly = document.createElementNS('http://www.w3.org/2000/svg', 'polygon');
    poly.setAttribute('points', pts);
    poly.setAttribute('fill', 'url(#franceGrad)');
    poly.setAttribute('stroke', '#123564');
    poly.setAttribute('stroke-width', '3');
    group.appendChild(poly);
  }
  setupMapInteraction();
}

let mapZoom = 1, mapPanX = 0, mapPanY = 0;
let mapDragging = false, mapDragStart = {x:0, y:0};
let mapInteractionReady = false;
const MAP_ZOOM_MIN = 1;
const MAP_ZOOM_MAX = 6;

// Empeche la carte de sortir du cadre (plus de France "perdue" hors ecran)
function clampMapPan(){
  const wrap = document.getElementById('mapWrap');
  if(!wrap) return;
  const w = wrap.clientWidth, h = wrap.clientHeight;
  mapPanX = Math.min(0, Math.max(w - w * mapZoom, mapPanX));
  mapPanY = Math.min(0, Math.max(h - h * mapZoom, mapPanY));
}

function applyMapTransform(){
  clampMapPan();
  const el = document.getElementById('mapTransform');
  if(el) el.style.transform = `translate(${mapPanX}px, ${mapPanY}px) scale(${mapZoom})`;
}

// Zoome en gardant fixe le point (px, py) du cadre : le curseur ou le centre des deux doigts
function zoomMapAt(newZoom, px, py){
  newZoom = Math.min(MAP_ZOOM_MAX, Math.max(MAP_ZOOM_MIN, newZoom));
  const ratio = newZoom / mapZoom;
  mapPanX = px - (px - mapPanX) * ratio;
  mapPanY = py - (py - mapPanY) * ratio;
  mapZoom = newZoom;
  applyMapTransform();
}

function touchDist(t){
  return Math.hypot(t[0].clientX - t[1].clientX, t[0].clientY - t[1].clientY);
}
function touchMid(t, rect){
  return { x: (t[0].clientX + t[1].clientX) / 2 - rect.left, y: (t[0].clientY + t[1].clientY) / 2 - rect.top };
}

function setupMapInteraction(){
  if(mapInteractionReady) return;
  mapInteractionReady = true;
  const wrap = document.getElementById('mapWrap');
  if(!wrap) return;

  // --- Molette souris + trackpad (defilement a deux doigts ou pincement) ---
  // Zoom proportionnel a l'amplitude du geste : fluide au trackpad, par crans a la souris
  wrap.addEventListener('wheel', (e) => {
    e.preventDefault();
    const rect = wrap.getBoundingClientRect();
    let dy = e.deltaMode === 1 ? e.deltaY * 16 : e.deltaY;
    dy = Math.max(-150, Math.min(150, dy));
    // pincement trackpad (Chrome le signale avec ctrlKey) : plus sensible
    const sensibilite = e.ctrlKey ? 0.012 : 0.002;
    zoomMapAt(mapZoom * Math.exp(-dy * sensibilite), e.clientX - rect.left, e.clientY - rect.top);
  }, { passive: false });

  // --- Pincement trackpad sur Safari Mac (evenements "gesture" propres a Safari) ---
  let gestureStartZoom = 1;
  let touchPinch = null;
  wrap.addEventListener('gesturestart', (e) => {
    e.preventDefault();
    gestureStartZoom = mapZoom;
  });
  wrap.addEventListener('gesturechange', (e) => {
    e.preventDefault();
    if(touchPinch) return; // sur iPhone le pincement est deja gere par les evenements tactiles
    const rect = wrap.getBoundingClientRect();
    zoomMapAt(gestureStartZoom * e.scale, e.clientX - rect.left, e.clientY - rect.top);
  });
  wrap.addEventListener('gestureend', (e) => e.preventDefault());

  // --- Souris : cliquer-glisser ---
  wrap.addEventListener('mousedown', (e) => {
    mapDragging = true;
    mapDragStart = { x: e.clientX - mapPanX, y: e.clientY - mapPanY };
  });
  window.addEventListener('mousemove', (e) => {
    if(!mapDragging) return;
    mapPanX = e.clientX - mapDragStart.x;
    mapPanY = e.clientY - mapDragStart.y;
    applyMapTransform();
    // recale le point de depart si on a bute sur un bord, pour repartir sans temps mort
    mapDragStart = { x: e.clientX - mapPanX, y: e.clientY - mapPanY };
  });
  window.addEventListener('mouseup', () => { mapDragging = false; });

  // --- Tactile : un doigt = deplacer, deux doigts = pincer pour zoomer ---
  wrap.addEventListener('touchstart', (e) => {
    const rect = wrap.getBoundingClientRect();
    if(e.touches.length === 2){
      mapDragging = false;
      touchPinch = {
        dist: touchDist(e.touches),
        zoom: mapZoom,
        mid: touchMid(e.touches, rect),
        panX: mapPanX,
        panY: mapPanY
      };
    } else if(e.touches.length === 1){
      touchPinch = null;
      mapDragging = true;
      mapDragStart = { x: e.touches[0].clientX - mapPanX, y: e.touches[0].clientY - mapPanY };
    }
  }, { passive: false });

  wrap.addEventListener('touchmove', (e) => {
    e.preventDefault();
    if(touchPinch && e.touches.length === 2){
      const rect = wrap.getBoundingClientRect();
      const newZoom = Math.min(MAP_ZOOM_MAX, Math.max(MAP_ZOOM_MIN,
        touchPinch.zoom * touchDist(e.touches) / touchPinch.dist));
      // point de la carte qui etait sous les doigts au debut du pincement
      const mx = (touchPinch.mid.x - touchPinch.panX) / touchPinch.zoom;
      const my = (touchPinch.mid.y - touchPinch.panY) / touchPinch.zoom;
      const mid = touchMid(e.touches, rect);
      mapZoom = newZoom;
      mapPanX = mid.x - newZoom * mx;
      mapPanY = mid.y - newZoom * my;
      applyMapTransform();
    } else if(mapDragging && e.touches.length === 1){
      mapPanX = e.touches[0].clientX - mapDragStart.x;
      mapPanY = e.touches[0].clientY - mapDragStart.y;
      applyMapTransform();
      mapDragStart = { x: e.touches[0].clientX - mapPanX, y: e.touches[0].clientY - mapPanY };
    }
  }, { passive: false });

  wrap.addEventListener('touchend', (e) => {
    if(e.touches.length === 1){
      // on leve un doigt pendant un pincement : on continue a deplacer sans saut
      touchPinch = null;
      mapDragging = true;
      mapDragStart = { x: e.touches[0].clientX - mapPanX, y: e.touches[0].clientY - mapPanY };
    } else if(e.touches.length === 0){
      touchPinch = null;
      mapDragging = false;
    }
  });
}

let showOthers = true;

const DOT_RADIUS = {commun: 2.25, peucommun: 4.75, rare: 7.75, legendaire: 11.75};

function renderMapOverlay(){
  const overlay = document.getElementById('mapOverlay');
  const mineGroup = document.getElementById('mineDotsGroup');
  const mineBorderGroup = document.getElementById('mineDotsBorderGroup');
  if(!overlay || !mineGroup || !mineBorderGroup || !mapBounds) return;
  overlay.innerHTML = '';
  mineGroup.innerHTML = '';
  mineBorderGroup.innerHTML = '';

  // territoire des autres joueurs, en gris neutre (points HTML simples, pas de fusion)
  if(showOthers){
    for(const entry of othersMap.values()){
      if(!METRO_DEPT_RE.test(entry.dept)) continue;
      const p = project(entry.lat, entry.lon);
      const dot = document.createElement('div');
      dot.className = 'map-dot other ' + entry.tier.id;
      dot.style.left = (p.x * 100) + '%';
      dot.style.top = (p.y * 100) + '%';
      dot.style.background = colorForPlayer(entry.joueurId);
      dot.title = entry.nom + ' (' + entry.dept + ') — possédée par ' + entry.pseudo;
      overlay.appendChild(dot);
    }
  }

  // mon propre territoire, en cercles SVG (pour l'effet de fusion organique)
  for(const entry of collectionMap.values()){
    if(!METRO_DEPT_RE.test(entry.dept)) continue;
    const p = project(entry.lat, entry.lon);
    const cx = (p.x * 1000).toFixed(1);
    const cy = (p.y * 1000).toFixed(1);
    const r = DOT_RADIUS[entry.tier.id];

    // couche de contour : legerement plus grande, couleur unie sombre
    const borderCircle = document.createElementNS('http://www.w3.org/2000/svg', 'circle');
    borderCircle.setAttribute('cx', cx);
    borderCircle.setAttribute('cy', cy);
    borderCircle.setAttribute('r', r + 4);
    borderCircle.setAttribute('fill', '#0B2A4A');
    mineBorderGroup.appendChild(borderCircle);

    // couche coloree, par-dessus
    const circle = document.createElementNS('http://www.w3.org/2000/svg', 'circle');
    circle.setAttribute('cx', cx);
    circle.setAttribute('cy', cy);
    circle.setAttribute('r', r);
    circle.setAttribute('fill', entry.tier.color);
    const title = document.createElementNS('http://www.w3.org/2000/svg', 'title');
    title.textContent = entry.nom + ' (' + entry.dept + ') — ' + entry.tier.label;
    circle.appendChild(title);
    mineGroup.appendChild(circle);
  }
}

async function loadOthersPossessions(){
  const { data: userData } = await sb.auth.getUser();
  const uid = userData.user.id;
  const { data, error } = await sb
    .from('possessions')
    .select('commune_code, joueur_id, communes(code,nom,departement,latitude,longitude,tier), joueurs(pseudo)')
    .neq('joueur_id', uid);
  if(error){ console.error(error); return; }

  othersMap = new Map();
  for(const row of data){
    const c = row.communes;
    const tier = TIERS.find(t => t.id === c.tier);
    othersMap.set(c.code, {
      nom: c.nom, dept: c.departement, lat: c.latitude, lon: c.longitude, tier,
      pseudo: row.joueurs ? row.joueurs.pseudo : 'un autre joueur',
      joueurId: row.joueur_id
    });
  }
  renderMapOverlay();
}

// ---------- Collection (depuis la base de donnees) ----------
async function loadMyCollection(){
  const { data: userData } = await sb.auth.getUser();
  const uid = userData.user.id;
  const { data, error } = await sb
    .from('possessions')
    .select('commune_code, communes(code,nom,departement,population,latitude,longitude,tier,rang,palier_total)')
    .eq('joueur_id', uid);
  if(error){ console.error(error); return; }

  collectionMap = new Map();
  session = {commun:0, peucommun:0, rare:0, legendaire:0, total:0};
  for(const row of data){
    const c = row.communes;
    const tier = TIERS.find(t => t.id === c.tier);
    collectionMap.set(c.code, {
      code: c.code, nom: c.nom, dept: c.departement, pop: c.population,
      lat: c.latitude, lon: c.longitude, tier, rank: c.rang, tierSize: c.palier_total
    });
    session[c.tier]++;
    session.total++;
  }
  renderStats();
  renderCollection();
  renderMapOverlay();
  if(document.getElementById('sellableGrid')) renderSellableGrid();
}

function renderStats(){
  const rows = document.getElementById('statRows');
  rows.innerHTML = '';
  for(const t of TIERS){
    const n = session[t.id];
    const pct = session.total ? (n/session.total*100) : 0;
    const row = document.createElement('div');
    row.className = 'stat-row';
    row.innerHTML = `
      <div class="dot" style="background:${t.color}"></div>
      <div class="label">${t.label}</div>
      <div class="bar-track"><div class="bar-fill" style="width:${pct}%;background:${t.color}"></div></div>
      <div class="nums">${n} carte${n>1?'s':''} (${pct.toFixed(1)}%)</div>
    `;
    rows.appendChild(row);
  }
}

function renderCollection(){
  const countEl = document.getElementById('collectionCount');
  const gridEl = document.getElementById('collectionGrid');
  const entries = Array.from(collectionMap.values());
  countEl.textContent = entries.length;
  if(entries.length === 0){
    gridEl.innerHTML = '<p class="collection-empty">Aucune carte pour le moment — ouvre un paquet.</p>';
    return;
  }
  const sorted = entries.sort((a,b) => {
    const ra = TIERS.indexOf(a.tier), rb = TIERS.indexOf(b.tier);
    if(ra !== rb) return ra - rb;
    return b.pop - a.pop;
  });
  gridEl.innerHTML = sorted.map(entry => `
    <div class="mini-card ${entry.tier.id}" title="${entry.nom} (${entry.dept}) — ${entry.tier.label}">
      <div class="stripe"><span class="b"></span><span class="w"></span><span class="r"></span></div>
      <div class="body">
        <div class="name">${entry.nom}</div>
        <div class="rarity" style="background:${entry.tier.color}">${entry.tier.label}</div>
      </div>
    </div>
  `).join('');
}

// ---------- Cartes et paquet ----------
function makeCardEl(draw, onFlip){
  const wrap = document.createElement('div');
  wrap.className = 'card ' + draw.tier.id;
  wrap.innerHTML = `
    <div class="card-inner">
      <div class="face face-back"><div class="emblem">RF</div></div>
      <div class="face face-front">
        <div class="carte-cadre">
          <div class="carte-int">
            <div class="carte-haut">
              <span class="carte-rarete">${draw.tier.label}</span>
              <span class="carte-num">${draw.rank.toLocaleString('fr-FR')} / ${draw.tierSize.toLocaleString('fr-FR')}</span>
            </div>
            <div class="carte-art">${carteArtSvg(draw.code, draw.tier.id)}<span class="carte-dept">${draw.dept}</span></div>
            <div class="carte-infos">
              <p class="carte-nom">${draw.nom}</p>
              <p class="carte-departement">${DEPT_NAMES[draw.dept] || draw.dept}</p>
              <div class="carte-stats">
                <div><span>Habitants</span><b>${draw.pop.toLocaleString('fr-FR')}</b></div>
                <div><span>Rang</span><b>${draw.rank.toLocaleString('fr-FR')}</b></div>
              </div>
            </div>
            <div class="carte-lisere"><span></span><span></span><span></span></div>
          </div>
        </div>
      </div>
    </div>
  `;
  wrap.addEventListener('click', () => {
    if(!wrap.classList.contains('flipped')){
      wrap.classList.add('flipped');
      onFlip();
    }
  });

  // Inclinaison 3D + reflet des legendaires, a la souris et une fois la carte retournee
  if(!REDUCED_MOTION){
    const cadre = wrap.querySelector('.carte-cadre');
    wrap.addEventListener('pointermove', (e) => {
      if(e.pointerType !== 'mouse' || !wrap.classList.contains('flipped')) return;
      const r = wrap.getBoundingClientRect();
      const x = (e.clientX - r.left) / r.width;
      const y = (e.clientY - r.top) / r.height;
      cadre.style.transform = `rotateY(${(x - 0.5) * 16}deg) rotateX(${(0.5 - y) * 16}deg)`;
      cadre.style.setProperty('--hx', (x * 100) + '%');
      cadre.style.setProperty('--hy', (y * 100) + '%');
    });
    wrap.addEventListener('pointerleave', () => { cadre.style.transform = ''; });
  }
  return wrap;
}

let pendingFlips = 0;

function revealCards(draws){
  const zone = document.getElementById('packZone');
  zone.innerHTML = '';
  pendingFlips = draws.length;
  draws.forEach(draw => {
    zone.appendChild(makeCardEl(draw, () => {
      collectionMap.set(draw.code, draw);
      session[draw.tier.id]++;
      session.total++;
      renderStats();
      renderCollection();
      renderMapOverlay();
      pendingFlips--;
      if(pendingFlips <= 0){
        renderPackStatus();
      }
    }));
  });
}

function makePackEl(){
  const pack = document.createElement('div');
  pack.className = 'foilpack';
  pack.style.setProperty('--foil-color', '#0B2A55');
  pack.innerHTML = `<div class="body"><div class="mark">Paquet</div></div><div class="strip"></div>`;
  return pack;
}

// ---------- Jetons de paquets ----------
let packStatusCache = null;
let packStatusFetchedAt = 0;
let packStatusInterval = null;

async function loadPackStatus(){
  const { data, error } = await sb.rpc('statut_paquets');
  if(error){ console.error(error); return; }
  packStatusCache = data[0];
  packStatusFetchedAt = Date.now();
  renderPackStatus();
  if(!packStatusInterval){
    packStatusInterval = setInterval(renderPackStatus, 5000);
  }
}

function liveJetons(){
  if(!packStatusCache) return 0;
  const elapsedMin = (Date.now() - packStatusFetchedAt) / 60000;
  return Math.min(3, packStatusCache.jetons_actuels + elapsedMin / 20);
}

function renderPackStatus(){
  if(!packStatusCache) return;
  const live = liveJetons();
  const dispo = Math.floor(live);
  const achetesJour = (packStatusCache.paquets_achetes_date === new Date().toISOString().slice(0,10))
    ? packStatusCache.paquets_achetes_jour : 0;

  const puces = [`<span class="puce"><b>${dispo} sur 3</b> paquets gratuits</span>`];
  if(dispo < 3){
    const minutes = Math.ceil((1 - (live % 1)) * 20);
    puces.push(`<span class="puce">Prochain dans <b>${minutes} min</b></span>`);
  }
  puces.push(`<span class="puce">Achetés aujourd'hui <b>${achetesJour} sur 5</b></span>`);
  puces.push(`<span class="puce solde">Solde <b>${Number(packStatusCache.solde).toLocaleString('fr-FR')}</b></span>`);
  document.getElementById('packStatus').innerHTML = puces.join('');

  document.getElementById('openFreeBtn').disabled = dispo < 1;
  document.getElementById('openBuyBtn').disabled = achetesJour >= 5 || packStatusCache.solde < 200;
}

async function openPack(type){
  document.getElementById('openFreeBtn').disabled = true;
  document.getElementById('openBuyBtn').disabled = true;

  const { error: startError } = await sb.rpc('demarrer_paquet', { p_type: type });
  if(startError){
    alert(startError.message);
    await loadPackStatus();
    return;
  }
  await loadPackStatus();
  // on force le re-verrouillage : le paquet en cours n'est pas encore ouvert,
  // pas question de pouvoir en relancer un avant d'avoir retourne les cartes
  document.getElementById('openFreeBtn').disabled = true;
  document.getElementById('openBuyBtn').disabled = true;

  const zone = document.getElementById('packZone');
  zone.innerHTML = '';
  const pack = makePackEl();
  zone.appendChild(pack);

  pack.addEventListener('click', () => {
    pack.classList.add('tearing');
    setTimeout(async () => {
      const draws = [];
      for(let i = 0; i < 5; i++){
        const { data, error } = await sb.rpc('draw_commune', { p_saison: CURRENT_SEASON });
        if(error){
          alert('Tirage impossible : ' + error.message);
          break;
        }
        const row = data[0];
        const tier = TIERS.find(t => t.id === row.tier);
        draws.push({
          code: row.code, nom: row.nom, dept: row.departement, pop: row.population,
          lat: row.latitude, lon: row.longitude, tier, rank: row.rang, tierSize: row.palier_total
        });
      }
      if(draws.length === 0){
        renderPackStatus();
        return;
      }
      revealCards(draws);
    }, 650);
  }, { once: true });
}

document.getElementById('openFreeBtn').addEventListener('click', () => openPack('gratuit'));
document.getElementById('openBuyBtn').addEventListener('click', () => openPack('achete'));

document.getElementById('toggleOthersBtn').addEventListener('click', () => {
  showOthers = !showOthers;
  document.getElementById('toggleOthersBtn').textContent = showOthers
    ? 'Cacher le territoire des autres'
    : 'Afficher le territoire des autres';
  renderMapOverlay();
});

// ---------- Bourse ----------
const PRIX_RACHAT = {commun: 5, peucommun: 20, rare: 100, legendaire: 1000};
let myListings = new Map();

async function loadBourse(){
  const { data: userData } = await sb.auth.getUser();
  const uid = userData.user.id;

  const { data: joueurRow } = await sb.from('joueurs').select('solde').eq('id', uid).single();
  document.getElementById('soldeValue').textContent = joueurRow ? joueurRow.solde : '—';

  const { data: mine } = await sb.from('annonces').select('commune_code, prix').eq('joueur_id', uid);
  myListings = new Map((mine || []).map(a => [a.commune_code, a.prix]));

  renderSellableGrid();

  const { data: market } = await sb
    .from('annonces')
    .select('commune_code, prix, joueur_id, communes(nom,departement,tier), joueurs(pseudo)');
  renderMarketGrid(market || [], uid);
}

let sellFilterTier = 'tous';

function renderSellableGrid(){
  const grid = document.getElementById('sellableGrid');
  const searchEl = document.getElementById('sellSearch');
  const searchText = searchEl ? searchEl.value.trim().toLowerCase() : '';

  let entries = Array.from(collectionMap.values()).sort((a,b) => {
    const ra = TIERS.indexOf(a.tier), rb = TIERS.indexOf(b.tier);
    if(ra !== rb) return ra - rb;
    return b.pop - a.pop;
  });

  if(sellFilterTier !== 'tous'){
    entries = entries.filter(e => e.tier.id === sellFilterTier);
  }
  if(searchText){
    entries = entries.filter(e => e.nom.toLowerCase().includes(searchText));
  }

  if(collectionMap.size === 0){
    grid.innerHTML = '<p class="collection-empty">Tu ne possèdes aucune commune pour l\'instant.</p>';
    return;
  }
  if(entries.length === 0){
    grid.innerHTML = '<p class="collection-empty">Aucune commune ne correspond à la recherche.</p>';
    return;
  }
  grid.innerHTML = entries.map(entry => {
    const listedPrice = myListings.get(entry.code);
    const rachat = PRIX_RACHAT[entry.tier.id];
    const actions = listedPrice
      ? `<span class="bourse-price">En vente : ${listedPrice} pts</span>
         <button class="bourse-btn" data-action="retirer" data-code="${entry.code}">Retirer</button>`
      : `<button class="bourse-btn" data-action="vendre-jeu" data-code="${entry.code}">Vendre au jeu (${rachat} pts)</button>
         <button class="bourse-btn" data-action="mettre-vente" data-code="${entry.code}">Mettre en vente</button>`;
    return `
      <div class="bourse-row">
        <span class="bourse-dot" style="background:${entry.tier.color}"></span>
        <span class="bourse-name">${entry.nom} <span class="bourse-dept">(${entry.dept})</span></span>
        ${actions}
      </div>`;
  }).join('');
}

function renderMarketGrid(market, myUid){
  const grid = document.getElementById('marketGrid');
  if(market.length === 0){
    grid.innerHTML = '<p class="collection-empty">Aucune annonce pour le moment.</p>';
    return;
  }
  const tiersById = Object.fromEntries(TIERS.map(t => [t.id, t]));
  grid.innerHTML = market.map(a => {
    const c = a.communes;
    const tier = tiersById[c.tier];
    const isMine = a.joueur_id === myUid;
    const pseudo = isMine ? 'toi' : (a.joueurs ? a.joueurs.pseudo : 'un joueur');
    const action = isMine
      ? `<button class="bourse-btn" data-action="retirer" data-code="${a.commune_code}">Retirer</button>`
      : `<button class="bourse-btn" data-action="acheter" data-code="${a.commune_code}">Acheter</button>`;
    return `
      <div class="bourse-row">
        <span class="bourse-dot" style="background:${tier.color}"></span>
        <span class="bourse-name">${c.nom} <span class="bourse-dept">(${c.departement}) — vendu par ${pseudo}</span></span>
        <span class="bourse-price">${a.prix} pts</span>
        ${action}
      </div>`;
  }).join('');
}

document.addEventListener('click', async (e) => {
  const btn = e.target.closest('.bourse-btn');
  if(!btn) return;
  const action = btn.dataset.action;
  const code = btn.dataset.code;
  btn.disabled = true;
  try{
    if(action === 'vendre-jeu'){
      const { error } = await sb.rpc('vendre_au_jeu', { p_commune_code: code });
      if(error) throw error;
      collectionMap.delete(code);
      renderCollection(); renderStats(); renderMapOverlay();
    } else if(action === 'mettre-vente'){
      const prixStr = prompt('À quel prix veux-tu la vendre (en points) ?');
      const prix = parseInt(prixStr, 10);
      if(!prix || prix <= 0) { btn.disabled = false; return; }
      const { error } = await sb.rpc('mettre_en_vente', { p_commune_code: code, p_prix: prix });
      if(error) throw error;
    } else if(action === 'retirer'){
      const { error } = await sb.rpc('retirer_de_la_vente', { p_commune_code: code });
      if(error) throw error;
    } else if(action === 'acheter'){
      const { error } = await sb.rpc('acheter', { p_commune_code: code, p_saison: CURRENT_SEASON });
      if(error) throw error;
      await loadMyCollection();
      await loadOthersPossessions();
    } else if(action === 'attaquer'){
      // bloque le rafraichissement auto de la grille pendant l'attaque en cours
      combatActionEnCours = true;
      try{
        const { data, error } = await sb.rpc('attaquer', { p_commune_code: code });
        if(error) throw error;
        const result = data[0];
        if(result.conquise){
          alert('Commune conquise ! Tu as gagné le siège et le bonus.');
          await loadMyCollection();
          await loadOthersPossessions();
        } else if(result.gagne){
          alert(`Victoire ! Série : ${result.victoires_consecutives}/3`);
        } else {
          alert('Défaite. La série repart à zéro.');
        }
        await loadCombat();
      } finally {
        combatActionEnCours = false;
      }
      return;
    }
    await loadBourse();
  } catch(err){
    alert('Action impossible : ' + err.message);
    btn.disabled = false;
  }
});

document.getElementById('sellSearch').addEventListener('input', renderSellableGrid);

document.getElementById('sellFilters').addEventListener('click', (e) => {
  const pill = e.target.closest('.filter-pill');
  if(!pill) return;
  document.querySelectorAll('#sellFilters .filter-pill').forEach(p => p.classList.remove('active'));
  pill.classList.add('active');
  sellFilterTier = pill.dataset.tier;
  renderSellableGrid();
});

// ---------- Combat ----------
// Ces deux valeurs doivent rester alignees avec le SQL (fonctions attaquer et delai_attaque)
const IMMUNITE_MS = 3 * 3600 * 1000;
const DELAI_ATTAQUE_MS = {rare: 10 * 60 * 1000, legendaire: 3 * 3600 * 1000};

function coutAttaque(tierId){
  return Math.max(1, Math.round(PRIX_RACHAT[tierId] * 0.1));
}

// Affiche une duree lisible : "7 min", "2h", "2h45"
function formatDuree(ms){
  const totalMin = Math.max(1, Math.ceil(ms / 60000));
  if(totalMin < 60) return `${totalMin} min`;
  const h = Math.floor(totalMin / 60);
  const m = totalMin % 60;
  return m ? `${h}h${String(m).padStart(2, '0')}` : `${h}h`;
}

let combatCibles = [];
let combatSieges = new Map();
let combatFilterTier = 'tous';
let combatActionEnCours = false;

async function loadCombat(){
  const { data: userData } = await sb.auth.getUser();
  const uid = userData.user.id;

  const { data: joueurRow } = await sb.from('joueurs').select('solde').eq('id', uid).single();
  document.getElementById('soldeValueCombat').textContent = joueurRow ? joueurRow.solde : '—';

  const { data: cibles, error } = await sb
    .from('possessions')
    .select('commune_code, joueur_id, acquired_at, communes!inner(nom,departement,tier), joueurs(pseudo)')
    .neq('joueur_id', uid)
    .in('communes.tier', ['rare','legendaire']);
  if(error){ console.error(error); return; }

  const { data: mesSieges } = await sb
    .from('sieges')
    .select('commune_code, victoires_consecutives, dernier_round')
    .eq('attacker_id', uid);

  combatCibles = cibles || [];
  combatSieges = new Map((mesSieges || []).map(s => [s.commune_code, s]));
  renderCombatGrid();
}

function renderCombatGrid(){
  const grid = document.getElementById('combatGrid');
  const searchEl = document.getElementById('combatSearch');
  const searchText = searchEl ? searchEl.value.trim().toLowerCase() : '';

  let cibles = combatCibles;
  if(combatFilterTier !== 'tous'){
    cibles = cibles.filter(c => c.communes.tier === combatFilterTier);
  }
  if(searchText){
    cibles = cibles.filter(c => c.communes.nom.toLowerCase().includes(searchText));
  }

  if(combatCibles.length === 0){
    grid.innerHTML = '<p class="collection-empty">Aucune cible disponible pour le moment.</p>';
    return;
  }
  if(cibles.length === 0){
    grid.innerHTML = '<p class="collection-empty">Aucune cible ne correspond à la recherche.</p>';
    return;
  }

  const tiersById = Object.fromEntries(TIERS.map(t => [t.id, t]));
  const now = Date.now();

  grid.innerHTML = cibles.map(c => {
    const commune = c.communes;
    const tier = tiersById[commune.tier];
    const pseudo = c.joueurs ? c.joueurs.pseudo : 'un joueur';
    const acquiredAt = new Date(c.acquired_at).getTime();
    const immuniteFin = acquiredAt + IMMUNITE_MS;
    const encoreImmune = now < immuniteFin;

    const siege = combatSieges.get(c.commune_code);
    const victoires = siege ? siege.victoires_consecutives : 0;
    const dernierRound = siege && siege.dernier_round ? new Date(siege.dernier_round).getTime() : 0;
    const prochainRound = dernierRound ? dernierRound + DELAI_ATTAQUE_MS[commune.tier] : 0;
    const enAttente = now < prochainRound;

    const cout = coutAttaque(commune.tier);
    let statusTxt, statusClass, disabled;
    if(encoreImmune){
      statusTxt = `Protégée encore ${formatDuree(immuniteFin - now)}`;
      statusClass = '';
      disabled = true;
    } else if(enAttente){
      statusTxt = `Prochain round dans ${formatDuree(prochainRound - now)}`;
      statusClass = '';
      disabled = true;
    } else {
      statusTxt = 'Prête à attaquer';
      statusClass = 'ready';
      disabled = false;
    }

    const dots = [0,1,2].map(i => `<div class="cc-siege-dot ${i < victoires ? 'filled' : ''}"></div>`).join('');

    return `
      <div class="combat-card ${commune.tier}">
        <div class="tricolore"><span class="b"></span><span class="w"></span><span class="r"></span></div>
        <div class="cc-body">
          <span class="cc-badge">${tier.label}</span>
          <p class="cc-name">${commune.nom}</p>
          <p class="cc-owner">Possédée par ${pseudo}</p>
          <div class="cc-sieges">${dots}</div>
          <p class="cc-status ${statusClass}">${statusTxt}</p>
          <button class="bourse-btn cc-btn" data-action="attaquer" data-code="${c.commune_code}" ${disabled ? 'disabled' : ''}>Attaquer (${cout} pts)</button>
        </div>
      </div>`;
  }).join('');
}

// Rafraichit les decomptes toutes les 30 s quand l'onglet Combat est ouvert,
// pour que le bouton se debloque tout seul sans avoir a changer d'onglet
setInterval(() => {
  const panel = document.getElementById('panel-combat');
  if(!panel || !panel.classList.contains('active')) return;
  if(combatActionEnCours || combatCibles.length === 0) return;
  renderCombatGrid();
}, 30000);

document.getElementById('combatSearch').addEventListener('input', renderCombatGrid);
document.getElementById('combatFilters').addEventListener('click', (e) => {
  const pill = e.target.closest('.filter-pill');
  if(!pill) return;
  document.querySelectorAll('#combatFilters .filter-pill').forEach(p => p.classList.remove('active'));
  pill.classList.add('active');
  combatFilterTier = pill.dataset.tier;
  renderCombatGrid();
});

// ---------- Navigation par onglets ----------
document.querySelectorAll('.tab').forEach(tab => {
  tab.addEventListener('click', () => {
    document.querySelectorAll('.tab').forEach(t => t.classList.remove('active'));
    document.querySelectorAll('.tab-panel').forEach(p => p.classList.remove('active'));
    tab.classList.add('active');
    document.getElementById('panel-' + tab.dataset.tab).classList.add('active');
    if(tab.dataset.tab === 'territoire') sizeMapWrap(window.__mapAspectRatio);
    if(tab.dataset.tab === 'bourse') loadBourse();
    if(tab.dataset.tab === 'combat') loadCombat();
  });
});

initAuth();
