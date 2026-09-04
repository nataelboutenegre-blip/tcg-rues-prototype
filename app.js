let COMMUNES = [];

fetch('data/communes.json')
  .then(r => r.json())
  .then(data => {
    COMMUNES = data;
    buildIndex();
    renderStats();
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

let COMMUNES = [];
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