# patch312 : retirer une garnison rend 75 % de son énergie (au lieu de la moitié), arrondi en dessous (s2-79)
import pathlib

def rep(s, a, b, n=1):
    assert s.count(a) == n, (s.count(a), a[:100])
    return s.replace(a, b)

f = pathlib.Path('app.js'); s = f.read_text(encoding='utf-8')
assert 'patch312' not in s
s = rep(s, "Confirmer (+${Math.floor(g.energie / 2)})", "Confirmer (+${Math.floor(g.energie * 3 / 4)})")
s = rep(s, "<li>Retirer une garnison rend la moitié de son énergie.</li></ul>",
           "<li>Retirer une garnison rend les trois quarts de son énergie.</li></ul><!-- patch312 -->")
f.write_text(s, encoding='utf-8')

f = pathlib.Path('index.html'); s = f.read_text(encoding='utf-8')
assert 'patch312' not in s
s = rep(s, "<p>Retirer une garnison rend la moitié de son énergie. Une défense",
           "<p>Retirer une garnison rend les trois quarts de son énergie (patch312). Une défense".replace(" (patch312)", ""))
s = rep(s, "</b>. L'attaquant voit qu'une commune est en garnison, pas combien elle contient.</p>",
           "</b>. L'attaquant voit qu'une commune est en garnison, pas combien elle contient.</p><!-- patch312 -->")
f.write_text(s, encoding='utf-8')
print('patch312 appliqué')
