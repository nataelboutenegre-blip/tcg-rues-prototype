// --- Connexion Supabase ---
const SUPABASE_URL = 'https://yzcgroprydxhbwaufkdu.supabase.co';
const SUPABASE_ANON_KEY = 'sb_publishable_s829mEa2YUPWr9DOks2FTg_k9gpTQTA';
const sb = window.supabase.createClient(SUPABASE_URL, SUPABASE_ANON_KEY);
const CURRENT_SEASON = 'saison-1';
const VERSION_JEU = 'b17f23b3ca63';

// les taux de tirage ne sont plus ecrits ici : ils suivent le stock restant
// et se lisent avec taux_actuels(), cote base
const TIERS = [
  {id:'legendaire', label:'Légendaire', color:'#B0862C'},
  {id:'rare', label:'Rare', color:'#2A5FA8'},
  {id:'peucommun', label:'Peu commun', color:'#2E7D5B'},
  {id:'commun', label:'Commun', color:'#7C8798'},
];
const DEPT_NAMES = {"01":"Ain","02":"Aisne","03":"Allier","04":"Alpes-de-Haute-Provence","05":"Hautes-Alpes","06":"Alpes-Maritimes","07":"Ardèche","08":"Ardennes","09":"Ariège","10":"Aube","11":"Aude","12":"Aveyron","13":"Bouches-du-Rhône","14":"Calvados","15":"Cantal","16":"Charente","17":"Charente-Maritime","18":"Cher","19":"Corrèze","21":"Côte-d'Or","22":"Côtes-d'Armor","23":"Creuse","24":"Dordogne","25":"Doubs","26":"Drôme","27":"Eure","28":"Eure-et-Loir","29":"Finistère","2A":"Corse-du-Sud","2B":"Haute-Corse","30":"Gard","31":"Haute-Garonne","32":"Gers","33":"Gironde","34":"Hérault","35":"Ille-et-Vilaine","36":"Indre","37":"Indre-et-Loire","38":"Isère","39":"Jura","40":"Landes","41":"Loir-et-Cher","42":"Loire","43":"Haute-Loire","44":"Loire-Atlantique","45":"Loiret","46":"Lot","47":"Lot-et-Garonne","48":"Lozère","49":"Maine-et-Loire","50":"Manche","51":"Marne","52":"Haute-Marne","53":"Mayenne","54":"Meurthe-et-Moselle","55":"Meuse","56":"Morbihan","57":"Moselle","58":"Nièvre","59":"Nord","60":"Oise","61":"Orne","62":"Pas-de-Calais","63":"Puy-de-Dôme","64":"Pyrénées-Atlantiques","65":"Hautes-Pyrénées","66":"Pyrénées-Orientales","67":"Bas-Rhin","68":"Haut-Rhin","69":"Rhône","70":"Haute-Saône","71":"Saône-et-Loire","72":"Sarthe","73":"Savoie","74":"Haute-Savoie","75":"Paris","76":"Seine-Maritime","77":"Seine-et-Marne","78":"Yvelines","79":"Deux-Sèvres","80":"Somme","81":"Tarn","82":"Tarn-et-Garonne","83":"Var","84":"Vaucluse","85":"Vendée","86":"Vienne","87":"Haute-Vienne","88":"Vosges","89":"Yonne","90":"Territoire de Belfort","91":"Essonne","92":"Hauts-de-Seine","93":"Seine-Saint-Denis","94":"Val-de-Marne","95":"Val-d'Oise","971":"Guadeloupe","972":"Martinique","973":"Guyane","974":"La Réunion","975":"Saint-Pierre-et-Miquelon","976":"Mayotte"};
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

// ---------- Page de presentation ----------
// Affichee seulement a qui n'a jamais ouvert de session sur cet appareil.
// Le drapeau est pose a la premiere entree reelle dans le jeu, pas a la premiere
// visite : un curieux qui passe sans s'inscrire la revoit la fois suivante.
const CLE_DEJA_JOUE = 'terrafront-deja-joue';

// quelques departements colories, pour montrer a quoi ressemble une partie
const ZONES_LANDING = {
  '16':'#F0B429','17':'#F0B429','24':'#F0B429','87':'#F0B429',
  '33':'#2F7CF6','40':'#2F7CF6','47':'#2F7CF6',
  '13':'#E5484D','83':'#E5484D','84':'#E5484D','04':'#E5484D',
  '35':'#22A06B','22':'#22A06B','56':'#22A06B','44':'#22A06B',
  '59':'#8B5CF6','62':'#8B5CF6','02':'#8B5CF6',
  '67':'#00B4D8','68':'#00B4D8','57':'#00B4D8','88':'#00B4D8',
  '69':'#FF7A1A','42':'#FF7A1A','01':'#FF7A1A',
  '31':'#C026D3','81':'#C026D3','82':'#C026D3',
};

function dejaJoue(){
  try { return localStorage.getItem(CLE_DEJA_JOUE) === '1'; } catch(e){ return false; }
}
function marquerDejaJoue(){
  try { localStorage.setItem(CLE_DEJA_JOUE, '1'); } catch(e){}
}

// La carte reprend les contours deja utilises par le jeu : aucun fichier de plus
// a telecharger, et les bornes se calculent depuis ces memes contours.
async function dessinerCarteLanding(){
  const svg = document.getElementById('lpCarte');
  if(!svg || svg.dataset.pret) return;
  let deps;
  try {
    const rep = await fetch('contours-departements.json', { cache: 'force-cache' });
    if(!rep.ok) return;
    deps = await rep.json();
  } catch(e){ return; }   // sans carte la page reste lisible, on n'insiste pas

  let latMin = 90, latMax = -90, lonMin = 180, lonMax = -180;
  for(const poly of Object.values(deps)){
    for(const anneau of poly){
      for(const point of anneau){
        const lon = point[0], lat = point[1];
        if(lat < latMin) latMin = lat;
        if(lat > latMax) latMax = lat;
        if(lon < lonMin) lonMin = lon;
        if(lon > lonMax) lonMax = lon;
      }
    }
  }
  const marge = 0.04;
  const dLat = (latMax - latMin) * marge, dLon = (lonMax - lonMin) * marge;
  latMin -= dLat; latMax += dLat; lonMin -= dLon; lonMax += dLon;
  const latMoy = (latMin + latMax) / 2;
  const ratio = ((lonMax - lonMin) * Math.cos(latMoy * Math.PI / 180)) / (latMax - latMin);
  const L = 1000, H = Math.round(1000 / ratio);

  const chemin = (poly) => poly.map(anneau => 'M' + anneau.map(point => {
    const x = (point[0] - lonMin) / (lonMax - lonMin) * L;
    const y = (latMax - point[1]) / (latMax - latMin) * H;
    return x.toFixed(1) + ',' + y.toFixed(1);
  }).join('L') + 'Z').join('');

  const socle = Object.values(deps).map(p => '<path d="' + chemin(p) + '"/>').join('');
  const zones = Object.keys(ZONES_LANDING).filter(c => deps[c]).map(c => {
    const couleur = ZONES_LANDING[c];
    const opacite = couleur === '#F0B429' ? '0.8' : '0.62';
    return '<path d="' + chemin(deps[c]) + '" fill="' + couleur + '" fill-opacity="' + opacite + '"/>';
  }).join('');

  svg.setAttribute('viewBox', '0 0 ' + L + ' ' + H);
  svg.innerHTML =
    '<defs><linearGradient id="lpTerre" x1="0" y1="0" x2="0" y2="1">' +
    '<stop offset="0%" stop-color="#20406A"/><stop offset="100%" stop-color="#16294A"/>' +
    '</linearGradient></defs>' +
    '<g fill="url(#lpTerre)" stroke="rgba(169,188,212,0.26)" stroke-width="0.9" ' +
    'stroke-linejoin="round" vector-effect="non-scaling-stroke">' + socle + '</g>' +
    '<g stroke="rgba(15,31,56,0.35)" stroke-width="0.6">' + zones + '</g>';
  svg.dataset.pret = '1';
}

function montrerLanding(){
  const page = document.getElementById('landing');
  if(!page) return;
  document.getElementById('authScreen').style.display = 'none';
  document.getElementById('gameScreen').style.display = 'none';
  page.hidden = false;
  window.scrollTo(0, 0);
  dessinerCarteLanding();
}

function cacherLanding(){
  const page = document.getElementById('landing');
  if(page) page.hidden = true;
}

function quitterLanding(mode){
  cacherLanding();
  showAuth();
  ecranAuth('principal');
  modeAuth(mode);
  const champ = document.getElementById('authEmail');
  if(champ && !surTelephone()) champ.focus();
}

document.querySelectorAll('#landing [data-jouer]').forEach(b =>
  b.addEventListener('click', () => quitterLanding('inscription')));
document.getElementById('lpConnexion').addEventListener('click', () => quitterLanding('connexion'));
document.getElementById('authRetourLanding').addEventListener('click', montrerLanding);

function showAuth(msg, type = 'erreur'){
  if(menacesInterval){ clearInterval(menacesInterval); menacesInterval = null; }
  if(packStatusInterval){ clearInterval(packStatusInterval); packStatusInterval = null; }
  packStatusCache = null;
  document.getElementById('authScreen').style.display = 'flex';
  dessinerEventailAuth();
  document.getElementById('gameScreen').style.display = 'none';
  const el = document.getElementById('authMsg');
  el.textContent = msg ? messageLisible(msg) : '';
  el.className = 'auth-msg' + (msg ? ' ' + type : '');
}

async function showGame(session_){
  cacherLanding();
  marquerDejaJoue();
  document.getElementById('authScreen').style.display = 'none';
  document.getElementById('gameScreen').style.display = 'flex';
  document.getElementById('whoami').textContent = session_.user.email;
  await loadOutline();
  chargerTotalCommunes();
  await loadMyCollection();
  await loadOthersPossessions();
  await loadPackStatus();
  verifierTiragesEnAttente();
  loadMenaces();
  renderNotifications();
  peutEtreAfficherAccueil();
  loadObjectifs();
  loadClassement();
  loadJournal();
  loadAmis();
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

// true si on arrive depuis un lien de réinitialisation reçu par email
let recuperationEnCours = /type=recovery/.test(location.hash)
  || new URLSearchParams(location.search).get('type') === 'recovery';

async function initAuth(){
  const { data: { session: s } } = await sb.auth.getSession();
  if(recuperationEnCours){ showAuth(); ecranAuth('nouveau'); }
  else if(s) showGame(s);
  else if(dejaJoue()) showAuth();
  else montrerLanding();
  sb.auth.onAuthStateChange((event, s2) => {
    if(event === 'PASSWORD_RECOVERY'){
      recuperationEnCours = true;
      showAuth();
      ecranAuth('nouveau');
      return;
    }
    // pendant une réinitialisation Supabase ouvre une session : on n'entre pas dans le jeu pour autant
    if(recuperationEnCours && event !== 'SIGNED_OUT') return;
    if(s2) showGame(s2);
    else { showAuth(); ecranAuth('principal'); }
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
  // Sans pseudo, la base retombait sur la partie gauche de l'adresse e-mail,
  // et « prenom.nom » se retrouvait affiche dans le classement et sur la carte.
  if(pseudo.length < 3){
    showAuth('Choisis un pseudo d\u2019au moins 3 caractères : il sera visible par les autres joueurs.');
    document.getElementById('authPseudo').focus();
    return;
  }
  if(pseudo.length > 20){
    showAuth('Ton pseudo ne peut pas dépasser 20 caractères.');
    return;
  }
  const { error } = await sb.auth.signUp({ email, password, options: { data: { pseudo } } });
  if(error) showAuth(error.message);
  else { modeAuth('connexion'); showAuth('Compte créé. Tu peux te connecter.', 'succes'); }
});
// ---------- Mot de passe oublié ----------
// Trois écrans dans le même panneau : connexion, demande de lien, nouveau mot de passe
function ecranAuth(ecran){
  const q = (id) => document.getElementById(id);
  q('authBlocPrincipal').hidden = ecran !== 'principal';
  q('authBlocOubli').hidden = ecran !== 'oubli';
  q('authBlocNouveau').hidden = ecran !== 'nouveau';
  q('authOubliEnvoyer').hidden = ecran !== 'oubli';
  q('authNouveauValider').hidden = ecran !== 'nouveau';
  q('authOubliRetour').hidden = ecran === 'principal';
  const msg = q('authMsg');
  msg.textContent = ''; msg.className = 'auth-msg';
  if(ecran === 'principal'){
    const onglet = document.querySelector('.auth-onglets button.actif');
    modeAuth(onglet ? onglet.dataset.mode : 'connexion');
  } else {
    q('loginBtn').hidden = true;
    q('signupBtn').hidden = true;
    const premier = q(ecran === 'oubli' ? 'authOubliEmail' : 'authNouveau1');
    if(premier) premier.focus();
  }
}

document.getElementById('authOubliBtn').addEventListener('click', () => {
  document.getElementById('authOubliEmail').value = document.getElementById('authEmail').value.trim();
  ecranAuth('oubli');
});

document.getElementById('authOubliRetour').addEventListener('click', () => {
  recuperationEnCours = false;
  history.replaceState(null, '', location.pathname);
  ecranAuth('principal');
});

document.getElementById('authOubliEnvoyer').addEventListener('click', async (e) => {
  const btn = e.currentTarget;
  const email = document.getElementById('authOubliEmail').value.trim();
  if(!email){ showAuth('Indique ton adresse email.'); return; }
  btn.disabled = true;
  const { error } = await sb.auth.resetPasswordForEmail(email, { redirectTo: location.origin + location.pathname });
  btn.disabled = false;
  // message volontairement neutre : il ne révèle pas quelles adresses sont inscrites
  if(error && /rate limit|too many/i.test(error.message || '')) showAuth(error.message);
  else showAuth('Si un compte existe avec cette adresse, un lien vient de partir. Regarde aussi tes indésirables.', 'succes');
});

document.getElementById('authNouveauValider').addEventListener('click', async (e) => {
  const btn = e.currentTarget;
  const a = document.getElementById('authNouveau1').value;
  const b = document.getElementById('authNouveau2').value;
  if(a.length < 8){ showAuth('Le mot de passe doit faire au moins 8 caractères.'); return; }
  if(a !== b){ showAuth('Les deux mots de passe ne sont pas identiques.'); return; }
  btn.disabled = true;
  const { error } = await sb.auth.updateUser({ password: a });
  btn.disabled = false;
  if(error){ showAuth(error.message); return; }
  recuperationEnCours = false;
  history.replaceState(null, '', location.pathname);
  const { data: { session: s } } = await sb.auth.getSession();
  ecranAuth('principal');
  if(s){ showGame(s); notifier({ type: 'succes', titre: 'Mot de passe modifié' }); }
  else showAuth('Mot de passe modifié. Tu peux te connecter.', 'succes');
});

['authOubliEmail', 'authNouveau1', 'authNouveau2'].forEach(id => {
  document.getElementById(id).addEventListener('keydown', (e) => {
    if(e.key !== 'Enter') return;
    const btn = document.getElementById(id === 'authOubliEmail' ? 'authOubliEnvoyer' : 'authNouveauValider');
    if(btn && !btn.hidden) btn.click();
  });
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
// showGame() est appelee deux fois au demarrage : une fois par getSession(),
// une fois par onAuthStateChange que Supabase emet dans la foulee. Le test
// FRANCE_OUTLINE ne suffisait pas : les deux appels le franchissent pendant le
// fetch, et tout ce qui suit etait branche en double — dont les calques, dont
// les deux ecouteurs inversaient le meme reglage et s'annulaient au clic.
// On retient donc la promesse en cours plutot que le resultat.
let outlineEnCours = null;
function loadOutline(){
  if(FRANCE_OUTLINE) return Promise.resolve();
  if(!outlineEnCours) outlineEnCours = chargerContourFrance();
  return outlineEnCours;
}

async function chargerContourFrance(){
  const res = await fetch('data/france-outline.json');
  FRANCE_OUTLINE = await res.json();
  computeMapBounds();
  renderFranceOutline();
  if(MODE_CANVAS){
    CV.fond = null;
    initCanvas();
    brancherSurvolCanvas();
    brancherCalques();
    placerLegende();
    window.addEventListener('resize', placerLegende);
    // les frontieres viennent de ce fichier : on le demande sans attendre un dezoom
    chargerDepartements();
    demanderDessin();
  }
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
  if(MODE_CANVAS){ redimensionnerCanvas(); demanderDessin(); }
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

// Le zoom est un multiple de la largeur du cadre, pas une echelle de terrain :
// un plafond fixe a 6 donnait 7,2 px par kilometre sur un ecran de bureau et
// 2,3 sur un telephone. La meme carte, trois experiences differentes — d'ou la
// plainte, plus forte sur mobile. On vise desormais une echelle constante :
// 22 px/km, soit une commune moyenne de 5,5 km affichee sur environ 120 px,
// quelle que soit la taille de l'ecran.
const CIBLE_PX_PAR_KM = 22;
const LARGEUR_FRANCE_KM = 1000;
function zoomMaxCarte(){
  const wrap = document.getElementById('mapWrap');
  const w = wrap && wrap.clientWidth ? wrap.clientWidth : 1000;
  const cible = CIBLE_PX_PAR_KM * LARGEUR_FRANCE_KM / w;
  // le plancher garde l'ancien comportement sur tres grand ecran, le plafond
  // evite qu'un cadre minuscule autorise un zoom absurde
  return Math.max(6, Math.min(60, cible));
}

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
  // en canvas le deplacement est un simple changement de repere : pas de couche
  // promue par le navigateur, donc pas de flou et aucun redessin differe
  if(canvasActif()){ demanderDessin(); return; }
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
  mapFinMouvementTimer = setTimeout(() => {
    wrap.classList.remove('en-mouvement');
    // Un transform 3D promeut la couche en permanence : elle reste rasterisee au zoom
    // du debut du geste. Une fois le geste fini on repasse en 2D, ce qui rend la main
    // au moteur de rendu et redessine net.
    const couche = document.getElementById('mapTransform');
    if(couche) couche.style.transform =
      `translate(${mapPanX}px, ${mapPanY}px) scale(${mapZoom})`;
    // apres un deplacement, de nouveaux departements peuvent etre entres dans l'ecran
    if(mapZoom >= SEUIL_CONTOURS) renderMapOverlay();
  }, 200);
}

// Zoome en gardant fixe le point (px, py) du cadre : le curseur ou le centre des deux doigts
// vrai quand le changement de zoom fait apparaitre ou disparaitre des communes
function franchitUnSeuil(avant, apres){
  const seuils = Object.values(ZOOM_MINI).concat([SEUIL_CONTOURS]);
  return seuils.some(s => (avant < s) !== (apres < s));
}

function zoomMapAt(newZoom, px, py){
  newZoom = Math.min(zoomMaxCarte(), Math.max(MAP_ZOOM_MIN, newZoom));
  // On ne redessine qu'au franchissement d'un seuil : sinon chaque cran de molette
  // reconstruisait toute la carte. Le redessin de fin de geste est fait par signalerMouvementCarte.
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
      const newZoom = Math.min(zoomMaxCarte(), Math.max(MAP_ZOOM_MIN,
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

// ---------- Journal d'activite ----------
let journalMode = 'tous';
const ICONES_JOURNAL = {
  conquete: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M6.5 17.5L17 7M17 7h-4M17 7v4M17.5 17.5L7 7M7 7h4M7 7v4"/></svg>',
  defense: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linejoin="round"><path d="M12 3l7.5 3v5.5c0 4.6-3.2 8.3-7.5 9.5-4.3-1.2-7.5-4.9-7.5-9.5V6z"/><path d="M9 12l2 2 4-4"/></svg>',
  achat: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"><path d="M4 8h13l-3-3M17 8l-3 3M20 16H7l3-3M7 16l3 3"/></svg>',
  tirage: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="5" y="3" width="14" height="18" rx="2.5"/><path d="M5 14l5-3v9"/></svg>',
  echange: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M4 8h13l-3.5-3.5M17 8l-3.5 3.5"/><path d="M20 16H7l3.5-3.5M7 16l3.5 3.5"/></svg>',
};

function ilYA(date){
  const s = Math.max(0, Math.round((Date.now() - new Date(date).getTime()) / 1000));
  if(s < 60) return "à l'instant";
  if(s < 3600) return `il y a ${Math.floor(s / 60)} min`;
  if(s < 86400) return `il y a ${formatDuree(s * 1000)}`;
  const jours = Math.floor(s / 86400);
  return jours === 1 ? 'hier' : `il y a ${jours} jours`;
}

function ligneJournal(e){
  const moi = (p) => p ? `<b>${echapperTexte(p)}</b>` : 'un joueur';
  // "Tu as conquis" quand c'est moi, "ROBOI a conquis" sinon
  const acteur = e.je_suis_acteur ? '<b>Tu</b>' : moi(e.acteur_pseudo);
  const a = e.je_suis_acteur ? 'as' : 'a';
  const cible = e.je_suis_cible ? '<b>toi</b>' : moi(e.cible_pseudo);
  const commune = `<b class="jr-commune ${e.tier || ''}">${echapperTexte(e.commune_nom || 'une commune')}</b>`;
  let texte;
  if(e.type === 'conquete') texte = `${acteur} ${a} conquis ${commune}${e.cible_pseudo ? ` sur ${cible}` : ''}`;
  else if(e.type === 'defense') texte = `${acteur} ${a} repoussé une attaque de ${cible} sur ${commune}`;
  else if(e.type === 'achat') texte = `${acteur} ${a} acheté ${commune}${e.cible_pseudo ? ` à ${cible}` : ''}`;
  else if(e.type === 'echange') texte = `${acteur} ${a} reçu ${commune}${e.cible_pseudo ? ` de ${cible}` : ''} en échange`;
  else texte = `${acteur} ${a} tiré ${e.tier === 'legendaire' ? 'une légendaire' : 'une rare'} : ${commune}`;
  const perso = e.je_suis_cible && (e.type === 'conquete' || e.type === 'achat');
  return `
    <div class="jr-ligne ${e.type} ${perso ? 'perdu' : ''} ${e.je_suis_acteur ? 'moi' : ''}">
      <span class="jr-icone">${ICONES_JOURNAL[e.type] || ICONES_JOURNAL.tirage}</span>
      <span class="jr-texte">${texte}</span>
      <span class="jr-date">${ilYA(e.cree_le)}</span>
    </div>`;
}

async function loadJournal(){
  const bloc = document.getElementById('journal');
  const { data, error } = await sb.rpc('journal', { p_mode: journalMode, p_limite: 30 });
  if(error){
    if(bloc) bloc.hidden = true;
    return;
  }
  if(bloc) bloc.hidden = false;
  const liste = document.getElementById('journalListe');
  if(!liste) return;
  liste.innerHTML = (data || []).length
    ? data.map(ligneJournal).join('')
    : `<p class="collection-empty">${journalMode === 'moi' ? "Rien ne te concerne pour l'instant : ouvre des paquets et pars à l'attaque." : 'Aucune activité pour le moment.'}</p>`;
}

document.getElementById('journal').addEventListener('click', (e) => {
  const b = e.target.closest('[data-journal]');
  if(!b) return;
  journalMode = b.dataset.journal;
  document.querySelectorAll('#journal [data-journal]').forEach(x => x.classList.toggle('active', x === b));
  loadJournal();
});

// ---------- Classement ----------
let classementMode = 'general';
let classementComplet = false;
let classementDonnees = [];
let classementOuvert = (() => {
  try{
    const v = localStorage.getItem('tf-classement-ouvert');
    if(v !== null) return v === '1';
  } catch(e){}
  // replie par defaut sur telephone, pour laisser la place a la carte
  return !window.matchMedia('(max-width: 760px)').matches;
})();

async function loadClassement(){
  const bloc = document.getElementById('classement');
  const { data, error } = await sb.rpc('classement', { p_mode: classementMode, p_limite: classementComplet ? 50 : 10 });
  if(error){
    // classement.sql pas encore execute : on masque le bloc au lieu d'afficher un titre vide
    if(bloc) bloc.hidden = true;
    console.error('Classement :', error.message);
    return;
  }
  classementDonnees = data || [];
  renderClassement();
}

function renderClassement(){
  const podium = document.getElementById('clPodium');
  const liste = document.getElementById('clListe');
  const plus = document.getElementById('clPlus');
  const bloc = document.getElementById('classement');
  if(!podium || !liste || !bloc) return;
  bloc.hidden = false;
  bloc.classList.toggle('replie', !classementOuvert);
  const bouton = document.getElementById('clReplier');
  if(bouton){
    bouton.setAttribute('aria-expanded', String(classementOuvert));
    bouton.setAttribute('aria-label', classementOuvert ? 'Replier le classement' : 'Afficher le classement');
  }
  if(!classementOuvert){
    // replie : on ne garde que ma position, en une ligne
    const moi = classementDonnees.find(l => l.est_moi);
    podium.innerHTML = '';
    liste.innerHTML = moi
      ? `<button class="cl-ligne moi" data-joueur-id="${echapperTexte(moi.joueur_id)}">
           <span class="cl-rang">${moi.rang}</span>
           <span class="cl-pastille" style="background:${COULEUR_MOI}"></span>
           <span class="cl-pseudo"><b>Toi</b></span>
           <span class="cl-detail">${Number(moi.communes).toLocaleString('fr-FR')}</span>
           <span class="cl-score">${Number(moi.score).toLocaleString('fr-FR')}<small>pts</small></span>
         </button>` : '';
    if(plus) plus.hidden = true;
    return;
  }
  if(classementDonnees.length === 0){
    podium.innerHTML = '';
    liste.innerHTML = `<p class="collection-empty">${classementMode === 'mois' ? 'Aucune commune prise ce mois-ci pour le moment.' : 'Le classement apparaîtra dès que des communes seront possédées.'}</p>`;
    if(plus) plus.hidden = true;
    return;
  }
  const couleur = (l) => l.est_moi ? COULEUR_MOI : colorForPlayer(l.joueur_id);
  const nb = (n) => Number(n).toLocaleString('fr-FR');

  const trois = classementDonnees.filter(l => l.rang <= 3);
  const ordre = [trois.find(l => l.rang === 2), trois.find(l => l.rang === 1), trois.find(l => l.rang === 3)].filter(Boolean);
  podium.innerHTML = ordre.map(l => `
    <button class="cl-marche r${l.rang} ${l.est_moi ? 'moi' : ''}" data-joueur-id="${echapperTexte(l.joueur_id)}" title="Mettre son territoire en évidence">
      <span class="cl-rang">${l.rang}</span>
      <span class="cl-pastille" style="background:${couleur(l)}"></span>
      <span class="cl-pseudo">${l.est_moi ? 'Toi' : echapperTexte(l.pseudo)}</span>
      <span class="cl-score">${nb(l.score)}<small>pts</small></span>
      <span class="cl-detail">${nb(l.communes)} commune${l.communes > 1 ? 's' : ''}</span>
    </button>`).join('');

  const suite = classementDonnees.filter(l => l.rang > 3);
  liste.innerHTML = suite.map(l => `
    <button class="cl-ligne ${l.est_moi ? 'moi' : ''}" data-joueur-id="${echapperTexte(l.joueur_id)}" title="Mettre son territoire en évidence">
      <span class="cl-rang">${l.rang}</span>
      <span class="cl-pastille" style="background:${couleur(l)}"></span>
      <span class="cl-pseudo">${l.est_moi ? '<b>Toi</b>' : echapperTexte(l.pseudo)}</span>
      <span class="cl-mini">${l.legendaires > 0 ? `<i class="cl-etoile">★</i>${nb(l.legendaires)}` : ''}${l.rares > 0 ? `<i class="cl-rond"></i>${nb(l.rares)}` : ''}</span>
      <span class="cl-detail">${nb(l.communes)}</span>
      <span class="cl-score">${nb(l.score)}<small>pts</small></span>
    </button>`).join('');

  if(plus){
    plus.hidden = classementComplet || classementDonnees.length < 10;
  }
}

document.getElementById('classement').addEventListener('click', (e) => {
  if(e.target.closest('#clReplier')){
    classementOuvert = !classementOuvert;
    try{ localStorage.setItem('tf-classement-ouvert', classementOuvert ? '1' : '0'); } catch(err){}
    renderClassement();
    return;
  }
  const mode = e.target.closest('[data-mode]');
  if(mode){
    classementMode = mode.dataset.mode;
    classementComplet = false;
    document.querySelectorAll('#classement [data-mode]').forEach(b => b.classList.toggle('active', b === mode));
    loadClassement();
    return;
  }
  if(e.target.closest('#clPlus')){
    classementComplet = true;
    document.getElementById('clPlus').hidden = true;
    loadClassement();
    return;
  }
  // Depuis le classement, on ouvre la fiche. Le surlignage du territoire
  // obligeait de toute facon a changer d'onglet, et la fiche porte un bouton
  // qui le fait. La legende de la carte, elle, garde le clic direct : on y est
  // deja devant la carte et on veut aller vite.
  const ligne = e.target.closest('[data-joueur-id]');
  if(ligne) ouvrirProfil(ligne.dataset.joueurId);
});

// ---------- Contours reels des communes ----------
// Fichiers statiques (dossier contours/), charges par departement seulement en zoomant.
// Ils viennent de GitHub, pas de Supabase : ils ne consomment rien du quota.
const SEUIL_CONTOURS = 2.2;       // en dessous, on garde l'affichage simplifie
const CONTOURS = new Map();        // departement -> { communes } ou 'charge' / 'erreur'
let contoursEnCours = 0;

async function chargerContours(dep){
  if(CONTOURS.has(dep)) return CONTOURS.get(dep);
  CONTOURS.set(dep, null); // evite de demander deux fois le meme
  contoursEnCours++;
  try{
    const rep = await fetch(`contours/${dep}.json`, { cache: 'force-cache' });
    if(!rep.ok) throw new Error('introuvable');
    const data = await rep.json();
    CONTOURS.set(dep, data);
    return data;
  } catch(e){
    CONTOURS.set(dep, 'erreur');
    return 'erreur';
  } finally {
    contoursEnCours--;
    if(contoursEnCours === 0) renderMapOverlay();
  }
}

// departements actuellement visibles a l'ecran
function departementsVisibles(liste){
  const wrap = document.getElementById('mapWrap');
  if(!wrap) return new Set();
  const w = wrap.clientWidth, h = wrap.clientHeight;
  const vus = new Set();
  const ajouter = (c) => {
    if(c.lat == null) return;
    const p = project(c.lat, c.lon);
    const x = p.x * w * mapZoom + mapPanX, y = p.y * h * mapZoom + mapPanY;
    if(x > -60 && x < w + 60 && y > -60 && y < h + 60) vus.add(c.dept);
  };
  for(const c of liste) ajouter(c);
  // sans ca, une commune perdue dans un departement ou l'on ne possede plus
  // rien n'aurait jamais ses contours charges : elle resterait invisible
  if(CALQUES.passage) for(const c of perduesMap.values()) ajouter(c);
  return vus;
}

function cheminContour(poly){
  let d = '';
  for(const anneau of poly){
    d += 'M' + anneau.map(([lon, lat]) => {
      const p = project(lat, lon);
      return (p.x * MAP_W).toFixed(1) + ',' + (p.y * MAP_H).toFixed(1);
    }).join('L') + 'Z';
  }
  return d;
}

// ---------- Vue d'ensemble : la France par departements ----------
// De loin, on colorie chaque departement selon le joueur qui y domine.
let CONTOURS_DEPTS = null;   // null = pas encore demande, 'erreur' si indisponible
async function chargerDepartements(){
  if(CONTOURS_DEPTS) return CONTOURS_DEPTS;
  CONTOURS_DEPTS = 'attente';
  try{
    const rep = await fetch('contours-departements.json', { cache: 'force-cache' });
    if(!rep.ok) throw new Error('introuvable');
    CONTOURS_DEPTS = await rep.json();
  } catch(e){
    CONTOURS_DEPTS = 'erreur';
  }
  renderMapOverlay();
  return CONTOURS_DEPTS;
}

function dessinerDepartements(liste, joueurs){
  const couche = document.getElementById('mapTerritoires');
  const defs = document.getElementById('mapDefsDyn');
  const marq = document.getElementById('mapMarqueurs');
  const survol = document.getElementById('mapSurvol');
  const idSvg = (id) => 'j' + String(id).replace(/[^a-zA-Z0-9_-]/g, '');
  const e = 1 / Math.max(1, mapZoom);

  // qui domine chaque departement, et avec quelle avance
  const parDept = new Map();
  for(const c of liste){
    if(!parDept.has(c.dept)) parDept.set(c.dept, { total: 0, joueurs: new Map(), legendaires: [] });
    const d = parDept.get(c.dept);
    d.total++;
    d.joueurs.set(c.joueur, (d.joueurs.get(c.joueur) || 0) + 1);
    if(c.tier === 'legendaire') d.legendaires.push(c);
  }

  const parJoueur = new Map();
  let fond = '', marqueurs = '', zonesSurvol = '';
  for(const [dep, info] of parDept){
    const poly = CONTOURS_DEPTS[dep];
    if(!poly) continue;
    const d = cheminContour(poly);
    let chef = null, meilleur = 0;
    for(const [j, n] of info.joueurs){ if(n > meilleur){ meilleur = n; chef = j; } }
    const part = meilleur / info.total;
    if(!parJoueur.has(chef)) parJoueur.set(chef, '');
    const jo = joueurs.get(chef);
    // plus la domination est nette, plus la couleur est franche
    const force = (0.3 + 0.55 * part) * (jo.moi ? 1 : 0.8);
    parJoueur.set(chef, parJoueur.get(chef) + `<path d="${d}" fill="${jo.couleur}" fill-opacity="${force.toFixed(2)}"/>`);
    const nom = DEPT_NAMES[dep] || dep;
    const detail = [...info.joueurs.entries()].sort((a, b) => b[1] - a[1]).slice(0, 3)
      .map(([j, n]) => `${joueurs.get(j).moi ? 'toi' : joueurs.get(j).pseudo} : ${n}`).join(', ');
    zonesSurvol += `<path d="${d}" fill="transparent"><title>${echapperHtml(nom)} (${dep}) — ${info.total} commune${info.total > 1 ? 's' : ''} possédée${info.total > 1 ? 's' : ''}\n${echapperHtml(detail)}</title></path>`;
    for(const c of info.legendaires){
      const p = project(c.lat, c.lon);
      const j = joueurs.get(c.joueur);
      marqueurs += `<polygon points="${etoileSvg(p.x * MAP_W, p.y * MAP_H, (j.moi ? 7 : 6) * e)}" fill="${j.moi ? '#FFF6D6' : 'rgba(255,246,214,0.8)'}" stroke="#0B1830" stroke-width="${(1.2 * e).toFixed(2)}"/>`;
    }
  }

  defs.innerHTML = '';
  couche.innerHTML =
    [...parJoueur.entries()]
      .sort((a, b) => (a[0] === ID_MOI ? 1 : 0) - (b[0] === ID_MOI ? 1 : 0))
      .map(([id, d]) => `<g data-joueur="${idSvg(id)}">${d}</g>`).join('') +
    `<g fill="none" stroke="rgba(169,188,212,0.28)" stroke-width="${(0.9 * e).toFixed(2)}">${
      Object.keys(CONTOURS_DEPTS).map(dep => `<path d="${cheminContour(CONTOURS_DEPTS[dep])}"/>`).join('')}</g>`;
  marq.innerHTML = marqueurs;
  survol.innerHTML = zonesSurvol;

  if(joueurSurligne && !joueurs.has(joueurSurligne)) joueurSurligne = null;
  if(!showOthers && joueurSurligne !== ID_MOI) joueurSurligne = null;
  appliquerSurlignageCarte(idSvg);
  renderLegendeCarte(joueurs, idSvg);
}

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

// ============================================================
//  Rendu de la carte sur canvas  (?canvas=1)
// ============================================================
// Le SVG construit des milliers de noeuds a chaque redessin. Ici on peint
// directement : les chemins sont calcules une fois en Path2D, et le deplacement
// n'est plus une transformation CSS mais un changement de repere du contexte.
// Consequence : plus de couche promue par le navigateur, donc plus de flou.
// Le canvas est le rendu normal. ?svg=1 rebascule sur l'ancien rendu : porte de
// sortie a donner a un joueur qui signalerait un probleme d'affichage.
const MODE_CANVAS = !new URLSearchParams(location.search).has('svg');

const CV = {
  ctx: null,
  dpr: 1,
  largeur: 0, hauteur: 0,      // en pixels CSS
  dessinPlanifie: false,
  fond: null,                  // { terre, cote, topo, ombre } en Path2D
  cheminsCommunes: new Map(),  // code commune -> Path2D
  cheminsDepts: new Map(),     // numero departement -> Path2D
  frontieres: null,            // { fDept, fReg, etiquettes }, calcule une fois
  cellules: null,              // { cles, cellules, cercles } pour la vue de repli
  cellulesSignature: '',
  donnees: null,               // liste des territoires, recalculee seulement si besoin
  donneesSignature: '',
  survol: null,                // commune sous le curseur
  reperage: null,              // { delaunay, liste } pour retrouver une commune
};

function canvasActif(){
  return MODE_CANVAS && CV.ctx;
}

// L'echelle entre les coordonnees de la carte et les pixels du cadre.
// Le SVG utilise un viewBox 0 0 MAP_W MAP_H etire sur toute la largeur du cadre :
// on reproduit exactement le meme rapport pour que les deux rendus coincident.
function echelleCarte(){
  const wrap = document.getElementById('mapWrap');
  if(!wrap || !MAP_W) return 1;
  return wrap.clientWidth / MAP_W;
}

function initCanvas(){
  const cv = document.getElementById('mapCanvas');
  const wrap = document.getElementById('mapWrap');
  if(!cv || !wrap || !MODE_CANVAS) return;
  wrap.classList.add('en-canvas');
  CV.ctx = cv.getContext('2d');
  redimensionnerCanvas();
  window.addEventListener('resize', () => { redimensionnerCanvas(); demanderDessin(); });
}

function redimensionnerCanvas(){
  const cv = document.getElementById('mapCanvas');
  const wrap = document.getElementById('mapWrap');
  if(!cv || !wrap || !CV.ctx) return;
  // au-dela de 2 le gain est invisible et le cout de remplissage double
  CV.dpr = Math.min(window.devicePixelRatio || 1, 2);
  CV.largeur = wrap.clientWidth;
  CV.hauteur = wrap.clientHeight;
  cv.width = Math.round(CV.largeur * CV.dpr);
  cv.height = Math.round(CV.hauteur * CV.dpr);
}

function demanderDessin(){
  if(!canvasActif() || CV.dessinPlanifie) return;
  CV.dessinPlanifie = true;
  requestAnimationFrame(() => { CV.dessinPlanifie = false; dessinerCanvas(); });
}

// Le decor vient des chemins deja calcules dans le SVG : aucune geometrie a refaire.
function cheminsDuFond(){
  if(CV.fond) return CV.fond;
  const d = (id) => {
    const el = document.getElementById(id);
    const s = el && el.getAttribute('d');
    return s ? new Path2D(s) : null;
  };
  const terre = d('mapTerre');
  if(!terre) return null;              // le contour n'est pas encore charge
  CV.fond = { terre, cote: d('mapCote'), topo: d('mapTopo'), ombre: d('mapOmbre') };
  return CV.fond;
}

function cheminCommuneCanvas(code, poly){
  let p = CV.cheminsCommunes.get(code);
  if(!p){ p = new Path2D(cheminContour(poly)); CV.cheminsCommunes.set(code, p); }
  return p;
}

function cheminDeptCanvas(dep, poly){
  let p = CV.cheminsDepts.get(dep);
  if(!p){ p = new Path2D(cheminContour(poly)); CV.cheminsDepts.set(dep, p); }
  return p;
}

function dessinerCanvas(){
  if(!canvasActif() || !mapBounds) return;
  const ctx = CV.ctx;
  const k = echelleCarte() * mapZoom * CV.dpr;
  const tx = mapPanX * CV.dpr, ty = mapPanY * CV.dpr;

  ctx.setTransform(1, 0, 0, 1, 0, 0);
  ctx.clearRect(0, 0, CV.largeur * CV.dpr, CV.hauteur * CV.dpr);

  // la mer, en degrade comme dans le SVG
  const g = ctx.createRadialGradient(
    CV.largeur * CV.dpr * 0.45, CV.hauteur * CV.dpr * 0.4, 0,
    CV.largeur * CV.dpr * 0.45, CV.hauteur * CV.dpr * 0.4, CV.largeur * CV.dpr * 0.75);
  g.addColorStop(0, '#12294A');
  g.addColorStop(1, '#081427');
  ctx.fillStyle = g;
  ctx.fillRect(0, 0, CV.largeur * CV.dpr, CV.hauteur * CV.dpr);

  const fond = cheminsDuFond();
  if(!fond) return;

  ctx.setTransform(k, 0, 0, k, tx, ty);
  ctx.lineJoin = 'round';
  ctx.lineCap = 'round';
  const trait = (px) => px / k * CV.dpr;   // epaisseur constante a l'ecran

  // ombre portee, puis la terre
  if(fond.ombre){
    ctx.save(); ctx.translate(0, 7);
    ctx.fillStyle = 'rgba(0,0,0,0.28)'; ctx.fill(fond.ombre);
    ctx.restore();
  }
  const gt = ctx.createLinearGradient(0, 0, 0, MAP_H);
  gt.addColorStop(0, '#20406A');
  gt.addColorStop(1, '#172F52');
  ctx.fillStyle = gt;
  ctx.fill(fond.terre);

  if(fond.topo){
    ctx.save(); ctx.clip(fond.terre);
    ctx.strokeStyle = 'rgba(169,188,212,0.09)'; ctx.lineWidth = trait(1);
    ctx.stroke(fond.topo);
    ctx.restore();
  }

  dessinerTerritoiresCanvas(ctx, trait, k);

  if(fond.cote){
    ctx.strokeStyle = 'rgba(169,188,212,0.45)'; ctx.lineWidth = trait(1.2);
    ctx.stroke(fond.cote);
  }
  ctx.setTransform(1, 0, 0, 1, 0, 0);
  dessinerNomsRegions(ctx);
}

// Reprend le meme decoupage que le rendu SVG : de loin les departements,
// de pres les vraies communes, et a defaut des zones approchees.
// Le resultat ne change qu'avec les donnees, l'affichage des autres joueurs,
// ou le franchissement d'un palier de zoom : on le garde en cache, sinon on
// refait ce calcul soixante fois par seconde pendant un pincement.
function bandeDeZoom(){
  const seuils = Object.values(ZOOM_MINI).concat([SEUIL_CONTOURS]).sort((a, b) => a - b);
  let n = 0;
  for(const s of seuils) if(mapZoom >= s) n++;
  return n;
}

function territoiresVisiblesCache(){
  const signature = [collectionMap.size, othersMap.size, showOthers ? 1 : 0, bandeDeZoom()].join('|');
  if(CV.donnees && CV.donneesSignature === signature) return CV.donnees;
  CV.donneesSignature = signature;
  CV.donnees = territoiresVisibles();
  majReperage(CV.donnees.liste, CV.donnees.joueurs);
  return CV.donnees;
}

function territoiresVisibles(){
  const joueurs = new Map();
  joueurs.set(ID_MOI, { id: ID_MOI, pseudo: 'Toi', couleur: COULEUR_MOI, fonce: couleurFoncee(COULEUR_MOI), moi: true, nb: 0 });
  const liste = [];
  for(const e of collectionMap.values()){
    if(!METRO_DEPT_RE.test(e.dept) || e.lat == null) continue;
    liste.push({ code: e.code, nom: e.nom, dept: e.dept, lat: e.lat, lon: e.lon, tier: e.tier.id, joueur: ID_MOI });
    joueurs.get(ID_MOI).nb++;
  }
  MASQUEES_PAR_ZOOM.commun = 0;
  MASQUEES_PAR_ZOOM.peucommun = 0;
  for(const e of othersMap.values()){
    if(!METRO_DEPT_RE.test(e.dept) || e.lat == null) continue;
    const visible = mapZoom < SEUIL_CONTOURS || mapZoom >= (ZOOM_MINI[e.tier.id] || 1);
    if(showOthers && !visible && MASQUEES_PAR_ZOOM[e.tier.id] !== undefined) MASQUEES_PAR_ZOOM[e.tier.id]++;
    if(!joueurs.has(e.joueurId)){
      const couleur = colorForPlayer(e.joueurId);
      joueurs.set(e.joueurId, { id: e.joueurId, pseudo: e.pseudo, couleur, fonce: couleurFoncee(couleur), moi: false, nb: 0 });
    }
    joueurs.get(e.joueurId).nb++;
    if(showOthers && visible) liste.push({ code: e.code, nom: e.nom, dept: e.dept, lat: e.lat, lon: e.lon, tier: e.tier.id, joueur: e.joueurId });
  }
  return { liste, joueurs };
}

// un joueur mis en evidence eteint les autres
function opaciteJoueur(id, base){
  if(!joueurSurligne) return base;
  return id === joueurSurligne ? Math.min(1, base + 0.15) : base * 0.22;
}

function dessinerTerritoiresCanvas(ctx, trait, k){
  const { liste, joueurs } = territoiresVisiblesCache();
  if(joueurSurligne && !joueurs.has(joueurSurligne)) joueurSurligne = null;
  if(!showOthers && joueurSurligne !== ID_MOI) joueurSurligne = null;
  const mode = dessinerFondsCanvas(ctx, trait, k, liste, joueurs);
  dessinerFrontieres(ctx, trait, mode === 'contours');
  if(CALQUES.raretes) dessinerMarqueursCanvas(ctx, liste, joueurs, k, mode === 'depts');
  majLegendeSiBesoin(joueurs);
}

// Renvoie le mode retenu : 'depts', 'contours' ou 'cellules'.
function dessinerFondsCanvas(ctx, trait, k, liste, joueurs){
  const ordre = (ids) => ids.slice().sort((a, b) => (a === ID_MOI ? 1 : 0) - (b === ID_MOI ? 1 : 0));

  if(liste.length === 0) return 'vide';
  if(!CALQUES.communes) return mapZoom < SEUIL_CONTOURS ? 'depts' : 'contours';

  // ---- de loin : la France par departements ----
  if(mapZoom < SEUIL_CONTOURS){
    if(!CONTOURS_DEPTS) chargerDepartements();
    if(CONTOURS_DEPTS && CONTOURS_DEPTS !== 'erreur' && CONTOURS_DEPTS !== 'attente'){
      const chef = new Map();   // departement -> { joueur, force }
      const compte = new Map();
      for(const c of liste){
        if(!compte.has(c.dept)) compte.set(c.dept, new Map());
        const m = compte.get(c.dept);
        m.set(c.joueur, (m.get(c.joueur) || 0) + 1);
      }
      for(const [dep, m] of compte){
        let meilleur = null, n = 0, total = 0;
        for(const [j, v] of m){ total += v; if(v > n){ n = v; meilleur = j; } }
        const jo = joueurs.get(meilleur);
        // plus la domination est nette, plus la couleur est franche
        const force = (0.3 + 0.55 * (n / total)) * (jo && jo.moi ? 1 : 0.8);
        chef.set(dep, { joueur: meilleur, force });
      }
      for(const [dep, info] of chef){
        if(!CONTOURS_DEPTS[dep]) continue;
        const j = joueurs.get(info.joueur);
        if(!j) continue;
        ctx.globalAlpha = opaciteJoueur(info.joueur, info.force);
        ctx.fillStyle = j.couleur;
        ctx.fill(cheminDeptCanvas(dep, CONTOURS_DEPTS[dep]));
        ctx.globalAlpha = 1;
      }
      return 'depts';
    }
  }

  // ---- de pres : les vraies limites communales ----
  if(mapZoom >= SEUIL_CONTOURS){
    const deps = departementsVisibles(liste);
    let pretes = 0;
    for(const dep of deps){
      const c = CONTOURS.get(dep);
      if(c === undefined) chargerContours(dep);
      else if(c && c !== 'erreur') pretes++;
    }
    if(pretes > 0){
      const possedees = new Map(liste.map(c => [c.code, c]));
      const parJoueur = new Map();
      // les communes libres, en un seul chemin
      const libres = new Path2D();
      // calque « Mon passage » : ce que j'ai eu et que je n'ai plus.
      // Deux sorts differents — libre, on la repeint ; reprise, on se contente
      // d'un lisere pour ne pas mentir sur son proprietaire actuel.
      const passage = CALQUES.passage && perduesMap.size > 0;
      const perduLibre = new Path2D();
      const perduPris = new Path2D();
      for(const dep of deps){
        const contours = CONTOURS.get(dep);
        if(!contours || contours === 'erreur') continue;
        for(const code in contours){
          const p = cheminCommuneCanvas(code, contours[code]);
          const c = possedees.get(code);
          const etaitAMoi = passage && perduesMap.has(code);
          // quand on cache le territoire des autres, une commune reprise n'a
          // plus rien dessous : elle retombe naturellement dans « libre »
          if(!c){ (etaitAMoi ? perduLibre : libres).addPath(p); continue; }
          if(etaitAMoi) perduPris.addPath(p);
          if(!parJoueur.has(c.joueur)) parJoueur.set(c.joueur, new Path2D());
          parJoueur.get(c.joueur).addPath(p);
        }
      }
      ctx.fillStyle = 'rgba(22,48,79,0.75)';
      ctx.strokeStyle = '#20406A'; ctx.lineWidth = trait(0.6);
      ctx.fill(libres); ctx.stroke(libres);

      if(passage){
        ctx.fillStyle = COULEUR_MOI;
        // 0.20 virait au kaki sur le bleu du fond et ne se lisait plus comme
        // « c'etait a moi » ; 0.30 garde la parente avec le jaune plein tout
        // en restant nettement en retrait
        ctx.globalAlpha = 0.30;
        ctx.fill(perduLibre);
        ctx.globalAlpha = 0.75;
        ctx.strokeStyle = COULEUR_MOI; ctx.lineWidth = trait(1.2);
        ctx.setLineDash([trait(5), trait(4)]);
        ctx.stroke(perduLibre);
        ctx.setLineDash([]);
        ctx.globalAlpha = 1;
      }

      for(const id of ordre([...parJoueur.keys()])){
        const j = joueurs.get(id);
        const p = parJoueur.get(id);
        ctx.globalAlpha = opaciteJoueur(id, 1);
        ctx.strokeStyle = '#07111F'; ctx.lineWidth = trait(3.4); ctx.stroke(p);
        ctx.globalAlpha = opaciteJoueur(id, j.moi ? 0.95 : 0.78);
        ctx.fillStyle = j.couleur; ctx.fill(p);
        ctx.globalAlpha = opaciteJoueur(id, 0.55);
        ctx.strokeStyle = j.fonce; ctx.lineWidth = trait(0.7); ctx.stroke(p);
        ctx.globalAlpha = 1;
      }
      // le lisere des communes reprises : trace apres les fonds, sinon la
      // couleur du nouveau proprietaire le recouvrirait
      if(passage){
        ctx.strokeStyle = COULEUR_MOI;
        ctx.lineWidth = trait(3.4);
        ctx.globalAlpha = 0.95;
        ctx.stroke(perduPris);
        ctx.globalAlpha = 1;
      }

      // communes possedees dont le departement n'est pas encore charge : une
      // pastille, en attendant que ses vraies limites arrivent
      // un seul chemin par joueur : deux appels de dessin au lieu de deux par commune
      const ep = 1 / Math.max(1, mapZoom);
      const pastilles = new Map();
      for(const c of liste){
        const etat = CONTOURS.get(c.dept);
        if(etat && etat !== 'erreur') continue;
        if(!joueurs.has(c.joueur)) continue;
        if(!pastilles.has(c.joueur)) pastilles.set(c.joueur, new Path2D());
        const pt = project(c.lat, c.lon);
        const x = pt.x * MAP_W, y = pt.y * MAP_H, r = RAYON_ZONE[c.tier] * ep;
        const chemin = pastilles.get(c.joueur);
        chemin.moveTo(x + r, y);
        chemin.arc(x, y, r, 0, Math.PI * 2);
      }
      for(const id of ordre([...pastilles.keys()])){
        const j = joueurs.get(id), chemin = pastilles.get(id);
        ctx.globalAlpha = opaciteJoueur(id, j.moi ? 0.95 : 0.7);
        ctx.fillStyle = j.couleur; ctx.fill(chemin);
        ctx.globalAlpha = opaciteJoueur(id, 1);
        ctx.strokeStyle = '#07111F'; ctx.lineWidth = 2 * ep; ctx.stroke(chemin);
        ctx.globalAlpha = 1;
      }
      return 'contours';
    }
  }

  // ---- a defaut : zones approchees par cellules de Voronoi ----
  dessinerCellulesCanvas(ctx, trait, liste, joueurs, ordre);
  return 'cellules';
}

// La legende ne bouge que si la liste des joueurs ou le surlignage change :
// la redessiner a chaque image coutait plus cher que toute la carte.
let legendeSignature = '';
function majLegendeSiBesoin(joueurs){
  // sans l'etat replie ni la liste complete, les boutons de la legende
  // changeaient la variable sans jamais redessiner
  const sig = [...joueurs.values()].map(j => j.id + ':' + j.nb).join(',')
    + '|' + (joueurSurligne || '')
    + '|' + (legendeOuverte ? 1 : 0)
    + '|' + (listeJoueursComplete ? 1 : 0)
    + '|' + (showOthers ? 1 : 0)
    + '|' + TOTAL_COMMUNES;
  if(sig === legendeSignature) return;
  legendeSignature = sig;
  renderLegendeCarte(joueurs, (x) => 'j' + x);
}

function dessinerCellulesCanvas(ctx, trait, liste, joueurs, ordre){
  const signature = liste.length + ':' + liste.map(c => c.code).join(',');
  if(CV.cellulesSignature !== signature){
    CV.cellulesSignature = signature;
    const pts = liste.map(c => { const p = project(c.lat, c.lon); return [p.x * MAP_W, p.y * MAP_H]; });
    const parJoueur = new Map();
    let rayons = liste.map(c => RAYON_ZONE[c.tier]);
    let voronoi = null;
    if(D3_OK && liste.length > 0){
      const delaunay = d3.Delaunay.from(pts);
      voronoi = delaunay.voronoi([0, 0, MAP_W, MAP_H]);
      rayons = liste.map((c, i) => {
        let dMin = Infinity;
        for(const kk of delaunay.neighbors(i)){
          if(!liste[kk] || kk === i || liste[kk].joueur !== c.joueur) continue;
          dMin = Math.min(dMin, Math.hypot(pts[kk][0] - pts[i][0], pts[kk][1] - pts[i][1]));
        }
        return dMin <= 22 ? Math.max(RAYON_ZONE[c.tier], dMin * 0.62) : RAYON_ZONE[c.tier];
      });
    }
    liste.forEach((c, i) => {
      if(!parJoueur.has(c.joueur)) parJoueur.set(c.joueur, { cellules: new Path2D(), cercles: new Path2D() });
      const g = parJoueur.get(c.joueur);
      const [x, y] = pts[i], r = rayons[i];
      const cellule = voronoi ? voronoi.renderCell(i) : '';
      if(cellule) g.cellules.addPath(new Path2D(cellule));
      else { g.cellules.moveTo(x + r, y); g.cellules.arc(x, y, r, 0, Math.PI * 2); }
      g.cercles.moveTo(x + r, y); g.cercles.arc(x, y, r, 0, Math.PI * 2);
    });
    CV.cellules = parJoueur;
  }
  const parJoueur = CV.cellules;
  if(!parJoueur) return;
  for(const id of ordre([...parJoueur.keys()])){
    const j = joueurs.get(id);
    if(!j) continue;
    const g = parJoueur.get(id);
    // la cellule est rognee par un disque : une commune isolee reste une tache ronde,
    // deux voisines du meme joueur se rejoignent en un territoire continu
    ctx.save();
    ctx.clip(g.cercles);
    ctx.globalAlpha = opaciteJoueur(id, j.moi ? 0.95 : 0.62);
    ctx.fillStyle = j.couleur;
    ctx.fill(g.cellules);
    ctx.globalAlpha = opaciteJoueur(id, j.moi ? 0.6 : 0.25);
    ctx.strokeStyle = j.fonce; ctx.lineWidth = trait(j.moi ? 0.7 : 0.5);
    ctx.stroke(g.cellules);
    ctx.restore();
    ctx.globalAlpha = 1;
  }
}

// Etoiles et pastilles : taille constante a l'ecran, comme dans le SVG
function dessinerMarqueursCanvas(ctx, liste, joueurs, k, legendairesSeules){
  const e = 1 / Math.max(1, mapZoom);
  for(const c of liste){
    if(c.tier !== 'legendaire' && (legendairesSeules || c.tier !== 'rare')) continue;
    const j = joueurs.get(c.joueur);
    if(!j) continue;
    const p = project(c.lat, c.lon);
    const x = p.x * MAP_W, y = p.y * MAP_H;
    ctx.globalAlpha = opaciteJoueur(c.joueur, 1);
    if(c.tier === 'legendaire'){
      const r = (j.moi ? 7 : 6) * e;
      ctx.beginPath();
      for(let i = 0; i < 10; i++){
        const a = -Math.PI / 2 + i * Math.PI / 5;
        const rr = i % 2 ? r * 0.45 : r;
        ctx.lineTo(x + Math.cos(a) * rr, y + Math.sin(a) * rr);
      }
      ctx.closePath();
      ctx.fillStyle = j.moi ? '#FFF6D6' : 'rgba(255,246,214,' + (legendairesSeules ? '0.8' : '0.75') + ')';
      ctx.fill();
      ctx.strokeStyle = '#0B1830';
      ctx.lineWidth = (legendairesSeules ? 1.2 : (j.moi ? 1.4 : 1)) * e;
      ctx.stroke();
    } else {
      ctx.beginPath(); ctx.arc(x, y, 2.2 * e, 0, Math.PI * 2);
      ctx.fillStyle = j.moi ? '#fff' : 'rgba(255,255,255,0.7)';
      ctx.fill();
      ctx.strokeStyle = '#0B1830'; ctx.lineWidth = 1 * e; ctx.stroke();
    }
    ctx.globalAlpha = 1;
  }
}


// ---------- Regions, frontieres et calques ----------
// Les limites de region ne sont pas un fichier de plus : un segment partage par
// deux departements de regions differentes est une frontiere de region. La
// topologie des contours est propre (chaque segment interieur apparait
// exactement deux fois), donc le trace est exact.
const DEP_REGION = {
  '01':'Auvergne-Rhône-Alpes','03':'Auvergne-Rhône-Alpes','07':'Auvergne-Rhône-Alpes',
  '15':'Auvergne-Rhône-Alpes','26':'Auvergne-Rhône-Alpes','38':'Auvergne-Rhône-Alpes',
  '42':'Auvergne-Rhône-Alpes','43':'Auvergne-Rhône-Alpes','63':'Auvergne-Rhône-Alpes',
  '69':'Auvergne-Rhône-Alpes','73':'Auvergne-Rhône-Alpes','74':'Auvergne-Rhône-Alpes',
  '21':'Bourgogne-Franche-Comté','25':'Bourgogne-Franche-Comté','39':'Bourgogne-Franche-Comté',
  '58':'Bourgogne-Franche-Comté','70':'Bourgogne-Franche-Comté','71':'Bourgogne-Franche-Comté',
  '89':'Bourgogne-Franche-Comté','90':'Bourgogne-Franche-Comté',
  '22':'Bretagne','29':'Bretagne','35':'Bretagne','56':'Bretagne',
  '18':'Centre-Val de Loire','28':'Centre-Val de Loire','36':'Centre-Val de Loire',
  '37':'Centre-Val de Loire','41':'Centre-Val de Loire','45':'Centre-Val de Loire',
  '2A':'Corse','2B':'Corse',
  '08':'Grand Est','10':'Grand Est','51':'Grand Est','52':'Grand Est','54':'Grand Est',
  '55':'Grand Est','57':'Grand Est','67':'Grand Est','68':'Grand Est','88':'Grand Est',
  '02':'Hauts-de-France','59':'Hauts-de-France','60':'Hauts-de-France',
  '62':'Hauts-de-France','80':'Hauts-de-France',
  '75':'Île-de-France','77':'Île-de-France','78':'Île-de-France','91':'Île-de-France',
  '92':'Île-de-France','93':'Île-de-France','94':'Île-de-France','95':'Île-de-France',
  '14':'Normandie','27':'Normandie','50':'Normandie','61':'Normandie','76':'Normandie',
  '16':'Nouvelle-Aquitaine','17':'Nouvelle-Aquitaine','19':'Nouvelle-Aquitaine',
  '23':'Nouvelle-Aquitaine','24':'Nouvelle-Aquitaine','33':'Nouvelle-Aquitaine',
  '40':'Nouvelle-Aquitaine','47':'Nouvelle-Aquitaine','64':'Nouvelle-Aquitaine',
  '79':'Nouvelle-Aquitaine','86':'Nouvelle-Aquitaine','87':'Nouvelle-Aquitaine',
  '09':'Occitanie','11':'Occitanie','12':'Occitanie','30':'Occitanie','31':'Occitanie',
  '32':'Occitanie','34':'Occitanie','46':'Occitanie','48':'Occitanie','65':'Occitanie',
  '66':'Occitanie','81':'Occitanie','82':'Occitanie',
  '44':'Pays de la Loire','49':'Pays de la Loire','53':'Pays de la Loire',
  '72':'Pays de la Loire','85':'Pays de la Loire',
  '04':"Provence-Alpes-Côte d'Azur",'05':"Provence-Alpes-Côte d'Azur",
  '06':"Provence-Alpes-Côte d'Azur",'13':"Provence-Alpes-Côte d'Azur",
  '83':"Provence-Alpes-Côte d'Azur",'84':"Provence-Alpes-Côte d'Azur",
};

const CLE_CALQUES = 'terrafront-calques';
const CALQUES = (() => {
  // « passage » est eteint au depart : il demande un chargement de plus et
  // n'a de sens que pour un joueur qui a deja perdu des communes
  const defaut = { regions: true, depts: true, communes: true, noms: true,
                   raretes: true, passage: false };
  try {
    const v = JSON.parse(localStorage.getItem(CLE_CALQUES) || '{}');
    return Object.assign(defaut, v);
  } catch(e){ return defaut; }
})();

function enregistrerCalques(){
  try { localStorage.setItem(CLE_CALQUES, JSON.stringify(CALQUES)); } catch(e){}
}

// Un seul parcours des contours : on marque chaque segment, puis on en deduit
// les deux jeux de frontieres et la position des etiquettes de region.
function construireFrontieres(){
  if(CV.frontieres || !CONTOURS_DEPTS || CONTOURS_DEPTS === 'erreur' || CONTOURS_DEPTS === 'attente') return CV.frontieres;
  const proprio = new Map();
  const ajouter = (a, b, dep) => {
    // une cle stable quel que soit le sens de parcours du segment
    const cle = (a[0] < b[0] || (a[0] === b[0] && a[1] <= b[1]))
      ? a[0] + ',' + a[1] + '|' + b[0] + ',' + b[1]
      : b[0] + ',' + b[1] + '|' + a[0] + ',' + a[1];
    const e = proprio.get(cle);
    if(e) e.deps.push(dep);
    else proprio.set(cle, { a, b, deps: [dep] });
  };
  const parRegion = new Map();
  for(const dep in CONTOURS_DEPTS){
    for(const anneau of CONTOURS_DEPTS[dep]){
      const n = anneau.length;
      for(let i = 0; i < n; i++) ajouter(anneau[i], anneau[(i + 1) % n], dep);
      const reg = DEP_REGION[dep];
      if(reg){
        if(!parRegion.has(reg)) parRegion.set(reg, { lon: 0, lat: 0, n: 0 });
        const r = parRegion.get(reg);
        for(const p of anneau){ r.lon += p[0]; r.lat += p[1]; r.n++; }
      }
    }
  }
  const fDept = new Path2D(), fReg = new Path2D();
  for(const { a, b, deps } of proprio.values()){
    if(deps.length !== 2) continue;            // la cote est deja tracee ailleurs
    const pa = project(a[1], a[0]), pb = project(b[1], b[0]);
    const x1 = pa.x * MAP_W, y1 = pa.y * MAP_H, x2 = pb.x * MAP_W, y2 = pb.y * MAP_H;
    fDept.moveTo(x1, y1); fDept.lineTo(x2, y2);
    if(DEP_REGION[deps[0]] !== DEP_REGION[deps[1]]){
      fReg.moveTo(x1, y1); fReg.lineTo(x2, y2);
    }
  }
  const etiquettes = [];
  for(const [nom, r] of parRegion){
    const p = project(r.lat / r.n, r.lon / r.n);
    etiquettes.push({ nom: nom.toUpperCase(), x: p.x * MAP_W, y: p.y * MAP_H, poids: r.n });
  }
  // en cas de chevauchement, la plus grande region garde son nom
  etiquettes.sort((a, b) => b.poids - a.poids);
  CV.frontieres = { fDept, fReg, etiquettes };
  return CV.frontieres;
}

// Trois passes : un lisere sombre, un trait clair, un pointille sombre. La
// frontiere reste lisible aussi bien sur un territoire jaune que sur un bleu.
function dessinerFrontieres(ctx, trait, modeContours){
  const f = construireFrontieres();
  if(!f) { if(!CONTOURS_DEPTS) chargerDepartements(); return; }
  if(CALQUES.depts){
    // de pres, les limites communales portent deja le dessin : on attenue
    ctx.strokeStyle = modeContours ? 'rgba(169,188,212,0.16)' : 'rgba(169,188,212,0.28)';
    ctx.lineWidth = trait(0.9);
    ctx.stroke(f.fDept);
  }
  if(CALQUES.regions){
    ctx.strokeStyle = 'rgba(7,17,31,0.55)'; ctx.lineWidth = trait(4.6); ctx.stroke(f.fReg);
    ctx.strokeStyle = 'rgba(214,230,246,0.72)'; ctx.lineWidth = trait(2.1); ctx.stroke(f.fReg);
    ctx.setLineDash([trait(7), trait(5)]);
    ctx.strokeStyle = 'rgba(15,31,56,0.85)'; ctx.lineWidth = trait(1.1); ctx.stroke(f.fReg);
    ctx.setLineDash([]);
  }
}

// Les noms de region s'effacent quand on zoome : le detail prend le relais.
function dessinerNomsRegions(ctx){
  if(!CALQUES.noms) return;
  const f = CV.frontieres;
  if(!f) return;
  const opacite = mapZoom <= 1.6 ? 1 : mapZoom >= 2.6 ? 0 : (2.6 - mapZoom) / 1;
  if(opacite <= 0.02) return;
  const ech = echelleCarte() * mapZoom * CV.dpr;
  // la carte fait 330 px de large sur telephone et 900 sur ordinateur : une
  // taille fixe serait illisible d'un cote et minuscule de l'autre
  const taille = Math.round(Math.max(8.5, Math.min(13, CV.largeur / 72)) * CV.dpr);
  const interlettre = Math.max(0.6, taille / CV.dpr / 7);
  ctx.textAlign = 'center';
  ctx.textBaseline = 'middle';
  ctx.font = '800 ' + taille + 'px "Big Shoulders Display", Impact, sans-serif';
  if('letterSpacing' in ctx) ctx.letterSpacing = interlettre.toFixed(1) + 'px';
  ctx.globalAlpha = opacite;
  const poses = [];
  for(const e of f.etiquettes){
    const x = e.x * ech + mapPanX * CV.dpr, y = e.y * ech + mapPanY * CV.dpr;
    if(x < -80 || y < -20 || x > CV.largeur * CV.dpr + 80 || y > CV.hauteur * CV.dpr + 20) continue;
    const demiL = ctx.measureText(e.nom).width / 2 + 3 * CV.dpr;
    const demiH = taille * 0.78;
    const boite = [x - demiL, y - demiH, x + demiL, y + demiH];
    if(poses.some(b => boite[0] < b[2] && boite[2] > b[0] && boite[1] < b[3] && boite[3] > b[1])) continue;
    poses.push(boite);
    ctx.strokeStyle = 'rgba(7,17,31,0.85)'; ctx.lineWidth = 3.4 * CV.dpr;
    ctx.strokeText(e.nom, x, y);
    ctx.fillStyle = 'rgba(224,236,250,0.82)';
    ctx.fillText(e.nom, x, y);
  }
  ctx.globalAlpha = 1;
  if('letterSpacing' in ctx) ctx.letterSpacing = '0px';
}

function rendreCalques(){
  const zone = document.getElementById('mapCalques');
  if(!zone) return;
  const ICONES = {
    regions: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linejoin="round"><path d="M4 6.5 9.5 4l5 2.5L20 4v13.5L14.5 20l-5-2.5L4 20z"/><path d="M9.5 4v13.5M14.5 6.5V20"/></svg>',
    depts: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linejoin="round"><path d="M3 3h8v8H3zM13 3h8v8h-8zM3 13h8v8H3zM13 13h8v8h-8z"/></svg>',
    communes: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linejoin="round"><path d="M4 11 12 4l8 7"/><path d="M6 10v9h12v-9"/></svg>',
    noms: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round"><path d="M5 18 12 5l7 13M8 14h8"/></svg>',
    raretes: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.7" stroke-linejoin="round"><path d="m12 3.5 2.6 5.5 5.9.8-4.3 4.2 1 5.9-5.2-2.8-5.2 2.8 1-5.9L3.5 9.8l5.9-.8z"/></svg>',
    passage: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round"><path d="M4 19c3-7 6.5-10 9-10s3.5 1.5 3.5 3-1.5 2.5-3 2.5-2.5-1-2.5-2.5S12.5 5 16 4"/><circle cx="19.5" cy="4.5" r="1.6"/></svg>',
  };
  const NOMS = { regions: 'Régions', depts: 'Départements', communes: 'Communes',
                 noms: 'Noms', raretes: 'Raretés', passage: 'Mon passage' };
  zone.innerHTML = Object.keys(NOMS).map(id =>
    `<button data-calque="${id}" class="${CALQUES[id] ? 'actif' : ''}" aria-pressed="${!!CALQUES[id]}">${ICONES[id]}${NOMS[id]}</button>`
  ).join('');
}

// Sur telephone la carte fait 350 px de large : une legende posee dessus en
// cache la moitie et se retrouve coupee. On la descend sous la carte, et on la
// remet en surimpression des qu'il y a la place.
function placerLegende(){
  const leg = document.getElementById('mapLegende');
  const wrap = document.getElementById('mapWrap');
  const bas = document.getElementById('mapLegendeBas');
  if(!leg || !wrap || !bas) return;
  const dessous = surTelephone();
  const parentVoulu = dessous ? bas : wrap;
  if(leg.parentElement !== parentVoulu) parentVoulu.appendChild(leg);
  leg.classList.toggle('en-dessous', dessous);
}

function brancherCalques(){
  const zone = document.getElementById('mapCalques');
  if(!zone) return;
  rendreCalques();
  zone.addEventListener('click', (e) => {
    const b = e.target.closest('[data-calque]');
    if(!b) return;
    const id = b.dataset.calque;
    CALQUES[id] = !CALQUES[id];
    b.classList.toggle('actif', CALQUES[id]);
    b.setAttribute('aria-pressed', String(CALQUES[id]));
    enregistrerCalques();
    if(id === 'passage' && CALQUES.passage){
      // les communes perdues ne sont pas chargees au demarrage
      loadMaFrance().then(() => {
        if(!franceChargee){
          CALQUES.passage = false;
          b.classList.remove('actif');
          b.setAttribute('aria-pressed', 'false');
          enregistrerCalques();
          notifier({ type: 'info', titre: 'Mon passage arrive bientôt',
                     texte: "Ce calque n'est pas encore disponible." });
          return;
        }
        CV.donneesSignature = '';      // le cache doit reprendre les perdues
        demanderDessin();
      });
      return;
    }
    CV.donneesSignature = '';
    demanderDessin();
  });
}

// ---------- Retrouver la commune sous le doigt ----------
// Le SVG offrait le survol gratuitement avec des <title>. Ici on garde un index
// des points visibles et on cherche le plus proche.
function majReperage(liste, joueurs){
  if(!D3_OK || liste.length === 0){ CV.reperage = null; return; }
  const pts = liste.map(c => { const p = project(c.lat, c.lon); return [p.x * MAP_W, p.y * MAP_H]; });
  CV.reperage = { delaunay: d3.Delaunay.from(pts), liste, joueurs, pts };
}

// (x, y) en pixels CSS dans le cadre -> coordonnees de la carte
function ecranVersCarte(x, y){
  const ech = echelleCarte() * mapZoom;
  return { x: (x - mapPanX) / ech, y: (y - mapPanY) / ech };
}

function communeSousLePoint(xCss, yCss){
  const r = CV.reperage;
  if(!r) return null;
  const p = ecranVersCarte(xCss, yCss);
  const i = r.delaunay.find(p.x, p.y);
  if(i == null || i < 0) return null;
  const c = r.liste[i];
  // au-dela d'une certaine distance on considere qu'on a clique a cote
  const [px, py] = r.pts[i];
  const limite = Math.max(RAYON_ZONE[c.tier] || 4, 14 / mapZoom);
  if(Math.hypot(px - p.x, py - p.y) > limite) return null;
  return { commune: c, joueur: r.joueurs.get(c.joueur) };
}


// Combien de communes existe-t-il ? Sert au compteur de communes libres.
// Une seule requete, sans ramener la moindre ligne.
let TOTAL_COMMUNES = 0;
async function chargerTotalCommunes(){
  if(TOTAL_COMMUNES) return TOTAL_COMMUNES;
  const { count, error } = await sb.from('communes').select('*', { count: 'exact', head: true });
  if(!error && count){
    TOTAL_COMMUNES = count;
    legendeSignature = '';        // la legende peut maintenant afficher le pot
    if(canvasActif()) demanderDessin();
  }
  return TOTAL_COMMUNES;
}

// ---------- Panneau contextuel de la carte ----------
// Cliquer une commune ouvre sa fiche sur place. Les actions ne rejouent pas
// les interfaces existantes : elles basculent vers le bon onglet en pre-filtrant
// sur la commune, ce qui evite de dupliquer le combat, la bourse et l'echange.
let panneauCommune = null;

const ICONES_PC = {
  attaque: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><path d="M14.5 14.5 19.5 19.5a1.5 1.5 0 0 1-2 2L12.5 16.5"/><path d="M18.5 3.5 8 14M18.5 3.5h-3M18.5 3.5v3"/><path d="M9.5 14.5 4.5 19.5a1.5 1.5 0 0 0 2 2l5-5"/><path d="M5.5 3.5 16 14M5.5 3.5h3M5.5 3.5v3"/></svg>',
  echange: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><path d="M4 8h13l-3.5-3.5M17 8l-3.5 3.5"/><path d="M20 16H7l3.5-3.5M7 16l3.5 3.5"/></svg>',
  bouclier: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linejoin="round"><path d="M12 3l7.5 3v5.5c0 4.6-3.2 8.3-7.5 9.5-4.3-1.2-7.5-4.9-7.5-9.5V6z"/></svg>',
  vente: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><path d="M3.6 12.4 12 4h7.5a.5.5 0 0 1 .5.5V12l-8.4 8.4a1.4 1.4 0 0 1-2 0l-6-6a1.4 1.4 0 0 1 0-2z"/><circle cx="16.2" cy="7.8" r="1.3"/></svg>',
  joueur: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="8" r="3.4"/><path d="M5.5 20a6.5 6.5 0 0 1 13 0"/></svg>',
};

const nbFr = (n) => Number(n).toLocaleString('fr-FR');

function fermerPanneau(){
  const el = document.getElementById('mapPanneau');
  if(el) el.hidden = true;
  const wrap = document.getElementById('mapWrap');
  if(wrap) wrap.classList.remove('panneau-ouvert');
  panneauCommune = null;
}

function ouvrirPanneau(code, xCss, yCss){
  const el = document.getElementById('mapPanneau');
  if(!el) return;
  const mienne = collectionMap.get(code);
  const autre = mienne ? null : othersMap.get(code);
  const c = mienne || autre;
  if(!c){ fermerPanneau(); return; }
  panneauCommune = code;

  const maintenant = Date.now();
  const protegee = c.bouclierJusqua > maintenant;
  // toutes les raretes sont attaquables depuis la carte ; l'onglet Combat
  // reste le tableau des grosses cibles, il ne liste que rares et legendaires
  const attaquable = !mienne && !protegee;
  const immunisee = !mienne && c.acquiredAt && c.acquiredAt > maintenant - 3 * 3600e3;
  const enVente = mienne ? myListings.get(code) : null;

  // sieges en cours, uniquement connus pour mes communes
  let alerte = '';
  if(mienne){
    const s = siegesParCommune().get(code);
    if(s){
      alerte = `<p class="pc-alerte">${s.nb > 1 ? s.nb + ' joueurs t’attaquent' : 'Un joueur t’attaque'} — meilleure série <b>${s.max}/3</b></p>`;
    }
  }

  const lignes = [];
  if(c.pop != null) lignes.push(['Population', nbFr(c.pop)]);
  if(mienne && c.rank) lignes.push(['Rang national', nbFr(c.rank) + '<sup>e</sup>']);
  lignes.push(['Propriétaire', mienne
    ? '<b>Toi</b>'
    : `<button class="pc-proprio" data-profil="${echapperHtml(c.joueurId)}">${echapperHtml(c.pseudo)}</button>`]);
  if(protegee) lignes.push(['Bouclier', 'jusqu’à ' + new Date(c.bouclierJusqua).toLocaleString('fr-FR', { hour: '2-digit', minute: '2-digit', day: 'numeric', month: 'short' })]);
  else if(mienne) lignes.push(['Bouclier', 'Aucun']);
  if(enVente != null) lignes.push(['En vente', nbFr(enVente) + ' pts']);
  if(c.acquiredAt) lignes.push([mienne ? 'Possédée depuis' : 'Prise le', new Date(c.acquiredAt).toLocaleDateString('fr-FR')]);

  const actions = [];
  if(attaquable && !immunisee) actions.push(['attaque', 'attaque', 'Attaquer', 'Attaquer ' + c.nom]);
  if(!mienne) actions.push(['', 'echange', 'Proposer un échange', 'Échanger contre ' + c.nom]);
  if(mienne && (c.tier.id === 'rare' || c.tier.id === 'legendaire') && !protegee)
    actions.push(['', 'bouclier', 'Poser un bouclier', 'Protéger ' + c.nom]);
  if(mienne && enVente == null) actions.push(['', 'vente', 'Mettre en vente', 'Vendre ' + c.nom]);

  let note = '';
  if(!mienne && protegee) note = 'Protégée par un bouclier : impossible de l’attaquer pour l’instant.';
  else if(immunisee) note = 'Prise il y a moins de 3 heures : encore immunisée.';

  el.innerHTML = `
    <div class="pc-tete">
      <div class="pc-titre">
        <b>${echapperHtml(c.nom)}</b>
        <span class="pc-dep">${echapperHtml(DEPT_NAMES[c.dept] || '')} (${echapperHtml(c.dept)})</span>
      </div>
      <span class="pc-rarete ${c.tier.id}">${c.tier.label || LIBELLE_TIER[c.tier.id]}</span>
      <button class="pc-fermer" data-pc="fermer" aria-label="Fermer">&times;</button>
    </div>
    ${alerte}
    <div class="pc-lignes">${lignes.map(([a, b]) => `<div class="pc-ligne"><span>${a}</span><b>${b}</b></div>`).join('')}</div>
    ${note ? `<p class="pc-note">${note}</p>` : ''}
    ${actions.length ? `<div class="pc-actions">${actions.map(([cl, ic, txt, titre]) =>
      `<button class="pc-action ${cl}" data-pc="${ic}" title="${echapperHtml(titre)}">${ICONES_PC[ic]}${txt}</button>`).join('')}</div>` : ''}`;

  el.hidden = false;
  const wrap = document.getElementById('mapWrap');
  if(wrap) wrap.classList.add('panneau-ouvert');
  el.scrollTop = 0;
  placerPanneau(el, xCss, yCss);
}


// ---------- Attaquer depuis le panneau ----------
// L'onglet Combat ne peut pas lister les 30 000 communes du pays : la guerre
// locale se mene sur la carte, la ou le joueur voit son front.
let attaqueEnCours = false;

async function ouvrirAttaque(code){
  const el = document.getElementById('mapPanneau');
  const c = othersMap.get(code);
  if(!el || !c) return;
  panneauCommune = code;

  el.innerHTML = `
    <div class="pc-tete">
      <div class="pc-titre">
        <b>Attaquer ${echapperHtml(c.nom)}</b>
        <span class="pc-dep">à ${echapperHtml(c.pseudo)}</span>
      </div>
      <button class="pc-fermer" data-pc="retour" aria-label="Retour">&larr;</button>
    </div>
    <p class="pc-chargement">Calcul de tes chances…</p>`;
  el.hidden = false;

  const { data: userData } = await sb.auth.getUser();
  const uid = userData.user.id;
  const [apercu, siege] = await Promise.all([
    sb.rpc('apercu_attaque', { p_commune_code: code, p_intensite: intensiteChoisie }),
    sb.from('sieges').select('victoires_consecutives, dernier_round')
      .eq('attacker_id', uid).eq('commune_code', code).maybeSingle(),
  ]);
  if(panneauCommune !== code) return;          // le joueur est passe a autre chose

  if(apercu.error){
    el.querySelector('.pc-chargement').outerHTML =
      `<p class="pc-note">Impossible de calculer tes chances : ${echapperHtml(apercu.error.message)}</p>`;
    return;
  }
  rendreAttaque(code, apercu.data[0], siege.data || null);
}

function rendreAttaque(code, a, siege){
  const el = document.getElementById('mapPanneau');
  const c = othersMap.get(code);
  if(!el || !c) return;

  const serie = siege ? siege.victoires_consecutives : 0;
  const dernier = siege && siege.dernier_round ? new Date(siege.dernier_round).getTime() : 0;
  const prochain = dernier + (DELAI_ATTAQUE_MS[c.tier.id] || 0);
  const attente = Math.max(0, prochain - Date.now());

  const pastilles = INTENSITES.map(i => `
    <button class="pc-int ${i.id === intensiteChoisie ? 'actif' : ''}" data-pc="intensite" data-int="${i.id}">
      <span>${i.label}</span><small>${i.facteur === 1 ? 'prix normal' : (i.facteur < 1 ? '⅓ du prix' : 'prix doublé')}</small>
    </button>`).join('');

  el.innerHTML = `
    <div class="pc-tete">
      <div class="pc-titre">
        <b>Attaquer ${echapperHtml(c.nom)}</b>
        <span class="pc-dep">${c.tier.label || LIBELLE_TIER[c.tier.id]} · à ${echapperHtml(c.pseudo)}</span>
      </div>
      <button class="pc-fermer" data-pc="retour" aria-label="Retour">&larr;</button>
    </div>

    <div class="pc-prox ${a.a_distance ? 'loin' : ''}">
      ${a.a_distance
        ? 'Aucune de tes communes à moins de 20 km : <b>attaque à distance</b>, tes chances baissent.'
        : `<b>${a.proches}</b> de tes communes à moins de 20 km`}
    </div>

    <div class="pc-serie">
      <span>Série en cours</span>
      <span class="pc-points">${[0,1,2].map(i => `<i class="${i < serie ? 'pris' : ''}"></i>`).join('')}</span>
      <b>${serie} / 3</b>
    </div>

    <div class="pc-ints">${pastilles}</div>

    <div class="pc-jauge">
      <div class="pc-jauge-tete"><span>Chances de victoire</span><b>${a.chances} %</b></div>
      <div class="pc-jauge-barre"><i style="width:${a.chances}%"></i></div>
    </div>

    <div class="pc-actions">
      <button class="pc-action attaque" data-pc="assaut" ${attente > 0 || attaqueEnCours ? 'disabled' : ''}>
        ${attente > 0 ? 'Encore ' + formatDuree(attente) + ' à attendre' : `Lancer l’assaut — ${a.cout} pts`}
      </button>
    </div>`;
  placerPanneau(el, parseFloat(el.style.left) || 40, parseFloat(el.style.top) || 40);
}

async function lancerAssaut(code){
  if(attaqueEnCours) return;
  const c = othersMap.get(code);
  if(!c) return;
  attaqueEnCours = true;
  const bouton = document.querySelector('#mapPanneau [data-pc="assaut"]');
  if(bouton){ bouton.disabled = true; bouton.textContent = 'Assaut en cours…'; }
  try{
    const nom = c.nom, tier = c.tier.id, dept = c.dept;
    const { data, error } = await sb.rpc('attaquer', { p_commune_code: code, p_intensite: intensiteChoisie });
    if(error) throw error;
    const r = data[0];
    if(r.conquise){
      await loadMyCollection();
      await loadOthersPossessions();
      fermerPanneau();
      celebrerConquete({ nom, tier, dept, bonus: Math.floor(PRIX_RACHAT[tier] * BONUS_CONQUETE_PART) });
    } else if(r.gagne){
      notifier({ type: 'victoire', titre: `Victoire contre ${nom} (−${r.cout} pts)`,
        texte: r.victoires_consecutives >= 2 ? 'Encore une victoire pour la conquérir.' : `Série : ${r.victoires_consecutives} sur 3`,
        serie: r.victoires_consecutives });
    } else {
      notifier({ type: 'defaite', titre: `Défaite contre ${nom} (−${r.cout} pts)`,
        texte: `À ${r.chances} % : la série repart à zéro.`, serie: 0 });
    }
    loadPackStatus();
    loadObjectifs();
    renderMapOverlay();
    if(!r.conquise && panneauCommune === code) ouvrirAttaque(code);
  } catch(e){
    notifier({ type: 'erreur', titre: 'Attaque impossible', texte: messageLisible(e.message || String(e)) });
    if(panneauCommune === code) ouvrirAttaque(code);
  } finally {
    attaqueEnCours = false;
  }
}

// Sur telephone le panneau est colle en bas par la feuille de style ; sur
// ordinateur on le pose a cote du clic sans le laisser sortir du cadre.
function placerPanneau(el, xCss, yCss){
  if(surTelephone()){ el.style.left = ''; el.style.top = ''; return; }
  const wrap = document.getElementById('mapWrap');
  if(!wrap) return;
  const b = el.getBoundingClientRect();
  const marge = 12;
  let gauche = xCss + 16;
  let haut = yCss - b.height / 2;
  if(gauche + b.width > wrap.clientWidth - marge) gauche = xCss - b.width - 16;
  gauche = Math.max(marge, Math.min(gauche, wrap.clientWidth - b.width - marge));
  haut = Math.max(marge, Math.min(haut, wrap.clientHeight - b.height - marge));
  el.style.left = Math.round(gauche) + 'px';
  el.style.top = Math.round(haut) + 'px';
}

// Les actions renvoient vers l'onglet concerne, la recherche deja remplie sur
// la commune : pas de duplication du combat, de la bourse ni de l'echange.
function allerVers(onglet, champId, texte, apres){
  const tab = document.querySelector('.tab[data-tab="' + onglet + '"]');
  if(tab) tab.click();
  setTimeout(() => {
    const champ = document.getElementById(champId);
    if(champ){
      champ.value = texte;
      champ.dispatchEvent(new Event('input', { bubbles: true }));
    }
    if(apres) apres();
    const zone = document.getElementById('panel-' + onglet);
    if(zone && zone.scrollIntoView) zone.scrollIntoView({ behavior: 'smooth', block: 'start' });
  }, 140);
}

document.getElementById('mapPanneau').addEventListener('click', (e) => {
  const prof = e.target.closest('[data-profil]');
  if(prof){ ouvrirProfil(prof.dataset.profil); return; }
  const b = e.target.closest('[data-pc]');
  if(!b) return;
  const quoi = b.dataset.pc;
  const code = panneauCommune;
  const c = code ? (collectionMap.get(code) || othersMap.get(code)) : null;
  if(quoi === 'fermer' || !c){ fermerPanneau(); return; }
  if(quoi === 'retour'){ ouvrirPanneau(code, parseFloat(e.currentTarget.style.left) || 40, parseFloat(e.currentTarget.style.top) || 40); return; }
  if(quoi === 'assaut'){ lancerAssaut(code); return; }
  if(quoi === 'intensite'){
    intensiteChoisie = b.dataset.int;
    try{ localStorage.setItem('tf-intensite', intensiteChoisie); } catch(err){}
    renderIntensite();
    ouvrirAttaque(code);
    return;
  }
  if(quoi === 'attaque'){ ouvrirAttaque(code); return; }
  // les actions restantes quittent la carte pour l'onglet concerne
  fermerPanneau();
  if(quoi === 'echange') allerVers('echange', 'echSearch', c.nom, () => {
    // l'echange se fait a rarete egale : on se place d'emblee sur la bonne
    const onglet = document.querySelector('#echTiers [data-tier="' + c.tier.id + '"]');
    if(onglet) onglet.click();
  });
  else if(quoi === 'bouclier') allerVers('defense', 'boucliersSearch', c.nom);
  else if(quoi === 'vente') allerVers('bourse', 'sellSearch', c.nom);
});

document.addEventListener('keydown', (e) => {
  if(e.key === 'Escape' && panneauCommune) fermerPanneau();
});

function brancherSurvolCanvas(){
  const cv = document.getElementById('mapCanvas');
  const bulle = document.getElementById('mapInfobulle');
  if(!cv || !bulle) return;
  cv.addEventListener('pointermove', (e) => {
    if(mapDragging){ bulle.hidden = true; return; }
    const rect = cv.getBoundingClientRect();
    const t = communeSousLePoint(e.clientX - rect.left, e.clientY - rect.top);
    if(!t){ bulle.hidden = true; CV.survol = null; return; }
    CV.survol = t.commune;
    bulle.hidden = false;
    bulle.textContent = t.commune.nom + ' (' + t.commune.dept + '), '
      + LIBELLE_TIER[t.commune.tier] + ', '
      + (t.joueur.moi ? 'à toi' : 'à ' + t.joueur.pseudo);
    const bb = bulle.getBoundingClientRect();
    let gauche = e.clientX - rect.left + 14;
    if(gauche + bb.width > rect.width) gauche = e.clientX - rect.left - bb.width - 14;
    bulle.style.left = Math.max(4, gauche) + 'px';
    bulle.style.top = Math.max(4, e.clientY - rect.top - bb.height - 12) + 'px';
  });
  cv.addEventListener('pointerleave', () => { bulle.hidden = true; CV.survol = null; });

  // un deplacement de la carte ne doit pas etre pris pour un clic
  let depart = null;
  cv.addEventListener('pointerdown', (e) => { depart = { x: e.clientX, y: e.clientY }; });
  cv.addEventListener('pointerup', (e) => {
    if(!depart) return;
    const bouge = Math.hypot(e.clientX - depart.x, e.clientY - depart.y);
    depart = null;
    if(bouge > 6) return;
    const rect = cv.getBoundingClientRect();
    const x = e.clientX - rect.left, y = e.clientY - rect.top;
    const t = communeSousLePoint(x, y);
    if(t) ouvrirPanneau(t.commune.code, x, y);
    else fermerPanneau();
  });
}

function renderMapOverlay(){
  if(canvasActif()){
    CV.cellulesSignature = ''; CV.donneesSignature = '';
    // la commune affichee a pu changer de main entre-temps
    if(panneauCommune && !collectionMap.has(panneauCommune) && !othersMap.has(panneauCommune)) fermerPanneau();
    demanderDessin();
    return;
  }
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
    liste.push({ code: e.code, nom: e.nom, dept: e.dept, lat: e.lat, lon: e.lon, tier: e.tier.id, joueur: ID_MOI });
    joueurs.get(ID_MOI).nb++;
  }
  MASQUEES_PAR_ZOOM.commun = 0;
  MASQUEES_PAR_ZOOM.peucommun = 0;
  for(const e of othersMap.values()){
    if(!METRO_DEPT_RE.test(e.dept) || e.lat == null) continue;
    const visibleAuZoom = mapZoom < SEUIL_CONTOURS || mapZoom >= (ZOOM_MINI[e.tier.id] || 1);
    if(showOthers && !visibleAuZoom && MASQUEES_PAR_ZOOM[e.tier.id] !== undefined) MASQUEES_PAR_ZOOM[e.tier.id]++;
    if(!joueurs.has(e.joueurId)){
      const couleur = colorForPlayer(e.joueurId);
      joueurs.set(e.joueurId, { id: e.joueurId, pseudo: e.pseudo, couleur, fonce: couleurFoncee(couleur), moi: false, nb: 0 });
    }
    joueurs.get(e.joueurId).nb++;
    if(showOthers && visibleAuZoom) liste.push({ code: e.code, nom: e.nom, dept: e.dept, lat: e.lat, lon: e.lon, tier: e.tier.id, joueur: e.joueurId });
  }

  // De loin : la France par departements. De pres : les vraies communes.
  if(mapZoom < SEUIL_CONTOURS && liste.length > 0){
    if(!CONTOURS_DEPTS) chargerDepartements();
    else if(CONTOURS_DEPTS !== 'erreur' && CONTOURS_DEPTS !== 'attente'){
      dessinerDepartements(liste, joueurs);
      return;
    }
  }
  const avecContours = mapZoom >= SEUIL_CONTOURS && liste.length > 0;
  if(avecContours){
    const deps = departementsVisibles(liste);
    let pretes = 0;
    for(const dep of deps){
      const c = CONTOURS.get(dep);
      if(c === undefined){ chargerContours(dep); }
      else if(c && c !== 'erreur') pretes++;
    }
    if(pretes > 0){
      dessinerContours(liste, joueurs, deps);
      return;
    }
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

// Dessin des vraies communes : un bloc de couleur par joueur, frontieres reelles
function dessinerContours(liste, joueurs, deps){
  const couche = document.getElementById('mapTerritoires');
  const defs = document.getElementById('mapDefsDyn');
  const marq = document.getElementById('mapMarqueurs');
  const survol = document.getElementById('mapSurvol');
  const idSvg = (id) => 'j' + String(id).replace(/[^a-zA-Z0-9_-]/g, '');

  // tout ce qui est dessine par-dessus la carte garde la meme taille a l'ecran quel que soit le zoom
  const e = 1 / Math.max(1, mapZoom);
  const possedees = new Map(liste.map(c => [c.code, c]));
  const parJoueur = new Map();
  let libres = '', pastilles = '', zonesSurvol = '';

  for(const dep of deps){
    const contours = CONTOURS.get(dep);
    if(!contours || contours === 'erreur') continue;
    for(const code in contours){
      const d = cheminContour(contours[code]);
      const c = possedees.get(code);
      if(!c){ libres += `<path d="${d}"/>`; continue; }
      if(!parJoueur.has(c.joueur)) parJoueur.set(c.joueur, { d: '', marqueurs: '' });
      const g = parJoueur.get(c.joueur);
      g.d += d;
      const p = project(c.lat, c.lon);
      const x = p.x * MAP_W, y = p.y * MAP_H;
      const j = joueurs.get(c.joueur);
      if(c.tier === 'legendaire'){
        g.marqueurs += `<polygon points="${etoileSvg(x, y, (j.moi ? 7 : 6) * e)}" fill="${j.moi ? '#FFF6D6' : 'rgba(255,246,214,0.75)'}" stroke="#0B1830" stroke-width="${(1.2 * e).toFixed(2)}"/>`;
      } else if(c.tier === 'rare'){
        g.marqueurs += `<circle cx="${x.toFixed(1)}" cy="${y.toFixed(1)}" r="${(2.2 * e).toFixed(2)}" fill="${j.moi ? '#fff' : 'rgba(255,255,255,0.7)'}" stroke="#0B1830" stroke-width="${(1 * e).toFixed(2)}"/>`;
      }
      zonesSurvol += `<path d="${d}" fill="transparent"><title>${echapperHtml(c.nom)} (${c.dept}), ${LIBELLE_TIER[c.tier]}, ${j.moi ? 'à toi' : 'à ' + echapperHtml(j.pseudo)}</title></path>`;
    }
  }

  // communes possedees dont le departement n'est pas encore charge : pastille simple
  for(const c of liste){
    const etat = CONTOURS.get(c.dept);
    if(etat && etat !== 'erreur') continue;
    const p = project(c.lat, c.lon);
    const j = joueurs.get(c.joueur);
    pastilles += `<circle cx="${(p.x * MAP_W).toFixed(1)}" cy="${(p.y * MAP_H).toFixed(1)}" r="${(RAYON_ZONE[c.tier] * e).toFixed(2)}" fill="${j.couleur}" fill-opacity="${j.moi ? 0.95 : 0.7}" stroke="#07111F" stroke-width="${(2 * e).toFixed(2)}"/>`;
  }

  const ordre = [...parJoueur.keys()].sort((a, b) => (a === ID_MOI ? 1 : 0) - (b === ID_MOI ? 1 : 0));
  defs.innerHTML = '';
  couche.innerHTML =
    `<g class="communes-libres" fill="#16304F" fill-opacity="0.75" stroke="#20406A" stroke-width="${(0.6 * e).toFixed(2)}">${libres}</g>` +
    ordre.map(id => {
      const j = joueurs.get(id);
      const g = parJoueur.get(id);
      return `<g data-joueur="${idSvg(id)}">
        <path d="${g.d}" fill="none" stroke="#07111F" stroke-width="${(3.4 * e).toFixed(2)}" stroke-linejoin="round"/>
        <path d="${g.d}" fill="${j.couleur}" fill-opacity="${j.moi ? 0.95 : 0.78}" stroke="${j.fonce}" stroke-opacity="0.55" stroke-width="${(0.7 * e).toFixed(2)}"/>
      </g>`;
    }).join('');
  marq.innerHTML = ordre.map(id => `<g data-joueur="${idSvg(id)}">${parJoueur.get(id).marqueurs}</g>`).join('') + `<g>${pastilles}</g>`;
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

// Qui domine chaque departement : deja calcule pour colorier la carte de loin,
// on le reutilise tel quel pour la legende.
function departementsDomines(){
  const parDept = new Map();
  const compter = (e, id) => {
    if(!METRO_DEPT_RE.test(e.dept)) return;
    if(!parDept.has(e.dept)) parDept.set(e.dept, new Map());
    const m = parDept.get(e.dept);
    m.set(id, (m.get(id) || 0) + 1);
  };
  for(const e of collectionMap.values()) compter(e, ID_MOI);
  for(const e of othersMap.values()) compter(e, e.joueurId);
  const domines = new Map();
  for(const m of parDept.values()){
    let chef = null, meilleur = 0;
    for(const [id, n] of m){ if(n > meilleur){ meilleur = n; chef = id; } }
    if(chef) domines.set(chef, (domines.get(chef) || 0) + 1);
  }
  return domines;
}

function renderLegendeCarte(joueurs, idSvg){
  const leg = document.getElementById('mapLegende');
  if(!leg) return;
  const moi = joueurs.get(ID_MOI);
  const autres = [...joueurs.values()].filter(j => !j.moi && j.nb > 0).sort((a, b) => b.nb - a.nb);
  const NB_VISIBLES = 5;
  const affiches = showOthers ? (listeJoueursComplete ? autres : autres.slice(0, NB_VISIBLES)) : [];
  const reste = showOthers ? autres.length - affiches.length : 0;
  const domines = departementsDomines();
  const meilleurScore = Math.max(1, moi.nb, ...autres.map(j => j.nb));
  const pct = (n) => TOTAL_COMMUNES ? (100 * n / TOTAL_COMMUNES) : 0;
  const rangs = new Map([moi, ...autres].sort((a, b) => b.nb - a.nb).map((j, i) => [j.id, i + 1]));

  const ligne = (j) => {
    const d = domines.get(j.id) || 0;
    // a l'echelle de la France toutes les barres seraient invisibles :
    // elles comparent les joueurs entre eux, le pourcentage exact est a cote
    const largeur = Math.max(3, 100 * j.nb / meilleurScore);
    return `<button class="leg-joueur ${joueurSurligne === j.id ? 'actif' : ''} ${j.moi ? 'moi' : ''}" data-joueur-id="${echapperHtml(j.id)}" aria-pressed="${joueurSurligne === j.id}">
      <span class="leg-rang">${rangs.get(j.id) || ''}</span>
      <span class="leg-pastille" style="background:${j.couleur}"></span>
      <span class="leg-mid">
        <span class="leg-pseudo">${j.moi ? '<b>Toi</b>' : echapperHtml(j.pseudo)}</span>
        <span class="leg-sous">${d > 0 ? d + ' dép. dominé' + (d > 1 ? 's' : '') : 'aucun département'}</span>
        <span class="leg-barre"><i style="width:${largeur.toFixed(1)}%;background:${j.couleur}"></i></span>
      </span>
      <span class="leg-chiffres"><b>${j.nb.toLocaleString('fr-FR')}</b>${TOTAL_COMMUNES ? `<small>${pct(j.nb).toFixed(1)} %</small>` : ''}</span>
    </button>`;
  };

  // Le pot commun : ce qui reste a prendre. Visible de tous, et c'est aussi
  // notre tableau de bord sur l'epuisement des communes.
  const prises = collectionMap.size + othersMap.size;
  const libres = TOTAL_COMMUNES ? Math.max(0, TOTAL_COMMUNES - prises) : 0;
  const ligneLibres = TOTAL_COMMUNES ? `
      <div class="leg-libres">
        <span class="leg-pastille libre"></span>
        <span class="leg-mid">
          <span class="leg-pseudo">Communes libres</span>
          <span class="leg-sous">encore à prendre</span>
        </span>
        <span class="leg-chiffres"><b>${libres.toLocaleString('fr-FR')}</b><small>${pct(libres).toFixed(1)} %</small></span>
      </div>` : '';
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
      ${ligneLibres}
      ${(() => {
        const n = MASQUEES_PAR_ZOOM.commun + MASQUEES_PAR_ZOOM.peucommun;
        return n > 0 ? `<p class="leg-indice leg-zoom">${n.toLocaleString('fr-FR')} petite${n > 1 ? 's' : ''} commune${n > 1 ? 's' : ''} masquée${n > 1 ? 's' : ''} : zoome pour les voir.</p>` : '';
      })()}
      <p class="leg-indice">Clique sur un joueur pour mettre son territoire en évidence.</p>
      <div class="leg-traits">
        <div><svg width="30" height="8"><line x1="1" y1="4" x2="29" y2="4" stroke="#D6E6F6" stroke-width="2.2" stroke-opacity=".72"/><line x1="1" y1="4" x2="29" y2="4" stroke="#0F1F38" stroke-width="1.1" stroke-dasharray="5 4"/></svg>Région</div>
        <div><svg width="30" height="8"><line x1="1" y1="4" x2="29" y2="4" stroke="#A9BCD4" stroke-width="1" stroke-opacity=".45"/></svg>Département</div>
      </div>
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
// Supabase plafonne chaque requete a 1000 lignes : on demande par tranches
async function toutesLesLignes(construireRequete){
  const TAILLE = 1000;
  let tout = [], debut = 0;
  for(;;){
    const { data, error } = await construireRequete().range(debut, debut + TAILLE - 1);
    if(error) return { data: null, error };
    tout = tout.concat(data || []);
    if(!data || data.length < TAILLE) return { data: tout, error: null };
    debut += TAILLE;
  }
}

async function loadOthersPossessions(){
  const { data: userData } = await sb.auth.getUser();
  const uid = userData.user.id;
  window.__monId = uid;
  // Sans pagination, l'API s'arrete a 1000 lignes et une partie du territoire
  // des autres joueurs n'apparait jamais sur la carte.
  const { data, error } = await toutesLesLignes(() => sb
    .from('possessions')
    .select('commune_code, joueur_id, bouclier_jusqua, acquired_at, communes(code,nom,departement,population,latitude,longitude,tier), joueurs(pseudo)')
    .neq('joueur_id', uid));
  if(error){ console.error(error); return; }

  othersMap = new Map();
  for(const row of data){
    const c = row.communes;
    const tier = TIERS.find(t => t.id === c.tier);
    othersMap.set(c.code, {
      code: c.code,
      nom: c.nom, dept: c.departement, pop: c.population,
      lat: c.latitude, lon: c.longitude, tier,
      pseudo: row.joueurs ? row.joueurs.pseudo : 'un autre joueur',
      joueurId: row.joueur_id,
      acquiredAt: row.acquired_at ? new Date(row.acquired_at).getTime() : 0,
      bouclierJusqua: row.bouclier_jusqua ? new Date(row.bouclier_jusqua).getTime() : 0
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
        ({ data, error } = await toutesLesLignes(() => sb
      .from('possessions').select(champs + champsCommune).eq('joueur_id', uid)));
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
let menacesSignature = '';

// "cote" doit trouver "Côte-d'Or"
const sansAccents = (s) => String(s).toLowerCase().normalize('NFD').replace(/[\u0300-\u036f]/g, '');

// Nom de departement saisi en entier, ou sans ambiguite : on renvoie son numero
function codeDepartement(texte){
  const t = sansAccents(texte || '');
  if(t.length < 3) return null;
  const codes = Object.keys(DEPT_NAMES);
  const exact = codes.find(c => sansAccents(DEPT_NAMES[c]) === t);
  if(exact) return exact;
  const debuts = codes.filter(c => sansAccents(DEPT_NAMES[c]).startsWith(t));
  return debuts.length === 1 ? debuts[0] : null;
}

// Une recherche peut viser un nom de commune, un numero de departement ou son nom
function correspondRecherche(nom, dept, recherche){
  if(!recherche) return true;
  return sansAccents(nom).includes(recherche)
      || String(dept).toLowerCase().includes(recherche)
      || sansAccents(DEPT_NAMES[dept] || '').includes(recherche);
}

// Sieges en cours sur mes communes, regroupes : combien d'attaquants, meilleure serie
function siegesParCommune(){
  const par = new Map();
  for(const s of menaces){
    if(!(s.victoires_consecutives > 0)) continue;
    const e = par.get(s.commune_code) || { nb: 0, max: 0 };
    e.nb++;
    if(s.victoires_consecutives > e.max) e.max = s.victoires_consecutives;
    par.set(s.commune_code, e);
  }
  return par;
}
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

// ---------- Ma France : tout ce que le joueur a possede un jour ----------
// La carte du Territoire montre l'instant present. Celle-ci montre le passage :
// une commune perdue y reste coloriee. C'est la seule progression du jeu qui ne
// peut que monter, et pour un joueur qui s'est fait reprendre son territoire
// c'est la difference entre 33 communes a regarder et 438.
let vueCollection = 'mienne';          // 'mienne' | 'france'
let perduesMap = new Map();
let resumeFrance = null;
let franceChargee = false;

async function loadMaFrance(){
  if(franceChargee) return;
  franceChargee = true;                // une seule fois par session
  const [perdues, resume] = await Promise.all([
    sb.rpc('mes_communes_perdues'),
    sb.rpc('ma_france_resume')
  ]);
  if(perdues.error || resume.error){
    // le SQL n'est peut-etre pas encore passe : on laisse la vue par defaut
    console.warn('Ma France indisponible', perdues.error || resume.error);
    franceChargee = false;
    return;
  }
  perduesMap = new Map();
  for(const r of (perdues.data || [])){
    const tier = TIERS.find(t => t.id === r.tier);
    if(!tier) continue;
    perduesMap.set(r.code, {
      code: r.code, nom: r.nom, dept: r.dep, pop: r.pop,
      lat: r.lat, lon: r.lon, tier, rank: r.rang, tierSize: r.total,
      perdue: true, acquiredAt: 0, bouclierJusqua: 0, conquiseLe: 0
    });
  }
  resumeFrance = Array.isArray(resume.data) ? resume.data[0] : resume.data;
  majResumeFrance();
  dessinerMaFrance();
}

function majResumeFrance(){
  if(!resumeFrance) return;
  const d = Number(resumeFrance.decouvertes) || 0;
  const p = Number(resumeFrance.perdues) || 0;
  const t = Number(resumeFrance.total) || 1;
  const pct = 100 * d / t;
  const fixe = (x) => x.toLocaleString('fr-FR');
  const mettre = (id, v) => { const e = document.getElementById(id); if(e) e.textContent = v; };
  mettre('cfDecouvertes', fixe(d));
  mettre('cfPerdues', fixe(p));
  const j = document.getElementById('cfJauge');
  // en dessous de 0,4 % la barre serait invisible : on garde un trait
  if(j) j.style.width = Math.max(pct, d > 0 ? 0.4 : 0) + '%';
  const txt = document.getElementById('cfJaugeTxt');
  if(txt) txt.innerHTML = '<b>' + fixe(d) + '</b> communes sur ' + fixe(t)
    + ' — <b>' + pct.toLocaleString('fr-FR', {minimumFractionDigits:1, maximumFractionDigits:1})
    + ' %</b> de la France découverte';
}

// La carte est redessinee a la demande : pas d'animation, pas de zoom, c'est
// une image de synthese qu'on regarde, pas un terrain de jeu.
function dessinerMaFrance(){
  const cv = document.getElementById('collFranceCarte');
  if(!cv || !FRANCE_OUTLINE || !mapBounds) return;
  const largeur = cv.clientWidth || cv.parentElement?.clientWidth || 420;
  if(largeur < 40) return;                       // panneau encore masque
  const ratio = MAP_H / MAP_W;
  const hauteur = Math.round(largeur * ratio);
  const dpr = Math.min(window.devicePixelRatio || 1, 2);
  cv.width = Math.round(largeur * dpr);
  cv.height = Math.round(hauteur * dpr);
  cv.style.height = hauteur + 'px';
  const ctx = cv.getContext('2d');
  ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
  ctx.clearRect(0, 0, largeur, hauteur);

  // le contour, dans les tons de la carte principale
  ctx.beginPath();
  for(const ring of FRANCE_OUTLINE){
    ring.forEach(([lon, lat], i) => {
      const p = project(lat, lon);
      const x = p.x * largeur, y = p.y * hauteur;
      if(i === 0) ctx.moveTo(x, y); else ctx.lineTo(x, y);
    });
    ctx.closePath();
  }
  ctx.fillStyle = '#16294A';
  ctx.fill();
  ctx.strokeStyle = 'rgba(169,188,212,0.35)';
  ctx.lineWidth = 1;
  ctx.stroke();

  const rayon = Math.max(1.2, largeur / 200);
  const points = (liste, couleur, alpha, r) => {
    ctx.fillStyle = couleur;
    ctx.globalAlpha = alpha;
    ctx.beginPath();
    for(const e of liste){
      if(e.lat == null || e.lon == null) continue;
      const p = project(e.lat, e.lon);
      const x = p.x * largeur, y = p.y * hauteur;
      ctx.moveTo(x + r, y);
      ctx.arc(x, y, r, 0, Math.PI * 2);
    }
    ctx.fill();
    ctx.globalAlpha = 1;
  };
  // les perdues d'abord : les possedees passent par-dessus
  points(perduesMap.values(), '#F0B429', 0.30, rayon);
  points(collectionMap.values(), '#F0B429', 0.95, rayon * 1.08);
}

window.addEventListener('resize', () => {
  if(vueCollection === 'france') dessinerMaFrance();
});

function renderCollection(){
  const countEl = document.getElementById('collectionCount');
  const gridEl = document.getElementById('collectionGrid');
  // en vue « Ma France » la grille montre aussi ce qui a ete perdu
  const entries = vueCollection === 'france'
    ? Array.from(collectionMap.values()).concat(Array.from(perduesMap.values()))
    : Array.from(collectionMap.values());
  countEl.textContent = entries.length.toLocaleString('fr-FR');
  renderCollectionFilters(entries);
  if(entries.length === 0){
    gridEl.innerHTML = '<p class="collection-empty">Aucune carte pour le moment. Ouvre un paquet.</p>';
    return;
  }
  const champ = document.getElementById('collectionSearch');
  const recherche = sansAccents(champ ? champ.value.trim() : '');
  const sieges = siegesParCommune();
  const visibles = entries
    .filter(e => collectionFilterTier === 'tous' || e.tier.id === collectionFilterTier)
    .filter(e => correspondRecherche(e.nom, e.dept, recherche))
    .sort((a,b) => {
      const ra = TIERS.indexOf(a.tier), rb = TIERS.indexOf(b.tier);
      if(ra !== rb) return ra - rb;
      // a rarete egale, ce qu'on possede encore passe devant
      if(!!a.perdue !== !!b.perdue) return a.perdue ? 1 : -1;
      return b.pop - a.pop;
    });
  if(visibles.length === 0){
    gridEl.innerHTML = recherche
      ? '<p class="collection-empty">Aucune commune ne correspond à cette recherche.</p>'
      : '<p class="collection-empty">Aucune carte de cette rareté pour le moment.</p>';
    return;
  }
  gridEl.innerHTML = visibles.map(entry => {
    const s = sieges.get(entry.code);
    const badgeSiege = s
      ? `<span class="mini-siege" title="${s.nb > 1 ? s.nb + ' joueurs attaquent cette commune' : 'Un joueur attaque cette commune'} — meilleure série ${s.max} sur 3">${s.max}/3${s.nb > 1 ? ' ×' + s.nb : ''}</span>`
      : '';
    return `
    <div class="mini ${entry.tier.id}${entry.perdue ? ' perdue' : ''}" data-code="${entry.code}" role="button" tabindex="0" title="${echapperTexte(entry.nom)} (${entry.dept}) — ${entry.tier.label}${entry.perdue ? ' — tu ne la possèdes plus' : ''}">
      <div class="mini-int">
        ${entry.perdue ? '<span class="mini-perdue">PERDUE</span>' : ''}
        <div class="mini-art">${miniArtSvg(entry.code, entry.tier.id)}<span class="mini-dept">${entry.dept}</span>${entry.bouclierJusqua > Date.now() ? `<span class="mini-bouclier" title="Protégée par un bouclier">${ICONE_BOUCLIER}</span>` : ''}${badgeSiege}</div>
        <div class="mini-infos">
          <p class="mini-nom ${entry.nom.length > 14 ? 'long' : ''}">${entry.nom}</p>
          ${entry.rank ? `<span class="mini-num">n° ${Number(entry.rank).toLocaleString('fr-FR')}<span class="mini-total"> / ${Number(entry.tierSize).toLocaleString('fr-FR')}</span></span>` : ''}
          <span class="mini-rarete">${entry.tier.label}</span>
        </div>
        <div class="mini-lisere"><span></span><span></span><span></span></div>
      </div>
    </div>`;
  }).join('');
}


// ---------- La fiche d'une commune ----------
// Ce qui s'ouvre quand on clique une carte de la collection. Les faits
// viennent de communes.faits, calcule une fois par faits-communes.sql : rien
// n'est genere ici, donc rien a verifier.

let fermerFiche = null;
const ficheCache = new Map();

// Un appel par commune, garde en memoire. La colonne gentile n'existe pas
// encore : on tente avec, on se replie sans, et la fiche la prendra toute
// seule le jour ou elle arrive.
let ficheChampsOk = null;
async function detailsCommune(code){
  if(ficheCache.has(code)) return ficheCache.get(code);
  const variantes = ficheChampsOk ? [ficheChampsOk] : ['faits, gentile', 'faits'];
  let d = null;
  for(const champs of variantes){
    const { data, error } = await sb.from('communes').select(champs).eq('code', code).limit(1);
    if(!error){ ficheChampsOk = champs; d = (data && data[0]) || {}; break; }
  }
  if(!d) d = {};
  ficheCache.set(code, d);
  return d;
}

// Purement decoratif : le texte du fait est la seule verite, l'icone se
// devine depuis lui. Aucun fait ne depend de cette fonction.
function iconeFait(t){
  const s = (t || '').toLowerCase();
  if(s.indexOf('plus au nord') >= 0 || s.indexOf('plus au sud') >= 0
     || s.indexOf('plus à l') >= 0) return '🧭';
  if(s.indexOf('moins peuplée') >= 0) return '📉';
  if(s.indexOf('plus peuplée') >= 0 || s.indexOf('plus peuplées') >= 0) return '📈';
  if(s.indexOf('portent ce nom') >= 0) return '👥';
  if(s.indexOf('commence par') >= 0) return '🔤';
  if(s.indexOf('deux sens') >= 0) return '🔁';
  if(s.indexOf('plus court') >= 0 || s.indexOf('plus longs') >= 0) return '📏';
  if(s.indexOf('par la population') >= 0) return '📊';
  return '✨';
}

function faitsTries(faits){
  if(!Array.isArray(faits)) return [];
  return faits
    .filter(f => f && f.t)
    .slice()
    .sort((a, b) => (Number(a.r) || 9) - (Number(b.r) || 9));
}

async function ouvrirFicheCommune(code){
  const entry = collectionMap.get(code) || perduesMap.get(code);
  if(!entry) return;
  rendreFiche(entry, null);                   // tout de suite, sans attendre
  let d = {};
  try { d = await detailsCommune(code); } catch(e){ d = {}; }
  // l'utilisateur a pu refermer ou ouvrir une autre carte entre-temps
  const ouverte = document.querySelector('#fenetre .fiche[data-code="' + code + '"]');
  if(ouverte) rendreFiche(entry, d);
}

function rendreFiche(entry, d){
  const nb = (x) => Number(x || 0).toLocaleString('fr-FR');
  const tier = entry.tier;
  const faits = d ? faitsTries(d.faits) : null;
  const gentile = d && d.gentile ? String(d.gentile).trim() : '';

  // Le rachat n'a de sens que sur une commune qu'on possede encore.
  const troisieme = entry.perdue
    ? '<div class="fc-ch"><b class="fc-perdue">Perdue</b><span>statut</span></div>'
    : '<div class="fc-ch"><b>' + nb(PRIX_RACHAT[tier.id]) + ' pts</b><span>rachat</span></div>';

  let savais;
  if(faits === null){
    savais = '<p class="fc-attente">Recherche des faits…</p>';
  } else if(faits.length === 0){
    savais = '';
  } else {
    const [phare, ...reste] = faits;
    savais = '<h3>Le savais-tu ?</h3>'
      + '<div class="fc-fait phare"><i>🏅</i><span><b>' + echapperTexte(phare.t) + '</b></span></div>'
      + reste.map(f => '<div class="fc-fait"><i>' + iconeFait(f.t) + '</i><span>'
          + echapperTexte(f.t) + '</span></div>').join('');
  }

  fermerFiche = ouvrirFenetre(`
    <div class="fenetre fiche ${tier.id}" data-code="${echapperTexte(entry.code)}"
         role="dialog" aria-modal="true" aria-labelledby="fcNom">
      <button class="fc-fermer" data-fc="fermer" aria-label="Fermer">✕</button>
      <div class="fc-tete">
        <div class="fc-carte">
          <div class="carte-cadre">
            <div class="carte-int">
              <div class="carte-haut">
                <span class="carte-rarete">${tier.label}</span>
                ${entry.rank ? `<span class="carte-num">${nb(entry.rank)} / ${nb(entry.tierSize)}</span>` : ''}
              </div>
              <div class="carte-art">${carteArtSvg(entry.code, tier.id)}<span class="carte-dept">${echapperTexte(entry.dept)}</span></div>
              <div class="carte-lisere"><span></span><span></span><span></span></div>
            </div>
          </div>
        </div>
      </div>
      <div class="fc-corps">
        <h2 id="fcNom" class="fc-nom ${entry.nom.length > 22 ? 'long' : ''}">${echapperTexte(entry.nom)}</h2>
        <p class="fc-dep">${DEPT_NAMES[entry.dept] ? echapperTexte(DEPT_NAMES[entry.dept]) + ' (' + echapperTexte(entry.dept) + ')' : echapperTexte(entry.dept)}</p>
        ${gentile ? `<p class="fc-gent">les ${echapperTexte(gentile)}</p>` : ''}
        <div class="fc-chiffres">
          <div class="fc-ch"><b>${nb(entry.pop)}</b><span>habitants</span></div>
          <div class="fc-ch"><b class="fc-rar">${tier.label}</b><span>rareté</span></div>
          ${troisieme}
        </div>
        ${savais}
        <div class="fc-actions">
          <button class="fc-btn principal" data-fc="carte">Voir sur la carte</button>
        </div>
      </div>
    </div>`);

  const boite = document.querySelector('#fenetre .fiche');
  if(!boite) return;
  boite.addEventListener('click', (e) => {
    const b = e.target.closest('[data-fc]');
    if(!b) return;
    if(b.dataset.fc === 'fermer'){ fermerFiche(null); return; }
    if(b.dataset.fc === 'carte') voirCommuneSurCarte(entry);
  });
  const premier = boite.querySelector('.fc-btn');
  if(premier && faits !== null) premier.focus();
}

// Place la commune au centre du cadre. Les deux rendus, canvas et SVG,
// lisent le meme couple (mapZoom, mapPan) : il suffit de le poser.
function centrerSurCommune(lat, lon){
  const wrap = document.getElementById('mapWrap');
  if(!wrap || !mapBounds || lat == null || lon == null) return false;
  const largeur = wrap.clientWidth, hauteur = wrap.clientHeight;
  if(!largeur || !hauteur) return false;
  const p = project(lat, lon);
  const ech = echelleCarte();
  mapZoom = Math.min(zoomMaxCarte(), Math.max(MAP_ZOOM_MIN, 12));
  mapPanX = largeur / 2 - p.x * MAP_W * ech * mapZoom;
  mapPanY = hauteur / 2 - p.y * MAP_H * ech * mapZoom;
  applyMapTransform();
  renderMapOverlay();
  demanderDessin();
  // applyMapTransform borne le cadrage : pres d'un bord la commune n'est plus
  // au centre. On lit donc le decalage APRES, sinon l'anneau vise a cote.
  marquerCommuneVisee(p.x * MAP_W * ech * mapZoom + mapPanX,
                      p.y * MAP_H * ech * mapZoom + mapPanY);
  return true;
}

let viseeTimer = null;
function marquerCommuneVisee(x, y){
  const wrap = document.getElementById('mapWrap');
  if(!wrap) return;
  const ancien = wrap.querySelector('.carte-visee');
  if(ancien) ancien.remove();
  clearTimeout(viseeTimer);
  const rond = document.createElement('div');
  rond.className = 'carte-visee';
  rond.style.left = x + 'px';
  rond.style.top = y + 'px';
  wrap.appendChild(rond);
  // il disparait seul : un repere permanent deviendrait du decor
  viseeTimer = setTimeout(() => rond.remove(), 4000);
}

function voirCommuneSurCarte(entry){
  if(fermerFiche) fermerFiche(null);
  const onglet = document.querySelector('.tab[data-tab="territoire"]');
  if(onglet) onglet.click();
  const carte = document.getElementById('mapWrap');
  if(carte && carte.scrollIntoView) carte.scrollIntoView({ behavior: 'smooth', block: 'center' });
  // le panneau vient d'etre affiche : il n'a ses dimensions qu'a l'image suivante
  requestAnimationFrame(() => requestAnimationFrame(() => {
    if(!centrerSurCommune(entry.lat, entry.lon)){
      notifier({ type: 'info', titre: 'Position inconnue',
                 texte: 'Cette commune n’a pas de coordonnées : la carte est restée où elle était.' });
    }
  }));
}

const grilleColl = document.getElementById('collectionGrid');
if(grilleColl){
  grilleColl.addEventListener('click', (e) => {
    const m = e.target.closest('.mini[data-code]');
    if(m) ouvrirFicheCommune(m.dataset.code);
  });
  grilleColl.addEventListener('keydown', (e) => {
    if(e.key !== 'Enter' && e.key !== ' ') return;
    const m = e.target.closest('.mini[data-code]');
    if(!m) return;
    e.preventDefault();
    ouvrirFicheCommune(m.dataset.code);
  });
}

document.getElementById('collectionSearch').addEventListener('input', renderCollection);
document.getElementById('boucliersSearch').addEventListener('input', renderBoucliers);
document.getElementById('echSearchMien').addEventListener('input', renderEchangeMien);

document.getElementById('collectionFilters').addEventListener('click', (e) => {
  const b = e.target.closest('.coll-filtre');
  if(!b) return;
  collectionFilterTier = b.dataset.tier;
  renderCollection();
});

document.querySelector('.coll-vue').addEventListener('click', async (e) => {
  const b = e.target.closest('[data-vue]');
  if(!b || b.dataset.vue === vueCollection) return;
  vueCollection = b.dataset.vue;
  document.querySelectorAll('.coll-vue button').forEach(x => {
    const actif = x.dataset.vue === vueCollection;
    x.classList.toggle('actif', actif);
    x.setAttribute('aria-selected', String(actif));
  });
  const bloc = document.getElementById('collFrance');
  if(vueCollection === 'france'){
    await loadMaFrance();
    if(!franceChargee){
      // les fonctions ne sont pas encore en base : on revient en arriere
      // proprement plutot que d'afficher une carte vide et des tirets
      vueCollection = 'mienne';
      document.querySelectorAll('.coll-vue button').forEach(x => {
        const actif = x.dataset.vue === 'mienne';
        x.classList.toggle('actif', actif);
        x.setAttribute('aria-selected', String(actif));
      });
      notifier({ type: 'info', titre: 'Ma France arrive bientôt',
                 texte: "Cette vue n'est pas encore disponible." });
      return;
    }
    if(bloc) bloc.hidden = false;
    majResumeFrance();
    // le canvas n'a de largeur qu'une fois le bloc affiche
    requestAnimationFrame(dessinerMaFrance);
  } else if(bloc){
    bloc.hidden = true;
  }
  renderCollection();
});



// ---------- Amis ----------
// Purement social : aucune treve, aucun bonus, aucun echange privilegie.
// Avec des inscriptions gratuites par e-mail, le moindre avantage lie a
// l'amitie serait exploite par trois comptes du meme joueur.
let amisListe = [];
let amisEtat = new Map();          // id du joueur -> 'accepte' | 'demande' | 'recue' | 'bloque'
let amisCharges = false;

async function loadAmis(){
  const { data, error } = await sb.rpc('mes_amis');
  if(error){
    // amis.sql pas encore execute : on laisse le bloc masque
    amisCharges = false;
    return;
  }
  amisCharges = true;
  amisListe = Array.isArray(data) ? data : [];
  amisEtat = new Map(amisListe.map(x => [x.id, x.etat]));
  renderAmis();
}

function pastilleAmi(x){
  if(x.avatar) return `<span class="am-pastille">${echapperTexte(x.avatar)}</span>`;
  const init = String(x.pseudo || '?').trim().charAt(0).toUpperCase();
  return `<span class="am-pastille init" style="color:${colorForPlayer(x.id)}">${echapperTexte(init)}</span>`;
}

function dateCourte(s){
  if(!s) return '';
  const d = new Date(s);
  const jours = Math.floor((Date.now() - d.getTime()) / 86400000);
  if(jours <= 0) return "aujourd'hui";
  if(jours === 1) return 'hier';
  return 'le ' + d.toLocaleDateString('fr-FR', { day: 'numeric', month: 'long' });
}

function renderAmis(){
  const bloc = document.getElementById('amis');
  const corps = document.getElementById('amCorps');
  if(!bloc || !corps) return;
  if(!amisCharges){ bloc.hidden = true; return; }
  bloc.hidden = false;

  const par = (e) => amisListe.filter(x => x.etat === e);
  const recues  = par('recue');
  const acceptes = par('accepte');
  const envoyees = par('demande');
  const bloques  = par('bloque');

  const cpt = document.getElementById('amCompte');
  if(cpt) cpt.textContent = acceptes.length
    + (recues.length ? ' · ' + recues.length + ' demande' + (recues.length > 1 ? 's' : '') : '');

  const nb = (n) => Number(n || 0).toLocaleString('fr-FR');
  const ligne = (x, actes, classe) => `
    <div class="am-ligne ${classe || ''}" data-ami="${echapperTexte(x.id)}">
      ${pastilleAmi(x)}
      <span class="am-qui"><b>${echapperTexte(x.pseudo)}</b><span>${actes.sous}</span></span>
      <span class="am-actes">${actes.html}</span>
    </div>`;

  let html = '';

  if(recues.length){
    html += '<h3>Demandes reçues</h3><div class="am-demandes">' + recues.map(x => ligne(x, {
      sous: nb(x.communes) + ' commune' + (x.communes > 1 ? 's' : '') + ' · ' + dateCourte(x.depuis),
      html: `<button class="am-btn oui" data-am="accepter">Accepter</button>
             <button class="am-btn non" data-am="refuser">Refuser</button>`
    })).join('') + '</div>';
  }

  html += '<h3>Mes amis</h3>';
  html += acceptes.length
    ? acceptes.map(x => ligne(x, {
        sous: nb(x.communes) + ' commune' + (x.communes > 1 ? 's' : '') + ' · ami depuis ' + dateCourte(x.depuis),
        html: `<button class="am-btn" data-am="voir">Voir</button>`
      })).join('')
    : '<p class="am-vide">Personne pour le moment. Cherche un joueur par son pseudo.</p>';

  if(envoyees.length){
    html += '<h3>Demandes envoyées</h3>' + envoyees.map(x => ligne(x, {
      sous: 'envoyée ' + dateCourte(x.depuis),
      html: `<span class="am-attente">en attente</span>
             <button class="am-btn non" data-am="refuser">Annuler</button>`
    })).join('');
  }

  if(bloques.length){
    html += '<h3>Bloqués</h3>' + bloques.map(x => ligne(x, {
      sous: 'bloqué ' + dateCourte(x.depuis),
      html: `<button class="am-btn non" data-am="debloquer">Débloquer</button>`
    }, 'bloque')).join('');
  }

  corps.innerHTML = html;
}

async function actionAmi(action, id, bouton){
  const appels = {
    accepter:  ['accepter_ami',     { p_ami: id }],
    refuser:   ['retirer_ami',      { p_ami: id }],
    debloquer: ['debloquer_joueur', { p_ami: id }],
    ajouter:   ['demander_ami',     { p_ami: id }],
    bloquer:   ['bloquer_joueur',   { p_ami: id }],
  };
  const appel = appels[action];
  if(!appel) return false;
  if(bouton) bouton.disabled = true;
  const { error } = await sb.rpc(appel[0], appel[1]);
  if(bouton) bouton.disabled = false;
  if(error){
    notifier({ type: 'erreur', titre: 'Amis', texte: messageLisible(error.message) });
    return false;
  }
  await loadAmis();
  return true;
}

document.getElementById('amCorps').addEventListener('click', async (e) => {
  const b = e.target.closest('[data-am]');
  if(!b) return;
  const id = b.closest('[data-ami]')?.dataset.ami;
  if(!id) return;
  if(b.dataset.am === 'voir'){ ouvrirProfil(id); return; }
  await actionAmi(b.dataset.am, id, b);
});

// ---------- Chercher un joueur ----------
// Une recherche par pseudo, pas la liste de tous les joueurs : a dix-huit ce
// serait pratique, a deux cents ce serait un annuaire — et un annuaire est
// exactement l'outil de qui cherche a importuner du monde.
document.getElementById('amAjouter').addEventListener('click', () => {
  const zone = document.getElementById('amRecherche');
  zone.hidden = !zone.hidden;
  if(!zone.hidden) document.getElementById('amChamp').focus();
  else { document.getElementById('amChamp').value = ''; document.getElementById('amResultats').innerHTML = ''; }
});

let rechercheAmiMinuteur = null;
document.getElementById('amChamp').addEventListener('input', (e) => {
  clearTimeout(rechercheAmiMinuteur);
  const q = e.target.value.trim();
  const zone = document.getElementById('amResultats');
  if(q.length < 2){ zone.innerHTML = ''; return; }
  // on attend une pause de frappe : sinon une requete part a chaque lettre
  rechercheAmiMinuteur = setTimeout(async () => {
    const { data, error } = await sb.from('joueurs')
      .select('id, pseudo, avatar').ilike('pseudo', '%' + q + '%').limit(8);
    if(error){ zone.innerHTML = ''; return; }
    const moi = window.__monId || '';
    const trouves = (data || []).filter(x => x.id !== moi);
    if(trouves.length === 0){
      zone.innerHTML = '<p class="am-vide">Aucun joueur de ce nom.</p>';
      return;
    }
    zone.innerHTML = trouves.map(x => {
      const etat = amisEtat.get(x.id);
      const acte = etat === 'accepte'  ? '<span class="am-attente">déjà ami</span>'
                 : etat === 'demande'  ? '<span class="am-attente">demande envoyée</span>'
                 : etat === 'recue'    ? '<button class="am-btn oui" data-amr="accepter">Accepter</button>'
                 : etat === 'bloque'   ? '<button class="am-btn non" data-amr="debloquer">Débloquer</button>'
                 : '<button class="am-btn oui" data-amr="ajouter">Ajouter</button>';
      return `<div class="am-ligne" data-ami="${echapperTexte(x.id)}">
        ${pastilleAmi(x)}
        <span class="am-qui"><b>${echapperTexte(x.pseudo)}</b></span>
        <span class="am-actes">${acte}</span>
      </div>`;
    }).join('');
  }, 280);
});

document.getElementById('amResultats').addEventListener('click', async (e) => {
  const b = e.target.closest('[data-amr]');
  if(!b) return;
  const id = b.closest('[data-ami]')?.dataset.ami;
  if(!id) return;
  if(await actionAmi(b.dataset.amr, id, b)){
    document.getElementById('amChamp').dispatchEvent(new Event('input', { bubbles: true }));
    notifier({ type: 'succes', titre: 'Amis',
               texte: b.dataset.amr === 'ajouter' ? 'Demande envoyée.' : 'C’est fait.' });
  }
});

// ---------- Mon solde, mes tirages ----------
// La table joueurs n'est plus lisible en dehors de id, pseudo et avatar : une
// policy RLS ne filtre que des lignes, jamais des colonnes, et celle du SELECT
// laissait donc voir le solde et le rythme de jeu de tout le monde. On demande
// desormais son propre etat a une fonction, qui ne rend que sa ligne.
async function monEtat(){
  const { data, error } = await sb.rpc('mon_etat');
  if(error) return null;
  return Array.isArray(data) ? (data[0] || null) : data;
}

// ---------- Profil d'un joueur ----------
// Une seule fenetre pour tout le monde : sur son propre profil, les boutons
// d'action laissent la place aux boutons de modification.
const AVATARS = [
  '🐺','🦊','🦅','🐗','🦌','🐻','🦉','🐎','🦁','🐉',
  '⚔️','🛡️','🏰','👑','⚓','🗡️','🏹','🔱','⛰️','🌊',
  '🍷','🧀','🥖','🌻','🌲','🗼','⚜️','🔥','❄️','⭐'
];

// Le titre ne se saisit pas : il se deduit de la region ou le joueur a le
// plus de communes. Rien a stocker, rien a moderer, et il suit le territoire.
function regionsTriees(deps){
  const parRegion = new Map();
  for(const d of (deps || [])){
    const r = DEP_REGION[d.dep];
    if(!r) continue;
    parRegion.set(r, (parRegion.get(r) || 0) + (Number(d.n) || 0));
  }
  return [...parRegion.entries()].sort((x, y) => y[1] - x[1]);
}

// Une table plutot qu'une regle : « du Grand Est » et « du Centre-Val de Loire »
// font mentir n'importe quelle regex, et il n'y a que treize regions.
const ARTICLE_REGION = {
  'Auvergne-Rhône-Alpes':        "d'Auvergne-Rhône-Alpes",
  'Bourgogne-Franche-Comté':     'de Bourgogne-Franche-Comté',
  'Bretagne':                    'de Bretagne',
  'Centre-Val de Loire':         'du Centre-Val de Loire',
  'Corse':                       'de Corse',
  'Grand Est':                   'du Grand Est',
  'Hauts-de-France':             'des Hauts-de-France',
  'Île-de-France':               "d'Île-de-France",
  'Normandie':                   'de Normandie',
  'Nouvelle-Aquitaine':          'de Nouvelle-Aquitaine',
  'Occitanie':                   "d'Occitanie",
  'Pays de la Loire':            'des Pays de la Loire',
  "Provence-Alpes-Côte d'Azur":  "de Provence-Alpes-Côte d'Azur",
};
function articleRegion(r){ return ARTICLE_REGION[r] || 'de ' + r; }

function titreDepuisDeps(deps){
  const regions = regionsTriees(deps);
  if(regions.length === 0) return 'Sans terre';
  const total = regions.reduce((s, [, n]) => s + n, 0);
  const [region, max] = regions[0];
  const part = total > 0 ? max / total : 0;
  // trois paliers : le titre dit aussi a quel point le joueur est concentre
  const rang = part >= 0.6 ? 'Seigneur' : part >= 0.3 ? 'Maître' : 'Baron';
  return rang + ' ' + articleRegion(region);
}

function avatarHtml(p, couleur){
  if(p.avatar) return `<span class="pr-emoji">${echapperTexte(p.avatar)}</span>`;
  // pas d'avatar choisi : l'initiale du pseudo, dans la couleur du joueur
  const init = String(p.pseudo || '?').trim().charAt(0).toUpperCase();
  return `<span class="pr-initiale" style="color:${couleur}">${echapperTexte(init)}</span>`;
}

let profilEnCours = null;
let fermerProfil = null;

// L'etat du lien se lit dans la liste deja chargee : pas d'appel de plus a
// l'ouverture d'une fiche.
function boutonAmiProfil(id){
  const etat = amisEtat.get(id);
  if(etat === 'accepte') return '<button class="pr-ami pose" data-pr="retirer-ami">✓ Ami</button>';
  if(etat === 'demande') return '<button class="pr-ami pose" data-pr="retirer-ami">Demande envoyée</button>';
  if(etat === 'recue')   return '<button class="pr-ami" data-pr="accepter-ami">Accepter</button>';
  if(etat === 'bloque')  return '';
  return '<button class="pr-ami" data-pr="ajouter-ami">+ Ami</button>';
}

async function ouvrirProfil(joueurId){
  if(!joueurId) return;
  const { data, error } = await sb.rpc('profil_joueur', { p_joueur: joueurId });
  if(error || !data){
    // profil-joueur.sql pas encore execute : on le dit au lieu d'ouvrir un vide
    notifier({ type: 'info', titre: 'Profil indisponible',
               texte: "Cette fiche n'est pas encore disponible." });
    return;
  }
  profilEnCours = data;
  rendreProfil();
}

function rendreProfil(){
  const p = profilEnCours;
  if(!p) return;
  const moi = !!p.est_moi;
  const couleur = moi ? COULEUR_MOI : colorForPlayer(p.id);
  const nb = (x) => Number(x || 0).toLocaleString('fr-FR');
  const regions = regionsTriees(p.deps);
  const depuis = p.depuis
    ? new Date(p.depuis).toLocaleDateString('fr-FR', { day: 'numeric', month: 'long', year: 'numeric' })
    : null;

  const phares = (p.phares || []).map(c => {
    const t = TIERS.find(x => x.id === c.tier);
    return `<div class="pr-phare">
      <span class="pr-phare-nom"><b>${echapperTexte(c.nom)}</b>
        <span>${echapperTexte(DEPT_NAMES[c.dep] || '')} (${echapperTexte(c.dep)}) · ${nb(c.pop)} hab.</span></span>
      <span class="pr-tag ${echapperTexte(c.tier)}">${echapperTexte(t ? t.label : c.tier)}</span>
    </div>`;
  }).join('') || '<p class="pr-vide">Aucune commune pour le moment.</p>';

  const puces = regions.slice(0, 4).map(([r, n], i) =>
    `<span class="pr-puce${i === 0 ? ' or' : ''}">${i === 0 ? '👑 ' : ''}${echapperTexte(r)}<i>${nb(n)}</i></span>`
  ).join('') || '<span class="pr-puce">Aucune région</span>';

  const actions = moi
    ? `<button class="pr-btn principal" data-pr="avatar">Changer d'avatar</button>
       <button class="pr-btn" data-pr="pseudo">Changer de pseudo</button>`
    : `<button class="pr-btn principal" data-pr="territoire">Voir son territoire</button>
       <button class="pr-btn" data-pr="echange">Proposer un échange</button>`;

  fermerProfil = ouvrirFenetre(`
    <div class="fenetre profil" role="dialog" aria-modal="true" aria-labelledby="prNom"
         style="--joueur:${couleur}">
      <div class="pr-tete">
        ${moi ? '' : boutonAmiProfil(p.id)}
        <button class="pr-fermer" data-pr="fermer" aria-label="Fermer">✕</button>
        <div class="pr-avatar">${avatarHtml(p, couleur)}</div>
        <h2 id="prNom">${echapperTexte(p.pseudo)}</h2>
        <p class="pr-sous"><b>${echapperTexte(titreDepuisDeps(p.deps))}</b>${
          p.rang > 0 ? ` · <span class="pr-rang">${p.rang}${p.rang === 1 ? 'er' : 'e'}</span>` : ''}</p>
      </div>
      <div class="pr-corps">
        <div class="pr-chiffres">
          <div class="pr-ch"><b style="color:${couleur}">${nb(p.communes)}</b><span>communes</span></div>
          <div class="pr-ch"><b>${nb(p.departements)}</b><span>départements</span></div>
          <div class="pr-ch"><b style="color:var(--c-legendaire)">${nb(p.legendaires)}</b><span>légendaires</span></div>
          <div class="pr-ch"><b style="color:var(--c-rare)">${nb(p.rares)}</b><span>rares</span></div>
        </div>

        <h3>Territoire</h3>
        <div class="pr-puces">${puces}</div>

        <h3>Communes phares</h3>
        ${phares}

        <h3>En chiffres</h3>
        <div class="pr-puces">
          ${depuis ? `<span class="pr-puce">📅 Depuis le ${echapperTexte(depuis)}</span>` : ''}
          <span class="pr-puce">⚔️ ${nb(p.conquetes)} conquête${p.conquetes > 1 ? 's' : ''}</span>
          <span class="pr-puce">🛡️ ${nb(p.perdues)} perdue${p.perdues > 1 ? 's' : ''} au combat</span>
          <span class="pr-puce">👥 ${nb(p.habitants)} habitants</span>
        </div>

        <div class="pr-actions">${actions}</div>
        ${moi ? '' : `<button class="pr-bloquer" data-pr="${
          amisEtat.get(p.id) === 'bloque' ? 'debloquer' : 'bloquer'}">${
          amisEtat.get(p.id) === 'bloque' ? 'Débloquer ce joueur' : 'Bloquer ce joueur'}</button>`}
      </div>
    </div>`, () => { profilEnCours = null; fermerProfil = null; });
}

// Les actions de la fiche, par delegation sur le fond de fenetre
document.getElementById('fenetre').addEventListener('click', async (e) => {
  const b = e.target.closest('[data-pr]');
  if(!b || !profilEnCours) return;
  const p = profilEnCours;
  const action = b.dataset.pr;

  if(action === 'fermer'){
    if(fermerProfil) fermerProfil(null);
    return;
  }

  if(action === 'territoire'){
    const id = p.est_moi ? ID_MOI : p.id;
    joueurSurligne = id;
    CV.donneesSignature = '';
    if(fermerProfil) fermerProfil(null);
    const onglet = document.querySelector('.tab[data-tab="territoire"]');
    if(onglet) onglet.click();
    renderMapOverlay();
    demanderDessin();
    const carte = document.getElementById('mapWrap');
    if(carte && carte.scrollIntoView) carte.scrollIntoView({ behavior: 'smooth', block: 'center' });
    return;
  }

  const liens = { 'ajouter-ami':'ajouter', 'retirer-ami':'refuser',
                  'accepter-ami':'accepter', 'bloquer':'bloquer', 'debloquer':'debloquer' };
  if(liens[action]){
    if(action === 'bloquer' &&
       !confirm('Bloquer ' + p.pseudo + ' ?\n\nVotre amitié sera supprimée et il ne pourra plus '
                + 'te demander en ami ni joindre un mot à ses propositions d’échange.')) return;
    if(await actionAmi(liens[action], p.id, b)) rendreProfil();
    return;
  }

  if(action === 'echange'){
    if(fermerProfil) fermerProfil(null);
    const onglet = document.querySelector('.tab[data-tab="echange"]');
    if(onglet) onglet.click();
    return;
  }

  if(action === 'avatar'){
    const zone = b.closest('.pr-actions');
    const deja = zone.querySelector('.pr-choix');
    if(deja){ deja.remove(); return; }
    const choix = document.createElement('div');
    choix.className = 'pr-choix';
    choix.innerHTML = AVATARS.map(x =>
      `<button data-pr="avatar-choix" data-emoji="${x}" class="${p.avatar === x ? 'actif' : ''}">${x}</button>`
    ).join('');
    zone.appendChild(choix);
    return;
  }

  if(action === 'avatar-choix'){
    const emoji = b.dataset.emoji;
    const { error } = await sb.rpc('changer_avatar', { p_avatar: emoji });
    if(error){ notifier({ type: 'erreur', titre: 'Avatar', texte: messageLisible(error.message) }); return; }
    profilEnCours.avatar = emoji;
    rendreProfil();
    notifier({ type: 'succes', titre: 'Avatar changé' });
    return;
  }

  if(action === 'pseudo'){
    const nouveau = prompt(
      'Ton nouveau pseudo, entre 3 et 20 caractères.\n\nTu ne pourras plus en changer avant sept jours.',
      p.pseudo);
    if(nouveau == null) return;
    const { data, error } = await sb.rpc('changer_pseudo', { p_pseudo: nouveau });
    if(error){ notifier({ type: 'erreur', titre: 'Pseudo', texte: messageLisible(error.message) }); return; }
    profilEnCours.pseudo = data;
    rendreProfil();
    notifier({ type: 'succes', titre: 'Pseudo changé', texte: 'Tu es maintenant ' + data + '.' });
    loadClassement();
    return;
  }
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
        loadObjectifs();
        // les cartes restent affichees : c'est le joueur qui decide de passer au suivant
        loadPackStatus().then(proposerPaquetSuivant);
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
    </div>
    <div class="paquet-eclat"></div>
    <div class="paquet-bouts">${MORCEAUX_PAQUET}</div>`;
  return pack;
}

// ---------- Jetons de paquets ----------
let packStatusCache = null;
let packStatusFetchedAt = 0;
let packStatusInterval = null;
let dispoPrecedente = null;   // pour reperer le moment ou un jeton se recharge

// Morceaux de papier projetes a la dechirure : positions figees, calculees une fois
const MORCEAUX_PAQUET = [
  [-64, -78, -150], [-38, -96, 110], [-12, -104, -60], [14, -100, 140],
  [42, -88, -110], [66, -66, 70], [-52, -44, 40], [54, -38, -80], [4, -58, 190],
].map(([tx, ty, r], i) =>
  `<i style="--tx:${tx}px;--ty:${ty}px;--r:${r}deg;--d:${i * 22}ms"></i>`).join('');

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

  // un jeton vient de se recharger pendant que le joueur est sur le jeu
  if(dispoPrecedente !== null && dispo > dispoPrecedente && !paquetEnCours){
    notifier({
      type: 'succes',
      titre: 'Un paquet gratuit t\'attend',
      texte: dispo > 1 ? `Tu en as ${dispo} en réserve.` : 'Clique dessus pour le déchirer.'
    });
  }
  dispoPrecedente = dispo;
  majPaquetPret(dispo);
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

// Le paquet se tend, puis se dechire. Le tirage part pendant l'animation,
// pour ne pas laisser le joueur attendre une fois le paquet disparu.
async function dechirerPaquet(pack, nbCartes){
  const zone = document.getElementById('packZone');
  pack.classList.add('tension');
  if(!REDUCED_MOTION) await new Promise(r => setTimeout(r, 200));
  pack.classList.add('dechire');
  const animation = new Promise(resolve => setTimeout(resolve, REDUCED_MOTION ? 0 : 660));
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
    if(zone) zone.innerHTML = '';
    paquetEnCours = false;
    loadPackStatus();
    return;
  }
  revealCards(draws);
}

function afficherPaquetATirer(type, nbCartes){
  const zone = document.getElementById('packZone');
  zone.innerHTML = '';
  const pack = makePackEl(type);
  zone.appendChild(pack);
  pack.addEventListener('click', () => dechirerPaquet(pack, nbCartes), { once: true });
}

// Paquet pose sur l'ecran d'arrivee : un seul clic le paie et le dechire.
function afficherPaquetPret(type){
  const zone = document.getElementById('packZone');
  if(!zone) return;
  zone.innerHTML = '';
  const pack = makePackEl(type);
  pack.dataset.pret = '1';
  pack.setAttribute('aria-label', 'Ouvrir un paquet gratuit');
  zone.appendChild(pack);
  pack.addEventListener('click', async () => {
    if(paquetEnCours) return;
    paquetEnCours = true;
    renderPackStatus();
    const err = await payerPaquet(type);
    if(err){
      paquetEnCours = false;
      notifier({ type: 'erreur', titre: 'Impossible d\'ouvrir le paquet', texte: messageLisible(err.message) });
      loadPackStatus();
      return;
    }
    delete pack.dataset.pret;
    loadPackStatus();
    dechirerPaquet(pack, 5);
  }, { once: true });
}

// Tant qu'un paquet gratuit attend, il est visible sans qu'on ait a cliquer sur un bouton.
function majPaquetPret(dispo){
  const zone = document.getElementById('packZone');
  if(!zone || paquetEnCours) return;
  const pret = zone.querySelector('.paquet[data-pret]');
  if(dispo >= 1 && zone.children.length === 0) afficherPaquetPret('gratuit');
  else if(dispo < 1 && pret) zone.innerHTML = '';
}

// Paquet paye mais pas encore ouvert (page fermee ou rechargee) : on le represente
async function verifierTiragesEnAttente(){
  if(paquetEnCours) return;
  const { data: u } = await sb.auth.getUser();
  if(!u || !u.user) return;
  const data = await monEtat();
  if(!data || !(data.tirages_restants > 0)) return;
  paquetEnCours = true;
  renderPackStatus();
  afficherPaquetATirer('gratuit', Math.min(5, data.tirages_restants));
  notifier({ type: 'info', titre: 'Tu as un paquet non ouvert', texte: 'Clique dessus dans l\'onglet Tirage pour le déchirer.' });
}

// Un paquet attend encore : on propose un bouton sous les cartes, sans les effacer.
async function proposerPaquetSuivant(){
  if(paquetEnCours) return;
  const zone = document.getElementById('packZone');
  if(!zone || zone.querySelector('.suivant-ligne')) return;
  const { data: u } = await sb.auth.getUser();
  if(!u || !u.user) return;
  const data = await monEtat();
  const restants = data && data.tirages_restants > 0 ? data.tirages_restants : 0;
  if(restants <= 0) return;

  // tant qu'il reste des tirages, on ne peut pas en lancer un nouveau par-dessus
  paquetEnCours = true;
  renderPackStatus();

  const paquets = Math.ceil(restants / 5);
  const ligne = document.createElement('div');
  ligne.className = 'suivant-ligne';
  const btn = document.createElement('button');
  btn.className = 'open-btn';
  btn.textContent = paquets > 1
    ? `Ouvrir le paquet suivant (${paquets} en attente)`
    : 'Ouvrir le paquet suivant';
  btn.addEventListener('click', () => {
    afficherPaquetATirer('gratuit', Math.min(5, restants));
  }, { once: true });
  ligne.appendChild(btn);
  zone.appendChild(ligne);
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

  const joueurRow = await monEtat();
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
  const champB = document.getElementById('boucliersSearch');
  const rechercheB = sansAccents(champB ? champB.value.trim() : '');
  const toutes = Array.from(collectionMap.values())
    .filter(e => e.tier.id === 'rare' || e.tier.id === 'legendaire')
    .filter(e => correspondRecherche(e.nom, e.dept, rechercheB))
    .sort((a, b) => TIERS.indexOf(a.tier) - TIERS.indexOf(b.tier) || b.pop - a.pop);
  if(toutes.length === 0){
    grid.innerHTML = rechercheB
      ? '<p class="collection-empty">Aucune commune ne correspond à cette recherche.</p>'
      : '<p class="collection-empty">Tu n\'as aucune commune rare ou légendaire à protéger.</p>';
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
  const searchText = sansAccents(searchEl ? searchEl.value.trim() : '');

  let entries = Array.from(collectionMap.values()).sort((a,b) => {
    const ra = TIERS.indexOf(a.tier), rb = TIERS.indexOf(b.tier);
    if(ra !== rb) return ra - rb;
    return b.pop - a.pop;
  });

  if(sellFilterTier !== 'tous'){
    entries = entries.filter(e => e.tier.id === sellFilterTier);
  }
  if(searchText){
    entries = entries.filter(e => correspondRecherche(e.nom, e.dept, searchText));
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
        let { data, error } = await sb.rpc('attaquer', { p_commune_code: code, p_intensite: intensiteChoisie });
        // si intensite.sql n'a pas encore ete execute, on attaque comme avant
        if(error && /p_intensite|does not exist|could not find/i.test(error.message || '')){
          ({ data, error } = await sb.rpc('attaquer', { p_commune_code: code }));
        }
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
            titre: `Victoire contre ${nomCible}${result.cout ? ` (−${result.cout} pts)` : ''}`,
            texte: result.victoires_consecutives >= 2 ? 'Encore une victoire pour la conquérir.' : `Série : ${result.victoires_consecutives} sur 3`,
            serie: result.victoires_consecutives
          });
        } else {
          notifier({ type: 'defaite', titre: `Défaite contre ${nomCible}${result.cout ? ` (−${result.cout} pts)` : ''}`, texte: `Attaque ${intensite().label.toLowerCase()} à ${intensite().chances} % : la série repart à zéro.`, serie: 0 });
        }
        await loadCombat();
        loadPackStatus();
        loadObjectifs();
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
// doit rester aligne avec delai_attaque() dans combat-proximite.sql
const DELAI_ATTAQUE_MS = {
  commun: 2 * 60 * 1000,
  peucommun: 5 * 60 * 1000,
  rare: 10 * 60 * 1000,
  legendaire: 3 * 3600 * 1000,
};

// doit rester aligne avec intensite.sql
const INTENSITES = [
  { id: 'prudente', label: 'Prudente', chances: 35, facteur: 0.35, aide: 'Le moins cher, mais il faudra souvent recommencer.' },
  { id: 'normale', label: 'Normale', chances: 50, facteur: 1, aide: 'Le bon compromis entre coût et rapidité.' },
  { id: 'offensive', label: 'Offensive', chances: 65, facteur: 2, aide: 'Deux fois plus rapide pour conclure, mais ça coûte.' },
];
let intensiteChoisie = 'normale';
try{
  const v = localStorage.getItem('tf-intensite');
  if(v && INTENSITES.some(i => i.id === v)) intensiteChoisie = v;
} catch(e){}
const intensite = (id) => INTENSITES.find(i => i.id === (id || intensiteChoisie)) || INTENSITES[1];

function coutIntensite(tierId, id){
  return Math.max(1, Math.round(coutAttaque(tierId) * intensite(id).facteur));
}

// doit rester aligne avec cout_attaque() en base : le serveur ne suit plus
// le prix de rachat, il a sa propre echelle
const COUT_ATTAQUE = { commun: 3, peucommun: 5, rare: 10, legendaire: 100 };
function coutAttaque(tierId){
  return COUT_ATTAQUE[tierId] || 3;
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
  // la collection affiche les sieges : on ne la redessine que s'ils ont change
  const signature = menaces.map(m => m.commune_code + ':' + m.victoires_consecutives).sort().join('|');
  if(signature !== menacesSignature){
    menacesSignature = signature;
    if(document.getElementById('collectionGrid')) renderCollection();
  }
}

function renderMenaces(){
  const enDanger = menaces.filter(m => m.victoires_consecutives > 0);
  const badge = document.getElementById('combatBadge');
  if(badge){
    badge.hidden = enDanger.length === 0;
    badge.textContent = enDanger.length;
    majBadgePlus();
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
            : (m.attaquant_id ? `<button class="menace-defendre" data-commune="${m.commune_code}" data-attaquant="${m.attaquant_id}" data-nom="${echapperTexte(m.nom)}">${ICONE_BOUCLIER}Défendre (${coutIntensite(m.tier)} pts, ${intensite().chances} %)</button>` : '')) : ''}
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

// ---------- Les chances du moment, dans l'onglet Regles ----------
// Le serveur pondere chaque palier par ce qu'il lui reste de communes libres :
// les pourcentages bougent donc tout seuls au fil de la saison. On les relit a
// chaque ouverture de l'onglet plutot que de les figer dans la page.
const COULEUR_TIER = {
  legendaire: 'var(--c-legendaire)', rare: 'var(--c-rare)',
  peucommun: 'var(--c-peucommun)', commun: 'var(--c-commun)'
};
let tauxEnCours = false;

async function loadTauxTirage(){
  if(tauxEnCours) return;
  tauxEnCours = true;
  try{
    const { data, error } = await sb.rpc('taux_actuels');
    if(error || !Array.isArray(data)) return;   // on laisse le tiret, sans bruit
    for(const ligne of data){
      const cell = document.querySelector('#panel-regles [data-taux="' + ligne.tier + '"]');
      if(!cell) continue;
      const total = parseInt(
        (document.querySelector('#panel-regles [data-total="' + ligne.tier + '"]')?.textContent || '0')
          .replace(/[^0-9]/g, ''), 10) || 0;
      const libres = Number(ligne.libres) || 0;
      const part = total > 0 ? Math.round(100 * libres / total) : 0;
      const chance = Number(ligne.chance) || 0;
      cell.style.color = COULEUR_TIER[ligne.tier] || '';
      cell.innerHTML =
        fmtTaux(chance) + '\u00A0%' +
        '<span class="jauge"><i style="width:' + part + '%;background:' +
          (COULEUR_TIER[ligne.tier] || 'var(--brume)') + '"></i></span>' +
        // le total est deja dans la colonne Communes : le repeter ici
        // n'apporte rien et elargit la colonne sur mobile
        '<span class="sous">' + (libres === 0
          ? 'palier épuisé'
          : fmtNombre(libres) + (libres > 1 ? ' libres' : ' libre')) +
        '</span>';
    }
  } finally {
    tauxEnCours = false;
  }
}

// toujours deux decimales : une legendaire a 0,05 % a besoin des deux, et une
// precision qui change d'une ligne a l'autre dans la meme colonne fait bancal
function fmtTaux(x){
  return x.toLocaleString('fr-FR', { minimumFractionDigits: 2, maximumFractionDigits: 2 });
}
function fmtNombre(n){ return n.toLocaleString('fr-FR'); }

document.getElementById('reglesBtnMobile').addEventListener('click', () => document.getElementById('reglesBtn').click());

document.getElementById('reglesBtn').addEventListener('click', () => {
  const tab = document.querySelector('.tab[data-tab="regles"]');
  if(tab){ tab.click(); return; }
  loadTauxTirage();
  // l'onglet Regles n'est plus dans la barre : on l'ouvre a la main
  document.querySelectorAll('.tab').forEach(t => t.classList.remove('active'));
  document.querySelectorAll('.tab-panel').forEach(p => p.classList.toggle('active', p.id === 'panel-regles'));
  document.getElementById('reglesBtn').classList.add('actif');
  document.getElementById('reglesBtnMobile').classList.add('actif');
  renderNotifications();
  window.scrollTo({ top: 0, behavior: 'smooth' });
});

document.getElementById('combatMenacesListe').addEventListener('click', async (e) => {
  const btn = e.target.closest('.menace-defendre');
  if(!btn || btn.disabled) return;
  btn.disabled = true;
  try{
    let { data, error } = await sb.rpc('defendre', { p_commune_code: btn.dataset.commune, p_attaquant: btn.dataset.attaquant, p_intensite: intensiteChoisie });
    if(error && /p_intensite|does not exist|could not find/i.test(error.message || '')){
      ({ data, error } = await sb.rpc('defendre', { p_commune_code: btn.dataset.commune, p_attaquant: btn.dataset.attaquant }));
    }
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
      notifier({ type: 'defaite', titre: `Défense ratée à ${btn.dataset.nom}`, texte: `L'attaquant garde ses victoires (−${r ? r.cout : ''} pts).` });
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

  const joueurRow = await monEtat();
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

function renderIntensite(){
  const zone = document.getElementById('combatIntensite');
  if(!zone) return;
  zone.innerHTML = INTENSITES.map(i => `
    <button class="intensite ${i.id === intensiteChoisie ? 'actif' : ''}" data-intensite="${i.id}" aria-pressed="${i.id === intensiteChoisie}">
      <span class="int-label">${i.label}</span>
      <span class="int-chances">${i.chances} %</span>
      <span class="int-cout">${i.facteur === 1 ? 'prix normal' : (i.facteur < 1 ? 'un tiers du prix' : 'prix doublé')}</span>
    </button>`).join('') + `<p class="int-aide">${intensite().aide}</p>`;
}

document.getElementById('combatIntensite').addEventListener('click', (e) => {
  const b = e.target.closest('[data-intensite]');
  if(!b) return;
  intensiteChoisie = b.dataset.intensite;
  try{ localStorage.setItem('tf-intensite', intensiteChoisie); } catch(err){}
  renderIntensite();
  renderCombatGrid();
  renderMenaces();
});

function renderCombatGrid(){
  renderIntensite();
  const grid = document.getElementById('combatGrid');
  const searchEl = document.getElementById('combatSearch');
  const searchText = sansAccents(searchEl ? searchEl.value.trim() : '');

  let cibles = combatCibles;
  if(combatFilterTier !== 'tous'){
    cibles = cibles.filter(c => c.communes.tier === combatFilterTier);
  }
  if(searchText){
    cibles = cibles.filter(c => correspondRecherche(c.communes.nom, c.communes.departement, searchText));
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

    const cout = coutIntensite(commune.tier);
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
          <button class="cible-attaquer" data-action="attaquer" data-code="${c.commune_code}" ${disabled ? 'disabled' : ''}>Attaquer <b>${cout} pts</b><i>${intensite().chances} %</i></button>
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

// ---------- Navigation : barre du bas et menu "Plus" sur telephone ----------
// Les 4 onglets principaux restent dans la barre, les autres passent dans le menu.
const ONGLETS_BARRE = ['tirage', 'collection', 'combat', 'defense'];
const ONGLETS_MENU = ['territoire', 'communaute', 'bourse', 'echange', 'succes'];
const ICONE_PROFIL = '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><circle cx="12" cy="8" r="3.6"/><path d="M4.5 20a7.5 7.5 0 0 1 15 0"/></svg>';
const ICONE_REGLES = '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M4 5.5A2.5 2.5 0 0 1 6.5 3H20v15H6.5A2.5 2.5 0 0 0 4 20.5z"/><path d="M4 20.5A2.5 2.5 0 0 0 6.5 23H20v-5"/><path d="M9 8h7M9 11.5h5"/></svg>';
const ICONE_SORTIE = '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" aria-hidden="true"><path d="M15 4H8a2 2 0 0 0-2 2v12a2 2 0 0 0 2 2h7"/><path d="M11 12h10m-3-3 3 3-3 3"/></svg>';
const surTelephone = () => window.matchMedia('(max-width: 720px)').matches;
const LIEN_DISCORD = 'https://discord.gg/T6suSy6xa7';
const ICONE_DISCORD = '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M21 11.5a8.4 8.4 0 0 1-9 8.4 9.6 9.6 0 0 1-2.8-.4L4 21l1.5-4.1A8.2 8.2 0 0 1 3 11.5 8.4 8.4 0 0 1 12 3a8.4 8.4 0 0 1 9 8.5z"/><path d="M9 11h.01M12 11h.01M15 11h.01"/></svg>';

function construireMenuPlus(){
  const liste = document.getElementById('feuilleListe');
  if(!liste) return;
  const entrees = ONGLETS_MENU.map(id => {
    const tab = document.querySelector(`.tab[data-tab="${id}"]`);
    if(!tab) return '';
    const icone = tab.querySelector('.icon').innerHTML;
    const nom = tab.childNodes[2] ? tab.childNodes[2].textContent.trim() : id;
    const badge = tab.querySelector('.tab-badge');
    const nb = badge && !badge.hidden ? `<span class="fp-badge">${badge.textContent}</span>` : '';
    return `<button class="fp-item" data-aller="${id}">${icone}${nom}${nb}</button>`;
  }).join('');
  liste.innerHTML = entrees + `
    <div class="fp-sep"></div>
    <button class="fp-item" data-aller="profil">${ICONE_PROFIL}Mon profil</button>
    <button class="fp-item" data-aller="regles">${ICONE_REGLES}Règles du jeu</button>
    <a class="fp-item fp-lien" href="${LIEN_DISCORD}" target="_blank" rel="noopener">${ICONE_DISCORD}Rejoindre le Discord</a>
    <button class="fp-item sortie" data-deconnexion>${ICONE_SORTIE}Se déconnecter</button>`;
}

function ouvrirMenuPlus(ouvert){
  const feuille = document.getElementById('feuillePlus');
  const voile = document.getElementById('voileMenu');
  const bouton = document.getElementById('btnPlus');
  if(!feuille || !voile) return;
  if(ouvert) construireMenuPlus();
  feuille.hidden = false;
  voile.hidden = false;
  requestAnimationFrame(() => {
    feuille.classList.toggle('ouvert', ouvert);
    voile.classList.toggle('ouvert', ouvert);
  });
  bouton.setAttribute('aria-expanded', String(ouvert));
  bouton.classList.toggle('actif', ouvert);
  if(!ouvert){
    setTimeout(() => { feuille.hidden = true; voile.hidden = true; }, 220);
  }
}

// La pastille des attaques suit l'onglet Defense : sur la barre, ou sur "Plus" s'il est dans le menu
function majBadgePlus(){
  const source = document.getElementById('combatBadge');
  const cible = document.getElementById('plusBadge');
  if(!source || !cible) return;
  const dansLeMenu = surTelephone() && ONGLETS_MENU.includes('defense');
  cible.hidden = !dansLeMenu || source.hidden;
  cible.textContent = source.textContent;
}

document.getElementById('btnPlus').addEventListener('click', (e) => {
  e.stopPropagation();
  ouvrirMenuPlus(!document.getElementById('feuillePlus').classList.contains('ouvert'));
});
document.getElementById('voileMenu').addEventListener('click', () => ouvrirMenuPlus(false));
document.addEventListener('keydown', (e) => {
  if(e.key === 'Escape' && document.getElementById('feuillePlus').classList.contains('ouvert')) ouvrirMenuPlus(false);
});
document.getElementById('feuilleListe').addEventListener('click', (e) => {
  // un lien externe ouvre son onglet tout seul : on se contente de refermer le menu
  if(e.target.closest('.fp-lien')){ ouvrirMenuPlus(false); return; }
  const b = e.target.closest('[data-aller], [data-deconnexion]');
  if(!b) return;
  ouvrirMenuPlus(false);
  if(b.hasAttribute('data-deconnexion')){ sb.auth.signOut(); return; }
  if(b.dataset.aller === 'profil'){ ouvrirProfil(window.__monId || null); return; }
  if(b.dataset.aller === 'regles'){ document.getElementById('reglesBtn').click(); return; }
  const tab = document.querySelector(`.tab[data-tab="${b.dataset.aller}"]`);
  if(tab) tab.click();
});

// ---------- Navigation par onglets ----------
document.querySelectorAll('.tab[data-tab]').forEach(tab => {
  tab.addEventListener('click', () => {
    document.querySelectorAll('.tab').forEach(t => t.classList.remove('active'));
    document.querySelectorAll('.tab-panel').forEach(p => p.classList.remove('active'));
    document.getElementById('reglesBtn').classList.remove('actif');
    document.getElementById('reglesBtnMobile').classList.remove('actif');
    document.getElementById('btnPlus').classList.remove('actif');
    tab.classList.add('active');
    majBadgePlus();
    window.scrollTo({ top: 0, behavior: 'instant' in window ? 'instant' : 'auto' });
    document.getElementById('panel-' + tab.dataset.tab).classList.add('active');
    if(tab.dataset.tab === 'territoire') sizeMapWrap(window.__mapAspectRatio);
    if(tab.dataset.tab === 'communaute'){ loadClassement(); loadJournal(); loadAmis(); }
    if(tab.dataset.tab === 'bourse') loadBourse();
    if(tab.dataset.tab === 'tirage'){ loadPackStatus(); loadObjectifs(); }
    if(tab.dataset.tab === 'defense'){ loadMenaces(); loadCombat(); renderIntensite('defense'); }
    if(tab.dataset.tab === 'combat') loadCombat();
    if(tab.dataset.tab === 'succes') loadSucces();
    if(tab.dataset.tab === 'echange') loadEchanges();
    if(tab.dataset.tab === 'regles') loadTauxTirage();
  });
});

// en revenant sur le site (autre appli, autre onglet), on relit jetons et solde
document.addEventListener('visibilitychange', () => {
  if(!document.hidden && packStatusCache) loadPackStatus();
});

// ---------- Objectifs ----------
let objectifsListe = [];
let objectifsTout = false;

async function loadObjectifs(){
  const { data, error } = await sb.rpc('objectifs');
  const bloc = document.getElementById('objectifs');
  if(error){
    if(bloc) bloc.hidden = true;
    return;
  }
  objectifsListe = data || [];
  renderObjectifs();
}

function carteObjectif(o){
  const pct = Math.min(100, Math.round(100 * o.avancement / o.cible));
  const recompense = o.recompense === 'points'
    ? `${Number(o.valeur).toLocaleString('fr-FR')} pts`
    : (o.valeur > 1 ? `${o.valeur} paquets` : '1 paquet');
  const etat = o.reclame
    ? '<span class="obj-fait">Récupéré</span>'
    : (o.reclamable ? `<button class="obj-btn" data-objectif="${echapperTexte(o.id)}">Récupérer</button>` : '');
  return `
    <div class="obj ${o.reclamable ? 'pret' : ''} ${o.reclame ? 'fait' : ''}">
      <div class="obj-texte">
        <b>${echapperTexte(o.titre)}</b>
        <span>${echapperTexte(o.detail)}</span>
        <span class="obj-barre"><i style="width:${pct}%"></i></span>
      </div>
      <div class="obj-droite">
        <span class="obj-chiffres">${Number(o.avancement).toLocaleString('fr-FR')} / ${Number(o.cible).toLocaleString('fr-FR')}</span>
        <span class="obj-gain gain-${o.recompense}">${recompense}</span>
        ${etat}
      </div>
    </div>`;
}

function renderObjectifs(){
  const bloc = document.getElementById('objectifs');
  if(!bloc) return;
  bloc.hidden = objectifsListe.length === 0;
  if(objectifsListe.length === 0) return;

  const jour = objectifsListe.filter(o => o.categorie === 'jour');
  let uniques = objectifsListe.filter(o => o.categorie !== 'jour');
  // par defaut : ceux a récupérer, puis les plus proches du but
  const enCours = uniques.filter(o => !o.reclame)
    .sort((a, b) => (b.reclamable - a.reclamable) || (b.avancement / b.cible - a.avancement / a.cible));
  const visibles = objectifsTout ? uniques : enCours.slice(0, 3);

  const prets = objectifsListe.filter(o => o.reclamable).length;
  const pastille = document.getElementById('objPret');
  if(pastille){
    pastille.hidden = prets === 0;
    pastille.textContent = prets > 1 ? `${prets} récompenses à récupérer` : '1 récompense à récupérer';
  }
  document.getElementById('objJour').innerHTML =
    `<h3>Aujourd'hui</h3>` + jour.map(carteObjectif).join('');
  document.getElementById('objUnique').innerHTML =
    `<h3>${objectifsTout ? 'Tous les défis' : 'Tes prochains défis'}</h3>` + visibles.map(carteObjectif).join('');
  const plus = document.getElementById('objPlus');
  if(plus){
    plus.hidden = objectifsTout || uniques.length <= visibles.length;
    plus.textContent = `Voir les ${uniques.length} défis`;
  }
}

document.getElementById('objectifs').addEventListener('click', async (e) => {
  if(e.target.closest('#objPlus')){
    objectifsTout = true;
    renderObjectifs();
    return;
  }
  const btn = e.target.closest('[data-objectif]');
  if(!btn) return;
  btn.disabled = true;
  try{
    const { data, error } = await sb.rpc('reclamer_objectif', { p_id: btn.dataset.objectif });
    if(error) throw error;
    const r = data && data[0];
    notifier({ type: 'succes', titre: 'Objectif atteint', texte: r ? r.message : 'Récompense récupérée' });
    await loadObjectifs();
    await loadPackStatus();
    if(r && r.recompense === 'paquet') verifierTiragesEnAttente();
  } catch(err){
    notifier({ type: 'erreur', titre: 'Impossible de récupérer', texte: messageLisible(err.message) });
    btn.disabled = false;
  }
});

// ---------- Succes : completion par departement ----------
// Une commune possedee au moins une fois reste acquise pour toujours : la progression
// ne se perd jamais, meme si la commune est revendue ou conquise par quelqu'un d'autre.
let succesListe = [];
let succesTout = false;

async function loadSucces(){
  const liste = document.getElementById('scListe');
  if(!liste) return;
  const { data, error } = await sb.rpc('succes');
  if(error){
    console.error(error);
    liste.innerHTML = '<p class="collection-empty">Impossible de charger tes succès pour le moment.</p>';
    return;
  }
  succesListe = (data || []).filter(d => Number(d.total) > 0);
  renderSucces();
}

function ligneSucces(d){
  const possedees = Number(d.possedees);
  const total = Number(d.total);
  const pct = total ? Math.min(100, Math.round(100 * possedees / total)) : 0;
  const fini = possedees >= total;
  const nom = DEPT_NAMES[d.departement] || d.departement;
  const etat = d.reclame
    ? '<span class="obj-fait">Récupéré</span>'
    : (fini ? `<button class="obj-btn" data-departement="${echapperTexte(d.departement)}">Récupérer</button>` : '');
  return `
    <div class="obj ${fini && !d.reclame ? 'pret' : ''} ${d.reclame ? 'fait' : ''}">
      <div class="obj-texte">
        <b>${echapperTexte(nom)} <span class="sc-num">(${echapperTexte(d.departement)})</span></b>
        <span class="obj-barre"><i style="width:${pct}%"></i></span>
      </div>
      <div class="obj-droite">
        <span class="obj-chiffres">${possedees.toLocaleString('fr-FR')} / ${total.toLocaleString('fr-FR')}</span>
        <span class="obj-gain gain-points">${Number(d.recompense).toLocaleString('fr-FR')} pts</span>
        ${etat}
      </div>
    </div>`;
}

function renderSucces(){
  const liste = document.getElementById('scListe');
  if(!liste) return;

  const vues = succesListe.reduce((n, d) => n + Number(d.possedees), 0);
  const total = succesListe.reduce((n, d) => n + Number(d.total), 0);
  const elTotal = document.getElementById('scTotal');
  if(elTotal) elTotal.textContent = `${vues.toLocaleString('fr-FR')} / ${total.toLocaleString('fr-FR')} communes découvertes`;

  const prets = succesListe.filter(d => Number(d.possedees) >= Number(d.total) && !d.reclame).length;
  const elPrets = document.getElementById('scPrets');
  if(elPrets){
    elPrets.hidden = prets === 0;
    elPrets.textContent = prets > 1 ? `${prets} récompenses à récupérer` : '1 récompense à récupérer';
  }

  if(succesListe.length === 0){
    liste.innerHTML = '<p class="collection-empty">Ouvre un paquet pour commencer ta collection.</p>';
    return;
  }

  // ceux a recuperer d'abord, puis les plus avances
  const tri = [...succesListe].sort((a, b) => {
    const pa = Number(a.possedees) >= Number(a.total) && !a.reclame;
    const pb = Number(b.possedees) >= Number(b.total) && !b.reclame;
    if(pa !== pb) return pb - pa;
    return (Number(b.possedees) / Number(b.total)) - (Number(a.possedees) / Number(a.total));
  });
  const visibles = succesTout ? tri : tri.slice(0, 8);
  liste.innerHTML = visibles.map(ligneSucces).join('');

  const plus = document.getElementById('scPlus');
  if(plus){
    plus.hidden = succesTout || tri.length <= visibles.length;
    plus.textContent = `Voir les ${tri.length} départements`;
  }
}

// le solde s'affiche a trois endroits : on les remet a jour ensemble
async function rafraichirSoldes(){
  const { data: userData } = await sb.auth.getUser();
  if(!userData || !userData.user) return;
  const row = await monEtat();
  if(!row) return;
  ['soldeValue', 'soldeValueCombat', 'soldeValueDefense'].forEach(id => {
    const el = document.getElementById(id);
    if(el) el.textContent = row.solde;
  });
}

document.getElementById('panel-succes').addEventListener('click', async (e) => {
  if(e.target.closest('#scPlus')){
    succesTout = true;
    renderSucces();
    return;
  }
  const btn = e.target.closest('[data-departement]');
  if(!btn) return;
  btn.disabled = true;
  try{
    const { data, error } = await sb.rpc('reclamer_departement', { p_departement: btn.dataset.departement });
    if(error) throw error;
    const r = data && data[0];
    notifier({ type: 'succes', titre: 'Département terminé', texte: r ? r.message : 'Récompense récupérée' });
    await loadSucces();
    await rafraichirSoldes();
  } catch(err){
    notifier({ type: 'erreur', titre: 'Impossible de récupérer', texte: messageLisible(err.message) });
    btn.disabled = false;
  }
});

// ---------- Echange de communes entre joueurs ----------
// Meme rarete des deux cotes, et une commission prelevee a chacun : sans cette
// friction, un joueur pourrait faire remonter les bonnes cartes de comptes secondaires.
const COMMISSION_ECHANGE = { commun: 1, peucommun: 4, rare: 20, legendaire: 200 };

let echangesEnCours = [];
let echangeTier = 'commun';
let echangeMien = null;    // code de ma commune
let echangeCible = null;   // { commune_code, nom, departement, pseudo }
let echangeCibles = [];
let echangeRecherche = '';
let echangeMinuteur = null;

async function loadEchanges(){
  const { data, error } = await sb.rpc('mes_echanges');
  if(error) console.error(error);
  echangesEnCours = error ? [] : (data || []);
  renderEchangePropositions();
  majBadgeEchange();
  renderEchangeMien();
  await chargerCiblesEchange();
  const { data: userData } = await sb.auth.getUser();
  if(userData && userData.user){
    const row = await monEtat();
    const el = document.getElementById('soldeValueEchange');
    if(el && row) el.textContent = row.solde;
  }
}

function majBadgeEchange(){
  const recues = echangesEnCours.filter(e => e.sens === 'recu').length;
  const badge = document.getElementById('echangeBadge');
  if(!badge) return;
  badge.hidden = recues === 0;
  badge.textContent = recues;
}

function ligneEchange(e){
  const recu = e.sens === 'recu';
  const reste = new Date(e.expire_le).getTime() - Date.now();
  const boutons = recu
    ? `<button class="obj-btn" data-accepter="${e.id}">Accepter</button>
       <button class="ech-refus" data-refuser="${e.id}">Refuser</button>`
    : `<button class="ech-refus" data-refuser="${e.id}">Annuler</button>`;
  return `
    <div class="ech-prop ${recu ? 'recu' : ''}">
      <div class="ech-prop-tete">
        <span>${recu
          ? `<b>${echapperTexte(e.autre_pseudo || 'Un joueur')}</b> te propose`
          : `Proposé à <b>${echapperTexte(e.autre_pseudo || 'un joueur')}</b>`}</span>
        <span class="ech-expire">${reste > 0 ? 'expire dans ' + formatDuree(reste) : 'expiré'}</span>
      </div>
      <div class="ech-prop-corps">
        <div class="ech-face recoit">
          <span>Tu reçois</span>
          <b>${echapperTexte(e.je_recois_nom)}</b>
          <small>(${echapperTexte(e.je_recois_dept)})</small>
        </div>
        <div class="ech-face donne">
          <span>Tu donnes</span>
          <b>${echapperTexte(e.je_donne_nom)}</b>
          <small>(${echapperTexte(e.je_donne_dept)})</small>
        </div>
      </div>
      <div class="ech-prop-pied">
        <span class="ech-commission">Commission ${e.commission} pts</span>
        <div class="ech-actions">${boutons}</div>
      </div>
    </div>`;
}

function renderEchangePropositions(){
  const bloc = document.getElementById('echPropositions');
  const liste = document.getElementById('echListe');
  if(!bloc || !liste) return;
  bloc.hidden = echangesEnCours.length === 0;
  liste.innerHTML = echangesEnCours.map(ligneEchange).join('');
}

// mes communes de la rarete choisie, hors boucliers et hors annonces en cours
function renderEchangeMien(){
  const zone = document.getElementById('echMien');
  if(!zone) return;
  const maintenant = Date.now();
  const champM = document.getElementById('echSearchMien');
  const rechercheM = sansAccents(champM ? champM.value.trim() : '');
  const miennes = [...collectionMap.values()]
    .filter(c => c.tier && c.tier.id === echangeTier)
    .filter(c => !(c.bouclierJusqua > maintenant))
    .filter(c => !myListings.has(c.code))
    .filter(c => correspondRecherche(c.nom, c.dept, rechercheM))
    .sort((a, b) => a.nom.localeCompare(b.nom, 'fr'));

  if(miennes.length === 0){
    zone.innerHTML = rechercheM
      ? '<p class="collection-empty">Aucune de tes communes ne correspond à cette recherche.</p>'
      : '<p class="collection-empty">Tu n\'as aucune commune échangeable de cette rareté.</p>';
    echangeMien = null;
    majResumeEchange();
    return;
  }
  if(echangeMien && !miennes.some(c => c.code === echangeMien)) echangeMien = null;

  zone.innerHTML = miennes.map(c => `
    <button class="ech-item ${echangeTier} ${echangeMien === c.code ? 'choisi' : ''}" data-mien="${echapperTexte(c.code)}">
      <b>${echapperTexte(c.nom)}</b>
      <small>${echapperTexte(DEPT_NAMES[c.dept] || '')} (${echapperTexte(c.dept)})</small>
    </button>`).join('');
  majResumeEchange();
}

async function chargerCiblesEchange(){
  const zone = document.getElementById('echCibles');
  if(!zone) return;
  zone.innerHTML = '<p class="collection-empty">Chargement…</p>';
  // le serveur ne connait que les numeros de departement : "charente" devient "16"
  const { data, error } = await sb.rpc('cibles_echange', {
    p_tier: echangeTier, p_recherche: codeDepartement(echangeRecherche) || echangeRecherche
  });
  if(error){
    console.error(error);
    zone.innerHTML = '<p class="collection-empty">Impossible de charger les communes des autres joueurs.</p>';
    return;
  }
  echangeCibles = data || [];
  renderEchangeCibles();
}

function renderEchangeCibles(){
  const zone = document.getElementById('echCibles');
  if(!zone) return;
  if(echangeCibles.length === 0){
    zone.innerHTML = '<p class="collection-empty">Aucune commune disponible de cette rareté.</p>';
    echangeCible = null;
    majResumeEchange();
    return;
  }
  if(echangeCible && !echangeCibles.some(c => c.commune_code === echangeCible.commune_code)) echangeCible = null;

  zone.innerHTML = echangeCibles.map(c => `
    <button class="ech-item ${echangeTier} ${echangeCible && echangeCible.commune_code === c.commune_code ? 'choisi' : ''}" data-cible="${echapperTexte(c.commune_code)}">
      <b>${echapperTexte(c.nom)}</b>
      <small>${echapperTexte(c.departement)} · ${echapperTexte(c.pseudo || 'un joueur')}</small>
    </button>`).join('');
  majResumeEchange();
}

function majResumeEchange(){
  const resume = document.getElementById('echResume');
  const bouton = document.getElementById('echEnvoyer');
  if(!resume || !bouton) return;
  const pret = echangeMien && echangeCible;
  resume.hidden = !pret;
  bouton.disabled = !pret;
  if(!pret){
    bouton.textContent = 'Choisis deux communes';
    return;
  }
  const mienne = collectionMap.get(echangeMien);
  const commission = COMMISSION_ECHANGE[echangeTier] || 1;
  resume.innerHTML = `
    <span><b>${echapperTexte(mienne ? mienne.nom : echangeMien)}</b> contre <b>${echapperTexte(echangeCible.nom)}</b></span>
    <span class="ech-commission">${commission} pts de commission pour chacun</span>`;
  bouton.textContent = 'Envoyer la proposition';
}

document.getElementById('echTiers').addEventListener('click', async (e) => {
  const b = e.target.closest('[data-tier]');
  if(!b) return;
  document.querySelectorAll('#echTiers .filter-pill').forEach(p => p.classList.remove('active'));
  b.classList.add('active');
  echangeTier = b.dataset.tier;
  echangeMien = null;
  echangeCible = null;
  renderEchangeMien();
  await chargerCiblesEchange();
});

document.getElementById('echSearch').addEventListener('input', (e) => {
  echangeRecherche = e.target.value.trim();
  clearTimeout(echangeMinuteur);
  echangeMinuteur = setTimeout(chargerCiblesEchange, 300);
});

document.getElementById('echMien').addEventListener('click', (e) => {
  const b = e.target.closest('[data-mien]');
  if(!b) return;
  echangeMien = echangeMien === b.dataset.mien ? null : b.dataset.mien;
  renderEchangeMien();
});

document.getElementById('echCibles').addEventListener('click', (e) => {
  const b = e.target.closest('[data-cible]');
  if(!b) return;
  const c = echangeCibles.find(x => x.commune_code === b.dataset.cible);
  echangeCible = (echangeCible && echangeCible.commune_code === b.dataset.cible) ? null : c;
  renderEchangeCibles();
});

document.getElementById('echEnvoyer').addEventListener('click', async (e) => {
  if(!echangeMien || !echangeCible) return;
  const btn = e.currentTarget;
  btn.disabled = true;
  try{
    const { data, error } = await sb.rpc('proposer_echange', {
      p_ma_commune: echangeMien, p_sa_commune: echangeCible.commune_code
    });
    if(error) throw error;
    const r = data && data[0];
    notifier({ type: 'succes', titre: 'Proposition envoyée', texte: r ? r.message : '' });
    echangeMien = null;
    echangeCible = null;
    await loadEchanges();
  } catch(err){
    notifier({ type: 'erreur', titre: 'Échange impossible', texte: messageLisible(err.message) });
    btn.disabled = false;
  }
});

document.getElementById('echListe').addEventListener('click', async (e) => {
  const accepter = e.target.closest('[data-accepter]');
  const refuser = e.target.closest('[data-refuser]');
  const btn = accepter || refuser;
  if(!btn) return;
  btn.disabled = true;
  try{
    if(accepter){
      const { data, error } = await sb.rpc('accepter_echange', { p_id: Number(accepter.dataset.accepter) });
      if(error) throw error;
      const r = data && data[0];
      notifier({ type: 'succes', titre: 'Échange conclu', texte: r ? r.message : '' });
      await loadMyCollection();
      await loadOthersPossessions();
    } else {
      const { data, error } = await sb.rpc('refuser_echange', { p_id: Number(refuser.dataset.refuser) });
      if(error) throw error;
      const r = data && data[0];
      notifier({ type: 'info', titre: r ? r.message : 'Proposition retirée' });
    }
    await loadEchanges();
  } catch(err){
    notifier({ type: 'erreur', titre: 'Action impossible', texte: messageLisible(err.message) });
    btn.disabled = false;
  }
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
  await loadObjectifs();
  await loadClassement();
  await loadJournal();
  await loadMyCollection();
  await loadOthersPossessions();
  await loadPackStatus();
  await loadMenaces();
  const actif = document.querySelector('.tab-panel.active');
  if(actif && actif.id === 'panel-bourse') await loadBourse();
  if(actif && (actif.id === 'panel-combat' || actif.id === 'panel-defense')) await loadCombat();
}

// ---------- Mot d'accueil, au tout premier lancement ----------
const CLE_ACCUEIL = 'tf-accueil-vu';

function accueilDejaVu(){
  try{ return localStorage.getItem(CLE_ACCUEIL) === '1'; } catch(e){ return false; }
}
function marquerAccueilVu(){
  try{ localStorage.setItem(CLE_ACCUEIL, '1'); } catch(e){}
}

// ---------- Guidage des nouveaux joueurs ----------
// Quatre bulles ancrees sur de vrais elements. Sur telephone, ou si la cible est
// masquee (onglet range dans le menu "Plus"), la bulle se pose en bas de l'ecran.
const CLE_GUIDE = 'terrafront-guide-vu';
const ETAPES_GUIDE = [
  {
    cible: '#packZone .paquet, #openFreeBtn',
    titre: 'Ouvre ton premier paquet',
    texte: 'Chaque paquet contient 5 vraies communes de France, à leur vraie place sur la carte. Tu en reçois un gratuit toutes les 20 minutes, et tu peux en garder 3 d\'avance.'
  },
  {
    cible: '.tab[data-tab="collection"]',
    titre: 'Ta collection',
    texte: 'Tes communes s\'accumulent ici. Une commune n\'appartient qu\'à un seul joueur à la fois : tant que tu la gardes, personne d\'autre au monde ne peut l\'avoir.'
  },
  {
    cible: '.tab[data-tab="territoire"]',
    titre: 'Ton territoire',
    texte: 'Tes communes se colorent sur la carte de France. Deux voisines se rejoignent en un seul territoire, et une frontière apparaît face aux autres joueurs.'
  },
  {
    cible: '.tab[data-tab="combat"]',
    titre: 'Attaque, et défends-toi',
    texte: 'Les communes rares et légendaires des autres joueurs se prennent par la force : trois victoires d\'affilée. Et les tiennes peuvent partir pareil, alors garde un œil sur l\'onglet Défense.'
  },
];

let guideIndex = -1;
let guideCibleActuelle = null;

function guideDejaVu(){
  try { return localStorage.getItem(CLE_GUIDE) === '1'; } catch(e){ return false; }
}
function marquerGuideVu(){
  try { localStorage.setItem(CLE_GUIDE, '1'); } catch(e){}
}

function trouverCibleGuide(selecteur){
  for(const sel of selecteur.split(',')){
    const el = document.querySelector(sel.trim());
    if(el && el.getBoundingClientRect().width > 0) return el;
  }
  return null;
}

function placerBulleGuide(cible){
  const bulle = document.getElementById('guideBulle');
  if(!bulle) return;
  bulle.classList.remove('en-bas');
  if(!cible || surTelephone()){
    bulle.classList.add('en-bas');
    bulle.style.left = '';
    bulle.style.top = '';
    return;
  }
  const r = cible.getBoundingClientRect();
  const b = bulle.getBoundingClientRect();
  let gauche = r.left + r.width / 2 - b.width / 2;
  let haut = r.bottom + 14;
  if(haut + b.height > window.innerHeight - 12) haut = Math.max(12, r.top - b.height - 14);
  gauche = Math.max(12, Math.min(gauche, window.innerWidth - b.width - 12));
  bulle.style.left = Math.round(gauche) + 'px';
  bulle.style.top = Math.round(haut) + 'px';
}

function afficherEtapeGuide(){
  const etape = ETAPES_GUIDE[guideIndex];
  if(!etape){ fermerGuide(); return; }
  const voile = document.getElementById('guideVoile');
  const bulle = document.getElementById('guideBulle');
  if(!voile || !bulle) return;

  if(guideCibleActuelle) guideCibleActuelle.classList.remove('guide-cible');
  const cible = trouverCibleGuide(etape.cible);
  guideCibleActuelle = cible;
  if(cible) cible.classList.add('guide-cible');

  voile.hidden = false;
  bulle.hidden = false;
  document.getElementById('guideCompteur').textContent = `Étape ${guideIndex + 1} sur ${ETAPES_GUIDE.length}`;
  document.getElementById('guideTitre').textContent = etape.titre;
  document.getElementById('guideTexte').textContent = etape.texte;
  document.getElementById('guideSuivant').textContent =
    guideIndex === ETAPES_GUIDE.length - 1 ? 'C\'est parti' : 'Suivant';
  placerBulleGuide(cible);
  document.getElementById('guideSuivant').focus();
}

function demarrerGuide(){
  guideIndex = 0;
  afficherEtapeGuide();
}

function fermerGuide(){
  const voile = document.getElementById('guideVoile');
  const bulle = document.getElementById('guideBulle');
  if(guideCibleActuelle){ guideCibleActuelle.classList.remove('guide-cible'); guideCibleActuelle = null; }
  if(voile) voile.hidden = true;
  if(bulle) bulle.hidden = true;
  guideIndex = -1;
  marquerGuideVu();
}

document.getElementById('guideSuivant').addEventListener('click', () => {
  guideIndex++;
  afficherEtapeGuide();
});
document.getElementById('guidePasser').addEventListener('click', fermerGuide);
document.getElementById('guideVoile').addEventListener('click', fermerGuide);
document.addEventListener('keydown', (e) => {
  if(e.key === 'Escape' && guideIndex >= 0) fermerGuide();
});
window.addEventListener('resize', () => {
  if(guideIndex >= 0) placerBulleGuide(guideCibleActuelle);
});
document.getElementById('revoirGuide').addEventListener('click', () => {
  const tab = document.querySelector('.tab[data-tab="tirage"]');
  if(tab) tab.click();
  setTimeout(demarrerGuide, 120);
});

function fermerAccueil(versTirage){
  const voile = document.getElementById('voileAccueil');
  if(!voile || voile.hidden) return;
  marquerAccueilVu();
  voile.classList.remove('ouvert');
  setTimeout(() => { voile.hidden = true; }, 200);
  if(versTirage){
    const tab = document.querySelector('.tab[data-tab="tirage"]');
    if(tab) tab.click();
  }
}

async function peutEtreAfficherAccueil(){
  // ?accueil=1 dans l'adresse force l'affichage, pour le tester ou le montrer
  const force = new URLSearchParams(location.search).get('accueil') === '1';
  if(!force){
    if(accueilDejaVu()) return;
    // un joueur qui a deja des cartes n'est pas un nouveau : on ne l'embete pas
    if(collectionMap.size > 0){ marquerAccueilVu(); return; }
  }
  const voile = document.getElementById('voileAccueil');
  if(!voile) return;
  voile.hidden = false;
  requestAnimationFrame(() => voile.classList.add('ouvert'));
  const go = document.getElementById('accueilGo');
  if(go) go.focus();
}

// "Ouvrir mon premier paquet" enchaine sur le guide ; "Passer" et "Voir les regles" non
document.getElementById('accueilGo').addEventListener('click', () => {
  fermerAccueil(true);
  if(!guideDejaVu()) setTimeout(demarrerGuide, 280);
});
document.getElementById('accueilPasser').addEventListener('click', () => {
  fermerAccueil(false);
  marquerGuideVu();
});
document.getElementById('accueilRegles').addEventListener('click', () => {
  fermerAccueil(false);
  marquerGuideVu();
  document.getElementById('reglesBtn').click();
});
document.addEventListener('keydown', (e) => {
  if(e.key === 'Escape') fermerAccueil(false);
});

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
