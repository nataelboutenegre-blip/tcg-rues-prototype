# patch272 : l'énergie des quêtes affichée sur 50 par jour (avec s2-66)
import pathlib
def rep(s, a, b, n=1):
    assert s.count(a) == n, (a[:90], s.count(a)); return s.replace(a, b)
f = pathlib.Path('app.js'); s = f.read_text(encoding='utf-8')
assert 'patch272' not in s
s = rep(s, "⚡ ${ej} / 35 d'énergie de quêtes</span>", "⚡ ${ej} / 50 d'énergie de quêtes</span>")   # patch272
s = rep(s, "    `<h3>Aujourd'hui${ej !== null ?", "    // patch272 : plafond de l'énergie des quêtes 50 / jour (s2-66)\n    `<h3>Aujourd'hui${ej !== null ?")
f.write_text(s, encoding='utf-8')
print('patch272 appliqué')
