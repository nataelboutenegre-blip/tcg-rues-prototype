# patch408 (11/11/2026) : la vue outre-mer du Front (bug signalé par Arkhannou sur Mayotte)
#  - calque Clans : le contour du clan est tracé autour de son territoire, comme sur la carte de France (patch212),
#    et plus autour de chaque commune (grille épaisse aux couleurs du clan) ;
#  - le calque d'animation des bombes de la carte de France (#mapBombeFx) est caché en vue outre-mer
#    (un cercle de bombe restait par-dessus les territoires).
import sys
def rep(chemin, avant, apres, nb=1):
    t = open(chemin, encoding='utf-8').read()
    n = t.count(avant)
    if n != nb: sys.exit(f'{chemin} : {n} au lieu de {nb} pour {avant[:70]!r}')
    open(chemin, 'w', encoding='utf-8').write(t.replace(avant, apres))
A, C = 'app.js', 'style.css'
if 'patch408' in open(A, encoding='utf-8').read(): sys.exit('déjà appliqué')

rep(A, """  const clans = (typeof CALQUES !== 'undefined' && CALQUES.clans && typeof clansCarte !== 'undefined') ? clansCarte : null;
  for(const code in contours){""",
"""  const clans = (typeof CALQUES !== 'undefined' && CALQUES.clans && typeof clansCarte !== 'undefined') ? clansCarte : null;
  const parClan = clans ? new Map() : null;   // patch408 : un contour par clan, pas un par commune
  for(const code in contours){""")
rep(A, """    const clan = clans && c && clans.get(mienne ? window.__monId : autre.joueurId);
    if(clan){ ctx.strokeStyle = clan.couleur; ctx.lineWidth = grand ? 2.6 : 1.8; ctx.stroke(p); }""",
"""    const clan = clans && c && clans.get(mienne ? window.__monId : autre.joueurId);
    if(clan){
      const k = clan.tag || clan.couleur;
      if(!parClan.has(k)) parClan.set(k, { couleur: clan.couleur, chemin: new Path2D() });
      parClan.get(k).chemin.addPath(p);
    }""")
rep(A, """  if(OMF.bulle && OMF.bulle.dep === dep){
    const c = tu.chemins.find(([code]) => code === OMF.bulle.code);""",
"""  // patch408 : le tour du territoire de chaque clan, tracé seulement à l'extérieur (comme patch212)
  if(parClan) for(const { couleur, chemin } of parClan.values()){
    const dehors = new Path2D();
    dehors.rect(-larg, -haut, larg * 3, haut * 3);
    dehors.addPath(chemin);
    ctx.save();
    ctx.clip(dehors, 'evenodd');
    ctx.strokeStyle = '#07111F'; ctx.lineWidth = grand ? 5 : 3.4; ctx.stroke(chemin);
    ctx.strokeStyle = couleur; ctx.lineWidth = grand ? 3.2 : 2.2; ctx.stroke(chemin);
    ctx.restore();
  }
  if(OMF.bulle && OMF.bulle.dep === dep){
    const c = tu.chemins.find(([code]) => code === OMF.bulle.code);""")
rep(C, """.map-wrap.outremer .map-reduire, .map-wrap.outremer #mapLegende{ display:none !important; }""",
""".map-wrap.outremer .map-reduire, .map-wrap.outremer #mapLegende, .map-wrap.outremer #mapBombeFx{ display:none !important; }   /* patch408 : + #mapBombeFx */""")
print('patch408 OK')
