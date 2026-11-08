# patch388 : la soirée de la roue du Front (s2-125, demande de Nataël 8/11) : chaque soir de 21 h à 23 h,
# 15 tours offerts, sans jeton, hors du compte du jour, perdus à 23 h.
# - bandeau au-dessus des jetons : avant 21 h « Ce soir de 21 h à 23 h : 15 tours offerts »,
#   pendant « Soirée de la roue · 12 tours offerts jusqu'à 23 h », puis « joués : rendez-vous demain » ;
# - le bouton Tourner marche avec un tour du soir même sans jeton ou après les tours du jour ;
# - à 21 h, la roue se relit d'elle-même si l'onglet est ouvert.
import pathlib

def rep(s, avant, apres, n=1):
    c = s.count(avant)
    assert c == n, f'{c} fois au lieu de {n} : {avant[:70]!r}'
    return s.replace(avant, apres)

F = pathlib.Path('app.js'); s = F.read_text(encoding='utf-8')
assert 'patch388' not in s

s = rep(s, """      <div class="rdf-jetons"><span class="rdf-slots" id="rdfSlots"></span>""",
           """      <div class="rdf-soir" id="rdfSoir" hidden></div>
      <div class="rdf-jetons"><span class="rdf-slots" id="rdfSlots"></span>""")

s = rep(s, """function renderRoueInfos(){
  const el = document.getElementById('roueFront');
  if(!el || el.hidden || !ROUE || !el.offsetParent) return;   // onglet caché : rien à écrire
  const live = roueJetons(), dispo = Math.floor(live);
  const par = Number(ROUE.par_jour) || 15, faits = Number(ROUE.tours_jour) || 0, fini = faits >= par, reste = Math.max(0, par - faits);""",
"""// patch388 : la soirée de la roue (s2-125)
let roueSoirRelu = 0;
function roueSoirFenetre(){
  const d = ROUE && ROUE.soir_debut ? new Date(ROUE.soir_debut).getTime() : 0, f = ROUE && ROUE.soir_fin ? new Date(ROUE.soir_fin).getTime() : 0;
  return { d, f, n: Number(ROUE && ROUE.soir_tours) || 0 };
}
function roueSoirReste(){
  if(!ROUE || !ROUE.soir) return 0;
  const { f } = roueSoirFenetre();
  if(f && Date.now() >= f) return 0;
  return Math.max(0, Number(ROUE.soir_restants) || 0);
}
function roueSoirHtml(){
  const { d, f, n } = roueSoirFenetre();
  if(!n || !d || !f) return '';
  const h = (t) => new Date(t).toLocaleTimeString('fr-FR', { hour: 'numeric', timeZone: 'Europe/Paris' }).replace(/\\s+/g, '\\u00a0');
  const now = Date.now(), r = roueSoirReste();
  if(now < d) return `<span class="rdf-lune">🌙</span><span>Ce soir de ${h(d)} à ${h(f)} : <b>${n} tours offerts</b></span>`;
  if(now >= f) return '';
  if(r > 0) return `<span class="rdf-lune">🌙</span><span><b>Soirée de la roue</b> · ${r} tour${r > 1 ? 's' : ''} offert${r > 1 ? 's' : ''} jusqu’à ${h(f)}</span>`;
  return ROUE.soir ? `<span class="rdf-lune">🌙</span><span>Tes ${n} tours du soir sont joués : rendez-vous demain à ${h(d)}</span>` : '';
}

function renderRoueInfos(){
  const el = document.getElementById('roueFront');
  if(!el || el.hidden || !ROUE || !el.offsetParent) return;   // onglet caché : rien à écrire
  const live = roueJetons(), dispo = Math.floor(live);
  const fen = roueSoirFenetre(), soir = roueSoirReste();   // patch388
  if(fen.n && fen.d && !ROUE.soir && Date.now() >= fen.d && Date.now() < fen.f && Date.now() - roueSoirRelu > 60000){ roueSoirRelu = Date.now(); chargerRoue(); }
  const sh = roueSoirHtml(), sb2 = document.getElementById('rdfSoir');
  if(sb2){ sb2.hidden = !sh; sb2.classList.toggle('actif', soir > 0); roueEcrire('rdfSoir', sh); }
  const par = Number(ROUE.par_jour) || 15, faits = Number(ROUE.tours_jour) || 0, fini = faits >= par && soir < 1, reste = Math.max(0, par - faits);""")

s = rep(s, """    const peut = !roueTourne && !fini && dispo >= 1;
    roueEcrire('rdfCentre', roueTourne ? 'Tourner' : fini ? 'Demain<small>plus de tour</small>' : dispo < 1 ? `${roueMmss(prochain)}<small>prochain tour</small>` : 'Tourner');""",
"""    const peut = !roueTourne && (soir >= 1 || (!fini && dispo >= 1));   // patch388 : un tour du soir suffit
    roueEcrire('rdfCentre', roueTourne ? 'Tourner' : soir >= 1 ? 'Tourner<small>offert</small>' : fini ? 'Demain<small>plus de tour</small>' : dispo < 1 ? `${roueMmss(prochain)}<small>prochain tour</small>` : 'Tourner');""")

s = rep(s, """  if(Math.floor(roueJetons()) < 1 || Number(ROUE.tours_jour) >= Number(ROUE.par_jour)) return;
  const el = document.getElementById('roueFront');""",
"""  if(roueSoirReste() < 1 && (Math.floor(roueJetons()) < 1 || Number(ROUE.tours_jour) >= Number(ROUE.par_jour))) return;   // patch388
  const el = document.getElementById('roueFront');""")
s = rep(s, """  ROUE.tours_jour = Number(data.tours_jour); if(data.par_jour) ROUE.par_jour = Number(data.par_jour);""",
           """  ROUE.tours_jour = Number(data.tours_jour); if(data.par_jour) ROUE.par_jour = Number(data.par_jour);
  if(data.soir !== undefined){ ROUE.soir = !!data.soir; ROUE.soir_restants = Number(data.soir_restants) || 0; }   // patch388""")
s = rep(s, """  roueEcrire('rdfJour', fini ? `${par} tours faits aujourd’hui` : `${reste} tour${reste > 1 ? 's' : ''} restant${reste > 1 ? 's' : ''} aujourd’hui`);""",
           """  roueEcrire('rdfJour', soir > 0 ? `Les tours du soir ne comptent pas dans tes ${par} tours du jour`   // patch388
    : fini ? `${par} tours faits aujourd’hui` : `${reste} tour${reste > 1 ? 's' : ''} restant${reste > 1 ? 's' : ''} aujourd’hui`);""")
F.write_text(s, encoding='utf-8')

C = pathlib.Path('style.css'); c = C.read_text(encoding='utf-8')
assert 'patch388' not in c
c += """
/* patch388 : la soirée de la roue */
.rdf-soir{ display:flex; align-items:center; justify-content:center; gap:8px; margin:12px auto 0; padding:7px 12px; max-width:320px;
  border-radius:12px; font-size:.78rem; line-height:1.3; color:#C9D5E6; background:rgba(120,110,220,.12); border:1px solid rgba(150,140,240,.25); text-align:left; }
.rdf-soir[hidden]{ display:none; }
.rdf-soir b{ color:#fff; }
.rdf-soir.actif{ background:rgba(120,110,220,.24); border-color:rgba(170,160,255,.55); color:#E4E1FF; box-shadow:0 0 18px -6px rgba(150,140,255,.7); }
.rdf-lune{ font-size:1rem; line-height:1; }
"""
C.write_text(c, encoding='utf-8')
print('patch388 ok')
