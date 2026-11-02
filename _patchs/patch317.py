# patch317 : la chance affichée compte déjà la garnison (avec s2-82, 2/11)
#  Le texte du badge de la fiche d'attaque dit que le pourcentage en tient compte,
#  pour qu'on ne divise pas une deuxième fois de tête.
import pathlib

def rep(s, a, b, n=1):
    assert s.count(a) == n, (s.count(a), a[:100])
    return s.replace(a, b)

f = pathlib.Path('app.js'); s = f.read_text(encoding='utf-8')
assert "la chance affichée en tient déjà compte" not in s

s = rep(s, """<span><b>Commune en garnison.</b> Chaque victoire peut être annulée par une défense automatique (1 chance sur 2).</span></div>` : ''}""",
           """<span><b>Commune en garnison.</b> Une victoire sur deux est annulée par sa défense : la chance affichée en tient déjà compte.</span></div>` : ''}""")

f.write_text(s, encoding='utf-8')
print('patch317 ok')
