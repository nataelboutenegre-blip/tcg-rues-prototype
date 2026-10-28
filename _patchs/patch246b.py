# patch246b : règles — en outre-mer, tout le territoire compte comme voisin (s2-49)
import pathlib
f = pathlib.Path('index.html'); s = f.read_text(encoding='utf-8')
a = "et tenir des communes voisines aide aussi."
assert s.count(a) == 1, s.count(a)
s = s.replace(a, "et tenir des communes voisines aide aussi : en outre-mer, toutes tes communes du même territoire comptent comme voisines, même loin.")
f.write_text(s, encoding='utf-8'); print('patch246b ok')
