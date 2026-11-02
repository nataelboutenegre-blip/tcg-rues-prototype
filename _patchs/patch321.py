# patch321 : retouches des Aurore après les retours de Maroli (2/11 au soir)
#  1. Le n° du département : plus d'ombre (à travers un chiffre translucide, elle faisait
#     un double chiffre sale), juste un blanc léger.
#  2. Le reflet : sur les petites cartes il est plus discret (0,3 → 0,16) ; dans la fiche il
#     n'apparaît que quand on incline la carte, plus fort à mesure qu'on l'incline, et
#     disparaît au repos (fini la bande brillante au milieu).
#  3. Sur ordinateur à écran normal (souris, moins de 1,5 pixel par point), l'aurore de la
#     fiche reste immobile comme avant patch318 : la carte y est agrandie 1,65 fois et
#     l'animation empêche le navigateur de la redessiner nette.
import pathlib

def rep(s, a, b, n=1):
    assert s.count(a) == n, (s.count(a), a[:100])
    return s.replace(a, b)

f = pathlib.Path('style.css'); s = f.read_text(encoding='utf-8')
assert 'patch321' not in s
s = rep(s, """.mini.aurore .mini-dept{ color:rgba(255,255,255,.42); text-shadow:0 1px 2px rgba(0,0,0,.3); }""",
           """.mini.aurore .mini-dept{ color:rgba(255,255,255,.34); text-shadow:none; }   /* patch321 : sans ombre (double chiffre) */""")
s = rep(s, """.c3d .mini.aurore .au-reflet{ --hx:calc(35% + var(--gx, 50%) * .3); opacity:.42; }
""", """/* patch321 : le reflet ne vient qu'en inclinant la carte (0 au repos, 0,3 incliné à fond) */
.mini .au-reflet{ opacity:.16; }
.c3d .mini.aurore .au-reflet{ --hx:calc(35% + var(--gx, 50%) * .3); opacity:calc(max(var(--gx, 50%) - 50%, 50% - var(--gx, 50%)) * .6); }
/* patch321 : sur ordinateur à écran normal, l'aurore de la fiche reste immobile (sinon la carte agrandie est floue) */
@media (hover: hover) and (pointer: fine) and (max-resolution: 1.49dppx){
  .c3d .mini.aurore .au-voile i:nth-child(n), .c3d .mini.aurore .au-etoiles i{ animation:none; }
}
""")
f.write_text(s, encoding='utf-8')
print('patch321 ok')
