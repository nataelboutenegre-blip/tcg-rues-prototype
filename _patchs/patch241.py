# patch241 : l'infobulle de la carte dit « Aurore » (l'étoile Aurore était prise pour une épique : Boule2Pain)
import pathlib
f = pathlib.Path('app.js'); s = f.read_text(encoding='utf-8')
def rep(s, a, b, n=1):
    assert s.count(a) == n, (a[:80], s.count(a)); return s.replace(a, b)
s = rep(s, """      + LIBELLE_TIER[t.commune.tier] + ', '
      + (t.joueur.moi ? 'à toi' : 'à ' + t.joueur.pseudo);""",
"""      + LIBELLE_TIER[t.commune.tier] + (auroreFront(t.commune.code) ? ' Aurore' : '') + ', '   // patch241
      + (t.joueur.moi ? 'à toi' : 'à ' + t.joueur.pseudo);""")
s = rep(s, "${LIBELLE_TIER[c.tier]}, ${j.moi ? 'à toi' : 'à ' + echapperHtml(j.pseudo)}</title>",
           "${LIBELLE_TIER[c.tier]}${auroreFront(c.code) ? ' Aurore' : ''}, ${j.moi ? 'à toi' : 'à ' + echapperHtml(j.pseudo)}</title>", 2)
f.write_text(s, encoding='utf-8'); print('patch241 ok')
