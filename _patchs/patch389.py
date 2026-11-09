# patch389 : les tours offerts de la roue en réserve (s2-126). Le tour en plus de la Relance va dans
# une réserve de tours offerts, joués avant les jetons et hors des tours du jour (Maroli, 9/11).
# - la ligne sous les jetons dit « + N tours offerts, hors des 30 du jour » ;
# - le bouton Tourner marche avec un tour offert, même sans jeton ou après les tours du jour ;
# - le texte de la Relance le dit.
import pathlib

def rep(s, avant, apres, n=1):
    c = s.count(avant)
    assert c == n, f'{c} fois au lieu de {n} : {avant[:70]!r}'
    return s.replace(avant, apres)

F = pathlib.Path('app.js'); s = F.read_text(encoding='utf-8')
assert 'patch389' not in s
s = rep(s, """  const par = Number(ROUE.par_jour) || 15, faits = Number(ROUE.tours_jour) || 0, fini = faits >= par && soir < 1, reste = Math.max(0, par - faits);""",
           """  const offr = Math.max(0, Number(ROUE.offerts) || 0);   // patch389 : tours offerts en réserve
  const par = Number(ROUE.par_jour) || 15, faits = Number(ROUE.tours_jour) || 0, fini = faits >= par && soir < 1 && offr < 1, reste = Math.max(0, par - faits);""")
s = rep(s, """  roueEcrire('rdfJour', soir > 0 ? `Les tours du soir ne comptent pas dans tes ${par} tours du jour`   // patch388""",
           """  roueEcrire('rdfJour', soir > 0 ? `Les tours du soir ne comptent pas dans tes ${par} tours du jour`   // patch388
    : offr > 0 ? `<b class="rdf-offerts">+ ${offr} tour${offr > 1 ? 's' : ''} offert${offr > 1 ? 's' : ''}</b>, hors des ${par} du jour · ${reste} restant${reste > 1 ? 's' : ''} aujourd’hui`   // patch389""")
s = rep(s, """    const peut = !roueTourne && (soir >= 1 || (!fini && dispo >= 1));   // patch388 : un tour du soir suffit
    roueEcrire('rdfCentre', roueTourne ? 'Tourner' : soir >= 1 ? 'Tourner<small>offert</small>'""",
           """    const peut = !roueTourne && (soir >= 1 || offr >= 1 || (!fini && dispo >= 1));   // patch388, patch389 : un tour du soir ou offert suffit
    roueEcrire('rdfCentre', roueTourne ? 'Tourner' : soir >= 1 || offr >= 1 ? 'Tourner<small>offert</small>'""")
s = rep(s, """  if(roueSoirReste() < 1 && (Math.floor(roueJetons()) < 1 || Number(ROUE.tours_jour) >= Number(ROUE.par_jour))) return;   // patch388""",
           """  if(roueSoirReste() < 1 && !(Number(ROUE.offerts) > 0) && (Math.floor(roueJetons()) < 1 || Number(ROUE.tours_jour) >= Number(ROUE.par_jour))) return;   // patch388, patch389""")
s = rep(s, """  if(data.soir !== undefined){ ROUE.soir = !!data.soir; ROUE.soir_restants = Number(data.soir_restants) || 0; }   // patch388""",
           """  if(data.soir !== undefined){ ROUE.soir = !!data.soir; ROUE.soir_restants = Number(data.soir_restants) || 0; }   // patch388
  if(data.offerts !== undefined) ROUE.offerts = Number(data.offerts) || 0;   // patch389""")
s = rep(s, """note = nOff > 1 ? `Ton tour est rendu et tu en gagnes ${nOff - 1 > 1 ? nOff - 1 : 'un'} de plus : relance la roue !`""",
           """note = nOff > 1 ? `Ton tour est rendu et tu gagnes ${nOff - 1 > 1 ? nOff - 1 + ' tours offerts' : 'un tour offert'}, hors des ${Number(ROUE && ROUE.par_jour) || 30} du jour : relance la roue !`   /* patch389 */""")
F.write_text(s, encoding='utf-8')

C = pathlib.Path('style.css'); c = C.read_text(encoding='utf-8')
assert 'patch389' not in c
c += """
/* patch389 : tours offerts en réserve */
.rdf-jour .rdf-offerts{ color:#C9C2FF; font-weight:700; }
"""
C.write_text(c, encoding='utf-8')
print('patch389 ok')
