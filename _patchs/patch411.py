# patch411 (11/11/2026) : échange depuis la carte, seules mes communes de la bonne rareté ressortent (idée d'Arkhannou)
# Avant : toutes mes communes ressortaient (joueursSurlignes = moi) ; une commune d'une autre rareté disait seulement
# « choisis une commune rare » une fois touchée.
# Maintenant, pendant l'échange : mes communes d'une autre rareté sont voilées, celles de la bonne rareté sont
# entourées de jaune ; le bandeau le dit.
import sys
def rep(chemin, avant, apres, nb=1):
    t = open(chemin, encoding='utf-8').read()
    n = t.count(avant)
    if n != nb: sys.exit(f'{chemin} : {n} au lieu de {nb} pour {avant[:70]!r}')
    open(chemin, 'w', encoding='utf-8').write(t.replace(avant, apres))
A = 'app.js'
if 'patch411' in open(A, encoding='utf-8').read(): sys.exit('déjà appliqué')

rep(A, """      const parJT = rar ? new Map() : null;                  // 'joueur|rareté' -> chemin
""", """      const parJT = rar ? new Map() : null;                  // 'joueur|rareté' -> chemin
      const eccHors = echCarte ? new Path2D() : null, eccOk = echCarte ? new Path2D() : null;   // patch411 : échange en cours
""")
rep(A, """          const jc = parClan && joueurs.get(c.joueur);   // patch212""",
"""          if(eccHors && c.joueur === ID_MOI) (c.tier === echCarte.tier ? eccOk : eccHors).addPath(p);   // patch411
          const jc = parClan && joueurs.get(c.joueur);   // patch212""")
rep(A, """      // patch212 : le tour du territoire de chaque clan, trace seulement a
""", """      // patch411 : échange en cours, mes communes d'une autre rareté voilées, les bonnes entourées
      if(eccHors){
        ctx.globalAlpha = 1;
        ctx.fillStyle = 'rgba(7,17,31,.74)'; ctx.fill(eccHors);
        ctx.strokeStyle = '#07111F'; ctx.lineWidth = trait(3.6); ctx.stroke(eccOk);
        ctx.strokeStyle = '#FFD36B'; ctx.lineWidth = trait(2); ctx.stroke(eccOk);
      }
      // patch212 : le tour du territoire de chaque clan, trace seulement a
""")
rep(A, """<br><span>Touche une de tes communes <b class="rarete ${t}">${eccLibelle(t)}s</b> pour la proposer.""",
"""<br><span>Seules tes communes <b class="rarete ${t}">${eccLibelle(t)}s</b> ressortent, entourées de jaune : touches-en une pour la proposer.""")
print('patch411 OK')
