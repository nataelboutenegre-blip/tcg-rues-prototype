# patch247 : « Voir tout » du classement affiche 100 joueurs au lieu de 50
import pathlib
f = pathlib.Path('app.js'); s = f.read_text(encoding='utf-8')
a = "const limite = classementComplet ? 50 : 10;"
assert s.count(a) == 1
s = s.replace(a, "const limite = classementComplet ? 100 : 10;   // patch247 : 50 -> 100")
f.write_text(s, encoding='utf-8'); print('patch247 ok')
