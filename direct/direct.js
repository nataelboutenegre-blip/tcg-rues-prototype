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
const VUE = { lon0: -5.25, lon1: 9.65, lat0: 41.3, lat1: 51.15 }, W = 1080, H = 1060;
const KX = Math.cos((VUE.lat0 + VUE.lat1) / 2 * Math.PI / 180);
const ECH = Math.min(W / ((VUE.lon1 - VUE.lon0) * KX), H / (VUE.lat1 - VUE.lat0));
const OX = (W - (VUE.lon1 - VUE.lon0) * KX * ECH) / 2, OY = (H - (VUE.lat1 - VUE.lat0) * ECH) / 2;
const px = (lon) => OX + (lon - VUE.lon0) * KX * ECH, py = (lat) => OY + (VUE.lat1 - lat) * ECH;

const D = { id: null, cat: null, chemins: new Map(), depBords: [], clans: new Map(), joueurs: new Map(), proprio: new Map(),
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

// ---------- la carte ----------
const canvas = document.getElementById('carte'), ctx = canvas.getContext('2d');
const DPR = Math.min(2, window.devicePixelRatio || 1);
canvas.width = W * DPR; canvas.height = H * DPR; ctx.scale(DPR, DPR);
function chemin(rings){
  const p = new Path2D();
  for(const r of rings){
    if(!r || r.length < 3) continue;
    p.moveTo(px(r[0][0]), py(r[0][1]));
    for(let i = 1; i < r.length; i++) p.lineTo(px(r[i][0]), py(r[i][1]));
    p.closePath();
  }
  return p;
}
async function chargerContours(){
  const deps = await fetch('../contours-departements.json', { cache: 'force-cache' }).then((r) => r.json());
  for(const [dep, rings] of Object.entries(deps)){ if(dep.length === 2) D.depBords.push(chemin(rings)); }
  const liste = Object.keys(deps).filter((d) => d.length === 2);
  for(let i = 0; i < liste.length; i += 12){
    await Promise.all(liste.slice(i, i + 12).map((dep) => fetch('../contours/' + dep + '.json?v=' + CONTOURS_V, { cache: 'force-cache' })
      .then((r) => r.ok ? r.json() : {}).then((j) => { for(const [code, rings] of Object.entries(j)) D.chemins.set(code, chemin(rings)); })
      .catch(() => {})));
  }
}
function couleurDe(code){
  const j = D.proprio.get(code);
  if(!j) return LIBRE;
  const jo = D.joueurs.get(j), cl = jo && jo.clan ? D.clans.get(jo.clan) : null;
  return cl ? cl.couleur : SEUL;
}
function peindre(code){
  const p = D.chemins.get(code);
  if(!p) return;
  const c = couleurDe(code);
  ctx.fillStyle = c; ctx.strokeStyle = c; ctx.lineWidth = 0.6;
  ctx.fill(p); ctx.stroke(p);
}
function bords(){
  ctx.strokeStyle = 'rgba(169,188,212,.22)'; ctx.lineWidth = 0.8;
  for(const p of D.depBords) ctx.stroke(p);
}
function toutPeindre(){
  ctx.fillStyle = MER; ctx.fillRect(0, 0, W, H);
  for(const code of D.chemins.keys()) peindre(code);
  bords();
}

// ---------- l'état et les changements ----------
function lireJoueurs(liste){ for(const j of liste || []) D.joueurs.set(j[0], { pseudo: j[1], clan: j[2] || null }); }
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
      peindre(code); peint = true;
    }
    if(peint) bords();
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
  const x = px(r[5]), y = py(r[4]), def = type === 'defense' ? ' def' : '';
  const box = document.getElementById('eclairs');
  const a = document.createElement('div'); a.className = 'anneau' + def; a.style.left = x + 'px'; a.style.top = y + 'px';
  const p = document.createElement('div'); p.className = 'point' + def; p.style.left = x + 'px'; p.style.top = y + 'px';
  const g = document.createElement('div'); g.className = 'etiquette' + def + (x > W * 0.62 ? ' gauche' : ''); g.style.left = x + 'px'; g.style.top = y + 'px';
  g.innerHTML = type === 'conquete'
    ? (tag ? '<b>[' + esc(tag) + '] ' : '<b>') + esc(acteur || 'Un joueur') + '</b> prend <b>' + esc(nom) + '</b>' + (cible ? '<small>à ' + esc(cible) + '</small>' : '')
    : '🛡 <b>' + esc(nom) + '</b> tient bon<small>' + (tag ? '[' + esc(tag) + '] ' : '') + esc(acteur || '') + ' repousse ' + esc(cible || '') + '</small>';
  box.append(a, p, g);
  // au plus 3 étiquettes à la fois
  const tags = box.querySelectorAll('.etiquette');
  if(tags.length > 3) tags[0].remove();
  setTimeout(() => { a.remove(); p.remove(); g.remove(); }, 61000);
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
