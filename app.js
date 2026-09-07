let COMMUNES = [];

fetch('data/communes.json')
  .then(r => r.json())
  .then(data => {
    COMMUNES = data;
    buildIndex();
    renderStats();
    computeMapBounds();
  });

const METRO_DEPT_RE = /^(0[1-9]|[1-8][0-9]|9[0-5]|2A|2B)$/;
const MAINLAND_NO_CORSICA_RE = /^(0[1-9]|[1-8][0-9]|9[0-5])$/;
let mapBounds = null;

function computeMapBounds(){
  let latMin=90, latMax=-90, lonMin=180, lonMax=-180;
  for(const c of COMMUNES){
    const dept = c[1], lat = c[4], lon = c[5];
    if(lat == null || lon == null) continue;
    if(!MAINLAND_NO_CORSICA_RE.test(dept)) continue;
    if(lat<latMin) latMin=lat;
    if(lat>latMax) latMax=lat;
    if(lon<lonMin) lonMin=lon;
    if(lon>lonMax) lonMax=lon;
  }
  mapBounds = {latMin, latMax, lonMin, lonMax};

  const meanLat = (latMin + latMax) / 2;
  const lonSpanCorrected = (lonMax - lonMin) * Math.cos(meanLat * Math.PI / 180);
  const latSpan = latMax - latMin;
  const wrap = document.getElementById('mapWrap');
  if(wrap) wrap.style.aspectRatio = (lonSpanCorrected / latSpan).toFixed(4);
}

function project(lat, lon){
  const {latMin, latMax, lonMin, lonMax} = mapBounds;
  const x = (lon - lonMin) / (lonMax - lonMin);
  const y = (latMax - lat) / (latMax - latMin);
  return {x, y};
}

function renderMapOverlay(){
  const overlay = document.getElementById('mapOverlay');
  if(!overlay || !mapBounds) return;
  overlay.innerHTML = '';
  for(const entry of collectionMap.values()){
    if(entry.lat == null || entry.lon == null) continue;
    if(!MAINLAND_NO_CORSICA_RE.test(entry.dept)) continue;
    const p = project(entry.lat, entry.lon);
    const dot = document.createElement('div');
    dot.className = 'map-dot ' + entry.tier.id;
    dot.style.left = (p.x * 100) + '%';
    dot.style.top = (p.y * 100) + '%';
    dot.title = entry.nom + ' (' + entry.dept + ') — ' + entry.tier.label + (entry.count > 1 ? ' ×' + entry.count : '');
    overlay.appendChild(dot);
  }
}

const TIERS = [
  {id:'legendaire', label:'Légendaire', color:'#B0862C', min:200000, max:Infinity, target:0.83},
  {id:'rare', label:'Rare', color:'#2A5FA8', min:20000, max:200000, target:11.40},
  {id:'peucommun', label:'Peu commun', color:'#2E7D5B', min:2000, max:20000, target:36.85},
  {id:'commun', label:'Commun', color:'#7C8798', min:0, max:2000, target:50.92},
];

function tierFor(pop){
  return TIERS.find(t => pop >= t.min && pop < t.max) || TIERS[TIERS.length-1];
}

let TIER_BUCKETS = {};
let TIER_RANK = {};

const DEPT_NAMES = {"01":"Ain","02":"Aisne","03":"Allier","04":"Alpes-de-Haute-Provence","05":"Hautes-Alpes","06":"Alpes-Maritimes","07":"Ardèche","08":"Ardennes","09":"Ariège","10":"Aube","11":"Aude","12":"Aveyron","13":"Bouches-du-Rhône","14":"Calvados","15":"Cantal","16":"Charente","17":"Charente-Maritime","18":"Cher","19":"Corrèze","21":"Côte-d'Or","22":"Côtes-d'Armor","23":"Creuse","24":"Dordogne","25":"Doubs","26":"Drôme","27":"Eure","28":"Eure-et-Loir","29":"Finistère","2A":"Corse-du-Sud","2B":"Haute-Corse","30":"Gard","31":"Haute-Garonne","32":"Gers","33":"Gironde","34":"Hérault","35":"Ille-et-Vilaine","36":"Indre","37":"Indre-et-Loire","38":"Isère","39":"Jura","40":"Landes","41":"Loir-et-Cher","42":"Loire","43":"Haute-Loire","44":"Loire-Atlantique","45":"Loiret","46":"Lot","47":"Lot-et-Garonne","48":"Lozère","49":"Maine-et-Loire","50":"Manche","51":"Marne","52":"Haute-Marne","53":"Mayenne","54":"Meurthe-et-Moselle","55":"Meuse","56":"Morbihan","57":"Moselle","58":"Nièvre","59":"Nord","60":"Oise","61":"Orne","62":"Pas-de-Calais","63":"Puy-de-Dôme","64":"Pyrénées-Atlantiques","65":"Hautes-Pyrénées","66":"Pyrénées-Orientales","67":"Bas-Rhin","68":"Haut-Rhin","69":"Rhône","70":"Haute-Saône","71":"Saône-et-Loire","72":"Sarthe","73":"Savoie","74":"Haute-Savoie","75":"Paris","76":"Seine-Maritime","77":"Seine-et-Marne","78":"Yvelines","79":"Deux-Sèvres","80":"Somme","81":"Tarn","82":"Tarn-et-Garonne","83":"Var","84":"Vaucluse","85":"Vendée","86":"Vienne","87":"Haute-Vienne","88":"Vosges","89":"Yonne","90":"Territoire de Belfort","91":"Essonne","92":"Hauts-de-Seine","93":"Seine-Saint-Denis","94":"Val-de-Marne","95":"Val-d'Oise"};

function buildIndex(){
  TIER_BUCKETS = {};
  TIER_RANK = {};
  for(const t of TIERS) TIER_BUCKETS[t.id] = [];
  COMMUNES.forEach((c, i) => {
    TIER_BUCKETS[tierFor(c[2]).id].push(i);
  });
  for(const t of TIERS){
    const bucket = TIER_BUCKETS[t.id];
    bucket.sort((a, b) => COMMUNES[b][2] - COMMUNES[a][2]); // population decroissante
    bucket.forEach((idx, i) => { TIER_RANK[idx] = i + 1; });
  }
}

function pickTier(){
  const r = Math.random() * 100;
  let cum = 0;
  for(const t of TIERS){
    cum += t.target;
    if(r < cum) return t;
  }
  return TIERS[TIERS.length - 1];
}

function drawOne(){
  const tier = pickTier();
  const bucket = TIER_BUCKETS[tier.id];
  const idx = bucket[Math.floor(Math.random() * bucket.length)];
  const c = COMMUNES[idx];
  return { nom: c[0], dept: c[1], pop: c[2], nbVoies: c[3], lat: c[4], lon: c[5], code: c[6], tier, rank: TIER_RANK[idx], tierSize: bucket.length };
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

let collectionMap = new Map();

function addToCollection(draw){
  const key = draw.nom + '|' + draw.dept;
  if(collectionMap.has(key)){
    collectionMap.get(key).count++;
  } else {
    collectionMap.set(key, {...draw, count: 1});
  }
  renderMapOverlay();
  renderCollection();
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
    <div class="mini-card ${entry.tier.id}" title="${entry.nom} (${entry.dept}) — ${entry.tier.label}${entry.count>1 ? ' ×'+entry.count : ''}">
      <div class="stripe"><span class="b"></span><span class="w"></span><span class="r"></span></div>
      <div class="body">
        <div class="name">${entry.nom}</div>
        <div class="rarity" style="background:${entry.tier.color}">${entry.tier.label}</div>
      </div>
      ${entry.count>1 ? `<div class="qty">×${entry.count}</div>` : ''}
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
          <p class="commune-name">${draw.nom}</p>
          <div class="fields">
            <div class="field"><span>Département</span><b>${DEPT_NAMES[draw.dept] || draw.dept}</b></div>
            <div class="field"><span>Population</span><b>${draw.pop.toLocaleString('fr-FR')}</b></div>
            <div class="field"><span>Numéro</span><b>${draw.rank.toLocaleString('fr-FR')} / ${draw.tierSize.toLocaleString('fr-FR')}</b></div>
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
