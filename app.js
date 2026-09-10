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
  const { error } = await sb.auth.signUp({ email, password });
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

  wrap.addEventListener('touchstart', (e) => {
    if(e.touches.length !== 1) return;
    mapDragging = true;
    mapDragStart = { x: e.touches[0].clientX - mapPanX, y: e.touches[0].clientY - mapPanY };
  }, { passive: true });
  wrap.addEventListener('touchmove', (e) => {
    if(!mapDragging || e.touches.length !== 1) return;
    e.preventDefault();
    mapPanX = e.touches[0].clientX - mapDragStart.x;
    mapPanY = e.touches[0].clientY - mapDragStart.y;
    applyMapTransform();
  }, { passive: false });
  wrap.addEventListener('touchend', () => { mapDragging = false; });
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
      onFlip();
    }
  });
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
        document.getElementById('openBtn').disabled = false;
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

async function openPack(){
  document.getElementById('openBtn').disabled = true;
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
        document.getElementById('openBtn').disabled = false;
        return;
      }
      revealCards(draws);
    }, 650);
  }, { once: true });
}

document.getElementById('openBtn').addEventListener('click', openPack);

document.getElementById('toggleOthersBtn').addEventListener('click', () => {
  showOthers = !showOthers;
  document.getElementById('toggleOthersBtn').textContent = showOthers
    ? 'Cacher le territoire des autres'
    : 'Afficher le territoire des autres';
  renderMapOverlay();
});

// ---------- Navigation par onglets ----------
document.querySelectorAll('.tab').forEach(tab => {
  tab.addEventListener('click', () => {
    document.querySelectorAll('.tab').forEach(t => t.classList.remove('active'));
    document.querySelectorAll('.tab-panel').forEach(p => p.classList.remove('active'));
    tab.classList.add('active');
    document.getElementById('panel-' + tab.dataset.tab).classList.add('active');
    if(tab.dataset.tab === 'territoire') sizeMapWrap(window.__mapAspectRatio);
  });
});

initAuth();
