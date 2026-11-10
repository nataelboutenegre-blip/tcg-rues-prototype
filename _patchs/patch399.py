# patch399 (10/11/2026) : les clans de la carte se rechargent après un échec (Arkhannou, 10/11 :
# « je vois de nouveau les membres de mon clan », « la fonction clan ne marche plus »).
# clans_carte n'était demandé qu'une fois, 1,5 s après l'ouverture ; s'il échouait (jeton expiré au retour
# sur l'appli : 401 vus dans les journaux à 0 h et 3 h), les clans restaient vides toute la session :
# coéquipiers parmi les cibles du Combat, calque Clans vide.
import sys
def rep(chemin, avant, apres, nb=1):
    t = open(chemin, encoding='utf-8').read()
    n = t.count(avant)
    if n != nb: sys.exit(f'{chemin} : {n} au lieu de {nb} pour {avant[:70]!r}')
    open(chemin, 'w', encoding='utf-8').write(t.replace(avant, apres))
A = 'app.js'
rep(A, """async function loadClansCarte(){
  if(!CLANS) return;
  try{
    if(!monUidClan){ const { data: u } = await sb.auth.getUser(); monUidClan = u && u.user ? u.user.id : null; }
    const [{ data, error }] = await Promise.all([sb.rpc('clans_carte'), chargerBlasons()]);   // patch253
    tchatDemarrer();   // patch258
    if(error) return;
    clansCarte = new Map((data || []).map(r => [r.joueur_id, { tag: r.tag, couleur: r.couleur }]));""",
"""// patch399 : un échec (jeton expiré au retour sur l'appli…) n'est plus définitif
let clansCarteEchecs = 0, clansCarteLu = 0, clansCarteRelance = null;
function clansCarteReessayer(err){
  if(clansCarteRelance || clansCarteEchecs >= 6) return;
  const n = ++clansCarteEchecs;
  const jeton = /jwt|expired|401|token/i.test(String(err && (err.message || err.code || err.status || err) || ''));
  clansCarteRelance = setTimeout(async () => {
    clansCarteRelance = null;
    if(jeton){ try{ await sb.auth.refreshSession(); }catch(e){} }
    loadClansCarte();
  }, Math.min(60000, 3000 * n * n));
}
async function loadClansCarte(){
  if(!CLANS) return;
  try{
    if(!monUidClan){ const { data: u } = await sb.auth.getUser(); monUidClan = u && u.user ? u.user.id : null; }
    const [{ data, error }] = await Promise.all([sb.rpc('clans_carte'), chargerBlasons()]);   // patch253
    tchatDemarrer();   // patch258
    if(error || !monUidClan){ clansCarteReessayer(error || 'sans session'); return; }   // patch399
    clansCarteEchecs = 0; clansCarteLu = Date.now();
    clansCarte = new Map((data || []).map(r => [r.joueur_id, { tag: r.tag, couleur: r.couleur }]));""")
rep(A, """    if(typeof demanderDessin === 'function'){ CV.donneesSignature = ''; demanderDessin(); }
  }catch(e){ /* les clans restent invisibles */ }
}""", """    if(typeof demanderDessin === 'function'){ CV.donneesSignature = ''; demanderDessin(); }
  }catch(e){ clansCarteReessayer(e); }   // patch399 : avant, les clans restaient invisibles
}""")
rep(A, """if(CLANS) setTimeout(loadClansCarte, 1500);""",
"""if(CLANS) setTimeout(loadClansCarte, 1500);
// patch399 : relu au retour sur l'appli (après 5 min) et toutes les 10 min (arrivées et départs des clans)
if(CLANS){
  document.addEventListener('visibilitychange', () => {
    if(!document.hidden && Date.now() - clansCarteLu > 300000){ clansCarteEchecs = 0; loadClansCarte(); }
  });
  setInterval(() => { if(!document.hidden && Date.now() - clansCarteLu > 540000) loadClansCarte(); }, 600000);
}""")
print('patch399 ok')
