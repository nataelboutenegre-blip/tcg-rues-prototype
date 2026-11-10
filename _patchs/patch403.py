# patch403 (10/11/2026) : les fines limites des communes à l'intérieur d'un territoire s'effacent de loin
# (suite de la remarque d'Oshannir) : invisibles en vue large (zoom < 4), elles apparaissent en
# rapprochant et retrouvent leur force à partir du zoom 8, pour voir chaque commune et où taper.
import sys
def rep(chemin, avant, apres, nb=1):
    t = open(chemin, encoding='utf-8').read()
    n = t.count(avant)
    if n != nb: sys.exit(f'{chemin} : {n} au lieu de {nb} pour {avant[:70]!r}')
    open(chemin, 'w', encoding='utf-8').write(t.replace(avant, apres))
A = 'app.js'
rep(A, """      ctx.fillStyle = 'rgba(22,48,79,0.75)';
      ctx.strokeStyle = '#20406A'; ctx.lineWidth = trait(0.6);
      ctx.fill(libres); ctx.stroke(libres);""",
"""      ctx.fillStyle = 'rgba(22,48,79,0.75)';
      ctx.strokeStyle = '#20406A'; ctx.lineWidth = trait(0.6);
      ctx.fill(libres); ctx.stroke(libres);
      // patch403 : de loin, un territoire d'un seul tenant sans ses limites intérieures
      const interieur = Math.max(0, Math.min(1, (mapZoom - 4) / 4));""")
rep(A, """          ctx.globalAlpha = opaciteJoueur(id, 0.55);
          ctx.strokeStyle = '#07111F'; ctx.lineWidth = trait(0.7); ctx.stroke(p);""",
"""          if(interieur > 0){   // patch403
            ctx.globalAlpha = opaciteJoueur(id, 0.55 * interieur);
            ctx.strokeStyle = '#07111F'; ctx.lineWidth = trait(0.7); ctx.stroke(p);
          }""")
rep(A, """        ctx.globalAlpha = opaciteJoueur(id, 0.55);
        ctx.strokeStyle = j.fonce; ctx.lineWidth = trait(0.7); ctx.stroke(p);
        ctx.globalAlpha = 1;""",
"""        if(interieur > 0){   // patch403
          ctx.globalAlpha = opaciteJoueur(id, 0.55 * interieur);
          ctx.strokeStyle = j.fonce; ctx.lineWidth = trait(0.7); ctx.stroke(p);
        }
        ctx.globalAlpha = 1;""")
print('patch403 OK')
