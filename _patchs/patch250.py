# patch250 : échanges de clan — 3 par jour, 3 propositions en attente (avec s2-50)
import pathlib
def rep(s, a, b, n=1):
    assert s.count(a) == n, (a[:90], s.count(a)); return s.replace(a, b)
f = pathlib.Path('app.js'); s = f.read_text(encoding='utf-8')
s = rep(s, "const restant = Math.max(0, (e.max || 2) - (e.faits || 0));", "const restant = Math.max(0, (e.max || 3) - (e.faits || 0));   // patch250")
s = rep(s, "Tu as fait tes 2 échanges du jour. Reviens demain.", "Tu as fait tes 3 échanges du jour. Reviens demain.")
s = rep(s, "<li>2 échanges par jour et par joueur. Une proposition expire au bout de 24 h.</li>",
           "<li>3 échanges par jour et par joueur, 3 propositions en attente au plus. Une proposition expire au bout de 24 h.</li>")
f.write_text(s, encoding='utf-8')
f = pathlib.Path('index.html'); s = f.read_text(encoding='utf-8')
s = rep(s, "2 échanges par jour au plus ; pas une commune", "3 échanges par jour au plus (et 3 propositions en attente) ; pas une commune")
f.write_text(s, encoding='utf-8')
print('patch250 ok')
