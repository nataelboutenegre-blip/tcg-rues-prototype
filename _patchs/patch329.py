# patch329 (3/11/2026) : l'état compact de la carte (s2-89), saison 3 étape 1
# loadOthersPossessions ne lit plus ~25 000 lignes avec la fiche de chaque
# commune : une lecture compacte (carte_etat), la fiche vient du catalogue des
# communes (carte_catalogue, gardé dans le navigateur par IndexedDB tant que sa
# version ne change pas), puis seulement ce qui a changé (carte_depuis) :
# toutes les 60 s quand le jeu est visible, au retour sur le jeu, et à chaque
# appel de loadOthersPossessions (après une conquête, un échange…).
# Une commune de MA collection qui change de main relance loadMyCollection.
# Si s2-89 n'est pas passé (fonction absente), l'ancien chargement reste.
# Rien ne change à l'écran, sauf que la carte se met à jour toute seule.
import pathlib

F = pathlib.Path('app.js')
s = F.read_text(encoding='utf-8')

def rep(avant, apres, n=1):
    global s
    c = s.count(avant)
    assert c == n, f'{c} fois au lieu de {n} : {avant[:70]!r}'
    s = s.replace(avant, apres)

rep("""async function loadOthersPossessions(){
  const { data: userData } = await sb.auth.getUser();
  const uid = userData.user.id;
  window.__monId = uid;
  await chargerCouleursTerritoire();   // patch158
""", """// ---------- patch329 : l'état compact de la carte (s2-89) ----------
var CARTE = { dispo: null, id: null, cat: null, catVersion: null, uid: null, enCours: null, suivi: false, mesTimer: null };
const CARTE_TIERS = ['commun', 'peucommun', 'rare', 'epique', 'legendaire'];
// un petit coffre dans le navigateur (IndexedDB) ; null si indisponible (navigation privée…)
function carteCoffre(mode, f){
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
async function carteCatalogue(version){
  if(CARTE.cat && version && CARTE.catVersion === version) return CARTE.cat;
  let lignes = null, v = version;
  const garde = version ? await carteCoffre('readonly', st => st.get('catalogue')) : null;
  if(garde && garde.version === version && Array.isArray(garde.c)) lignes = garde.c;
  if(!lignes){
    const { data, error } = await sb.rpc('carte_catalogue');
    if(error || !data || !Array.isArray(data.c)) return null;
    lignes = data.c; v = data.version;
    carteCoffre('readwrite', st => st.put({ version: v, c: lignes }, 'catalogue'));
  }
  const m = new Map();
  for(const r of lignes) m.set(String(r[0]), r);
  CARTE.cat = m; CARTE.catVersion = v;
  return m;
}
// une commune absente du catalogue (ajoutée depuis la nuit) : sa fiche directement
async function carteComplements(codes){
  for(let i = 0; i < codes.length; i += 200){
    const { data } = await sb.from('communes').select('code,nom,departement,population,latitude,longitude,tier').in('code', codes.slice(i, i + 200));
    for(const c of data || []){
      const t = CARTE_TIERS.indexOf(c.tier);
      CARTE.cat.set(String(c.code), [c.code, c.nom, c.departement, c.population, c.latitude, c.longitude, t < 0 ? null : t]);
    }
  }
}
function carteEntree(code, pseudo, joueurId, acq, boucl){
  const r = CARTE.cat && CARTE.cat.get(code);
  if(!r) return null;
  const tid = r[6] == null ? null : CARTE_TIERS[r[6]];
  return { code, nom: r[1], dept: r[2], pop: r[3], lat: r[4], lon: r[5], tier: TIERS.find(t => t.id === tid),
    pseudo: pseudo || 'un autre joueur', joueurId,
    acquiredAt: acq ? acq * 1000 : 0, bouclierJusqua: boucl ? boucl * 1000 : 0 };
}
async function carteToutCharger(uid){
  const { data, error } = await sb.rpc('carte_etat');
  if(error){ if(fonctionAbsente(error)) CARTE.dispo = false; return false; }
  if(!data || !Array.isArray(data.p)) return false;
  const cat = await carteCatalogue(data.catalogue);
  if(!cat) return false;
  const J = data.joueurs || [];
  const manquants = [];
  for(const r of data.p){ const j = J[r[1]]; if(j && j[0] !== uid && !cat.has(String(r[0]))) manquants.push(String(r[0])); }
  if(manquants.length) await carteComplements(manquants);
  const m = new Map();
  for(const r of data.p){
    const j = J[r[1]];
    if(!j || j[0] === uid) continue;
    const e = carteEntree(String(r[0]), j[1], j[0], r[2], r[3]);
    if(e) m.set(e.code, e);
  }
  othersMap = m;
  CARTE.id = Number(data.id) || 0; CARTE.uid = uid; CARTE.dispo = true;
  return true;
}
function carteMesPlusTard(){
  clearTimeout(CARTE.mesTimer);
  CARTE.mesTimer = setTimeout(() => { loadMyCollection().catch(() => {}); }, 1500);
}
async function carteDelta(rendre){
  if(!CARTE.dispo || CARTE.id == null || !CARTE.uid) return false;
  const { data, error } = await sb.rpc('carte_depuis', { p_id: CARTE.id });
  if(error || !data) return false;
  if(data.complet){
    const ok = await carteToutCharger(CARTE.uid);
    if(ok){ carteMesPlusTard(); if(rendre){ renderMapOverlay(); majBlasonsJournal(); } }
    return ok;
  }
  const ps = new Map((data.joueurs || []).map(j => [j[0], j[1]]));
  // l'état final de chaque commune (les lignes arrivent dans l'ordre, avec un recouvrement)
  const fin = new Map();
  for(const x of data.ch || []) fin.set(String(x[1]), x);
  const manquants = [...fin.values()].filter(x => x[2] && x[2] !== CARTE.uid && !CARTE.cat.has(String(x[1]))).map(x => String(x[1]));
  if(manquants.length) await carteComplements(manquants);
  let bouge = false, mes = false;
  for(const [code, x] of fin){
    const jid = x[2] || null, acq = Number(x[3]) || 0, boucl = Number(x[4]) || 0;
    if(collectionMap.has(code) ? jid !== CARTE.uid : jid === CARTE.uid) mes = true;
    const avant = othersMap.get(code);
    if(!jid || jid === CARTE.uid){ if(avant){ othersMap.delete(code); bouge = true; } continue; }
    if(avant && avant.joueurId === jid && avant.acquiredAt === acq * 1000 && avant.bouclierJusqua === boucl * 1000) continue;
    const e = carteEntree(code, ps.get(jid) || (avant && avant.joueurId === jid ? avant.pseudo : null), jid, acq, boucl);
    if(e){ othersMap.set(code, e); bouge = true; }
  }
  CARTE.id = Math.max(CARTE.id, Number(data.id) || 0);
  if(bouge && rendre){ renderMapOverlay(); majBlasonsJournal(); }
  if(mes) carteMesPlusTard();
  return true;
}
function carteActualiser(uid, rendre){
  if(CARTE.enCours) return CARTE.enCours;
  const p = (CARTE.id != null && CARTE.uid === uid) ? carteDelta(rendre) : carteToutCharger(uid);
  CARTE.enCours = p.catch((e) => { console.error(e); return false; }).finally(() => { CARTE.enCours = null; });
  return CARTE.enCours;
}
function carteSuivre(){
  if(CARTE.suivi) return;
  CARTE.suivi = true;
  const tic = () => { if(CARTE.dispo && CARTE.uid && !document.hidden) carteActualiser(CARTE.uid, true); };
  setInterval(tic, 60000);
  VERIF_AU_RETOUR.push(tic);
}

async function loadOthersPossessions(){
  const { data: userData } = await sb.auth.getUser();
  const uid = userData.user.id;
  window.__monId = uid;
  await chargerCouleursTerritoire();   // patch158
  // patch329 : l'état compact (s2-89), puis seulement les changements
  if(CARTE.dispo !== false){
    const ok = await carteActualiser(uid, false);
    if(ok){
      carteSuivre();
      renderMapOverlay();
      majBlasonsJournal();   // patch275
      return;
    }
  }
""")

F.write_text(s, encoding='utf-8')
print('patch329 appliqué')
