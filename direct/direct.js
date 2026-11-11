// TerraFront · la carte en direct (s2-90). Page publique, sans connexion.
// Scène fixe de 1920 × 1080 (OBS) mise à l'échelle de la fenêtre.
// Lit : direct_catalogue (gardé dans IndexedDB, partagé avec le jeu),
// direct_etat puis direct_depuis toutes les 15 s, direct_fil toutes les 10 s,
// direct_chiffres toutes les 60 s ; les joueurs en ligne par le canal de présence du jeu.
'use strict';
const SUPABASE_URL = 'https://yzcgroprydxhbwaufkdu.supabase.co';
const SUPABASE_ANON_KEY = 'sb_publishable_s829mEa2YUPWr9DOks2FTg_k9gpTQTA';
const sb = window.supabase.createClient(SUPABASE_URL, SUPABASE_ANON_KEY, { auth: { persistSession: false, autoRefreshToken: false } });
const CONTOURS_V = '4';
const DEPT_NAMES = {"01":"Ain","02":"Aisne","03":"Allier","04":"Alpes-de-Haute-Provence","05":"Hautes-Alpes","06":"Alpes-Maritimes","07":"Ardèche","08":"Ardennes","09":"Ariège","10":"Aube","11":"Aude","12":"Aveyron","13":"Bouches-du-Rhône","14":"Calvados","15":"Cantal","16":"Charente","17":"Charente-Maritime","18":"Cher","19":"Corrèze","21":"Côte-d'Or","22":"Côtes-d'Armor","23":"Creuse","24":"Dordogne","25":"Doubs","26":"Drôme","27":"Eure","28":"Eure-et-Loir","29":"Finistère","2A":"Corse-du-Sud","2B":"Haute-Corse","30":"Gard","31":"Haute-Garonne","32":"Gers","33":"Gironde","34":"Hérault","35":"Ille-et-Vilaine","36":"Indre","37":"Indre-et-Loire","38":"Isère","39":"Jura","40":"Landes","41":"Loir-et-Cher","42":"Loire","43":"Haute-Loire","44":"Loire-Atlantique","45":"Loiret","46":"Lot","47":"Lot-et-Garonne","48":"Lozère","49":"Maine-et-Loire","50":"Manche","51":"Marne","52":"Haute-Marne","53":"Mayenne","54":"Meurthe-et-Moselle","55":"Meuse","56":"Morbihan","57":"Moselle","58":"Nièvre","59":"Nord","60":"Oise","61":"Orne","62":"Pas-de-Calais","63":"Puy-de-Dôme","64":"Pyrénées-Atlantiques","65":"Hautes-Pyrénées","66":"Pyrénées-Orientales","67":"Bas-Rhin","68":"Haut-Rhin","69":"Rhône","70":"Haute-Saône","71":"Saône-et-Loire","72":"Sarthe","73":"Savoie","74":"Haute-Savoie","75":"Paris","76":"Seine-Maritime","77":"Seine-et-Marne","78":"Yvelines","79":"Deux-Sèvres","80":"Somme","81":"Tarn","82":"Tarn-et-Garonne","83":"Var","84":"Vaucluse","85":"Vendée","86":"Vienne","87":"Haute-Vienne","88":"Vosges","89":"Yonne","90":"Territoire de Belfort","91":"Essonne","92":"Hauts-de-Seine","93":"Seine-Saint-Denis","94":"Val-de-Marne","95":"Val-d'Oise","971":"Guadeloupe","972":"Martinique","973":"Guyane","974":"La Réunion","975":"Saint-Pierre-et-Miquelon","976":"Mayotte"};
const TIERS = ['commun', 'peucommun', 'rare', 'epique', 'legendaire'];
const MER = '#0A1628', LIBRE = '#1E3A60', SEUL = '#3A5378';
// patch414 : la Suisse (saison 3), même interrupteur que le jeu : SUISSE_OUVERTE le jour J, ?suisse=test pour essayer
const SUISSE_OUVERTE = false;
const SUISSE = SUISSE_OUVERTE || /[?&]suisse=test\b/.test(location.search);
const CANTONS = {"AG":"Argovie","AI":"Appenzell Rhodes-Intérieures","AR":"Appenzell Rhodes-Extérieures","BE":"Berne","BL":"Bâle-Campagne","BS":"Bâle-Ville","FR":"Fribourg","GE":"Genève","GL":"Glaris","GR":"Grisons","JU":"Jura","LU":"Lucerne","NE":"Neuchâtel","NW":"Nidwald","OW":"Obwald","SG":"Saint-Gall","SH":"Schaffhouse","SO":"Soleure","SZ":"Schwytz","TG":"Thurgovie","TI":"Tessin","UR":"Uri","VD":"Vaud","VS":"Valais","ZG":"Zoug","ZH":"Zurich"};
if(SUISSE) Object.assign(DEPT_NAMES, CANTONS);
const VUE = { lon0: -5.25, lon1: SUISSE ? 10.8 : 9.65, lat0: 41.3, lat1: 51.15 }, W = 1080, H = 1060;
const KX = Math.cos((VUE.lat0 + VUE.lat1) / 2 * Math.PI / 180);
const ECH = Math.min(W / ((VUE.lon1 - VUE.lon0) * KX), H / (VUE.lat1 - VUE.lat0));
const OX = (W - (VUE.lon1 - VUE.lon0) * KX * ECH) / 2, OY = (H - (VUE.lat1 - VUE.lat0) * ECH) / 2;
const px = (lon) => OX + (lon - VUE.lon0) * KX * ECH, py = (lat) => OY + (VUE.lat1 - lat) * ECH;

const D = { id: null, cat: null, chemins: new Map(), depBords: [], lacs: null, frontiere: null, clans: new Map(), joueurs: new Map(), proprio: new Map(),
  vus: new Set(), fil: [], premierFil: true, premierAppel: true, enCours: false };
const esc = (s) => String(s == null ? '' : s).replace(/[&<>"']/g, (c) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]));
const nb = (n) => Number(n || 0).toLocaleString('fr-FR');

// ---------- la scène à l'échelle de la fenêtre ----------
function ajuster(){
  const k = Math.min(window.innerWidth / 1920, window.innerHeight / 1080);
  const s = document.getElementById('scene');
  s.style.transform = 'translate(' + ((window.innerWidth - 1920 * k) / 2) + 'px,' + ((window.innerHeight - 1080 * k) / 2) + 'px) scale(' + k + ')';
}
window.addEventListener('resize', ajuster);

// ---------- le catalogue, gardé dans le navigateur (même coffre que le jeu) ----------
function coffre(mode, f){
  return new Promise((ok) => {
    try{
      const r = indexedDB.open('tf-carte', 1);
      r.onupgradeneeded = () => { try{ r.result.createObjectStore('kv'); }catch(e){} };
      r.onerror = () => ok(null);
      r.onsuccess = () => {
        let db = null;
        try{
          db = r.result;
          const tx = db.transaction('kv', mode), q = f(tx.objectStore('kv'));
          tx.oncomplete = () => { ok(q && q.result !== undefined ? q.result : null); db.close(); };
          tx.onerror = tx.onabort = () => { ok(null); try{ db.close(); }catch(e){} };
        }catch(e){ ok(null); try{ if(db) db.close(); }catch(e2){} }
      };
    }catch(e){ ok(null); }
  });
}
async function catalogue(version){
  if(D.cat && D.catVersion === version) return D.cat;
  let lignes = null, v = version;
  const garde = version ? await coffre('readonly', (st) => st.get('catalogue')) : null;
  if(garde && garde.version === version && Array.isArray(garde.c)) lignes = garde.c;
  if(!lignes){
    const { data, error } = await sb.rpc('direct_catalogue');
    if(error || !data || !Array.isArray(data.c)) return null;
    lignes = data.c; v = data.version;
    coffre('readwrite', (st) => st.put({ version: v, c: lignes }, 'catalogue'));
  }
  D.cat = new Map(lignes.map((r) => [String(r[0]), r])); D.catVersion = v;
  return D.cat;
}

// ---------- la carte : zoom et déplacement comme dans Territoire ----------
const canvas = document.getElementById('carte'), ctx = canvas.getContext('2d');
const DPR = Math.min(2, window.devicePixelRatio || 1);
canvas.width = W * DPR; canvas.height = H * DPR;
const BOITES = new Map();   // code -> [x0, y0, x1, y1] en coordonnées de base
const VU = { k: 1, x: 0, y: 0 };   // écran = base × k + (x, y)
const K_MAX = 40;
// mes communes : seulement si le jeu est ouvert et connecté dans ce navigateur
// (on lit l'identifiant du joueur ; aucun appel n'est fait en son nom)
// ou ?joueur=Pseudo dans l'adresse (pour OBS, qui n'a pas la session du jeu).
// Mes communes gardent simplement ma couleur de jeu (celle que les autres voient), sans mise en avant.
const PARAMS = new URLSearchParams(location.search);
let MON_ID = (() => {
  try{ const j = JSON.parse(localStorage.getItem('sb-yzcgroprydxhbwaufkdu-auth-token') || 'null'); return j && j.user && j.user.id || null; }catch(e){ return null; }
})();
const PSEUDO_VOULU = (PARAMS.get('joueur') || '').trim().toLowerCase();
// la couleur d'un joueur dans le jeu : celle qu'il a choisie, sinon la même couleur automatique que le jeu
const OPPONENT_COLORS = ['#E5484D','#8E7CF6','#2EC4B6','#F76B15','#E93D82','#3DD68C','#5EB1EF','#FF977D','#9EB1FF','#12A594','#D6409F','#C2A383'];
function couleurJeu(id){
  const jo = D.joueurs.get(id);
  if(jo && jo.couleur) return jo.couleur;
  let h = 0;
  for(let i = 0; i < id.length; i++) h = (h * 31 + id.charCodeAt(i)) >>> 0;
  return OPPONENT_COLORS[h % OPPONENT_COLORS.length];
}
function chemin(rings, code){
  const p = new Path2D();
  let x0 = Infinity, y0 = Infinity, x1 = -Infinity, y1 = -Infinity;
  for(const r of rings){
    if(!r || r.length < 3) continue;
    for(let i = 0; i < r.length; i++){
      const x = px(r[i][0]), y = py(r[i][1]);
      if(i === 0) p.moveTo(x, y); else p.lineTo(x, y);
      if(x < x0) x0 = x; if(x > x1) x1 = x; if(y < y0) y0 = y; if(y > y1) y1 = y;
    }
    p.closePath();
  }
  if(code) BOITES.set(code, [x0, y0, x1, y1]);
  return p;
}
async function chargerContours(){
  const deps = await fetch('../contours-departements.json', { cache: 'force-cache' }).then((r) => r.json());
  for(const [dep, rings] of Object.entries(deps)){ if(dep.length === 2) D.depBords.push(chemin(rings)); }
  const liste = Object.keys(deps).filter((d) => d.length === 2);
  if(SUISSE){   // patch414 : les cantons, les lacs et la frontière
    const lire = (f) => fetch('../data/' + f + '?v=1', { cache: 'force-cache' }).then((r) => r.ok ? r.json() : null).catch(() => null);
    const [cantons, lacs, frontiere] = await Promise.all([lire('contours-cantons.json'), lire('lacs-suisse.json'), lire('suisse-frontiere.json')]);
    for(const [c, rings] of Object.entries(cantons || {})){ D.depBords.push(chemin(rings)); liste.push(c); }
    if(lacs) D.lacs = chemin(lacs);
    if(frontiere) D.frontiere = chemin(frontiere);
  }
  for(let i = 0; i < liste.length; i += 12){
    await Promise.all(liste.slice(i, i + 12).map((dep) => fetch('../contours/' + dep + '.json?v=' + CONTOURS_V, { cache: 'force-cache' })
      .then((r) => r.ok ? r.json() : {}).then((j) => { for(const [code, rings] of Object.entries(j)) D.chemins.set(code, chemin(rings, code)); })
      .catch(() => {})));
  }
}
function couleurDe(code){
  const j = D.proprio.get(code);
  if(!j) return LIBRE;
  if(MON_ID && j === MON_ID) return couleurJeu(j);
  const jo = D.joueurs.get(j), cl = jo && jo.clan ? D.clans.get(jo.clan) : null;
  return cl ? cl.couleur : SEUL;
}
function poserVue(){ ctx.setTransform(DPR * VU.k, 0, 0, DPR * VU.k, DPR * VU.x, DPR * VU.y); }
function visible(code){
  const b = BOITES.get(code);
  if(!b) return true;
  const x0 = -VU.x / VU.k, y0 = -VU.y / VU.k, x1 = (W - VU.x) / VU.k, y1 = (H - VU.y) / VU.k;
  return b[2] >= x0 && b[0] <= x1 && b[3] >= y0 && b[1] <= y1;
}
function peindre(code){
  const p = D.chemins.get(code);
  if(!p || !visible(code)) return;
  const c = couleurDe(code);
  ctx.fillStyle = c; ctx.strokeStyle = c; ctx.lineWidth = 0.6 / VU.k;
  ctx.fill(p); ctx.stroke(p);
}
function bords(){
  if(D.lacs){ ctx.fillStyle = MER; ctx.fill(D.lacs); }   // patch414 : les lacs par-dessus les communes du bord (Léman)
  ctx.strokeStyle = 'rgba(169,188,212,.22)'; ctx.lineWidth = 0.8 / Math.sqrt(VU.k);
  for(const p of D.depBords) ctx.stroke(p);
  if(D.frontiere){ ctx.strokeStyle = 'rgba(169,188,212,.55)'; ctx.lineWidth = 1.6 / Math.sqrt(VU.k); ctx.stroke(D.frontiere); }
}
function toutPeindre(){
  ctx.setTransform(1, 0, 0, 1, 0, 0);
  ctx.fillStyle = MER; ctx.fillRect(0, 0, canvas.width, canvas.height);
  poserVue();
  for(const code of D.chemins.keys()) peindre(code);
  bords();
  placerEclairs();
}
// pendant un geste : l'image actuelle étirée (instantané), puis le vrai dessin au repos
let instantane = null, instVu = null, reposTimer = null;
function geste(){
  if(!instantane){
    instantane = document.createElement('canvas'); instantane.width = canvas.width; instantane.height = canvas.height;
    instantane.getContext('2d').drawImage(canvas, 0, 0); instVu = { ...VU };
  }
  const r = VU.k / instVu.k;
  ctx.setTransform(1, 0, 0, 1, 0, 0);
  ctx.fillStyle = MER; ctx.fillRect(0, 0, canvas.width, canvas.height);
  ctx.setTransform(r, 0, 0, r, DPR * (VU.x - instVu.x * r), DPR * (VU.y - instVu.y * r));
  ctx.drawImage(instantane, 0, 0);
  placerEclairs();
  clearTimeout(reposTimer);
  reposTimer = setTimeout(() => { instantane = null; toutPeindre(); }, 140);
}
function borner(){
  VU.k = Math.max(1, Math.min(K_MAX, VU.k));
  if(VU.k === 1){ VU.x = 0; VU.y = 0; return; }
  // au moins la moitié de l'écran reste sur la carte
  VU.x = Math.min(W * 0.5, Math.max(W * 0.5 - W * VU.k, VU.x));
  VU.y = Math.min(H * 0.5, Math.max(H * 0.5 - H * VU.k, VU.y));
}
function zoomer(f, cx, cy){
  const k = Math.max(1, Math.min(K_MAX, VU.k * f));
  const bx = (cx - VU.x) / VU.k, by = (cy - VU.y) / VU.k;
  VU.k = k; VU.x = cx - bx * k; VU.y = cy - by * k;
  borner(); geste();
}
function cadrer(x0, y0, x1, y1){
  const k = Math.max(1, Math.min(K_MAX, 0.85 * Math.min(W / Math.max(1, x1 - x0), H / Math.max(1, y1 - y0))));
  VU.k = k; VU.x = W / 2 - (x0 + x1) / 2 * k; VU.y = H / 2 - (y0 + y1) / 2 * k;
  borner(); geste();
}
// « Mon territoire » : le coin où j'ai le plus de communes (grille de 20 × 20, voisinage 3 × 3)
function monTerritoire(){
  const T = W / 20, cases = new Map(), pts = [];
  for(const [code, j] of D.proprio){
    if(j !== MON_ID || code.startsWith('97')) continue;
    const b = BOITES.get(code); if(!b) continue;
    const x = (b[0] + b[2]) / 2, y = (b[1] + b[3]) / 2, k = Math.floor(x / T) + ',' + Math.floor(y / T);
    pts.push([x, y, b]); cases.set(k, (cases.get(k) || 0) + 1);
  }
  if(!pts.length) return;
  let meilleur = null, n = -1;
  for(const k of cases.keys()){
    const [i, j] = k.split(',').map(Number); let t = 0;
    for(let di = -1; di <= 1; di++) for(let dj = -1; dj <= 1; dj++) t += cases.get((i + di) + ',' + (j + dj)) || 0;
    if(t > n){ n = t; meilleur = [i, j]; }
  }
  const [ci, cj] = meilleur, cx0 = (ci - 1) * T, cy0 = (cj - 1) * T, cx1 = (ci + 2) * T, cy1 = (cj + 2) * T;
  let x0 = Infinity, y0 = Infinity, x1 = -Infinity, y1 = -Infinity;
  for(const [x, y, b] of pts){
    if(x < cx0 || x > cx1 || y < cy0 || y > cy1) continue;
    x0 = Math.min(x0, b[0]); y0 = Math.min(y0, b[1]); x1 = Math.max(x1, b[2]); y1 = Math.max(y1, b[3]);
  }
  cadrer(x0 - 10, y0 - 10, x1 + 10, y1 + 10);
}
const pos = (e) => { const r = canvas.getBoundingClientRect(); return [(e.clientX - r.left) * W / r.width, (e.clientY - r.top) * H / r.height]; };
canvas.addEventListener('wheel', (e) => { e.preventDefault(); const [x, y] = pos(e); zoomer(Math.pow(1.0018, -e.deltaY), x, y); }, { passive: false });
canvas.addEventListener('dblclick', (e) => { const [x, y] = pos(e); zoomer(2, x, y); });
let glisse = null;
canvas.addEventListener('pointerdown', (e) => { glisse = { id: e.pointerId, p: pos(e), x: VU.x, y: VU.y }; canvas.setPointerCapture(e.pointerId); canvas.classList.add('glisse'); });
canvas.addEventListener('pointermove', (e) => {
  if(glisse && glisse.id === e.pointerId){
    const [x, y] = pos(e); VU.x = glisse.x + x - glisse.p[0]; VU.y = glisse.y + y - glisse.p[1]; borner(); geste(); cacherBulle(); return;
  }
  survol(e);
});
const fin = () => { glisse = null; canvas.classList.remove('glisse'); };
canvas.addEventListener('pointerup', fin); canvas.addEventListener('pointercancel', fin);
canvas.addEventListener('pointerleave', cacherBulle);
document.getElementById('zPlus').addEventListener('click', () => zoomer(1.6, W / 2, H / 2));
document.getElementById('zMoins').addEventListener('click', () => zoomer(1 / 1.6, W / 2, H / 2));
document.getElementById('zFrance').addEventListener('click', () => { VU.k = 1; VU.x = 0; VU.y = 0; geste(); });
const bMoi = document.getElementById('zMoi');
bMoi.addEventListener('click', monTerritoire);
let moiPret = false;
function activerMoi(){
  if(PSEUDO_VOULU && !moiPret){
    for(const [id, j] of D.joueurs) if(String(j.pseudo || '').toLowerCase() === PSEUDO_VOULU){ MON_ID = id; break; }
  }
  if(!MON_ID || moiPret) return;
  moiPret = true;
  bMoi.hidden = false;
}

// la commune sous la souris
const bulle = document.getElementById('bulle');
let survolT = 0;
function cacherBulle(){ bulle.hidden = true; }
function survol(e){
  const t = performance.now(); if(t - survolT < 40) return; survolT = t;
  const [sx, sy] = pos(e), bx = (sx - VU.x) / VU.k, by = (sy - VU.y) / VU.k;
  let trouve = null;
  ctx.setTransform(1, 0, 0, 1, 0, 0);
  for(const [code, b] of BOITES){
    if(bx < b[0] || bx > b[2] || by < b[1] || by > b[3]) continue;
    if(ctx.isPointInPath(D.chemins.get(code), bx, by)){ trouve = code; break; }
  }
  poserVue();
  if(!trouve){ cacherBulle(); return; }
  const r = D.cat && D.cat.get(trouve), j = D.proprio.get(trouve), jo = j ? D.joueurs.get(j) : null, cl = jo && jo.clan ? D.clans.get(jo.clan) : null;
  bulle.innerHTML = '<b>' + esc(r ? r[1] : trouve) + '</b> <span class="dep">' + esc(r ? r[2] : '') + '</span><small>'
    + (j ? (cl ? '<i style="background:' + esc(cl.couleur) + '"></i>[' + esc(cl.tag) + '] ' : '') + esc(jo ? jo.pseudo : 'un joueur') + (j === MON_ID ? ' (toi)' : '') : 'commune libre') + '</small>';
  bulle.hidden = false;
  bulle.style.left = (sx + 24) + 'px'; bulle.style.top = (sy + 24) + 'px';
}

// ---------- l'état et les changements ----------
function lireJoueurs(liste){ for(const j of liste || []) D.joueurs.set(j[0], { pseudo: j[1], clan: j[2] || null, couleur: j[3] || null }); }
async function etatComplet(){
  const { data, error } = await sb.rpc('direct_etat');
  if(error) return false;
  if(!data){ document.getElementById('pause').hidden = false; return false; }
  document.getElementById('pause').hidden = true;
  if(!(await catalogue(data.catalogue))) return false;
  D.clans = new Map((data.clans || []).map((c) => [c[0], { tag: c[1], nom: c[2], couleur: c[3] }]));
  D.joueurs = new Map(); lireJoueurs(data.joueurs);
  const ids = (data.joueurs || []).map((j) => j[0]);
  D.proprio = new Map();
  for(const r of data.p || []) D.proprio.set(String(r[0]), ids[r[1]]);
  D.id = Number(data.id) || 0;
  activerMoi();
  toutPeindre();
  return true;
}
async function changements(){
  if(D.enCours) return;
  D.enCours = true;
  try{
    if(D.id == null){ await etatComplet(); return; }
    const { data, error } = await sb.rpc('direct_depuis', { p_id: D.id });
    if(error) return;
    if(!data){ document.getElementById('pause').hidden = false; return; }
    if(data.complet){ D.id = null; await etatComplet(); return; }
    lireJoueurs(data.joueurs);
    const fin = new Map();
    for(const x of data.ch || []) fin.set(String(x[1]), x[2] || null);
    let peint = false;
    for(const [code, j] of fin){
      if((D.proprio.get(code) || null) === j) continue;
      if(j) D.proprio.set(code, j); else D.proprio.delete(code);
      peint = true;
    }
    if(peint && !instantane){ poserVue(); for(const [code] of fin) peindre(code); bords(); }
    D.id = Math.max(D.id, Number(data.id) || 0);
  }catch(e){ console.error(e); }
  finally{ D.enCours = false; }
}
// les couleurs des clans changent (un joueur rejoint ou quitte un clan) : relecture complète toutes les 10 min
setInterval(() => { D.id = null; changements(); }, 600000);

// ---------- le fil du Front ----------
const depNom = (d) => DEPT_NAMES[d] || d || '';
const tagHtml = (t) => { if(!t) return ''; const c = [...D.clans.values()].find((x) => x.tag === t); return ' <span class="tag" style="color:' + esc(c ? c.couleur : '#A9BCD4') + '">[' + esc(t) + ']</span>'; };
const depHtml = (d) => d ? '<span class="dep">' + esc(d) + '</span>' : '';
function texteEv(e){
  const [, type, , acteur, tag, cible, , nom, , dep] = e;
  const qui = '<b>' + esc(acteur || 'Un joueur') + '</b>' + tagHtml(tag), ou = '<b>' + esc(nom || '') + '</b>' + depHtml(dep);
  if(type === 'conquete') return ['⚔️', qui + ' prend ' + ou + (cible ? ' à ' + esc(cible) : '')];
  if(type === 'defense') return ['🛡️', qui + ' repousse ' + esc(cible || 'un attaquant') + ' à ' + ou];
  if(type === 'fonderie') return ['🏭', qui + ' construit une Fonderie à ' + ou];
  if(type === 'forteresse') return ['🏰', qui + ' élève une Forteresse à ' + ou];
  if(type === 'bombe_prep') return ['💣', 'Une bombe se prépare : <b>' + esc(depNom(dep)) + '</b>' + depHtml(dep)];
  if(type === 'bombe') return ['💥', qui + ' lâche une bombe sur ' + ou];
  return ['•', qui];
}
function ilYa(t){
  const s = Math.max(0, Math.round(Date.now() / 1000 - t));
  if(s < 60) return s + ' s';
  if(s < 3600) return Math.floor(s / 60) + ' min';
  return Math.floor(s / 3600) + ' h';
}
function rendreFil(){
  const el = document.getElementById('fil');
  const L = D.fil.slice(0, 7);
  if(!L.length){ el.innerHTML = '<p class="vide">Le Front est calme pour l’instant.</p>'; return; }
  const maintenant = Date.now() / 1000;
  el.innerHTML = L.map((e) => {
    const [ico, txt] = texteEv(e);
    return '<div class="ev' + (maintenant - e[2] < 60 ? ' neuf' : '') + '"><span class="ico">' + ico + '</span><span class="txt">' + txt + '</span><time>' + ilYa(e[2]) + '</time></div>';
  }).join('');
}
function eclair(e){
  const [, type, t, acteur, tag, cible, code, nom] = e;
  if(type !== 'conquete' && type !== 'defense') return;
  const r = D.cat && D.cat.get(String(code));
  if(!r || r[4] == null) return;
  const bx = px(r[5]), by = py(r[4]), def = type === 'defense' ? ' def' : '';
  const box = document.getElementById('eclairs');
  const a = document.createElement('div'); a.className = 'anneau' + def;
  const p = document.createElement('div'); p.className = 'point' + def;
  const g = document.createElement('div'); g.className = 'etiquette' + def;
  for(const el of [a, p, g]){ el.dataset.bx = bx; el.dataset.by = by; }
  g.innerHTML = type === 'conquete'
    ? (tag ? '<b>[' + esc(tag) + '] ' : '<b>') + esc(acteur || 'Un joueur') + '</b> prend <b>' + esc(nom) + '</b>' + (cible ? '<small>à ' + esc(cible) + '</small>' : '')
    : '🛡 <b>' + esc(nom) + '</b> tient bon<small>' + (tag ? '[' + esc(tag) + '] ' : '') + esc(acteur || '') + ' repousse ' + esc(cible || '') + '</small>';
  box.append(a, p, g);
  placerEclairs();
  // au plus 3 étiquettes à la fois
  const tags = box.querySelectorAll('.etiquette');
  if(tags.length > 3) tags[0].remove();
  setTimeout(() => { a.remove(); p.remove(); g.remove(); }, 61000);
}
function placerEclairs(){
  for(const el of document.querySelectorAll('#eclairs [data-bx]')){
    const x = Number(el.dataset.bx) * VU.k + VU.x, y = Number(el.dataset.by) * VU.k + VU.y;
    el.style.left = x + 'px'; el.style.top = y + 'px';
    el.style.visibility = (x < -40 || x > W + 40 || y < -40 || y > H + 40) ? 'hidden' : '';
    if(el.classList.contains('etiquette')) el.classList.toggle('gauche', x > W * 0.62);
  }
}
async function fil(){
  const { data, error } = await sb.rpc('direct_fil');
  if(error || !Array.isArray(data)) return;
  const nouveaux = data.filter((e) => !D.vus.has(e[0]));
  for(const e of data) D.vus.add(e[0]);
  D.fil = data;
  // au premier passage : seulement ce qui date de moins d'une minute clignote
  const aMontrer = D.premierFil ? nouveaux.filter((e) => Date.now() / 1000 - e[2] < 60) : nouveaux;
  D.premierFil = false;
  for(const e of aMontrer.slice(0, 5).reverse()) eclair(e);
  rendreFil();
  if(nouveaux.some((e) => e[1] === 'conquete') && !D.premierAppel){ setTimeout(changements, 1500); chiffres(); }
  D.premierAppel = false;
}

// ---------- les chiffres et les clans ----------
async function chiffres(){
  const { data, error } = await sb.rpc('direct_chiffres');
  if(error || !data) return;
  document.getElementById('cConquetes').textContent = nb(data.conquetes_jour);
  document.getElementById('cLibres').textContent = nb(data.libres);
  const L = (data.clans || []).slice(0, 5);
  document.getElementById('clans').innerHTML = '<div class="cl ent"><span></span><span>Clan</span><span class="v">Communes</span><span class="v">Aujourd’hui</span></div>'
    + L.map((c, i) => '<div class="cl"><span class="r">' + (i + 1) + '</span><span class="n"><i style="background:' + esc(c[3]) + '"></i>[' + esc(c[1]) + '] ' + esc(c[2]) + '</span>'
      + '<span class="v">' + nb(c[4]) + '</span><span class="v">+' + nb(c[5]) + ' <small>⚔</small></span></div>').join('');
}
function enLigne(){
  try{
    const canal = sb.channel('en-ligne');
    const maj = () => { document.getElementById('cEnLigne').textContent = nb(Object.keys(canal.presenceState()).length); };
    canal.on('presence', { event: 'sync' }, maj).subscribe();
  }catch(e){}
}
function heure(){
  document.getElementById('heure').textContent = new Date().toLocaleTimeString('fr-FR', { hour: '2-digit', minute: '2-digit', timeZone: 'Europe/Paris' });
}

// ---------- départ ----------
(async function demarrer(){
  ajuster(); heure();
  if(SUISSE){   // patch414
    const z = document.getElementById('zFrance'); if(z) z.textContent = 'Tout';
    const p = document.querySelector('.pied span'); if(p) p.textContent = 'Les 37 000 communes de France et de Suisse, à prendre. Gratuit.';
  }
  setInterval(heure, 10000);
  setInterval(rendreFil, 5000);
  chiffres(); setInterval(chiffres, 60000);
  enLigne();
  try{ await chargerContours(); }catch(e){ console.error(e); }
  await changements();
  document.getElementById('chargement').hidden = true;
  await fil();
  setInterval(fil, 10000);
  setInterval(changements, 15000);
})();
