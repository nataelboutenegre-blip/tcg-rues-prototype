# patch464 : cibles en double dans Combat (signalé par Arkhannou, 19/11).
# Deux loadCombat en même temps (ouverture de l'onglet + rafraîchissement) : chacun remplaçait
# combatCibles, puis, après son attente, y ajoutait les communes en combat hors liste (séries
# en cours sur des communes / peu communes non chargées). Le second ajoutait donc par-dessus le
# premier : les mêmes cartes deux fois. On construit la liste à part, sans doublon, et on ne
# l'installe qu'à la fin ; un appel dépassé par un plus récent ne touche plus à rien.
import os, sys
R = sys.argv[1] if len(sys.argv) > 1 else '.'
p = os.path.join(R, 'app.js'); t = open(p, encoding='utf-8').read()
def rep(a, b):
    global t
    assert t.count(a) == 1, (t.count(a), a[:60]); t = t.replace(a, b)

rep("""async function loadCombat(){
  if(SIEGE) sgChargerMes();   // patch405""",
"""let loadCombatNo = 0;   // patch464 : le dernier appel gagne
async function loadCombat(){
  const monNo = ++loadCombatNo;
  if(SIEGE) sgChargerMes();   // patch405""")
rep("""  let { data: cibles, error } = await toutesLesLignes(() => sb
    .from('possessions')
    .select('commune_code, joueur_id, acquired_at, bouclier_jusqua, ' + champsCible)
    .neq('joueur_id', uid)
    .in('communes.tier', tiersCombat()));""",
"""  const tiersDemandes = tiersCombat();   // patch464
  let { data: cibles, error } = await toutesLesLignes(() => sb
    .from('possessions')
    .select('commune_code, joueur_id, acquired_at, bouclier_jusqua, ' + champsCible)
    .neq('joueur_id', uid)
    .in('communes.tier', tiersDemandes));""")
rep("""  combatCibles = cibles || [];
  // un combat en cours sur une commune ou une peu commune doit rester visible
  // meme si son palier n'est pas charge
  const horsListe = (mesSieges || []).map(s => s.commune_code)
    .filter(code => !combatCibles.some(c => c.commune_code === code));
  if(horsListe.length){
    const { data: enPlus } = await sb.from('possessions')
      .select('commune_code, joueur_id, acquired_at, bouclier_jusqua, ' + champsCible)
      .neq('joueur_id', uid).in('commune_code', horsListe.slice(0, 200));
    if(enPlus) combatCibles = combatCibles.concat(enPlus);
  }
""",
"""  // patch464 : la liste se construit à part, sans doublon, puis remplace l'ancienne d'un coup
  const parCode = new Map();
  for(const c of (cibles || [])) parCode.set(c.commune_code, c);
  // un combat en cours sur une commune ou une peu commune doit rester visible
  // meme si son palier n'est pas charge
  const horsListe = (mesSieges || []).map(s => s.commune_code)
    .filter(code => !parCode.has(code));
  if(horsListe.length){
    const { data: enPlus } = await sb.from('possessions')
      .select('commune_code, joueur_id, acquired_at, bouclier_jusqua, ' + champsCible)
      .neq('joueur_id', uid).in('commune_code', horsListe.slice(0, 200));
    for(const c of (enPlus || [])) if(!parCode.has(c.commune_code)) parCode.set(c.commune_code, c);
  }
  if(monNo !== loadCombatNo) return;   // un appel plus récent s'en occupe
  // les communes / peu communes chargées entre-temps par assurerCiblesBas (pas demandées ici) restent
  for(const c of combatCibles){
    const tr = c.communes && c.communes.tier;
    if(!parCode.has(c.commune_code) && !tiersDemandes.includes(tr) && combatBasCharges.has(tr)) parCode.set(c.commune_code, c);
  }
  combatCibles = [...parCode.values()];
""")
open(p, 'w', encoding='utf-8').write(t); print('patch464 : ok')
