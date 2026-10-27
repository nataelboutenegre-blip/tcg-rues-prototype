# patch240b : le guide en bulles suit aussi la série gardée
import pathlib
f = pathlib.Path('app.js'); s = f.read_text(encoding='utf-8')
def rep(s, a, b, n=1):
    assert s.count(a) == n, (a[:80], s.count(a)); return s.replace(a, b)
s = rep(s, "se prennent par la force : trois victoires d\\'affilée.", "se prennent par la force : trois victoires, pas forcément d\\'affilée.")
s = rep(s, "texte: 'Trois victoires d\\'affilée prennent une commune.", "texte: 'Trois victoires prennent une commune, et une défaite ne te fait rien perdre.")
f.write_text(s, encoding='utf-8'); print('patch240b ok')
