# patch482 : ce qui a été lu (cloche, alertes de bombe) est retenu sur le compte, avec s3-41.
# Bug d'Oshannir : les mêmes alertes revenaient sur le téléphone après les avoir vues sur le PC.
# On garde aussi le localStorage : il marche sans réseau et avant que le compte réponde.
import os, sys
R = sys.argv[1] if len(sys.argv) > 1 else '.'
def rep(f, a, b, n=1):
    p = os.path.join(R, f); t = open(p, encoding='utf-8').read()
    if t.count(a) != n:
        if b in t: print(f'{f} : déjà fait ({a[:50]!r})'); return
        raise SystemExit(f'{f} : {t.count(a)} occurrence(s) au lieu de {n} pour {a[:80]!r}')
    open(p, 'w', encoding='utf-8').write(t.replace(a, b)); print(f'{f} : ok ({a[:50]!r})')
A = 'app.js'

# 1. la mémoire du compte, et la cloche qui la lit
rep(A, """function ncVus(){ try{ return new Set(JSON.parse(localStorage.getItem('tf-nc-vus') || '[]')); }catch(e){ return new Set(); } }
function ncMarquerVus(cles){
  const v = ncVus();
  for(const c of cles) v.add(c);
  try{ localStorage.setItem('tf-nc-vus', JSON.stringify([...v].slice(-500))); }catch(e){}
}""", """// patch482 : ce qui a été lu est aussi retenu sur le compte (s3-41), pour ne pas revoir sur le téléphone
// ce qu'on a déjà vu sur le PC. Clés « nc:… » (la cloche) et « bo:… » (les bombes), gardées 30 jours.
var CV_VUS = { set: new Set(), depuis: null, pret: false, envoi: new Set(), minuteur: null, attente: null };
async function vusCompteCharger(){
  try{
    const { data, error } = await sb.rpc('vus_lire', { p_depuis: CV_VUS.depuis });
    if(!error && Array.isArray(data))
      for(const r of data){ CV_VUS.set.add(r.cle); if(!CV_VUS.depuis || r.le > CV_VUS.depuis) CV_VUS.depuis = r.le; }
  }catch(e){}
  CV_VUS.pret = true;
}
function vusCompteAttendre(){ if(!CV_VUS.attente) CV_VUS.attente = vusCompteCharger(); return CV_VUS.attente; }
function vusCompteMarquer(cles){
  for(const c of cles){ if(!c || CV_VUS.set.has(c)) continue; CV_VUS.set.add(c); CV_VUS.envoi.add(c); }
  if(!CV_VUS.envoi.size || CV_VUS.minuteur) return;
  CV_VUS.minuteur = setTimeout(async () => {
    CV_VUS.minuteur = null;
    const l = [...CV_VUS.envoi].slice(0, 300);
    l.forEach(c => CV_VUS.envoi.delete(c));
    try{ const { error } = await sb.rpc('vus_marquer', { p_cles: l }); if(error) throw error; }
    catch(e){ return; }   // pas de réseau : le localStorage garde quand même la trace sur cet appareil
    if(CV_VUS.envoi.size) vusCompteMarquer([]);
  }, 1500);
}
function ncVus(){
  let s; try{ s = new Set(JSON.parse(localStorage.getItem('tf-nc-vus') || '[]')); }catch(e){ s = new Set(); }
  for(const c of CV_VUS.set) if(c.startsWith('nc:')) s.add(c.slice(3));   // patch482
  return s;
}
function ncMarquerVus(cles){
  let v; try{ v = new Set(JSON.parse(localStorage.getItem('tf-nc-vus') || '[]')); }catch(e){ v = new Set(); }
  for(const c of cles) v.add(c);
  try{ localStorage.setItem('tf-nc-vus', JSON.stringify([...v].slice(-500))); }catch(e){}
  vusCompteMarquer(cles.map(c => 'nc:' + c));   // patch482
}""")

# 2. la cloche relit la mémoire du compte à chaque chargement (seulement ce qui est nouveau)
rep(A, """async function ncCharger(){
  const rpc = async (n, a) => { try{ const { data, error } = await sb.rpc(n, a); return error ? undefined : data; }catch(e){ return undefined; } };
""", """async function ncCharger(){
  const rpc = async (n, a) => { try{ const { data, error } = await sb.rpc(n, a); return error ? undefined : data; }catch(e){ return undefined; } };
  const vusP = CV_VUS.attente ? vusCompteCharger() : vusCompteAttendre();   // patch482
""")
rep(A, """  NC.charge = Date.now();   // patch262
  ncConstruire();
}""", """  NC.charge = Date.now();   // patch262
  await vusP;   // patch482
  ncConstruire();
}""")

# 3. les bombes : une alerte vue sur un appareil ne revient pas sur l'autre
rep(A, """let bombesVues = null;
function bombesAnnoncer(){
  const L = BOMBES_ALERTES || [];
  const cle = (a) => (a.type === 'bombe' ? 'b' : 'p') + a.id;
  let vues = bombesVues;
  if(vues === null){
    try{ vues = JSON.parse(localStorage.getItem('tf-bombes-vues') || 'null'); }catch(e){ vues = null; }
  }
  const premier = !Array.isArray(vues);
  const deja = new Set(premier ? [] : vues);""", """let bombesVues = null, bombesAttente = false;
function bombesAnnoncer(){
  if(!CV_VUS.pret){   // patch482 : on attend la mémoire du compte avant d'annoncer
    if(!bombesAttente){ bombesAttente = true; vusCompteAttendre().then(() => { bombesAttente = false; bombesAnnoncer(); }); }
    return;
  }
  const L = BOMBES_ALERTES || [];
  const cle = (a) => (a.type === 'bombe' ? 'b' : 'p') + a.id;
  let vues = bombesVues;
  if(vues === null){
    try{ vues = JSON.parse(localStorage.getItem('tf-bombes-vues') || 'null'); }catch(e){ vues = null; }
  }
  const duCompte = [...CV_VUS.set].filter(c => c.startsWith('bo:')).map(c => c.slice(3));   // patch482
  const premier = !Array.isArray(vues) && !duCompte.length;
  const deja = new Set(premier ? [] : (vues || []).concat(duCompte));""")
rep(A, """  bombesVues = L.map(cle).concat(premier ? [] : vues).slice(0, 80);
  try{ localStorage.setItem('tf-bombes-vues', JSON.stringify(bombesVues)); }catch(e){}""", """  bombesVues = L.map(cle).concat(premier ? [] : (vues || [])).slice(0, 80);
  try{ localStorage.setItem('tf-bombes-vues', JSON.stringify(bombesVues)); }catch(e){}
  vusCompteMarquer(L.map(a => 'bo:' + cle(a)));   // patch482""")
print('patch482 : fini')
