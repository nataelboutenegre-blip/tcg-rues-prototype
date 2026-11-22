# patch498 : après une prise par siège, la liste d'Attaquer se relit (signalé par Oshannir, 22/11 19 h 02).
# Avant : seule l'attaque de la saison 2 remettait combatChargeLe à zéro (patch477) ; une commune prise par siège
# restait dans les cibles. Et une prise « toute seule » (énergie en attente, rare à 20 min, siège long) n'était vue
# qu'au rechargement de la page.
# - À la conquête par une vague : Combat se relit (tout de suite s'il est affiché), comme la carte.
# - mes_sieges est relu toutes les 2 min tant que j'ai un siège en cours et que la page est visible ; si un siège a
#   disparu de la liste (pris, tombé, abandonné), Combat, la carte et ma collection se relisent.
import os, sys, json
R = sys.argv[1] if len(sys.argv) > 1 else '.'
def rep(f, a, b, n=1):
    p = os.path.join(R, f); t = open(p, encoding='utf-8').read()
    if t.count(a) != n:
        if b in t: print(f'{f} : déjà fait ({a[:50]!r})'); return
        raise SystemExit(f'{f} : {t.count(a)} occurrence(s) au lieu de {n} pour {a[:80]!r}')
    open(p, 'w', encoding='utf-8').write(t.replace(a, b)); print(f'{f} : ok ({a[:50]!r})')
A = 'app.js'
rep(A, """async function sgChargerMes(){
  if(!SIEGE) return;
  const { data, error } = await sb.rpc('mes_sieges');
  if(error) return;
  sgMes = Array.isArray(data) ? data : [];""", """// patch498 : Combat, la carte et ma collection se relisent quand un de mes sièges a fini
function sgApresFin(){
  combatChargeLe = 0;
  const actif = document.querySelector('.tab-panel.active');
  if(actif && actif.id === 'panel-combat') loadCombat();
  Promise.all([loadMyCollection(), loadOthersPossessions()]).then(() => { try{ renderMapOverlay(); }catch(e){} }).catch(() => {});
}
function sgSuivreMes(){
  clearTimeout(SG_SUIVI);
  if(!SIEGE || !sgMes.length) return;
  SG_SUIVI = setTimeout(() => { if(document.hidden) sgSuivreMes(); else sgChargerMes(); }, 120000);
}
var SG_SUIVI = 0;
async function sgChargerMes(){
  if(!SIEGE) return;
  const { data, error } = await sb.rpc('mes_sieges');
  if(error) return;
  const avant = new Set((sgMes || []).map(s => String(s.commune)));
  sgMes = Array.isArray(data) ? data : [];
  const maintenant = new Set(sgMes.map(s => String(s.commune)));
  if([...avant].some(c => !maintenant.has(c))) sgApresFin();   // patch498 : un siège a disparu (pris, tombé, abandonné)
  sgSuivreMes();""")
rep(A, """  if(s.resultat === 'conquise'){
    sgFermer();""", """  if(s.resultat === 'conquise'){
    combatChargeLe = 0;   // patch498 : Combat se relira
    { const act = document.querySelector('.tab-panel.active'); if(act && act.id === 'panel-combat') setTimeout(loadCombat, 400); }
    sgFermer();""")
p = os.path.join(R, 'data', 'nouveautes.json'); d = json.load(open(p, encoding='utf-8'))
e = next(x for x in d if x.get('date') == '2026-11-22')
l = "Attaquer se met à jour après une prise par siège, même quand la commune tombe toute seule avec l'énergie en attente (signalé par Oshannir)."
e.setdefault('correctifs', [])
if l not in e['correctifs']: e['correctifs'].insert(0, l)
json.dump(d, open(p, 'w', encoding='utf-8'), ensure_ascii=False, indent=2); print('nouveautes.json : ok')
