# patch372 (8/11/2026) : la page plantait quand on enchaînait vite le bouton « + »
# d'une carte sur téléphone (signalé par Arkhannou sur Discord, capture « Aïe aïe aïe »).
#
# Cause trouvée au banc (pas de plantage sur ordinateur, mais le même emballement) :
# sur la carte du Radar, un passage par le zoom ×2,56, même d'une fraction de
# seconde, lançait le chargement des communes de ~46 départements, puis un
# redessin complet à chaque arrivée : ~14 blocages, ~1 s sur ordinateur, bien
# plus de temps et de mémoire sur un téléphone. Ma France faisait la même chose
# à partir du zoom ×3,24.
#   - Radar : les communes ne se chargent que quand le zoom est posé (300 ms sans
#     zoom ni glissement) ; les arrivées sont regroupées en un seul redessin ;
#     les communes n'apparaissent qu'à partir du zoom ×4 (au lieu de ×2,5, où
#     elles ne formaient qu'une trame illisible).
#   - Ma France : même chargement différé et même regroupement des redessins.
import pathlib

def rep(s, avant, apres, n=1):
    c = s.count(avant)
    assert c == n, f'{c} fois au lieu de {n} : {avant[:80]!r}'
    return s.replace(avant, apres)

F = pathlib.Path('app.js'); s = F.read_text(encoding='utf-8')
assert 'patch372' not in s, 'patch372 déjà appliqué'

# ---------- Radar ----------
s = rep(s, "const RADAR_SEUIL_COMMUNES = 2.5;          // zoom à partir duquel on dessine les communes",
"""const RADAR_SEUIL_COMMUNES = 4;            // zoom à partir duquel on dessine les communes (patch372 : 2,5 avant)
// patch372 : enchaîner « + » passait par des zooms intermédiaires qui lançaient
// chacun le chargement de dizaines de départements. On attend que le zoom soit
// posé, et les arrivées ne déclenchent qu'un redessin groupé.
let radarDernierZoom = 0, radarRedessinTimer = null;
const RADAR_ZOOM_POSE_MS = 300;""")
s = rep(s, "function radarRedessiner(){ if(!document.getElementById('rdManche').hidden) radarDessiner(radarDessinCourant); }",
"""function radarRedessiner(delai = 120){   // patch372 : groupé
  if(radarRedessinTimer) return;
  radarRedessinTimer = setTimeout(() => {
    radarRedessinTimer = null;
    if(!document.getElementById('rdManche').hidden) radarDessiner(radarDessinCourant);
  }, delai);
}""")
s = rep(s, """      for(const [dep, b] of Object.entries(radarDeps)){
        if(b[2] < v.x || b[0] > v.x + v.w || b[3] < v.y || b[1] > v.y + v.h) continue;
        const p = radarCommunes.get(dep);
        if(p) x.stroke(p); else radarChargerCommunes(dep);
      }""",
"""      const pose = performance.now() - radarDernierZoom >= RADAR_ZOOM_POSE_MS;   // patch372
      let attente = false;
      for(const [dep, b] of Object.entries(radarDeps)){
        if(b[2] < v.x || b[0] > v.x + v.w || b[3] < v.y || b[1] > v.y + v.h) continue;
        const p = radarCommunes.get(dep);
        if(p) x.stroke(p); else if(pose) radarChargerCommunes(dep); else attente = true;
      }
      if(attente) radarRedessiner(RADAR_ZOOM_POSE_MS + 20);""")
s = rep(s, """  const k = Math.min(RADAR_ZOOM_MAX, Math.max(1, radarZoom.k * f));
  if(k === radarZoom.k) return;""",
"""  const k = Math.min(RADAR_ZOOM_MAX, Math.max(1, radarZoom.k * f));
  if(k === radarZoom.k) return;
  radarDernierZoom = performance.now();   // patch372""")
s = rep(s, """    const m = svg.getScreenCTM();
    radarZoom.cx = g.cx - dx / m.a; radarZoom.cy = g.cy - dy / m.d;""",
"""    const m = svg.getScreenCTM();
    radarDernierZoom = performance.now();   // patch372 : glisser aussi
    radarZoom.cx = g.cx - dx / m.a; radarZoom.cy = g.cy - dy / m.d;""")

# ---------- Ma France ----------
s = rep(s, """function mfZoomer(f, px, py){
  const avant = MF.k;
  const k = Math.max(1, Math.min(60, avant * f));
  if(k === avant) return;""",
"""function mfZoomer(f, px, py){
  const avant = MF.k;
  const k = Math.max(1, Math.min(60, avant * f));
  if(k === avant) return;
  MF.dernierZoom = performance.now();   // patch372""")
s = rep(s, """  // les contours arrivent par departement : on redessine a chaque arrivee
  for(const dep of attente) chargerContours(dep).then(() => { if(terraVue === 'france') mfPlanifier(); });""",
"""  // les contours arrivent par departement. patch372 : seulement une fois le
  // zoom posé, et un seul redessin pour plusieurs arrivées rapprochées
  if(attente.length){
    const reste = 300 - (performance.now() - (MF.dernierZoom || 0));
    if(reste > 0) mfPlanifierPlusTard(reste + 20);
    else for(const dep of attente) chargerContours(dep).then(() => { if(terraVue === 'france') mfPlanifierPlusTard(120); });
  }""")
s = rep(s, """function mfPlanifier(){
  if(MF.prevu) return;""",
"""// patch372 : redessin groupé (arrivées de contours, fin de zoom)
function mfPlanifierPlusTard(delai){
  if(MF.plusTard) return;
  MF.plusTard = setTimeout(() => { MF.plusTard = null; mfPlanifier(); }, delai);
}

function mfPlanifier(){
  if(MF.prevu) return;""")
# glisser à un doigt dans Ma France : on attend aussi la fin du mouvement
s = rep(s, """    if(MF.pointeurs.size === 1){
      MF.ox += apres[0] - avant[0];
      MF.oy += apres[1] - avant[1];""",
"""    if(MF.pointeurs.size === 1){
      MF.dernierZoom = performance.now();   // patch372
      MF.ox += apres[0] - avant[0];
      MF.oy += apres[1] - avant[1];""")

F.write_text(s, encoding='utf-8')
print('patch372 ok')
