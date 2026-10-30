# patch274 : l'éclair de l'énergie dans le bloc « Libérer des communes » (Défendre) s'affichait en géant
# (patch273 ne donnait une taille à l'icône que dans la fiche et dans l'écran « Libérer plusieurs »).
import pathlib
f = pathlib.Path('style.css'); s = f.read_text(encoding='utf-8')
assert 'patch274' not in s
a = ".lib-fiche svg, .lib-ecran svg{ width:12px; height:12px; vertical-align:-1px; }"
assert s.count(a) == 1
s = s.replace(a, ".lib-fiche svg, .lib-ecran svg, .lib-entree svg{ width:12px; height:12px; vertical-align:-1px; }   /* patch274 : + .lib-entree */")
f.write_text(s, encoding='utf-8')
print('patch274 appliqué')
