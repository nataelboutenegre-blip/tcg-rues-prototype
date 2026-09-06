let COMMUNES = [];

fetch('data/communes.json')
  .then(r => r.json())
  .then(data => {
    COMMUNES = data;
    buildIndex();
    renderStats();
    initMap();
  });

const TIERS = [
  {id:'legendaire', label:'Légendaire', color:'#B0862C', min:200000, max:Infinity, target:0.83},
  {id:'rare', label:'Rare', color:'#2A5FA8', min:20000, max:200000, target:11.40},
  {id:'peucommun', label:'Peu commun', color:'#2E7D5B', min:2000, max:20000, target:36.85},
  {id:'commun', label:'Commun', color:'#7C8798', min:0, max:2000, target:50.92},
];

function tierFor(pop){
  return TIERS.find(t => pop >= t.min && pop < t.max) || TIERS[TIERS.length-1];
}

let CUM_WEIGHTS = [];
let TOTAL_WEIGHT = 0;

function buildIndex(){
  let running = 0;
  for(const c of COMMUNES){
    running += c[3]; // nb_voies = poids
    CUM_WEIGHTS.push(running);
  }
  TOTAL_WEIGHT = running;
}

function drawOne(){
  const r = Math.random() * TOTAL_WEIGHT;
  // recherche binaire
  let lo = 0, hi = CUM_WEIGHTS.length - 1;
  while(lo < hi){
    const mid = (lo + hi) >> 1;
    if(CUM_WEIGHTS[mid] < r) lo = mid + 1; else hi = mid;
  }
  const c = COMMUNES[lo];
  const streetNum = 1 + Math.floor(Math.random() * c[3]);
  return { nom: c[0], dept: c[1], pop: c[2], nbVoies: c[3], lat: c[4], lon: c[5], streetNum, tier: tierFor(c[2]) };
}

let session = {commun:0, peucommun:0, rare:0, legendaire:0, total:0};

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
      <div class="nums">${n} tirée${n>1?'s':''} (${pct.toFixed(1)}%)</div>
    `;
    rows.appendChild(row);
  }
}

let collectionList = [];

function addToCollection(draw){
  collectionList.push(draw);
  renderCollection();
  renderMapOverlay();
}

// --- Carte du territoire ---
const METRO_DEPT_RE = /^(0[1-9]|[1-8][0-9]|9[0-5]|2A|2B)$/;
const DEPT_NAMES = {"01":"Ain","02":"Aisne","03":"Allier","04":"Alpes-de-Haute-Provence","05":"Hautes-Alpes","06":"Alpes-Maritimes","07":"Ardèche","08":"Ardennes","09":"Ariège","10":"Aube","11":"Aude","12":"Aveyron","13":"Bouches-du-Rhône","14":"Calvados","15":"Cantal","16":"Charente","17":"Charente-Maritime","18":"Cher","19":"Corrèze","21":"Côte-d'Or","22":"Côtes-d'Armor","23":"Creuse","24":"Dordogne","25":"Doubs","26":"Drôme","27":"Eure","28":"Eure-et-Loir","29":"Finistère","2A":"Corse-du-Sud","2B":"Haute-Corse","30":"Gard","31":"Haute-Garonne","32":"Gers","33":"Gironde","34":"Hérault","35":"Ille-et-Vilaine","36":"Indre","37":"Indre-et-Loire","38":"Isère","39":"Jura","40":"Landes","41":"Loir-et-Cher","42":"Loire","43":"Haute-Loire","44":"Loire-Atlantique","45":"Loiret","46":"Lot","47":"Lot-et-Garonne","48":"Lozère","49":"Maine-et-Loire","50":"Manche","51":"Marne","52":"Haute-Marne","53":"Mayenne","54":"Meurthe-et-Moselle","55":"Meuse","56":"Morbihan","57":"Moselle","58":"Nièvre","59":"Nord","60":"Oise","61":"Orne","62":"Pas-de-Calais","63":"Puy-de-Dôme","64":"Pyrénées-Atlantiques","65":"Hautes-Pyrénées","66":"Pyrénées-Orientales","67":"Bas-Rhin","68":"Haut-Rhin","69":"Rhône","70":"Haute-Saône","71":"Saône-et-Loire","72":"Sarthe","73":"Savoie","74":"Haute-Savoie","75":"Paris","76":"Seine-Maritime","77":"Seine-et-Marne","78":"Yvelines","79":"Deux-Sèvres","80":"Somme","81":"Tarn","82":"Tarn-et-Garonne","83":"Var","84":"Vaucluse","85":"Vendée","86":"Vienne","87":"Haute-Vienne","88":"Vosges","89":"Yonne","90":"Territoire de Belfort","91":"Essonne","92":"Hauts-de-Seine","93":"Seine-Saint-Denis","94":"Val-de-Marne","95":"Val-d'Oise"};
let mapBounds = null;

function computeMapBounds(){
  let latMin=90, latMax=-90, lonMin=180, lonMax=-180;
  for(const c of COMMUNES){
    const dept = c[1], lat = c[4], lon = c[5];
    if(lat==null || lon==null) continue;
    if(!METRO_DEPT_RE.test(dept)) continue;
    if(lat<latMin) latMin=lat;
    if(lat>latMax) latMax=lat;
    if(lon<lonMin) lonMin=lon;
    if(lon>lonMax) lonMax=lon;
  }
  mapBounds = {latMin, latMax, lonMin, lonMax};
}

function project(lat, lon){
  const {latMin, latMax, lonMin, lonMax} = mapBounds;
  const x = (lon - lonMin) / (lonMax - lonMin);
  const y = (latMax - lat) / (latMax - latMin);
  return {x, y};
}

function initMap(){
  computeMapBounds();
  const canvas = document.getElementById('mapCanvas');
  if(!canvas) return;
  const ctx = canvas.getContext('2d');
  const w = canvas.width, h = canvas.height;

  // fond degrade bleu nuit
  const grad = ctx.createRadialGradient(w/2, h*0.4, 30, w/2, h*0.5, w*0.75);
  grad.addColorStop(0, '#123564');
  grad.addColorStop(1, '#061A34');
  ctx.fillStyle = grad;
  ctx.fillRect(0, 0, w, h);

  // grille discrete
  ctx.strokeStyle = 'rgba(148,177,214,0.08)';
  ctx.lineWidth = 1;
  const step = 32;
  for(let x = 0; x <= w; x += step){
    ctx.beginPath(); ctx.moveTo(x, 0); ctx.lineTo(x, h); ctx.stroke();
  }
  for(let y = 0; y <= h; y += step){
    ctx.beginPath(); ctx.moveTo(0, y); ctx.lineTo(w, y); ctx.stroke();
  }

  // points communes
  ctx.fillStyle = 'rgba(180,201,232,0.55)';
  const deptSum = new Map(); // code -> {sx, sy, n}
  for(const c of COMMUNES){
    const dept = c[1], lat = c[4], lon = c[5];
    if(lat==null || lon==null) continue;
    if(!METRO_DEPT_RE.test(dept)) continue;
    const p = project(lat, lon);
    ctx.fillRect(p.x * w, p.y * h, 1.3, 1.3);
    if(!deptSum.has(dept)) deptSum.set(dept, {sx:0, sy:0, n:0});
    const d = deptSum.get(dept);
    d.sx += p.x; d.sy += p.y; d.n++;
  }

  // noms des departements
  ctx.font = '11px Georgia, serif';
  ctx.fillStyle = 'rgba(148,177,214,0.65)';
  ctx.textAlign = 'center';
  deptSum.forEach((d, code) => {
    const name = DEPT_NAMES[code];
    if(!name) return;
    const x = (d.sx / d.n) * w;
    const y = (d.sy / d.n) * h;
    ctx.fillText(name, x, y);
  });
  setupMapInteraction();
}

let mapZoom = 1, mapPanX = 0, mapPanY = 0;
let mapDragging = false, mapDragStart = {x:0, y:0};
let mapInteractionReady = false;

function applyMapTransform(){
  const el = document.getElementById('mapTransform');
  if(el) el.style.transform = `translate(${mapPanX}px, ${mapPanY}px) scale(${mapZoom})`;
}

function setupMapInteraction(){
  if(mapInteractionReady) return;
  mapInteractionReady = true;
  const wrap = document.getElementById('mapWrap');
  if(!wrap) return;
  wrap.addEventListener('wheel', (e) => {
    e.preventDefault();
    const factor = e.deltaY < 0 ? 1.15 : 1/1.15;
    mapZoom = Math.min(6, Math.max(1, mapZoom * factor));
    if(mapZoom === 1){ mapPanX = 0; mapPanY = 0; }
    applyMapTransform();
  }, { passive: false });
  wrap.addEventListener('mousedown', (e) => {
    mapDragging = true;
    mapDragStart = { x: e.clientX - mapPanX, y: e.clientY - mapPanY };
  });
  window.addEventListener('mousemove', (e) => {
    if(!mapDragging) return;
    mapPanX = e.clientX - mapDragStart.x;
    mapPanY = e.clientY - mapDragStart.y;
    applyMapTransform();
  });
  window.addEventListener('mouseup', () => { mapDragging = false; });
}

function ownedCommunesMap(){
  const map = new Map();
  for(const draw of collectionList){
    const key = draw.nom + '|' + draw.dept;
    if(!map.has(key)){
      map.set(key, {nom: draw.nom, dept: draw.dept, lat: draw.lat, lon: draw.lon, tier: draw.tier, count: 1});
    } else {
      const entry = map.get(key);
      entry.count++;
      if(TIERS.indexOf(draw.tier) < TIERS.indexOf(entry.tier)) entry.tier = draw.tier;
    }
  }
  return map;
}

function renderMapOverlay(){
  const overlay = document.getElementById('mapOverlay');
  if(!overlay || !mapBounds) return;
  overlay.innerHTML = '';
  const owned = ownedCommunesMap();
  owned.forEach(entry => {
    if(entry.lat == null || entry.lon == null) return;
    const p = project(entry.lat, entry.lon);
    const dot = document.createElement('div');
    dot.className = 'map-dot ' + entry.tier.id;
    dot.style.left = (p.x * 100) + '%';
    dot.style.top = (p.y * 100) + '%';
    dot.title = entry.nom + ' (' + entry.dept + ') — ' + entry.tier.label + (entry.count > 1 ? ' ×' + entry.count : '');
    overlay.appendChild(dot);
  });
}

function renderCollection(){
  const countEl = document.getElementById('collectionCount');
  const gridEl = document.getElementById('collectionGrid');
  countEl.textContent = collectionList.length;
  if(collectionList.length === 0){
    gridEl.innerHTML = '<p class="collection-empty">Aucune carte pour le moment — ouvre un paquet.</p>';
    return;
  }
  const sorted = [...collectionList].sort((a,b) => {
    const ra = TIERS.indexOf(a.tier), rb = TIERS.indexOf(b.tier);
    if(ra !== rb) return ra - rb;
    return b.pop - a.pop;
  });
  gridEl.innerHTML = sorted.map(draw => `
    <div class="mini-card ${draw.tier.id}" title="${draw.nom} (${draw.dept}) — ${draw.tier.label}">
      <div class="stripe"><span class="b"></span><span class="w"></span><span class="r"></span></div>
      <div class="body">
        <div class="name">${draw.nom}</div>
        <div class="rarity" style="background:${draw.tier.color}">${draw.tier.label}</div>
      </div>
    </div>
  `).join('');
}

function makeCardEl(draw){
  const wrap = document.createElement('div');
  wrap.className = 'card ' + draw.tier.id;
  wrap.innerHTML = `
    <div class="card-inner">
      <div class="face face-back"><div class="emblem">RF</div></div>
      <div class="face face-front">
        <div class="tricolore"><span class="b"></span><span class="w"></span><span class="r"></span></div>
        <div class="card-body">
          <div class="rarity-tag" style="background:${draw.tier.color}">${draw.tier.label}</div>
          <div class="stamp" style="border-color:${draw.tier.color};color:${draw.tier.color}">Nº${draw.streetNum}</div>
          <p class="commune-name">${draw.nom}</p>
          <p class="voie-name">Voie nº${draw.streetNum} de la commune</p>
          <div class="fields">
            <div class="field"><span>Département</span><b>${draw.dept}</b></div>
            <div class="field"><span>Population</span><b>${draw.pop.toLocaleString('fr-FR')}</b></div>
            <div class="field"><span>Voies recensées</span><b>${draw.nbVoies}</b></div>
          </div>
        </div>
      </div>
    </div>
  `;
  wrap.addEventListener('click', () => {
    if(!wrap.classList.contains('flipped')){
      wrap.classList.add('flipped');
      session[draw.tier.id]++;
      session.total++;
      renderStats();
      addToCollection(draw);
      pendingFlips--;
      if(pendingFlips <= 0){
        document.getElementById('openBtn').disabled = false;
      }
    }
  });
  return wrap;
}

let pendingFlips = 0;

function revealCards(draws){
  const zone = document.getElementById('packZone');
  zone.innerHTML = '';
  pendingFlips = draws.length;
  draws.forEach(draw => zone.appendChild(makeCardEl(draw)));
}

function makePackEl(){
  const pack = document.createElement('div');
  pack.className = 'foilpack';
  pack.style.setProperty('--foil-color', '#0B2A55');
  pack.innerHTML = `<div class="body"><div class="mark">Paquet</div></div><div class="strip"></div>`;
  return pack;
}

function openPack(){
  document.getElementById('openBtn').disabled = true;
  const zone = document.getElementById('packZone');
  zone.innerHTML = '';
  const draws = [];
  for(let i=0;i<5;i++) draws.push(drawOne());
  const pack = makePackEl();
  zone.appendChild(pack);
  pack.addEventListener('click', () => {
    pack.classList.add('tearing');
    setTimeout(() => revealCards(draws), 650);
  }, { once: true });
}


buildIndex();
renderStats();
