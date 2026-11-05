// TerraFront · la régie du live (s2-103). On cherche une commune, on la touche :
// direct_montrer() la met à l'écran de la scène portrait (tiktok.html) pendant 15 s.
// Session du jeu partagée (même navigateur, même stockage) ; réservé à la modération.
'use strict';
const SUPABASE_URL = 'https://yzcgroprydxhbwaufkdu.supabase.co';
const SUPABASE_ANON_KEY = 'sb_publishable_s829mEa2YUPWr9DOks2FTg_k9gpTQTA';
const sb = window.supabase.createClient(SUPABASE_URL, SUPABASE_ANON_KEY);
const $ = (id) => document.getElementById(id);
const esc = (s) => String(s == null ? '' : s).replace(/[&<>"']/g, (c) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]));
const nb = (n) => Number(n || 0).toLocaleString('fr-FR');
// « Saint-Étienne », « st etienne », « saint etienne » : même clé
const cle = (s) => String(s || '').normalize('NFD').replace(/[̀-ͯ]/g, '').toLowerCase()
  .replace(/[’']/g, ' ').replace(/[^a-z0-9]+/g, ' ').replace(/\bst\b/g, 'saint').replace(/\bste\b/g, 'sainte').trim();

const R = { cat: [], parCode: new Map(), proprio: new Map(), joueurs: new Map(), clans: new Map(), deja: [] };
let ecran = { code: null, fin: 0, total: 15000, n: null };

function lien(etat, txt){ $('lien').className = 'lien ' + etat; $('lienTxt').textContent = txt; }
function message(html){ $('main').hidden = true; $('msg').innerHTML = html; $('msg').hidden = false; }
function erreur(t){ $('erreur').textContent = t || ''; $('erreur').hidden = !t; }

// ---------- le catalogue, gardé dans le navigateur (même coffre que le jeu et la carte en direct) ----------
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
  let lignes = null, v = version;
  const garde = version ? await coffre('readonly', (st) => st.get('catalogue')) : null;
  if(garde && garde.version === version && Array.isArray(garde.c)) lignes = garde.c;
  if(!lignes){
    const { data, error } = await sb.rpc('direct_catalogue');
    if(error || !data || !Array.isArray(data.c)) return false;
    lignes = data.c; v = data.version;
    coffre('readwrite', (st) => st.put({ version: v, c: lignes }, 'catalogue'));
  }
  // [code, nom, dép., habitants, lat, lon, …] ; triées des plus peuplées aux moins peuplées
  R.cat = lignes.map((r) => ({ code: String(r[0]), nom: r[1], dep: r[2], hab: Number(r[3]) || 0, cle: cle(r[1]) }))
    .sort((a, b) => b.hab - a.hab);
  R.parCode = new Map(R.cat.map((c) => [c.code, c]));
  return true;
}
async function etat(){
  const { data, error } = await sb.rpc('direct_etat');
  if(error || !data) return false;
  if(!R.cat.length && !(await catalogue(data.catalogue))) return false;
  R.clans = new Map((data.clans || []).map((c) => [c[0], { tag: c[1], couleur: c[3] }]));
  R.joueurs = new Map((data.joueurs || []).map((j) => [j[0], { pseudo: j[1], clan: j[2] || null }]));
  const ids = (data.joueurs || []).map((j) => j[0]);
  R.proprio = new Map((data.p || []).map((r) => [String(r[0]), ids[r[1]]]));
  return true;
}

// ---------- la recherche ----------
function tenant(code){
  const j = R.proprio.get(code);
  if(!j) return '<div class="etat libre">Libre</div>';
  const jo = R.joueurs.get(j), cl = jo && jo.clan ? R.clans.get(jo.clan) : null;
  return '<div class="etat"><i style="background:' + esc(cl ? cl.couleur : '#3A5378') + '"></i>' + (cl ? '[' + esc(cl.tag) + '] ' : '') + esc(jo ? jo.pseudo : 'un joueur') + '</div>';
}
function surligner(nom, q){
  // la partie tapée en or : le plus court début du nom qui donne la même clé
  if(!q || !cle(nom).startsWith(q)) return esc(nom);
  let i = 1;
  while(i < nom.length && cle(nom.slice(0, i)).length < q.length) i++;
  return '<u>' + esc(nom.slice(0, i)) + '</u>' + esc(nom.slice(i));
}
function chercher(){
  const brut = $('q').value;
  // un numéro de département au bout : « saint martin 17 »
  let q = cle(brut), dep = null;
  const m = q.match(/^(.+) (\d[\dab]\d?)$/);
  if(m){ q = m[1]; dep = m[2].toUpperCase(); }
  $('vider').hidden = !brut;
  const box = $('res');
  if(q.length < 2){ box.hidden = true; box.innerHTML = ''; return; }
  const debut = [], dedans = [];
  for(const c of R.cat){
    if(dep && c.dep !== dep) continue;
    if(c.cle.startsWith(q)){ debut.push(c); if(debut.length >= 30) break; }
    else if(dedans.length < 30 && c.cle.includes(' ' + q)) dedans.push(c);
  }
  const liste = debut.concat(dedans).slice(0, 30);
  box.innerHTML = liste.length
    ? liste.map((c) => '<button type="button" class="r" data-code="' + esc(c.code) + '"><div class="nom"><b>' + surligner(c.nom, q) + '</b><small>' + nb(c.hab) + ' hab.</small></div>'
        + '<span class="dep">' + esc(c.dep) + '</span>' + tenant(c.code) + '</button>').join('')
    : '<div class="vide">Aucune commune ne commence par « ' + esc(brut) + ' ».</div>';
  box.hidden = false;
}

// ---------- mettre à l'écran ----------
let occupe = false;
async function montrer(code, ajouter){
  if(occupe) return;
  occupe = true; erreur('');
  try{
    const args = { p_code: code, p_demandeur: ajouter ? null : ($('qui').value.trim() || null), p_duree: 15, p_ajouter: !!ajouter };
    const { data, error } = await sb.rpc('direct_montrer', args);
    if(error){ erreur(error.message || 'La scène n’a pas reçu la commune.'); return; }
    lu(data, true);
    if(code && !ajouter){
      $('q').value = ''; $('qui').value = ''; chercher();
      R.deja = [code].concat(R.deja.filter((c) => c !== code)).slice(0, 8);
      rendreDeja();
      window.scrollTo({ top: 0, behavior: 'smooth' });
    }
  }catch(e){ erreur('Pas de réseau ?'); }
  finally{ occupe = false; }
}
function rendreDeja(){
  $('dejaBloc').hidden = !R.deja.length;
  $('deja').innerHTML = R.deja.map((c) => { const x = R.parCode.get(c); return '<button type="button" data-code="' + esc(c) + '">' + esc(x ? x.nom : c) + '</button>'; }).join('');
}

// ---------- ce qui est à l'écran ----------
function lu(d, maintenant){
  if(!d) return;
  const reste = Number(d.reste) || 0;
  if(!d.code || reste <= 0){ ecran = { code: null, fin: 0, total: 15000, n: d.n }; rendreEcran(); return; }
  const fin = Date.now() + reste * 1000;
  if(d.n !== ecran.n || d.code !== ecran.code) ecran = { code: String(d.code), demandeur: d.demandeur, fin, total: reste * 1000, n: d.n };
  else if(maintenant || fin > ecran.fin + 1500){ ecran.total += Math.max(0, fin - ecran.fin); ecran.fin = fin; }
  rendreEcran();
}
function rendreEcran(){
  const on = !!ecran.code && ecran.fin > Date.now();
  $('ecran').hidden = !on;
  if(!on) return;
  const c = R.parCode.get(ecran.code);
  $('ecranNom').innerHTML = esc(c ? c.nom : ecran.code) + '<small>' + esc(c ? c.dep : '') + (ecran.demandeur ? ' · demandée par ' + esc(ecran.demandeur) : '') + '</small>';
}
function tic(){
  const reste = Math.max(0, ecran.fin - Date.now());
  if(ecran.code && reste <= 0){ ecran.code = null; rendreEcran(); }
  if(!ecran.code) return;
  $('reste').textContent = Math.ceil(reste / 1000) + ' s';
  $('ecranBarre').style.width = (100 * reste / ecran.total).toFixed(1) + '%';
}
async function suivre(){
  try{
    const { data, error } = await sb.rpc('direct_affiche');
    if(error){ lien('ko', 'Hors ligne'); return; }
    if(!data){ lien('ko', 'Direct en pause'); return; }
    lien('ok', 'Direct ouvert');
    lu(data, false);
  }catch(e){ lien('ko', 'Hors ligne'); }
}

// ---------- départ ----------
(async function demarrer(){
  const { data: s } = await sb.auth.getSession();
  if(!s || !s.session){
    lien('ko', 'Non connecté');
    message('Connecte-toi d’abord au jeu <b>dans ce navigateur</b> : <a href="../">ouvrir terrafront.fr</a>, puis reviens sur cette page.'
      + '<br><br><small>Sur iPhone, l’appli posée sur l’écran d’accueil ne partage pas sa connexion avec Safari.</small>');
    return;
  }
  const { data: ok, error } = await sb.rpc('direct_regie_ok');
  if(error || ok !== true){ lien('ko', 'Accès refusé'); message('Cette page est réservée à la régie du direct.'); return; }
  lien('', 'Chargement des communes…');
  if(!(await etat())){ lien('ko', 'Hors ligne'); message('Impossible de charger les communes. Le direct est peut-être en pause.'); return; }
  $('msg').hidden = true; $('main').hidden = false;
  await suivre();
  $('q').addEventListener('input', chercher);
  $('vider').addEventListener('click', () => { $('q').value = ''; chercher(); $('q').focus(); });
  $('res').addEventListener('click', (e) => { const b = e.target.closest('[data-code]'); if(b) montrer(b.dataset.code, false); });
  $('deja').addEventListener('click', (e) => { const b = e.target.closest('[data-code]'); if(b) montrer(b.dataset.code, false); });
  $('plus').addEventListener('click', () => { if(ecran.code) montrer(ecran.code, true); });
  $('france').addEventListener('click', () => montrer(null, false));
  setInterval(tic, 250);
  setInterval(suivre, 3000);
  setInterval(etat, 60000);   // qui tient quoi, pour la liste
  $('q').focus();
})();
