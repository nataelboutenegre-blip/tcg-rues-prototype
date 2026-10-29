# patch266 : la pastille de la cloche affichait « 0 » (remarque d'Oshannir) : display:flex passait devant [hidden]
import pathlib
f = pathlib.Path('style.css'); s = f.read_text(encoding='utf-8')
assert 'patch266' not in s
a = ".nc-voile{ position:fixed; inset:0;"
assert s.count(a) == 1
s = s.replace(a, "/* patch266 : rien de neuf = pas de pastille (avant, « 0 » restait affiché) */\n.nc-cloche .nc-pastille[hidden]{ display:none; }\n" + a)
f.write_text(s, encoding='utf-8')
print('patch266 appliqué')
