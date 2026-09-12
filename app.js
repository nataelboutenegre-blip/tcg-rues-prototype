// --- Connexion Supabase ---
const SUPABASE_URL = 'https://yzcgroprydxhbwaufkdu.supabase.co';
const SUPABASE_ANON_KEY = 'sb_publishable_s829mEa2YUPWr9DOks2FTg_k9gpTQTA';
const sb = window.supabase.createClient(SUPABASE_URL, SUPABASE_ANON_KEY);
const CURRENT_SEASON = 'saison-1';
const VERSION_JEU = 'd8d39a81f884';

const TIERS = [
  {id:'legendaire', label:'Légendaire', color:'#B0862C', target:0.83},
  {id:'rare', label:'Rare', color:'#2A5FA8', target:11.40},
  {id:'peucommun', label:'Peu commun', color:'#2E7D5B', target:36.85},
  {id:'commun', label:'Commun', color:'#7C8798', target:50.92},
];
const DEPT_NAMES = {"01":"Ain","02":"Aisne","03":"Allier","04":"Alpes-de-Haute-Provence","05":"Hautes-Alpes","06":"Alpes-Maritimes","07":"Ardèche","08":"Ardennes","09":"Ariège","10":"Aube","11":"Aude","12":"Aveyron","13":"Bouches-du-Rhône","14":"Calvados","15":"Cantal","16":"Charente","17":"Charente-Maritime","18":"Cher","19":"Corrèze","21":"Côte-d'Or","22":"Côtes-d'Armor","23":"Creuse","24":"Dordogne","25":"Doubs","26":"Drôme","27":"Eure","28":"Eure-et-Loir","29":"Finistère","2A":"Corse-du-Sud","2B":"Haute-Corse","30":"Gard","31":"Haute-Garonne","32":"Gers","33":"Gironde","34":"Hérault","35":"Ille-et-Vilaine","36":"Indre","37":"Indre-et-Loire","38":"Isère","39":"Jura","40":"Landes","41":"Loir-et-Cher","42":"Loire","43":"Haute-Loire","44":"Loire-Atlantique","45":"Loiret","46":"Lot","47":"Lot-et-Garonne","48":"Lozère","49":"Maine-et-Loire","50":"Manche","51":"Marne","52":"Haute-Marne","53":"Mayenne","54":"Meurthe-et-Moselle","55":"Meuse","56":"Morbihan","57":"Moselle","58":"Nièvre","59":"Nord","60":"Oise","61":"Orne","62":"Pas-de-Calais","63":"Puy-de-Dôme","64":"Pyrénées-Atlantiques","65":"Hautes-Pyrénées","66":"Pyrénées-Orientales","67":"Bas-Rhin","68":"Haut-Rhin","69":"Rhône","70":"Haute-Saône","71":"Saône-et-Loire","72":"Sarthe","73":"Savoie","74":"Haute-Savoie","75":"Paris","76":"Seine-Maritime","77":"Seine-et-Marne","78":"Yvelines","79":"Deux-Sèvres","80":"Somme","81":"Tarn","82":"Tarn-et-Garonne","83":"Var","84":"Vaucluse","85":"Vendée","86":"Vienne","87":"Haute-Vienne","88":"Vosges","89":"Yonne","90":"Territoire de Belfort","91":"Essonne","92":"Hauts-de-Seine","93":"Seine-Saint-Denis","94":"Val-de-Marne","95":"Val-d'Oise"};
const METRO_DEPT_RE = /^(0[1-9]|[1-8][0-9]|9[0-5]|2A|2B)$/;

// Couleurs des autres joueurs sur la carte (toi = dore). Au-dela de 12 joueurs, des couleurs se repetent.
const OPPONENT_COLORS = ['#E5484D','#8E7CF6','#2EC4B6','#F76B15','#E93D82','#3DD68C','#5EB1EF','#FF977D','#9EB1FF','#12A594','#D6409F','#C2A383'];
const COULEUR_MOI = '#F0B429';

function colorForPlayer(id){
  let hash = 0;
  for(let i = 0; i < id.length; i++){
    hash = (hash * 31 + id.charCodeAt(i)) >>> 0;
  }
  return OPPONENT_COLORS[hash % OPPONENT_COLORS.length];
}
// meme teinte, en plus sombre (lignes entre communes d'un meme joueur)
function couleurFoncee(hex){
  return '#' + [1, 3, 5].map(k => Math.round(parseInt(hex.slice(k, k + 2), 16) * 0.45).toString(16).padStart(2, '0')).join('');
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
function courbesDeNiveau(seed, w, h, anneaux, points = 90){
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
    for(let k = 0; k < points; k++){
      const t = k / points * Math.PI * 2;
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

// Epingle de carte, utilisee sur le dos des cartes et sur le paquet
const ICONE_EPINGLE = '<svg viewBox="0 0 24 24" fill="none" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M12 21s-7-6.2-7-11.5A7 7 0 0 1 19 9.5C19 14.8 12 21 12 21z"/><circle cx="12" cy="9.5" r="2.5"/></svg>';

// Le motif du dos est le meme pour toutes les cartes : on le calcule une seule fois
const DOS_MOTIF_SVG = (() => {
  const { d } = courbesDeNiveau(hashTexte('dos-de-carte'), 188, 263, 10);
  return `<svg class="dos-motif" viewBox="0 0 188 263" preserveAspectRatio="xMidYMid slice" aria-hidden="true">
    <path d="${d}" fill="none" stroke="rgba(169,188,212,0.16)" stroke-width="1"/>
  </svg>`;
})();

function paquetMotifSvg(type){
  const achete = type === 'achete';
  const clair = achete ? '#FCE38A' : '#3B6FB8';
  const moyen = achete ? '#F0B429' : '#1D3F72';
  const fonce = achete ? '#9A6412' : '#0B1D38';
  const trait = achete ? 'rgba(90,55,5,0.28)' : 'rgba(169,210,255,0.22)';
  const { d } = courbesDeNiveau(hashTexte('paquet-' + type), 200, 280, 12);
  return `<svg class="paquet-motif" viewBox="0 0 200 280" aria-hidden="true">
    <defs><linearGradient id="pg-${type}" x1="0" y1="0" x2="1" y2="1">
      <stop offset="0%" stop-color="${clair}"/><stop offset="55%" stop-color="${moyen}"/><stop offset="100%" stop-color="${fonce}"/>
    </linearGradient></defs>
    <rect width="200" height="280" fill="url(#pg-${type})"/>
    <path d="${d}" fill="none" stroke="${trait}" stroke-width="1.2"/>
  </svg>`;
}

// d3 sert a la carte (frontieres) et aux courbes de niveau ; si le CDN ne repond pas, on se rabat sur plus simple
const D3_OK = typeof d3 !== 'undefined' && !!d3.Delaunay && !!d3.contours;

// Relief imaginaire dont on trace les courbes de niveau : deux lignes d'altitudes differentes ne se croisent jamais
function lignesDeNiveau(seed, w, h, nbLignes, nbBosses){
  if(!D3_OK) return courbesDeNiveau(seed, w, h, nbLignes).d;
  const rnd = aleatoireStable(seed);
  const nx = 110, ny = Math.max(30, Math.round(110 * h / w));
  const marge = 0.08;
  const bosses = Array.from({length: nbBosses}, () => ({
    x: rnd() * nx, y: rnd() * ny,
    s: (0.1 + rnd() * 0.2) * nx,
    a: (rnd() < 0.35 ? -1 : 1) * (0.5 + rnd())
  }));
  const valeurs = new Float64Array(nx * ny);
  for(let jy = 0; jy < ny; jy++) for(let ix = 0; ix < nx; ix++){
    let v = 0.2 * ix / nx;
    for(const b of bosses){ const dx = ix - b.x, dy = jy - b.y; v += b.a * Math.exp(-(dx*dx + dy*dy) / (2 * b.s * b.s)); }
    valeurs[jy * nx + ix] = v;
  }
  let min = Infinity, max = -Infinity;
  for(const v of valeurs){ if(v < min) min = v; if(v > max) max = v; }
  const seuils = Array.from({length: nbLignes}, (_, k) => min + (max - min) * (k + 1) / (nbLignes + 1));
  const trace = d3.line().curve(d3.curveBasisClosed);
  const px = (x) => ((x - 0.5) / (nx - 1) * (1 + 2 * marge) - marge) * w;
  const py = (y) => ((y - 0.5) / (ny - 1) * (1 + 2 * marge) - marge) * h;
  let d = '';
  for(const geo of d3.contours().size([nx, ny]).thresholds(seuils)(valeurs)){
    for(const poly of geo.coordinates) for(const anneau of poly){
      d += trace(anneau.slice(0, -1).map(([x, y]) => [px(x), py(y)]));
    }
  }
  return d;
}

function dessinerFondTopo(){
  const svg = document.getElementById('fondTopo');
  if(!svg) return;
  svg.setAttribute('viewBox', '0 0 1600 1000');
  svg.setAttribute('preserveAspectRatio', 'xMidYMid slice');
  svg.innerHTML = `<path d="${lignesDeNiveau(911, 1600, 1000, 9, 6)}" fill="none" stroke="rgba(169,188,212,0.07)" stroke-width="1.2"/>`;
}
dessinerFondTopo();

let FRANCE_OUTLINE = null;
let MAP_W = 1000, MAP_H = 1000;
let mapBounds = null;
let collectionMap = new Map();
let othersMap = new Map();
let session = {commun:0, peucommun:0, rare:0, legendaire:0, total:0};

// ---------- Notifications (remplacent les fenetres grises du navigateur) ----------
const ICONES_NOTIF = {
  victoire: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"><path d="M5 12.5l4.5 4.5L19 7.5"/></svg>',
  defaite: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round"><path d="M6 6l12 12M18 6L6 18"/></svg>',
  erreur: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round"><path d="M12 7v6M12 17h.01"/><circle cx="12" cy="12" r="9.5"/></svg>',
  succes: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"><path d="M5 12.5l4.5 4.5L19 7.5"/></svg>',
  info: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round"><path d="M12 11v6M12 7h.01"/><circle cx="12" cy="12" r="9.5"/></svg>',
};

// Les messages d'erreur de Supabase arrivent en anglais : on traduit les plus courants
function messageLisible(msg){
  const m = String(msg || '');
  const table = [
    [/invalid login credentials/i, 'Email ou mot de passe incorrect.'],
    [/user already registered/i, 'Un compte existe déjà avec cet email.'],
    [/password should be at least (\d+)/i, (x) => `Le mot de passe doit faire au moins ${x[1]} caractères.`],
    [/email not confirmed/i, 'Confirme ton adresse email avant de te connecter (regarde tes mails).'],
    [/invalid format|unable to validate email/i, 'Adresse email invalide.'],
    [/failed to fetch|network/i, 'Connexion impossible. Vérifie ta connexion internet.'],
    [/rate limit|too many requests/i, 'Trop de tentatives. Réessaie dans quelques minutes.'],
  ];
  for(const [re, trad] of table){
    const x = m.match(re);
    if(x) return typeof trad === 'function' ? trad(x) : trad;
  }
  return m;
}

function notifier({ type = 'info', titre, texte = '', serie = null, duree }){
  const zone = document.getElementById('notifs');
  if(!zone) return;
  const el = document.createElement('div');
  el.className = 'notif ' + type;
  el.setAttribute('role', type === 'erreur' ? 'alert' : 'status');
  const ronds = serie === null ? '' : `<span class="notif-serie">${[0, 1, 2].map(i => `<i class="${i < serie ? 'plein' : ''}"></i>`).join('')}</span>`;
  el.innerHTML = `
    <span class="notif-icone">${ICONES_NOTIF[type] || ICONES_NOTIF.info}</span>
    <span class="notif-texte"><b>${echapperTexte(titre)}</b>${texte ? `<span>${echapperTexte(texte)}</span>` : ''}</span>
    ${ronds}
    <button class="notif-fermer" aria-label="Fermer">
      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round"><path d="M7 7l10 10M17 7L7 17"/></svg>
    </button>`;
  const fermer = () => {
    if(el.classList.contains('sortie')) return;
    el.classList.add('sortie');
    setTimeout(() => el.remove(), 220);
  };
  el.querySelector('.notif-fermer').addEventListener('click', fermer);
  zone.appendChild(el);
  // au-dela de 3 notifications, la plus ancienne s'en va
  const toutes = zone.querySelectorAll('.notif:not(.sortie)');
  if(toutes.length > 3) toutes[0].querySelector('.notif-fermer').click();
  requestAnimationFrame(() => el.classList.add('visible'));
  setTimeout(fermer, duree || (type === 'erreur' ? 6000 : 3500));
}
function echapperTexte(s){
  return String(s == null ? '' : s).replace(/[&<>"]/g, ch => ({'&':'&amp;', '<':'&lt;', '>':'&gt;', '"':'&quot;'}[ch]));
}

// ---------- Fenetres (conquete, prix de vente) ----------
let fenetreRetourFocus = null;
function ouvrirFenetre(html, onFermer){
  const fond = document.getElementById('fenetre');
  fenetreRetourFocus = document.activeElement;
  fond.innerHTML = html;
  fond.hidden = false;
  requestAnimationFrame(() => fond.classList.add('visible'));
  const fermer = (valeur) => {
    fond.classList.remove('visible');
    document.removeEventListener('keydown', surTouche);
    setTimeout(() => { fond.hidden = true; fond.innerHTML = ''; }, 180);
    if(fenetreRetourFocus && fenetreRetourFocus.focus) fenetreRetourFocus.focus();
    if(onFermer) onFermer(valeur);
  };
  const surTouche = (e) => { if(e.key === 'Escape') fermer(null); };
  document.addEventListener('keydown', surTouche);
  fond.onclick = (e) => { if(e.target === fond) fermer(null); };
  return fermer;
}

function celebrerConquete({ nom, tier, dept, bonus }){
  const t = TIERS.find(x => x.id === tier);
  const fermer = ouvrirFenetre(`
    <div class="fenetre conquete ${tier}" role="dialog" aria-modal="true" aria-labelledby="conqueteTitre">
      <div class="conquete-eclat" aria-hidden="true"></div>
      <p class="conquete-sur">Commune conquise</p>
      <h2 id="conqueteTitre">${echapperTexte(nom)}</h2>
      <p class="conquete-infos"><span class="conquete-rarete">${t ? t.label : ''}</span>${dept ? ` ${echapperTexte(DEPT_NAMES[dept] || '')} (${dept})` : ''}</p>
      <p class="conquete-bonus">+${Number(bonus).toLocaleString('fr-FR')} pts de bonus</p>
      <p class="conquete-note">Elle t'appartient maintenant et elle est protégée pendant 3 h. Revente au jeu possible dans 12 h.</p>
      <button class="open-btn" data-fermer>Génial !</button>
    </div>`);
  const btn = document.querySelector('#fenetre [data-fermer]');
  btn.addEventListener('click', () => fermer(true));
  btn.focus();
}

function demanderPrix({ nom, rachat }){
  return new Promise((resolve) => {
    const fermer = ouvrirFenetre(`
      <form class="fenetre prix" role="dialog" aria-modal="true" aria-labelledby="prixTitre" novalidate>
        <h2 id="prixTitre">Mettre en vente</h2>
        <p class="prix-commune">${echapperTexte(nom)}</p>
        <label class="prix-champ">
          <span>Ton prix</span>
          <span class="prix-saisie"><input type="number" inputmode="numeric" min="1" step="1" id="prixValeur" required><em>pts</em></span>
        </label>
        <p class="prix-aide">Le jeu te la rachète ${Number(rachat).toLocaleString('fr-FR')} pts si tu préfères vendre tout de suite.</p>
        <p class="prix-erreur" id="prixErreur" role="alert"></p>
        <div class="prix-boutons">
          <button type="button" class="open-btn secondary" data-annuler>Annuler</button>
          <button type="submit" class="open-btn">Mettre en vente</button>
        </div>
      </form>`, resolve);
    const form = document.querySelector('#fenetre form');
    const champ = document.getElementById('prixValeur');
    form.querySelector('[data-annuler]').addEventListener('click', () => fermer(null));
    form.addEventListener('submit', (e) => {
      e.preventDefault();
      const prix = parseInt(champ.value, 10);
      if(!prix || prix <= 0){
        document.getElementById('prixErreur').textContent = 'Indique un prix supérieur à 0.';
        champ.focus();
        return;
      }
      fermer(prix);
    });
    champ.focus();
  });
}

// ---------- Authentification ----------
function showAuth(msg, type = 'erreur'){
  document.getElementById('authScreen').style.display = 'flex';
  dessinerEventailAuth();
  document.getElementById('gameScreen').style.display = 'none';
  const el = document.getElementById('authMsg');
  el.textContent = msg ? messageLisible(msg) : '';
  el.className = 'auth-msg' + (msg ? ' ' + type : '');
}

async function showGame(session_){
  document.getElementById('authScreen').style.display = 'none';
  document.getElementById('gameScreen').style.display = 'flex';
  document.getElementById('whoami').textContent = session_.user.email;
  await loadOutline();
  await loadMyCollection();
  await loadOthersPossessions();
  await loadPackStatus();
  verifierTiragesEnAttente();
  loadMenaces();
  renderNotifications();
  verifierVersion();
  // arrivee depuis une notification : ?onglet=combat ou ?onglet=tirage
  if(new URLSearchParams(location.search).has('onglet')){
    ouvrirOngletDepuisUrl(location.href);
    history.replaceState(null, '', location.pathname);
  }
  if(!menacesInterval){
    // verifie toutes les minutes si une de mes communes est attaquee (pastille rouge sur l'onglet Combat)
    menacesInterval = setInterval(loadMenaces, 60000);
  }
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
  else { modeAuth('connexion'); showAuth('Compte créé. Tu peux te connecter.', 'succes'); }
});

// Onglets Connexion / Creer un compte
function modeAuth(mode){
  const inscription = mode === 'inscription';
  document.querySelectorAll('.auth-onglets button').forEach(b => {
    const actif = b.dataset.mode === mode;
    b.classList.toggle('actif', actif);
    b.setAttribute('aria-selected', String(actif));
  });
  document.getElementById('authChampPseudo').hidden = !inscription;
  document.getElementById('loginBtn').hidden = inscription;
  document.getElementById('signupBtn').hidden = !inscription;
  document.getElementById('authPassword').setAttribute('autocomplete', inscription ? 'new-password' : 'current-password');
  const msg = document.getElementById('authMsg');
  msg.textContent = ''; msg.className = 'auth-msg';
}
document.querySelectorAll('.auth-onglets button').forEach(b => b.addEventListener('click', () => modeAuth(b.dataset.mode)));
['authEmail', 'authPassword', 'authPseudo'].forEach(id => document.getElementById(id).addEventListener('keydown', (e) => {
  if(e.key !== 'Enter') return;
  const visible = document.getElementById('loginBtn').hidden ? 'signupBtn' : 'loginBtn';
  document.getElementById(visible).click();
}));
function dessinerEventailAuth(){
  const el = document.getElementById('authEventail');
  if(!el || el.childElementCount) return;
  const exemples = [['c1', '14333', 'Honfleur', 'Calvados (14)', 'peucommun', 'Peu commun'], ['c2', '68066', 'Colmar', 'Haut-Rhin (68)', 'rare', 'Rare'], ['c3', '33063', 'Bordeaux', 'Gironde (33)', 'legendaire', 'Légendaire']];
  el.innerHTML = exemples.map(([cls, code, nom, dep, tier, lab]) => `
    <div class="auth-carte ${cls} ${tier}"><div class="auth-carte-int">
      <span class="auth-carte-badge">${lab}</span>
      <div class="auth-carte-art">${miniArtSvg('auth' + code, tier)}</div>
      <p class="auth-carte-nom">${nom}</p><p class="auth-carte-dep">${dep}</p>
      <div class="mini-lisere"><span></span><span></span><span></span></div>
    </div></div>`).join('');
}

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
  MAP_W = 1000;
  MAP_H = Math.round(1000 / ratio);
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
  const svg = document.getElementById('mapFranceSvg');
  if(!svg || !mapBounds) return;
  svg.setAttribute('viewBox', `0 0 ${MAP_W} ${MAP_H}`);
  const contour = FRANCE_OUTLINE.map(ring => 'M' + ring.map(([lon, lat]) => {
    const p = project(lat, lon);
    return (p.x * MAP_W).toFixed(1) + ',' + (p.y * MAP_H).toFixed(1);
  }).join('L') + 'Z').join('');
  document.getElementById('clipTerrePath').setAttribute('d', contour);
  document.getElementById('mapTerre').setAttribute('d', contour);
  document.getElementById('mapOmbre').setAttribute('d', contour);
  document.getElementById('mapOmbre2').setAttribute('d', contour);
  document.getElementById('mapCote').setAttribute('d', contour);
  const mer = document.getElementById('mapMer');
  mer.setAttribute('width', MAP_W);
  mer.setAttribute('height', MAP_H);
  document.getElementById('mapTopo').setAttribute('d', lignesDeNiveau(4217, MAP_W, MAP_H, 11, 9));
  setupMapInteraction();
  renderMapOverlay();
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

// Les gestes envoient souvent plus d'evenements que l'ecran n'affiche d'images :
// on calcule tout de suite, mais on n'ecrit dans la page qu'une fois par image.
let mapTransformPlanifie = false;
let mapFinMouvementTimer = null;
function applyMapTransform(){
  clampMapPan();
  signalerMouvementCarte();
  if(mapTransformPlanifie) return;
  mapTransformPlanifie = true;
  requestAnimationFrame(() => {
    mapTransformPlanifie = false;
    const el = document.getElementById('mapTransform');
    if(el) el.style.transform = `translate3d(${mapPanX}px, ${mapPanY}px, 0) scale(${mapZoom})`;
  });
}

// Pendant un geste, la carte est deplacee comme une image deja dessinee (fluide).
// 200 ms apres le dernier mouvement, le navigateur la redessine nette au bon zoom.
function signalerMouvementCarte(){
  const wrap = document.getElementById('mapWrap');
  if(!wrap) return;
  wrap.classList.add('en-mouvement');
  clearTimeout(mapFinMouvementTimer);
  mapFinMouvementTimer = setTimeout(() => wrap.classList.remove('en-mouvement'), 200);
}

// Zoome en gardant fixe le point (px, py) du cadre : le curseur ou le centre des deux doigts
// vrai quand le changement de zoom fait apparaitre ou disparaitre des communes
function franchitUnSeuil(avant, apres){
  return Object.values(ZOOM_MINI).some(s => (avant < s) !== (apres < s));
}

function zoomMapAt(newZoom, px, py){
  newZoom = Math.min(MAP_ZOOM_MAX, Math.max(MAP_ZOOM_MIN, newZoom));
  if(franchitUnSeuil(mapZoom, newZoom)) setTimeout(renderMapOverlay, 0);
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
      if(franchitUnSeuil(mapZoom, newZoom)) setTimeout(renderMapOverlay, 0);
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

// ---------- Territoires sur la carte ----------
const RAYON_ZONE = {commun: 4.5, peucommun: 6.5, rare: 10, legendaire: 15};
// De loin, les petites communes des autres joueurs ne sont que du bruit : on les revele en zoomant.
const ZOOM_MINI = {commun: 2.6, peucommun: 1.8, rare: 1, legendaire: 1};
const MASQUEES_PAR_ZOOM = {commun: 0, peucommun: 0};
const LIBELLE_TIER = {commun: 'commun', peucommun: 'peu commun', rare: 'rare', legendaire: 'légendaire'};
const ID_MOI = '__moi__';
let joueurSurligne = null;
let listeJoueursComplete = false;
let legendeOuverte = (() => {
  try{
    const v = localStorage.getItem('tf-legende-ouverte');
    if(v !== null) return v === '1';
  } catch(e){}
  return !window.matchMedia('(max-width: 720px)').matches;
})();

function etoileSvg(x, y, r){
  const pts = [];
  for(let i = 0; i < 10; i++){
    const a = -Math.PI / 2 + i * Math.PI / 5, rr = i % 2 ? r * 0.45 : r;
    pts.push((x + rr * Math.cos(a)).toFixed(1) + ',' + (y + rr * Math.sin(a)).toFixed(1));
  }
  return pts.join(' ');
}
const echapperHtml = (s) => String(s).replace(/[&<>"]/g, ch => ({'&':'&amp;', '<':'&lt;', '>':'&gt;', '"':'&quot;'}[ch]));

let carteRenduPlanifie = false;
function renderMapOverlay(){
  // plusieurs appels rapproches (cartes retournees une par une) = un seul dessin
  if(carteRenduPlanifie) return;
  carteRenduPlanifie = true;
  requestAnimationFrame(() => { carteRenduPlanifie = false; dessinerTerritoires(); });
}

function dessinerTerritoires(){
  const couche = document.getElementById('mapTerritoires');
  const defs = document.getElementById('mapDefsDyn');
  const marq = document.getElementById('mapMarqueurs');
  const survol = document.getElementById('mapSurvol');
  if(!couche || !defs || !mapBounds) return;

  // joueurs presents : toi d'abord, puis les autres
  const joueurs = new Map();
  joueurs.set(ID_MOI, { id: ID_MOI, pseudo: 'Toi', couleur: COULEUR_MOI, fonce: couleurFoncee(COULEUR_MOI), moi: true, nb: 0 });
  const liste = [];
  for(const e of collectionMap.values()){
    if(!METRO_DEPT_RE.test(e.dept) || e.lat == null) continue;
    liste.push({ nom: e.nom, dept: e.dept, lat: e.lat, lon: e.lon, tier: e.tier.id, joueur: ID_MOI });
    joueurs.get(ID_MOI).nb++;
  }
  MASQUEES_PAR_ZOOM.commun = 0;
  MASQUEES_PAR_ZOOM.peucommun = 0;
  for(const e of othersMap.values()){
    if(!METRO_DEPT_RE.test(e.dept) || e.lat == null) continue;
    const visibleAuZoom = mapZoom >= (ZOOM_MINI[e.tier.id] || 1);
    if(showOthers && !visibleAuZoom && MASQUEES_PAR_ZOOM[e.tier.id] !== undefined) MASQUEES_PAR_ZOOM[e.tier.id]++;
    if(!joueurs.has(e.joueurId)){
      const couleur = colorForPlayer(e.joueurId);
      joueurs.set(e.joueurId, { id: e.joueurId, pseudo: e.pseudo, couleur, fonce: couleurFoncee(couleur), moi: false, nb: 0 });
    }
    joueurs.get(e.joueurId).nb++;
    if(showOthers && visibleAuZoom) liste.push({ nom: e.nom, dept: e.dept, lat: e.lat, lon: e.lon, tier: e.tier.id, joueur: e.joueurId });
  }

  const pts = liste.map(c => { const p = project(c.lat, c.lon); return [p.x * MAP_W, p.y * MAP_H]; });
  const parJoueur = new Map();
  const groupe = (id) => parJoueur.get(id) || parJoueur.set(id, { cercles: '', bords: '', cellules: '', marqueurs: '' }).get(id);
  let zonesSurvol = '';

  let voronoi = null, rayons = liste.map(c => RAYON_ZONE[c.tier]);
  if(D3_OK && liste.length > 0){
    const delaunay = d3.Delaunay.from(pts);
    voronoi = delaunay.voronoi([0, 0, MAP_W, MAP_H]);
    // une zone grandit jusqu'a ses voisines proches du meme joueur, pour former un territoire plein
    rayons = liste.map((c, i) => {
      let dMin = Infinity;
      for(const k of delaunay.neighbors(i)){
        if(!liste[k] || k === i || liste[k].joueur !== c.joueur) continue;
        dMin = Math.min(dMin, Math.hypot(pts[k][0] - pts[i][0], pts[k][1] - pts[i][1]));
      }
      return dMin <= 22 ? Math.max(RAYON_ZONE[c.tier], dMin * 0.62) : RAYON_ZONE[c.tier];
    });
  }

  liste.forEach((c, i) => {
    const [x, y] = pts[i];
    const r = rayons[i];
    const j = joueurs.get(c.joueur);
    const g = groupe(c.joueur);
    const cx = x.toFixed(1), cy = y.toFixed(1);
    g.cercles += `<circle cx="${cx}" cy="${cy}" r="${r.toFixed(1)}"/>`;
    g.bords += `<circle cx="${cx}" cy="${cy}" r="${(r + (j.moi ? 2.2 : 1.1)).toFixed(1)}"/>`;
    // deux communes aux memes coordonnees n'ont pas de cellule : on dessine alors un simple rond
    const cellule = voronoi ? voronoi.renderCell(i) : '';
    g.cellules += cellule ? `<path d="${cellule}"/>` : `<circle cx="${cx}" cy="${cy}" r="${r.toFixed(1)}"/>`;
    if(c.tier === 'legendaire'){
      g.marqueurs += `<polygon points="${etoileSvg(x, y, j.moi ? 7 : 6)}" fill="${j.moi ? '#FFF6D6' : 'rgba(255,246,214,0.75)'}" stroke="#0B1830" stroke-width="${j.moi ? 1.4 : 1}" stroke-opacity="${j.moi ? 1 : 0.5}" vector-effect="non-scaling-stroke"/>`;
    } else if(c.tier === 'rare'){
      g.marqueurs += `<circle cx="${cx}" cy="${cy}" r="2.2" fill="${j.moi ? '#fff' : 'rgba(255,255,255,0.7)'}" stroke="#0B1830" stroke-width="1" stroke-opacity="${j.moi ? 1 : 0.45}" vector-effect="non-scaling-stroke"/>`;
    }
    zonesSurvol += `<circle cx="${cx}" cy="${cy}" r="${Math.max(RAYON_ZONE[c.tier], 6)}" fill="transparent"><title>${echapperHtml(c.nom)} (${c.dept}), ${LIBELLE_TIER[c.tier]}, ${j.moi ? 'à toi' : 'à ' + echapperHtml(j.pseudo)}</title></circle>`;
  });

  // les autres joueurs d'abord, toi par-dessus
  const ordre = [...parJoueur.keys()].sort((a, b) => (a === ID_MOI ? 1 : 0) - (b === ID_MOI ? 1 : 0));
  const idSvg = (id) => 'j' + String(id).replace(/[^a-zA-Z0-9_-]/g, '');
  defs.innerHTML = ordre.map(id => `<clipPath id="zone-${idSvg(id)}">${parJoueur.get(id).cercles}</clipPath><clipPath id="bord-${idSvg(id)}">${parJoueur.get(id).bords}</clipPath>`).join('');
  couche.innerHTML =
    ordre.map(id => `<g data-joueur="${idSvg(id)}" clip-path="url(#bord-${idSvg(id)})"><g fill="#07111F" fill-opacity="${joueurs.get(id).moi ? 0.9 : 0.55}">${parJoueur.get(id).cellules}</g></g>`).join('') +
    ordre.map(id => {
      const j = joueurs.get(id);
      // les autres joueurs : plus transparents et sans lignes internes, pour ne pas saturer la carte
      return j.moi
        ? `<g data-joueur="${idSvg(id)}" clip-path="url(#zone-${idSvg(id)})"><g fill="${j.couleur}" fill-opacity="0.95" stroke="${j.fonce}" stroke-opacity="0.6" stroke-width="0.7" vector-effect="non-scaling-stroke">${parJoueur.get(id).cellules}</g></g>`
        : `<g data-joueur="${idSvg(id)}" clip-path="url(#zone-${idSvg(id)})"><g fill="${j.couleur}" fill-opacity="0.62" stroke="${j.fonce}" stroke-opacity="0.25" stroke-width="0.5" vector-effect="non-scaling-stroke">${parJoueur.get(id).cellules}</g></g>`;
    }).join('');
  marq.innerHTML = ordre.map(id => `<g data-joueur="${idSvg(id)}">${parJoueur.get(id).marqueurs}</g>`).join('');
  survol.innerHTML = zonesSurvol;

  if(joueurSurligne && !joueurs.has(joueurSurligne)) joueurSurligne = null;
  if(!showOthers && joueurSurligne !== ID_MOI) joueurSurligne = null;
  appliquerSurlignageCarte(idSvg);
  renderLegendeCarte(joueurs, idSvg);
}

function appliquerSurlignageCarte(idSvg){
  const svg = document.getElementById('mapFranceSvg');
  if(!svg) return;
  const cible = joueurSurligne ? idSvg(joueurSurligne) : null;
  svg.classList.toggle('surlignage', !!cible);
  svg.querySelectorAll('g[data-joueur]').forEach(g => g.classList.toggle('actif', g.dataset.joueur === cible));
}

function renderLegendeCarte(joueurs, idSvg){
  const leg = document.getElementById('mapLegende');
  if(!leg) return;
  const moi = joueurs.get(ID_MOI);
  const autres = [...joueurs.values()].filter(j => !j.moi && j.nb > 0).sort((a, b) => b.nb - a.nb);
  const NB_VISIBLES = 5;
  const affiches = showOthers ? (listeJoueursComplete ? autres : autres.slice(0, NB_VISIBLES)) : [];
  const reste = showOthers ? autres.length - affiches.length : 0;
  const ligne = (j) => `<button class="leg-joueur ${joueurSurligne === j.id ? 'actif' : ''}" data-joueur-id="${echapperHtml(j.id)}" aria-pressed="${joueurSurligne === j.id}">
      <span class="leg-pastille" style="background:${j.couleur}"></span>
      <span class="leg-pseudo">${j.moi ? '<b>Toi</b>' : echapperHtml(j.pseudo)}</span><span class="leg-nb">${j.nb.toLocaleString('fr-FR')}</span></button>`;
  leg.classList.toggle('repliee', !legendeOuverte);
  leg.innerHTML = `
    <div class="leg-tete">
      <h3>${legendeOuverte ? 'Joueurs' : 'Légende'}</h3>
      <button class="leg-bouton" data-leg="basculer" aria-expanded="${legendeOuverte}" aria-label="${legendeOuverte ? 'Replier la légende' : 'Afficher la légende'}">
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"><path d="M18 15l-6-6-6 6"/></svg>
      </button>
    </div>
    <div class="leg-corps">
      ${ligne(moi)}
      ${affiches.map(ligne).join('')}
      ${reste > 0 ? `<button class="leg-plus" data-leg="plus">+ ${reste} autre${reste > 1 ? 's' : ''} joueur${reste > 1 ? 's' : ''}</button>` : ''}
      ${listeJoueursComplete && autres.length > NB_VISIBLES && showOthers ? '<button class="leg-plus" data-leg="moins">Réduire la liste</button>' : ''}
      ${(() => {
        const n = MASQUEES_PAR_ZOOM.commun + MASQUEES_PAR_ZOOM.peucommun;
        return n > 0 ? `<p class="leg-indice leg-zoom">${n.toLocaleString('fr-FR')} petite${n > 1 ? 's' : ''} commune${n > 1 ? 's' : ''} masquée${n > 1 ? 's' : ''} : zoome pour les voir.</p>` : '';
      })()}
      <p class="leg-indice">Clique sur un joueur pour mettre son territoire en évidence.</p>
      <div class="leg-tailles">
        <div><svg width="10" height="10"><circle cx="5" cy="5" r="2.5" fill="#A9BCD4"/></svg>Commun</div>
        <div><svg width="14" height="14"><circle cx="7" cy="7" r="4" fill="#A9BCD4"/></svg>Peu c.</div>
        <div><svg width="20" height="20"><circle cx="10" cy="10" r="6.5" fill="#A9BCD4"/><circle cx="10" cy="10" r="2" fill="#fff" stroke="#0B1830"/></svg>Rare</div>
        <div><svg width="26" height="26"><circle cx="13" cy="13" r="10" fill="#A9BCD4"/><polygon points="${etoileSvg(13, 13, 6)}" fill="#FFF6D6" stroke="#0B1830"/></svg>Légend.</div>
      </div>
    </div>`;
}

(function brancherLegende(){
  const leg = document.getElementById('mapLegende');
  if(!leg) return;
  leg.addEventListener('click', (e) => {
    const action = e.target.closest('[data-leg]');
    if(action){
      if(action.dataset.leg === 'basculer'){
        legendeOuverte = !legendeOuverte;
        try{ localStorage.setItem('tf-legende-ouverte', legendeOuverte ? '1' : '0'); } catch(err){}
      }
      if(action.dataset.leg === 'plus') listeJoueursComplete = true;
      if(action.dataset.leg === 'moins') listeJoueursComplete = false;
      renderMapOverlay();
      return;
    }
    const ligne = e.target.closest('.leg-joueur');
    if(ligne){
      joueurSurligne = joueurSurligne === ligne.dataset.joueurId ? null : ligne.dataset.joueurId;
      renderMapOverlay();
    }
  });
  // la legende ne doit pas deplacer ni zoomer la carte en dessous
  ['mousedown', 'touchstart', 'wheel'].forEach(ev => leg.addEventListener(ev, (e) => e.stopPropagation(), { passive: true }));
})();

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
  const champsCommune = 'communes(code,nom,departement,population,latitude,longitude,tier,rang,palier_total)';
  // du plus complet au plus simple : si un fichier SQL n'a pas encore ete execute, le site se charge quand meme
  const variantes = [
    'commune_code, acquired_at, bouclier_debut, bouclier_jusqua, conquise_le, ',
    'commune_code, acquired_at, bouclier_debut, bouclier_jusqua, ',
    'commune_code, acquired_at, ',
  ];
  let data = null, error = null;
  for(const champs of variantes){
    ({ data, error } = await sb.from('possessions').select(champs + champsCommune).eq('joueur_id', uid));
    if(!error) break;
  }
  if(error){ console.error(error); return; }

  collectionMap = new Map();
  session = {commun:0, peucommun:0, rare:0, legendaire:0, total:0};
  for(const row of data){
    const c = row.communes;
    const tier = TIERS.find(t => t.id === c.tier);
    collectionMap.set(c.code, {
      code: c.code, nom: c.nom, dept: c.departement, pop: c.population,
      lat: c.latitude, lon: c.longitude, tier, rank: c.rang, tierSize: c.palier_total,
      acquiredAt: row.acquired_at ? new Date(row.acquired_at).getTime() : 0,
      bouclierDebut: row.bouclier_debut ? new Date(row.bouclier_debut).getTime() : 0,
      bouclierJusqua: row.bouclier_jusqua ? new Date(row.bouclier_jusqua).getTime() : 0,
      conquiseLe: row.conquise_le ? new Date(row.conquise_le).getTime() : 0
    });
    session[c.tier]++;
    session.total++;
  }
  renderStats();
  renderCollection();
  renderMapOverlay();
  if(document.getElementById('sellableGrid')) renderSellableGrid();
  if(document.getElementById('boucliersGrid')) renderBoucliers();
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

// ---------- Page Ma collection ----------
let collectionFilterTier = 'tous';
const miniArtCache = new Map();

function miniArtSvg(code, tierId){
  const cle = code + '|' + tierId;
  if(miniArtCache.has(cle)) return miniArtCache.get(cle);
  const [clair, fonce] = TEINTES_CARTE[tierId];
  const id = 'mg' + code;
  const { d, cx, cy } = courbesDeNiveau(hashTexte(String(code)), 160, 100, 6, 36);
  const svg = `<svg viewBox="0 0 160 100" preserveAspectRatio="xMidYMid slice" aria-hidden="true">
    <defs><radialGradient id="${id}" cx="${(cx / 160 * 100).toFixed(0)}%" cy="${cy.toFixed(0)}%" r="85%">
      <stop offset="0%" stop-color="${clair}"/><stop offset="100%" stop-color="${fonce}"/></radialGradient></defs>
    <rect width="160" height="100" fill="url(#${id})"/>
    <path d="${d}" fill="none" stroke="rgba(255,255,255,0.38)" stroke-width="1.2"/>
    <circle cx="${cx.toFixed(1)}" cy="${cy.toFixed(1)}" r="4.5" fill="#fff" stroke="${fonce}" stroke-width="2"/>
  </svg>`;
  miniArtCache.set(cle, svg);
  return svg;
}

function renderCollectionFilters(entries){
  const el = document.getElementById('collectionFilters');
  if(!el) return;
  const compte = Object.fromEntries(TIERS.map(t => [t.id, 0]));
  entries.forEach(e => compte[e.tier.id]++);
  const boutons = [`<button class="coll-filtre ${collectionFilterTier === 'tous' ? 'actif' : ''}" data-tier="tous">Toutes <span class="nb">${entries.length}</span></button>`]
    .concat(TIERS.map(t => `<button class="coll-filtre ${collectionFilterTier === t.id ? 'actif' : ''}" data-tier="${t.id}"><span class="point" style="background:${COULEURS_FILTRE[t.id]}"></span>${t.label} <span class="nb">${compte[t.id]}</span></button>`));
  el.innerHTML = boutons.join('');
}
const COULEURS_FILTRE = {legendaire:'#F0B429', rare:'#2F7CF6', peucommun:'#22A06B', commun:'#7E8BA0'};

function renderCollection(){
  const countEl = document.getElementById('collectionCount');
  const gridEl = document.getElementById('collectionGrid');
  const entries = Array.from(collectionMap.values());
  countEl.textContent = entries.length.toLocaleString('fr-FR');
  renderCollectionFilters(entries);
  if(entries.length === 0){
    gridEl.innerHTML = '<p class="collection-empty">Aucune carte pour le moment. Ouvre un paquet.</p>';
    return;
  }
  const visibles = entries
    .filter(e => collectionFilterTier === 'tous' || e.tier.id === collectionFilterTier)
    .sort((a,b) => {
      const ra = TIERS.indexOf(a.tier), rb = TIERS.indexOf(b.tier);
      if(ra !== rb) return ra - rb;
      return b.pop - a.pop;
    });
  if(visibles.length === 0){
    gridEl.innerHTML = '<p class="collection-empty">Aucune carte de cette rareté pour le moment.</p>';
    return;
  }
  gridEl.innerHTML = visibles.map(entry => `
    <div class="mini ${entry.tier.id}" title="${echapperTexte(entry.nom)} (${entry.dept}) — ${entry.tier.label}">
      <div class="mini-int">
        <div class="mini-art">${miniArtSvg(entry.code, entry.tier.id)}<span class="mini-dept">${entry.dept}</span>${entry.bouclierJusqua > Date.now() ? `<span class="mini-bouclier" title="Protégée par un bouclier">${ICONE_BOUCLIER}</span>` : ''}</div>
        <div class="mini-infos">
          <p class="mini-nom ${entry.nom.length > 14 ? 'long' : ''}">${entry.nom}</p>
          ${entry.rank ? `<span class="mini-num">n° ${Number(entry.rank).toLocaleString('fr-FR')}<span class="mini-total"> / ${Number(entry.tierSize).toLocaleString('fr-FR')}</span></span>` : ''}
          <span class="mini-rarete">${entry.tier.label}</span>
        </div>
        <div class="mini-lisere"><span></span><span></span><span></span></div>
      </div>
    </div>
  `).join('');
}

document.getElementById('collectionFilters').addEventListener('click', (e) => {
  const b = e.target.closest('.coll-filtre');
  if(!b) return;
  collectionFilterTier = b.dataset.tier;
  renderCollection();
});

// ---------- Cartes et paquet ----------
function makeCardEl(draw, onFlip){
  const wrap = document.createElement('div');
  wrap.className = 'card ' + draw.tier.id;
  wrap.innerHTML = `
    <div class="card-inner">
      <div class="face face-back">
        ${DOS_MOTIF_SVG}
        <span class="dos-coin hg"></span><span class="dos-coin hd"></span><span class="dos-coin bg"></span><span class="dos-coin bd"></span>
        <div class="dos-embleme">${ICONE_EPINGLE}</div>
      </div>
      <div class="face face-front">
        <div class="carte-cadre">
          <div class="carte-int">
            <div class="carte-haut">
              <span class="carte-rarete">${draw.tier.label}</span>
              <span class="carte-num">${draw.rank.toLocaleString('fr-FR')} / ${draw.tierSize.toLocaleString('fr-FR')}</span>
            </div>
            <div class="carte-art">${carteArtSvg(draw.code, draw.tier.id)}<span class="carte-dept">${draw.dept}</span></div>
            <div class="carte-infos">
              <p class="carte-nom ${draw.nom.length > 26 ? 'tres-long' : draw.nom.length > 16 ? 'long' : ''}" title="${echapperTexte(draw.nom)}">${draw.nom}</p>
              <p class="carte-departement">${DEPT_NAMES[draw.dept] ? `<span class="dep-nom">${DEPT_NAMES[draw.dept]}</span> <span class="dep-num">(${draw.dept})</span>` : `<span class="dep-num">${draw.dept}</span>`}</p>
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
let paquetEnCours = false;

function revealCards(draws){
  const zone = document.getElementById('packZone');
  zone.innerHTML = '';
  pendingFlips = draws.length;
  draws.forEach((draw, index) => {
    const carte = makeCardEl(draw, () => {
      collectionMap.set(draw.code, draw);
      session[draw.tier.id]++;
      session.total++;
      renderStats();
      renderCollection();
      renderMapOverlay();
      pendingFlips--;
      if(pendingFlips <= 0){
        paquetEnCours = false;
        loadPackStatus();
        verifierTiragesEnAttente();
      }
    });
    // les cartes arrivent l'une apres l'autre
    carte.classList.add('entree');
    carte.style.animationDelay = (index * 90) + 'ms';
    zone.appendChild(carte);
  });
}

// Paquet bleu pour le gratuit, dore pour celui achete
function makePackEl(type){
  const motif = paquetMotifSvg(type);
  const pack = document.createElement('button');
  pack.className = 'paquet ' + (type === 'achete' ? 'achete' : 'gratuit');
  pack.setAttribute('aria-label', 'Déchirer le paquet');
  pack.innerHTML = `
    <div class="paquet-languette">${motif}<div class="paquet-pointilles"></div></div>
    <div class="paquet-corps">${motif}
      <div class="paquet-etiquette">${ICONE_EPINGLE}<span class="paquet-titre">Paquet</span></div>
      <div class="paquet-bande">5 communes</div>
    </div>`;
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

  // pendant l'ouverture d'un paquet, on ne peut pas en relancer un autre
  document.getElementById('openFreeBtn').disabled = paquetEnCours || dispo < 1;
  document.getElementById('openBuyBtn').disabled = paquetEnCours || achetesJour >= 5 || packStatusCache.solde < 200;
}

// Si securite.sql n'a pas encore ete execute, les nouvelles fonctions n'existent pas : on utilise les anciennes
function fonctionAbsente(error){
  return !!error && (error.code === 'PGRST202' || /could not find the function/i.test(error.message || ''));
}
async function payerPaquet(type){
  let { error } = await sb.rpc('ouvrir_paquet', { p_type: type });
  if(fonctionAbsente(error)) ({ error } = await sb.rpc('demarrer_paquet', { p_type: type }));
  return error;
}
async function tirerUneCarte(){
  let { data, error } = await sb.rpc('tirer_carte', { p_saison: CURRENT_SEASON });
  if(fonctionAbsente(error)){
    ({ data, error } = await sb.rpc('draw_commune', { p_saison: CURRENT_SEASON }));
    if(!error) data = data && data[0];
  }
  return { row: data, error };
}

async function openPack(type){
  document.getElementById('openFreeBtn').disabled = true;
  document.getElementById('openBuyBtn').disabled = true;

  const startError = await payerPaquet(type);
  if(startError){
    notifier({ type: 'erreur', titre: 'Impossible d\'ouvrir le paquet', texte: messageLisible(startError.message) });
    await loadPackStatus();
    return;
  }
  // le paquet en cours n'est pas encore ouvert : pas question d'en relancer un avant d'avoir retourne les cartes
  paquetEnCours = true;
  await loadPackStatus();
  afficherPaquetATirer(type, 5);
}

function afficherPaquetATirer(type, nbCartes){
  const zone = document.getElementById('packZone');
  zone.innerHTML = '';
  const pack = makePackEl(type);
  zone.appendChild(pack);

  pack.addEventListener('click', async () => {
    pack.classList.add('dechire');
    // le tirage part tout de suite, pendant l'animation, pour ne pas attendre une fois le paquet disparu
    const animation = new Promise(resolve => setTimeout(resolve, REDUCED_MOTION ? 0 : 720));
    const draws = [];
    for(let i = 0; i < nbCartes; i++){
      const { row, error } = await tirerUneCarte();
      if(error || !row){
        if(error) notifier({ type: 'erreur', titre: 'Tirage interrompu', texte: messageLisible(error.message) });
        break;
      }
      const tier = TIERS.find(t => t.id === row.tier);
      draws.push({
        code: row.code, nom: row.nom, dept: row.departement, pop: row.population,
        lat: row.latitude, lon: row.longitude, tier, rank: row.rang, tierSize: row.palier_total
      });
    }
    await animation;
    if(draws.length === 0){
      zone.innerHTML = '';
      paquetEnCours = false;
      loadPackStatus();
      return;
    }
    revealCards(draws);
  }, { once: true });
}

// Paquet paye mais pas encore ouvert (page fermee ou rechargee) : on le represente
async function verifierTiragesEnAttente(){
  if(paquetEnCours) return;
  const { data: u } = await sb.auth.getUser();
  if(!u || !u.user) return;
  const { data, error } = await sb.from('joueurs').select('tirages_restants').eq('id', u.user.id).single();
  if(error || !data || !(data.tirages_restants > 0)) return;
  paquetEnCours = true;
  renderPackStatus();
  afficherPaquetATirer('gratuit', Math.min(5, data.tirages_restants));
  notifier({ type: 'info', titre: 'Tu as un paquet non ouvert', texte: 'Clique dessus dans l\'onglet Tirage pour le déchirer.' });
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
  soldeBourse = joueurRow ? joueurRow.solde : null;
  renderBoucliers();

  const { data: mine } = await sb.from('annonces').select('commune_code, prix').eq('joueur_id', uid);
  myListings = new Map((mine || []).map(a => [a.commune_code, a.prix]));

  renderSellableGrid();

  const { data: market } = await sb
    .from('annonces')
    .select('commune_code, prix, joueur_id, communes(nom,departement,tier), joueurs(pseudo)');
  renderMarketGrid(market || [], uid);
}

// ---------- Boucliers de protection ----------
const ICONE_BOUCLIER = '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linejoin="round" aria-hidden="true"><path d="M12 3l7.5 3v5.5c0 4.6-3.2 8.3-7.5 9.5-4.3-1.2-7.5-4.9-7.5-9.5V6z"/></svg>';
// doit rester aligne avec prix_bouclier() dans boucliers.sql
const OFFRES_BOUCLIER = [
  { id: '3h', label: '3 heures', ms: 3 * 3600e3, prix: { rare: 15, legendaire: 150 } },
  { id: '6h', label: '6 heures', ms: 6 * 3600e3, prix: { rare: 40, legendaire: 400 } },
  { id: '12h', label: '12 heures', ms: 12 * 3600e3, prix: { rare: 90, legendaire: 900 } },
];
const DELAI_ENTRE_BOUCLIERS_MS = 12 * 3600e3;
// doivent rester alignes avec defense_equilibrage.sql
const REVENTE_BLOQUEE_MS = 12 * 3600e3;
const BONUS_CONQUETE_PART = 0.5;
let soldeBourse = null;
let boucliersTout = false;

// etat d'une de mes communes vis-a-vis des boucliers
function etatBouclier(entry, now = Date.now()){
  if(entry.bouclierJusqua > now){
    if(entry.bouclierDebut > now) return { code: 'programme', texte: `Bouclier programmé : démarre dans ${formatDuree(entry.bouclierDebut - now)}`, achetable: false };
    return { code: 'actif', texte: `Protégée par un bouclier encore ${formatDuree(entry.bouclierJusqua - now)}`, achetable: false };
  }
  if(entry.bouclierJusqua && entry.bouclierJusqua + DELAI_ENTRE_BOUCLIERS_MS > now){
    return { code: 'recharge', texte: `Nouveau bouclier possible dans ${formatDuree(entry.bouclierJusqua + DELAI_ENTRE_BOUCLIERS_MS - now)}`, achetable: false };
  }
  if(entry.acquiredAt && entry.acquiredAt + IMMUNITE_MS > now){
    return { code: 'immunite', texte: `Acquise récemment, protégée encore ${formatDuree(entry.acquiredAt + IMMUNITE_MS - now)}`, achetable: true };
  }
  return { code: 'libre', texte: 'Sans protection', achetable: true };
}

function renderBoucliers(){
  const grid = document.getElementById('boucliersGrid');
  if(!grid) return;
  const now = Date.now();
  const toutes = Array.from(collectionMap.values())
    .filter(e => e.tier.id === 'rare' || e.tier.id === 'legendaire')
    .sort((a, b) => TIERS.indexOf(a.tier) - TIERS.indexOf(b.tier) || b.pop - a.pop);
  if(toutes.length === 0){
    grid.innerHTML = '<p class="collection-empty">Tu n\'as aucune commune rare ou légendaire à protéger.</p>';
    return;
  }
  // par defaut : celles qu'on attaque en ce moment, ou qui sont attaquables tout de suite
  const attaquees = new Set(menaces.filter(m => m.victoires_consecutives > 0).map(m => m.commune_code));
  const protegeables = boucliersTout
    ? toutes
    : toutes.filter(e => attaquees.has(e.code) || ['libre', 'recharge'].includes(etatBouclier(e, now).code));
  const bouton = document.getElementById('boucliersToutToggle');
  if(bouton){
    const masquees = toutes.length - protegeables.length;
    bouton.hidden = boucliersTout ? false : masquees === 0;
    bouton.querySelector('.compte-masquees')?.remove();
    if(!boucliersTout && masquees > 0){
      bouton.insertAdjacentHTML('beforeend', `<span class="en-cours-nb compte-masquees">+${masquees}</span>`);
    }
  }
  if(protegeables.length === 0){
    grid.innerHTML = '<p class="collection-empty">Aucune de tes communes n\'a besoin d\'un bouclier pour le moment.</p>';
    return;
  }
  grid.innerHTML = protegeables.map(e => {
    const etat = etatBouclier(e, now);
    const bouton = etat.achetable
      ? `<div class="ligne-actions"><button class="btn-p or" data-action="bouclier" data-code="${e.code}">Protéger</button></div>`
      : '';
    return `
      <div class="ligne ${e.tier.id}">
        <div class="ligne-texte">
          <span class="ligne-nom">${e.nom}</span>
          <span class="ligne-etat ${etat.code === 'actif' || etat.code === 'programme' ? 'bleu' : ''}">${etat.code === 'actif' || etat.code === 'programme' ? ICONE_BOUCLIER : ''}${etat.texte}</span>
        </div>
        ${bouton}
      </div>`;
  }).join('');
}

function choisirBouclier(entry){
  return new Promise((resolve) => {
    const tier = entry.tier.id;
    const solde = soldeBourse ?? (packStatusCache ? packStatusCache.solde : null);
    const etat = etatBouclier(entry);
    const options = OFFRES_BOUCLIER.map((o, i) => {
      const prix = o.prix[tier];
      const tropCher = solde !== null && solde < prix;
      return `
        <label class="offre ${tropCher ? 'indisponible' : ''}">
          <input type="radio" name="offre" value="${o.id}" ${tropCher ? 'disabled' : ''} ${i === 1 && !tropCher ? 'checked' : ''}>
          <span class="offre-duree">${o.label}</span>
          <span class="offre-prix">${prix.toLocaleString('fr-FR')} pts</span>
          ${tropCher ? '<span class="offre-note">Solde insuffisant</span>' : ''}
        </label>`;
    }).join('');
    const fermer = ouvrirFenetre(`
      <form class="fenetre prix bouclier-fenetre" role="dialog" aria-modal="true" aria-labelledby="bouclierTitre" novalidate>
        <h2 id="bouclierTitre"><span class="bouclier-titre-icone">${ICONE_BOUCLIER}</span>Bouclier</h2>
        <p class="prix-commune">${echapperTexte(entry.nom)}, ${entry.tier.label.toLowerCase()}</p>
        <div class="offres">${options}</div>
        ${etat.code === 'immunite' ? `<p class="prix-aide">Cette commune est encore protégée ${formatDuree(entry.acquiredAt + IMMUNITE_MS - Date.now())} grâce à son acquisition récente : le bouclier démarrera juste après.</p>` : ''}
        <p class="prix-aide">${solde !== null ? `Ton solde : ${Number(solde).toLocaleString('fr-FR')} pts. ` : ''}Après ce bouclier, 12 h sans protection possible.</p>
        <p class="prix-erreur" id="bouclierErreur" role="alert"></p>
        <div class="prix-boutons">
          <button type="button" class="open-btn secondary" data-annuler>Annuler</button>
          <button type="submit" class="open-btn">Activer</button>
        </div>
      </form>`, resolve);
    const form = document.querySelector('#fenetre form');
    form.querySelector('[data-annuler]').addEventListener('click', () => fermer(null));
    form.addEventListener('submit', (e) => {
      e.preventDefault();
      const choix = form.querySelector('input[name="offre"]:checked');
      if(!choix){
        document.getElementById('bouclierErreur').textContent = 'Choisis une durée.';
        return;
      }
      fermer(choix.value);
    });
    const premier = form.querySelector('input[name="offre"]:checked') || form.querySelector('[data-annuler]');
    premier.focus();
  });
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
      ? `<span class="chip-vente">En vente à ${Number(listedPrice).toLocaleString('fr-FR')} pts</span>
         <div class="ligne-actions"><button class="btn-p contour" data-action="retirer" data-code="${entry.code}">Retirer</button></div>`
      : `<div class="ligne-actions">${entry.conquiseLe && entry.conquiseLe + REVENTE_BLOQUEE_MS > Date.now()
            ? `<button class="btn-p contour" disabled title="Commune conquise récemment">Revente au jeu dans ${formatDuree(entry.conquiseLe + REVENTE_BLOQUEE_MS - Date.now())}</button>`
            : `<button class="btn-p contour" data-action="vendre-jeu" data-code="${entry.code}">Vendre au jeu <b>${rachat}</b></button>`}
         <button class="btn-p or" data-action="mettre-vente" data-code="${entry.code}">Mettre en vente</button></div>`;
    return `
      <div class="ligne ${entry.tier.id}">
        <div class="ligne-texte">
          <span class="ligne-nom">${entry.nom}</span>
          <span class="ligne-detail">${DEPT_NAMES[entry.dept] ? DEPT_NAMES[entry.dept] + ' ' : ''}(${entry.dept}), ${entry.tier.label.toLowerCase()}</span>
        </div>
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
    const pseudo = a.joueurs ? a.joueurs.pseudo : 'un joueur';
    const tropCher = !isMine && soldeBourse !== null && soldeBourse < a.prix;
    const action = isMine
      ? `<button class="btn-p contour" data-action="retirer" data-code="${a.commune_code}">Retirer</button>`
      : `<button class="btn-p or" data-action="acheter" data-code="${a.commune_code}" ${tropCher ? 'disabled title="Solde insuffisant"' : ''}>Acheter</button>`;
    const vendeur = isMine
      ? 'ton annonce'
      : `vendue par <i style="background:${colorForPlayer(a.joueur_id)}"></i>${echapperTexte(pseudo)}`;
    return `
      <div class="ligne ${c.tier}">
        <div class="ligne-texte">
          <span class="ligne-nom">${c.nom}</span>
          <span class="ligne-detail">${DEPT_NAMES[c.departement] ? DEPT_NAMES[c.departement] + ' ' : ''}(${c.departement}), ${tier.label.toLowerCase()}, ${vendeur}</span>
        </div>
        <span class="ligne-prix">${Number(a.prix).toLocaleString('fr-FR')}<small>pts</small></span>
        <div class="ligne-actions">${action}</div>
      </div>`;
  }).join('');
}

document.addEventListener('click', async (e) => {
  const btn = e.target.closest('button[data-action]');
  if(!btn || btn.disabled) return;
  const action = btn.dataset.action;
  const code = btn.dataset.code;
  btn.disabled = true;
  try{
    if(action === 'vendre-jeu'){
      const vendue = collectionMap.get(code);
      const { error } = await sb.rpc('vendre_au_jeu', { p_commune_code: code });
      if(error) throw error;
      collectionMap.delete(code);
      renderCollection(); renderStats(); renderMapOverlay();
      if(vendue) notifier({ type: 'succes', titre: `${vendue.nom} vendue au jeu`, texte: `+${PRIX_RACHAT[vendue.tier.id]} pts` });
    } else if(action === 'mettre-vente'){
      const entree = collectionMap.get(code);
      const prix = await demanderPrix({ nom: entree ? entree.nom : 'Cette commune', rachat: entree ? PRIX_RACHAT[entree.tier.id] : 0 });
      if(!prix){ btn.disabled = false; return; }
      const { error } = await sb.rpc('mettre_en_vente', { p_commune_code: code, p_prix: prix });
      if(error) throw error;
      notifier({ type: 'succes', titre: 'Annonce publiée', texte: `${entree ? entree.nom + ' est' : 'La commune est'} en vente à ${prix.toLocaleString('fr-FR')} pts` });
    } else if(action === 'retirer'){
      const { error } = await sb.rpc('retirer_de_la_vente', { p_commune_code: code });
      if(error) throw error;
      notifier({ type: 'info', titre: 'Annonce retirée' });
    } else if(action === 'acheter'){
      const { error } = await sb.rpc('acheter', { p_commune_code: code, p_saison: CURRENT_SEASON });
      if(error) throw error;
      await loadMyCollection();
      await loadOthersPossessions();
      const achetee = collectionMap.get(code);
      notifier({ type: 'succes', titre: achetee ? `${achetee.nom} est à toi` : 'Commune achetée' });
    } else if(action === 'bouclier'){
      const entree = collectionMap.get(code);
      if(!entree){ btn.disabled = false; return; }
      const duree = await choisirBouclier(entree);
      if(!duree){ btn.disabled = false; return; }
      const { data, error } = await sb.rpc('acheter_bouclier', { p_commune_code: code, p_duree: duree });
      if(error) throw error;
      const res = data && data[0];
      const fin = res ? new Date(res.fin) : null;
      notifier({
        type: 'succes',
        titre: `Bouclier activé sur ${entree.nom}`,
        texte: fin ? `Protégée jusqu'à ${fin.toLocaleString('fr-FR', { weekday: 'long', hour: '2-digit', minute: '2-digit' })} (−${res.prix} pts)` : ''
      });
      await loadMyCollection();
    } else if(action === 'attaquer'){
      // bloque le rafraichissement auto de la grille pendant l'attaque en cours
      combatActionEnCours = true;
      try{
        const { data, error } = await sb.rpc('attaquer', { p_commune_code: code });
        if(error) throw error;
        const result = data[0];
        const cible = combatCibles.find(x => x.commune_code === code);
        const nomCible = cible ? cible.communes.nom : 'la commune';
        if(result.conquise){
          await loadMyCollection();
          await loadOthersPossessions();
          celebrerConquete({
            nom: nomCible,
            tier: cible ? cible.communes.tier : '',
            dept: cible ? cible.communes.departement : '',
            bonus: cible ? Math.floor(PRIX_RACHAT[cible.communes.tier] * BONUS_CONQUETE_PART) : 0
          });
        } else if(result.gagne){
          notifier({
            type: 'victoire',
            titre: `Victoire contre ${nomCible}`,
            texte: result.victoires_consecutives >= 2 ? 'Encore une victoire pour la conquérir.' : `Série : ${result.victoires_consecutives} sur 3`,
            serie: result.victoires_consecutives
          });
        } else {
          notifier({ type: 'defaite', titre: `Défaite contre ${nomCible}`, texte: 'La série repart à zéro.', serie: 0 });
        }
        await loadCombat();
        loadPackStatus();
      } finally {
        combatActionEnCours = false;
      }
      return;
    }
    await loadBourse();
    loadPackStatus();
  } catch(err){
    notifier({ type: 'erreur', titre: 'Action impossible', texte: messageLisible(err.message) });
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
  if(h >= 48) return `${Math.floor(h / 24)} j ${h % 24} h`;
  return m ? `${h}h${String(m).padStart(2, '0')}` : `${h}h`;
}

// ---------- Mes communes attaquees ----------
let menaces = [];
let menacesInterval = null;

async function loadMenaces(){
  const { data, error } = await sb.rpc('sieges_contre_moi');
  if(error){ console.error(error); return; }
  menaces = data || [];
  renderMenaces();
  renderBoucliers();
}

function renderMenaces(){
  const enDanger = menaces.filter(m => m.victoires_consecutives > 0);
  const badge = document.getElementById('combatBadge');
  if(badge){
    badge.hidden = enDanger.length === 0;
    badge.textContent = enDanger.length;
    badge.title = enDanger.length > 1 ? `${enDanger.length} communes attaquées` : 'Une commune attaquée';
  }
  const bloc = document.getElementById('combatMenaces');
  const liste = document.getElementById('combatMenacesListe');
  if(!bloc || !liste) return;
  bloc.hidden = menaces.length === 0;
  if(menaces.length === 0){ liste.innerHTML = ''; return; }

  const now = Date.now();
  liste.innerHTML = menaces.map(m => {
    const tier = TIERS.find(t => t.id === m.tier);
    const v = m.victoires_consecutives;
    const dernier = new Date(m.dernier_round).getTime();
    let statut;
    const miennne = collectionMap.get(m.commune_code);
    const bouclierFin = miennne ? miennne.bouclierJusqua : 0;
    if(v > 0 && bouclierFin > now){
      statut = `Protégée par ton bouclier encore ${formatDuree(bouclierFin - now)}. La série de l'attaquant est en pause.`;
    } else if(v > 0){
      const prochain = dernier + (DELAI_ATTAQUE_MS[m.tier] || 0);
      const quand = now < prochain
        ? `Prochain assaut possible dans ${formatDuree(prochain - now)}.`
        : 'Peut repasser à l\'assaut à tout moment.';
      statut = (v >= 2 ? 'Plus qu\'une victoire avant de la perdre. ' : '') + quand;
    } else {
      statut = `Attaque repoussée il y a ${formatDuree(now - dernier)}.`;
    }
    const serie = [0, 1, 2].map(i => `<i class="${i < v ? 'pris' : ''}"></i>`).join('');
    return `
      <div class="menace ${v > 0 ? 'danger' : ''}">
        <span class="menace-point" style="background:${COULEURS_FILTRE[m.tier] || '#7E8BA0'}"></span>
        <div class="menace-texte">
          <span class="menace-titre"><b>${m.nom}</b> <span>${tier ? '(' + tier.label.toLowerCase() + ')' : ''}, attaquée par ${echapperTexte(m.attaquant_pseudo)}</span></span>
          <span class="menace-statut">${statut}</span>
          ${v > 0 && !(bouclierFin > now) ? (m.defense_utilisee
            ? '<span class="menace-note">Défense déjà utilisée contre cette attaque</span>'
            : (m.attaquant_id ? `<button class="menace-defendre" data-commune="${m.commune_code}" data-attaquant="${m.attaquant_id}" data-nom="${echapperTexte(m.nom)}">${ICONE_BOUCLIER}Défendre (${coutAttaque(m.tier)} pts, 1 chance sur 2)</button>` : '')) : ''}
        </div>
        <div class="menace-serie" title="${v} victoire${v > 1 ? 's' : ''} d'affilée sur 3">${serie}</div>
      </div>`;
  }).join('');
}

document.getElementById('boucliersToutToggle').addEventListener('click', (e) => {
  boucliersTout = !boucliersTout;
  const b = e.currentTarget;
  b.classList.toggle('active', boucliersTout);
  b.setAttribute('aria-pressed', String(boucliersTout));
  renderBoucliers();
});

document.getElementById('reglesBtn').addEventListener('click', () => {
  const tab = document.querySelector('.tab[data-tab="regles"]');
  if(tab){ tab.click(); return; }
  // l'onglet Regles n'est plus dans la barre : on l'ouvre a la main
  document.querySelectorAll('.tab').forEach(t => t.classList.remove('active'));
  document.querySelectorAll('.tab-panel').forEach(p => p.classList.toggle('active', p.id === 'panel-regles'));
  document.getElementById('reglesBtn').classList.add('actif');
  renderNotifications();
  window.scrollTo({ top: 0, behavior: 'smooth' });
});

document.getElementById('combatMenacesListe').addEventListener('click', async (e) => {
  const btn = e.target.closest('.menace-defendre');
  if(!btn || btn.disabled) return;
  btn.disabled = true;
  try{
    const { data, error } = await sb.rpc('defendre', { p_commune_code: btn.dataset.commune, p_attaquant: btn.dataset.attaquant });
    if(error) throw error;
    const r = data && data[0];
    if(r && r.reussie){
      notifier({
        type: 'victoire',
        titre: `Défense réussie à ${btn.dataset.nom}`,
        texte: r.victoires_restantes > 0 ? `L'attaquant perd une victoire (plus que ${r.victoires_restantes} sur 3).` : 'L\'attaquant perd sa victoire : son attaque repart de zéro.',
        serie: r.victoires_restantes
      });
    } else {
      notifier({ type: 'defaite', titre: `Défense ratée à ${btn.dataset.nom}`, texte: `L'attaquant garde ses victoires. (−${r ? r.cout : ''} pts)` });
    }
    await loadMenaces();
    loadPackStatus();
    if(packStatusCache){
      ['soldeValueCombat', 'soldeValueDefense'].forEach(id => {
        const el = document.getElementById(id);
        if(el) el.textContent = packStatusCache.solde;
      });
    }
  } catch(err){
    notifier({ type: 'erreur', titre: 'Défense impossible', texte: messageLisible(err.message) });
    btn.disabled = false;
  }
});

let combatCibles = [];
let combatSieges = new Map();
let combatFilterTier = 'tous';
let combatActionEnCours = false;
let combatProximite = false;
let combatEnCours = false;
let combatRayonKm = 20;

// Distance a vol d'oiseau entre deux points GPS, en km
function distanceKm(lat1, lon1, lat2, lon2){
  const R = 6371, rad = Math.PI / 180;
  const dLat = (lat2 - lat1) * rad, dLon = (lon2 - lon1) * rad;
  const a = Math.sin(dLat / 2) ** 2 + Math.cos(lat1 * rad) * Math.cos(lat2 * rad) * Math.sin(dLon / 2) ** 2;
  return 2 * R * Math.asin(Math.sqrt(a));
}

// Pour chaque cible : distance a la plus proche de mes communes, et son nom
function calculerDistancesCibles(){
  const miennes = Array.from(collectionMap.values()).filter(m => m.lat != null && m.lon != null);
  for(const c of combatCibles){
    c._distKm = null;
    c._procheDe = null;
    const lat = c.communes.latitude, lon = c.communes.longitude;
    if(lat == null || lon == null) continue;
    for(const m of miennes){
      // pre-filtre rapide : plus d'1 degre d'ecart en latitude = plus de 111 km
      if(Math.abs(m.lat - lat) > 1) continue;
      const d = distanceKm(lat, lon, m.lat, m.lon);
      if(c._distKm === null || d < c._distKm){ c._distKm = d; c._procheDe = m.nom; }
    }
    // au-dela de 100 km le pre-filtre peut rater la plus proche : on n'affiche rien
    if(c._distKm !== null && c._distKm > 100){ c._distKm = null; c._procheDe = null; }
  }
}

// "de Genilac" mais "d'Angers"
function deCommune(nom){
  return /^[AEIOUYÀÂÄÉÈÊËÎÏÔÖÙÛÜaeiouyàâäéèêëîïôöùûü]/.test(nom) ? "d'" + nom : 'de ' + nom;
}

async function loadCombat(){
  const { data: userData } = await sb.auth.getUser();
  const uid = userData.user.id;

  const { data: joueurRow } = await sb.from('joueurs').select('solde').eq('id', uid).single();
  const solde = joueurRow ? joueurRow.solde : '—';
  document.getElementById('soldeValueCombat').textContent = solde;
  const soldeDef = document.getElementById('soldeValueDefense');
  if(soldeDef) soldeDef.textContent = solde;

  const champsCible = 'communes!inner(nom,departement,tier,latitude,longitude), joueurs(pseudo)';
  let { data: cibles, error } = await sb
    .from('possessions')
    .select('commune_code, joueur_id, acquired_at, bouclier_jusqua, ' + champsCible)
    .neq('joueur_id', uid)
    .in('communes.tier', ['rare','legendaire']);
  if(error){
    ({ data: cibles, error } = await sb.from('possessions').select('commune_code, joueur_id, acquired_at, ' + champsCible)
      .neq('joueur_id', uid).in('communes.tier', ['rare','legendaire']));
  }
  if(error){ console.error(error); return; }

  const { data: mesSieges } = await sb
    .from('sieges')
    .select('commune_code, victoires_consecutives, dernier_round, defense_utilisee')
    .eq('attacker_id', uid)
    .then(r => r.error
      ? sb.from('sieges').select('commune_code, victoires_consecutives, dernier_round').eq('attacker_id', uid)
      : r);

  combatCibles = cibles || [];
  calculerDistancesCibles();
  loadMenaces();
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
  if(combatProximite){
    cibles = cibles
      .filter(c => c._distKm !== null && c._distKm <= combatRayonKm)
      .sort((a, b) => a._distKm - b._distKm);
  }

  // Combats en cours : cibles ou j'ai deja 1 ou 2 victoires d'affilee
  const victoiresDe = (c) => { const s = combatSieges.get(c.commune_code); return s ? s.victoires_consecutives : 0; };
  const prochainRoundDe = (c) => {
    const s = combatSieges.get(c.commune_code);
    return s && s.dernier_round ? new Date(s.dernier_round).getTime() + DELAI_ATTAQUE_MS[c.communes.tier] : 0;
  };
  const nbEnCours = combatCibles.filter(c => victoiresDe(c) > 0).length;
  const nbEl = document.getElementById('combatEnCoursNb');
  if(nbEl) nbEl.textContent = nbEnCours;
  if(combatEnCours){
    // les plus avancees d'abord, puis celles qu'on peut attaquer le plus tot
    cibles = cibles
      .filter(c => victoiresDe(c) > 0)
      .sort((a, b) => victoiresDe(b) - victoiresDe(a) || prochainRoundDe(a) - prochainRoundDe(b));
  }

  if(combatCibles.length === 0){
    grid.innerHTML = '<p class="collection-empty">Aucune cible disponible pour le moment.</p>';
    return;
  }
  if(cibles.length === 0){
    let msg = 'Aucune cible ne correspond à la recherche.';
    if(combatEnCours && nbEnCours === 0){
      msg = 'Aucun combat en cours. Gagne un premier round sur une cible pour la retrouver ici.';
    } else if(combatEnCours){
      msg = 'Aucun combat en cours ne correspond aux autres filtres.';
    } else if(combatProximite && collectionMap.size === 0){
      msg = 'Il te faut au moins une commune pour attaquer autour de ton territoire.';
    } else if(combatProximite){
      msg = `Aucune commune rare ou légendaire à moins de ${combatRayonKm} km de ton territoire.`;
    }
    grid.innerHTML = `<p class="collection-empty">${msg}</p>`;
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
    const bouclierFin = c.bouclier_jusqua ? new Date(c.bouclier_jusqua).getTime() : 0;
    let etatClasse, etatTexte, note = '', noteAlerte = false, disabled = true;
    if(bouclierFin > now){
      etatClasse = 'bouclier'; etatTexte = `${ICONE_BOUCLIER}${formatDuree(bouclierFin - now)}`;
      note = victoires > 0 ? 'Bouclier actif : ta série est en pause' : 'Protégée par un bouclier';
    } else if(encoreImmune){
      etatClasse = 'protegee'; etatTexte = `Acquise, ${formatDuree(immuniteFin - now)}`;
      note = 'Protection après acquisition';
    } else if(enAttente){
      etatClasse = 'attente'; etatTexte = formatDuree(prochainRound - now);
      note = `Prochain round dans ${formatDuree(prochainRound - now)}`;
    } else {
      etatClasse = 'pret'; etatTexte = 'Prête';
      disabled = false;
    }
    if(victoires > 0 && siege && siege.defense_utilisee){
      note = 'Le défenseur a déjà utilisé sa défense';
      noteAlerte = true;
    }
    const ronds = [0, 1, 2].map(i => `<i class="${i < victoires ? 'plein' : ''}"></i>`).join('');
    const distance = c._distKm !== null
      ? `<p class="cible-distance">À ${c._distKm < 10 ? c._distKm.toFixed(1).replace('.', ',') : Math.round(c._distKm)} km ${deCommune(c._procheDe)}</p>` : '';

    return `
      <article class="cible ${commune.tier}">
        <div class="cible-int">
          <div class="cible-haut">
            <span class="cible-rarete">${tier.label}</span>
            <span class="cible-etat ${etatClasse}">${etatTexte}</span>
          </div>
          <div class="cible-art">${miniArtSvg(c.commune_code, commune.tier)}<span class="cible-dept">${commune.departement}</span></div>
          <div class="cible-infos">
            <h3 class="cible-nom ${commune.nom.length > 16 ? 'long' : ''}">${commune.nom}</h3>
            <p class="cible-proprio"><i style="background:${colorForPlayer(c.joueur_id)}"></i>à <b>${echapperTexte(pseudo)}</b></p>
            ${distance}
          </div>
          <div class="cible-serie"><span>Ta série</span><span class="cible-ronds">${ronds}</span></div>
          <p class="cible-note ${noteAlerte ? 'alerte' : ''}">${note}</p>
          <button class="cible-attaquer" data-action="attaquer" data-code="${c.commune_code}" ${disabled ? 'disabled' : ''}>Attaquer <b>${cout} pts</b></button>
        </div>
      </article>`;
  }).join('');
}

// Rafraichit les decomptes toutes les 30 s quand l'onglet Combat est ouvert,
// pour que le bouton se debloque tout seul sans avoir a changer d'onglet
setInterval(() => {
  const defense = document.getElementById('panel-defense');
  if(defense && defense.classList.contains('active')){ renderMenaces(); renderBoucliers(); }
  const panel = document.getElementById('panel-combat');
  if(!panel || !panel.classList.contains('active')) return;
  if(combatActionEnCours || combatCibles.length === 0) return;
  renderCombatGrid();
}, 30000);

document.getElementById('combatSearch').addEventListener('input', renderCombatGrid);
document.getElementById('combatEnCoursToggle').addEventListener('click', () => {
  combatEnCours = !combatEnCours;
  const btn = document.getElementById('combatEnCoursToggle');
  btn.classList.toggle('active', combatEnCours);
  btn.setAttribute('aria-pressed', String(combatEnCours));
  renderCombatGrid();
});
document.getElementById('combatProxToggle').addEventListener('click', () => {
  combatProximite = !combatProximite;
  const btn = document.getElementById('combatProxToggle');
  btn.classList.toggle('active', combatProximite);
  btn.setAttribute('aria-pressed', String(combatProximite));
  document.getElementById('combatRayons').hidden = !combatProximite;
  renderCombatGrid();
});
document.getElementById('combatRayons').addEventListener('click', (e) => {
  const pill = e.target.closest('.filter-pill');
  if(!pill) return;
  document.querySelectorAll('#combatRayons .filter-pill').forEach(p => p.classList.remove('active'));
  pill.classList.add('active');
  combatRayonKm = Number(pill.dataset.km);
  renderCombatGrid();
});

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
    document.getElementById('reglesBtn').classList.remove('actif');
    tab.classList.add('active');
    document.getElementById('panel-' + tab.dataset.tab).classList.add('active');
    if(tab.dataset.tab === 'territoire') sizeMapWrap(window.__mapAspectRatio);
    if(tab.dataset.tab === 'bourse') loadBourse();
    if(tab.dataset.tab === 'tirage') loadPackStatus();
    if(tab.dataset.tab === 'defense'){ loadMenaces(); loadCombat(); }
    if(tab.dataset.tab === 'combat') loadCombat();
  });
});

// en revenant sur le site (autre appli, autre onglet), on relit jetons et solde
document.addEventListener('visibilitychange', () => {
  if(!document.hidden && packStatusCache) loadPackStatus();
});

// ---------- Mise a jour automatique ----------
// Sur l'ecran d'accueil d'un iPhone, il n'y a pas de bouton "recharger" : le jeu verifie
// lui-meme s'il existe une version plus recente, et se recharge tout seul.
let majEnCours = false;

async function verifierVersion({ silencieux = true } = {}){
  if(majEnCours) return false;
  try{
    const rep = await fetch('version.json?t=' + Date.now(), { cache: 'no-store' });
    if(!rep.ok) return false;
    const info = await rep.json();
    if(!info.version || info.version === VERSION_JEU) return false;
    majEnCours = true;
    if(!silencieux) notifier({ type: 'info', titre: 'Mise à jour du jeu', texte: 'Nouvelle version, un instant…', duree: 4000 });
    await appliquerMiseAJour();
    return true;
  } catch(e){
    return false;
  }
}

async function appliquerMiseAJour(){
  try{
    // on vide les fichiers gardes en memoire par le navigateur, puis on repart a neuf
    if('caches' in window){
      const noms = await caches.keys();
      await Promise.all(noms.map(n => caches.delete(n)));
    }
    const reg = enregistrementSW || (('serviceWorker' in navigator) ? await navigator.serviceWorker.getRegistration() : null);
    if(reg) await reg.update();
  } catch(e){}
  // l'adresse change a chaque version : le cache de la page ne peut pas resservir
  const url = new URL(location.href);
  url.searchParams.set('v', String(Date.now()));
  location.replace(url.toString());
}

// au demarrage, puis a chaque retour dans le jeu et toutes les 30 min
document.addEventListener('visibilitychange', () => { if(!document.hidden) verifierVersion(); });
setInterval(() => verifierVersion(), 30 * 60 * 1000);

// Tirer la page vers le bas pour rafraichir (comme dans une vraie application)
(function tirerPourRafraichir(){
  const seuil = 70;
  let depart = null, actif = false;
  const indicateur = document.createElement('div');
  indicateur.className = 'tirer-rafraichir';
  indicateur.innerHTML = '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"><path d="M3 12a9 9 0 1 1 3 6.7"/><path d="M3 20v-6h6"/></svg>';
  document.body.appendChild(indicateur);

  document.addEventListener('touchstart', (e) => {
    if(e.touches.length !== 1) return;
    // seulement si on est deja tout en haut, et pas sur la carte (qui gere ses propres gestes)
    const surCarte = e.target.closest('#mapWrap');
    depart = (!surCarte && window.scrollY <= 0) ? e.touches[0].clientY : null;
    actif = false;
  }, { passive: true });

  document.addEventListener('touchmove', (e) => {
    if(depart === null || e.touches.length !== 1) return;
    const dy = e.touches[0].clientY - depart;
    if(dy <= 0){ indicateur.style.transform = ''; indicateur.classList.remove('visible', 'pret'); actif = false; return; }
    actif = true;
    const tire = Math.min(dy * 0.5, 90);
    indicateur.classList.add('visible');
    indicateur.classList.toggle('pret', dy >= seuil);
    indicateur.style.transform = `translate(-50%, ${tire}px) rotate(${dy * 2}deg)`;
  }, { passive: true });

  document.addEventListener('touchend', async () => {
    if(depart === null || !actif){ depart = null; return; }
    const pret = indicateur.classList.contains('pret');
    indicateur.classList.remove('visible', 'pret');
    indicateur.style.transform = '';
    depart = null;
    if(!pret) return;
    indicateur.classList.add('visible', 'tourne');
    // si une nouvelle version existe, elle est appliquee ; sinon on recharge simplement les donnees
    const misAJour = await verifierVersion({ silencieux: false });
    if(misAJour) return;
    await rafraichirDonnees();
    indicateur.classList.remove('visible', 'tourne');
    notifier({ type: 'succes', titre: 'Données à jour', duree: 1800 });
  }, { passive: true });
})();

async function rafraichirDonnees(){
  await loadMyCollection();
  await loadOthersPossessions();
  await loadPackStatus();
  await loadMenaces();
  const actif = document.querySelector('.tab-panel.active');
  if(actif && actif.id === 'panel-bourse') await loadBourse();
  if(actif && (actif.id === 'panel-combat' || actif.id === 'panel-defense')) await loadCombat();
}

// ---------- Notifications sur telephone ----------
const NOTIF_IOS = /iPad|iPhone|iPod/.test(navigator.userAgent) || (navigator.platform === 'MacIntel' && navigator.maxTouchPoints > 1);
const NOTIF_INSTALLEE = window.matchMedia('(display-mode: standalone)').matches || window.navigator.standalone === true;
const NOTIF_SUPPORTEE = 'serviceWorker' in navigator && 'PushManager' in window && 'Notification' in window;
const ICONE_CLOCHE = '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M6 8a6 6 0 1 1 12 0c0 7 3 9 3 9H3s3-2 3-9"/><path d="M10.3 21a1.94 1.94 0 0 0 3.4 0"/></svg>';
let enregistrementSW = null;

if('serviceWorker' in navigator){
  navigator.serviceWorker.register('sw.js')
    .then(reg => { enregistrementSW = reg; renderNotifications(); })
    .catch(err => console.error('Service worker :', err));
  // clic sur une notification alors que le jeu est deja ouvert
  navigator.serviceWorker.addEventListener('message', (e) => {
    if(e.data && e.data.type === 'ouvrir') ouvrirOngletDepuisUrl(e.data.url);
  });
}

const ONGLETS_CONNUS = ['tirage', 'collection', 'territoire', 'bourse', 'combat', 'defense', 'regles'];
function ouvrirOngletDepuisUrl(url){
  try{
    const onglet = new URL(url, location.href).searchParams.get('onglet');
    if(!ONGLETS_CONNUS.includes(onglet)) return;
    if(onglet === 'regles'){ document.getElementById('reglesBtn').click(); return; }
    const tab = document.querySelector('.tab[data-tab="' + onglet + '"]');
    if(tab) tab.click();
  } catch(e){}
}

async function etatNotifications(){
  if(NOTIF_IOS && !NOTIF_INSTALLEE) return 'installer';
  if(!NOTIF_SUPPORTEE) return 'non-supporte';
  if(Notification.permission === 'denied') return 'refuse';
  try{
    const reg = enregistrementSW || await navigator.serviceWorker.getRegistration();
    const abo = reg ? await reg.pushManager.getSubscription() : null;
    return abo ? 'actif' : 'inactif';
  } catch(e){ return 'inactif'; }
}

function b64urlVersUint8(s){
  const b64 = s.replace(/-/g, '+').replace(/_/g, '/') + '==='.slice((s.length + 3) % 4);
  return Uint8Array.from(atob(b64), c => c.charCodeAt(0));
}

async function activerNotifications(bouton){
  if(bouton) bouton.disabled = true;
  try{
    // la demande d'autorisation doit partir tout de suite apres le clic (exigence d'Apple)
    const permission = await Notification.requestPermission();
    if(permission !== 'granted'){
      notifier({ type: 'erreur', titre: 'Notifications refusées', texte: 'Tu peux les réautoriser dans les réglages de ton téléphone.' });
      return;
    }
    const { data: cle, error } = await sb.rpc('cle_publique_notifications');
    if(error || !cle) throw new Error('Les notifications ne sont pas encore configurées sur le serveur.');
    const reg = enregistrementSW || await navigator.serviceWorker.ready;
    let abo = await reg.pushManager.getSubscription();
    if(!abo) abo = await reg.pushManager.subscribe({ userVisibleOnly: true, applicationServerKey: b64urlVersUint8(cle) });
    const cles = abo.toJSON().keys || {};
    const { error: e2 } = await sb.rpc('enregistrer_abonnement', { p_endpoint: abo.endpoint, p_p256dh: cles.p256dh, p_auth: cles.auth });
    if(e2) throw e2;
    notifier({ type: 'succes', titre: 'Notifications activées', texte: 'Tu seras prévenu si une commune est en danger ou si un paquet t\'attend.' });
  } catch(err){
    notifier({ type: 'erreur', titre: 'Activation impossible', texte: messageLisible(err.message) });
  } finally {
    if(bouton) bouton.disabled = false;
    renderNotifications();
  }
}

async function desactiverNotifications(bouton){
  if(bouton) bouton.disabled = true;
  try{
    const reg = enregistrementSW || await navigator.serviceWorker.getRegistration();
    const abo = reg ? await reg.pushManager.getSubscription() : null;
    if(abo){
      await sb.rpc('supprimer_abonnement', { p_endpoint: abo.endpoint });
      await abo.unsubscribe();
    }
    notifier({ type: 'info', titre: 'Notifications désactivées sur cet appareil' });
  } catch(err){
    notifier({ type: 'erreur', titre: 'Désactivation impossible', texte: messageLisible(err.message) });
  } finally {
    renderNotifications();
  }
}

function contenuNotifications(etat, avecPlusTard){
  const plusTard = avecPlusTard ? '<button class="btn-p contour" data-notif="plus-tard">Plus tard</button>' : '';
  const textes = {
    installer: ['Reçois les alertes sur ton iPhone', 'Ajoute TerraFront à ton écran d\'accueil : touche <strong>Partager</strong>, puis <strong>Sur l\'écran d\'accueil</strong>. Ouvre ensuite le jeu depuis cette icône et active les notifications dans l\'onglet Règles.', plusTard],
    inactif: ['Ne rate plus aucune attaque', 'Active les notifications pour être prévenu quand une de tes communes est en danger, ou quand un paquet gratuit t\'attend.', '<button class="btn-p or" data-notif="activer">Activer les notifications</button>' + plusTard],
    actif: ['Notifications activées', 'Cet appareil te prévient quand une commune est à 2 défaites de tomber, et quand un paquet gratuit est prêt.', '<button class="btn-p contour" data-notif="desactiver">Désactiver</button>'],
    refuse: ['Notifications bloquées', 'Tu les as refusées sur cet appareil. Pour les réactiver, passe par les réglages de ton téléphone, rubrique Notifications.', ''],
    'non-supporte': ['Notifications indisponibles', 'Ce navigateur ne permet pas de recevoir les notifications du jeu.', ''],
  };
  const [titre, texte, actions] = textes[etat];
  return `<span class="notif-icone-grande">${ICONE_CLOCHE}</span>
    <div class="notif-corps"><b>${titre}</b><p>${texte}</p></div>
    ${actions ? `<div class="notif-actions">${actions}</div>` : ''}`;
}

async function renderNotifications(){
  const etat = await etatNotifications();
  const carte = document.getElementById('notifCarte');
  if(carte){
    carte.className = 'notif-carte ' + etat;
    carte.innerHTML = contenuNotifications(etat, false);
  }
  const banniere = document.getElementById('notifBanniere');
  if(banniere){
    let masquee = false;
    try{ masquee = Date.now() - Number(localStorage.getItem('tf-banniere-notif') || 0) < 7 * 24 * 3600e3; } catch(e){}
    const surTelephone = NOTIF_IOS || window.matchMedia('(max-width: 760px)').matches;
    const utile = etat === 'installer' || etat === 'inactif';
    banniere.hidden = masquee || !surTelephone || !utile;
    if(!banniere.hidden) banniere.innerHTML = contenuNotifications(etat, true);
  }
}

document.addEventListener('click', (e) => {
  const b = e.target.closest('[data-notif]');
  if(!b) return;
  if(b.dataset.notif === 'activer') activerNotifications(b);
  if(b.dataset.notif === 'desactiver') desactiverNotifications(b);
  if(b.dataset.notif === 'plus-tard'){
    try{ localStorage.setItem('tf-banniere-notif', String(Date.now())); } catch(err){}
    document.getElementById('notifBanniere').hidden = true;
  }
});

// Sommaire des regles : ouvre la section visee
document.querySelectorAll('#panel-regles .sommaire a').forEach(a => a.addEventListener('click', () => {
  const cible = document.querySelector(a.getAttribute('href'));
  if(cible && cible.tagName === 'DETAILS') cible.open = true;
}));

initAuth();
