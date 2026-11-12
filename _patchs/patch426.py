# patch426 (12/11/2026) : le temps qu'il reste à une zone bombardée (idée d'Arkhannou).
#  - l'étiquette de la zone sur la carte : « 💥 +15 % · Vienne · 8h15 », redessinée chaque minute ;
#  - toucher l'étiquette (ou la pastille 💥) : l'impact se rejoue et un message dit « encore 8h15 » ;
#  - la fiche d'attaque d'une commune dans la zone : « +15 % : zone bombardée (Vienne) · encore 8h15 ».
import sys
def rep(chemin, avant, apres, nb=1):
    t = open(chemin, encoding='utf-8').read()
    n = t.count(avant)
    if n != nb: sys.exit(f'{chemin} : {n} au lieu de {nb} pour {avant[:70]!r}')
    open(chemin, 'w', encoding='utf-8').write(t.replace(avant, apres))
A = 'app.js'
if 'patch426' in open(A, encoding='utf-8').read(): sys.exit('déjà appliqué')

# l'étiquette sur la carte
rep(A, """    const f = trait(11), txt = `💥 +${btReglage('bombe_bonus', 15)} % · ${z.cible_nom || ''}`;""",
"""    const f = trait(11), txt = `💥 +${btReglage('bombe_bonus', 15)} % · ${z.cible_nom || ''} · ${formatDuree(new Date(z.fin).getTime() - Date.now())}`;   // patch426""")

# toucher l'étiquette : le message en plus de l'impact
rep(A, """    if(mx >= e.x - m && mx <= e.x + e.w + m && my >= e.y - m && my <= e.y + e.h + m){ bfxJouer(e.z, false); return true; }""",
"""    if(mx >= e.x - m && mx <= e.x + e.w + m && my >= e.y - m && my <= e.y + e.h + m){ bfxJouer(e.z, false); bombeZoneDire(e.z); return true; }""")

# la fiche d'attaque
rep(A, """<span>+${attaqueEffetBt.bombe} % : zone bombardée${attaqueEffetBt.bombe_sur ? ' (<b>' + echapperHtml(attaqueEffetBt.bombe_sur) + '</b>)' : ''}</span>""",
"""<span>+${attaqueEffetBt.bombe} % : zone bombardée${attaqueEffetBt.bombe_sur ? ' (<b>' + echapperHtml(attaqueEffetBt.bombe_sur) + '</b>)' : ''}${bombeZoneReste(attaqueEffetBt.bombe_sur)}</span>""")

open(A, 'a', encoding='utf-8').write("""
// ---------- patch426 : le temps qu'il reste à une zone bombardée (Arkhannou) ----------
function bombeZoneDire(z){
  const reste = new Date(z.fin).getTime() - Date.now();
  if(!(reste > 0)) return;
  const d = new Date(z.fin), h = d.getHours() + 'h' + String(d.getMinutes()).padStart(2, '0');
  notifier({ type: 'info', titre: '💥 Zone bombardée · ' + (z.cible_nom || ''),
             texte: `+${btReglage('bombe_bonus', 15)} % en attaque encore ${formatDuree(reste)} (jusqu’à ${h}).` });
}
function bombeZoneReste(nom){
  const t = Date.now();
  const z = (BOMBES_ZONES || []).filter(x => new Date(x.fin).getTime() > t && (!nom || x.cible_nom === nom))
    .sort((a, b) => new Date(b.fin).getTime() - new Date(a.fin).getTime())[0];
  return z ? ' · encore <b>' + formatDuree(new Date(z.fin).getTime() - t) + '</b>' : '';
}
setInterval(() => {   // l'étiquette suit la minute
  if(document.hidden || !SAISON2 || !(BOMBES_ZONES || []).length || modeJeu !== 'front') return;
  if(BOMBES_ZONES.some(z => new Date(z.fin).getTime() > Date.now() - 60e3)) demanderDessin();
}, 60e3);
""")
print('patch426 OK')
