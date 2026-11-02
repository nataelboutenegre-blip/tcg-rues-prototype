# patch318 : les cartes Aurore retravaillées (idée de Maroli, aperçu validé le 2/11, version A)
#  1. Le nom passe en bas, puis le n° à gauche et la rareté à droite (aux couleurs de la
#     rareté) ; le fondu sombre ne couvre plus que le bas, sous le texte : la photo respire.
#     Le numéro du département ressort un peu plus sur les ciels clairs.
#  2. Le liseré bleu-blanc-rouge devient un liseré aux couleurs de l'aurore (l'outre-mer a
#     déjà le sien) : on repère ses Aurore d'un coup d'œil dans la collection.
#  3. Dans la fiche (la carte en grand), l'Aurore s'anime comme au tirage : le voile dérive,
#     les étoiles scintillent, et le reflet irisé suit le doigt quand on incline la carte.
#     La grille de la collection reste immobile (coût), et « réduire les animations » est respecté.
#  Seulement du CSS, sur les petites cartes Aurore (collection, fiche, vitrine, résultats de
#  tirage). La grande carte du tirage ne change pas.
import pathlib

def rep(s, a, b, n=1):
    assert s.count(a) == n, (s.count(a), a[:100])
    return s.replace(a, b)

f = pathlib.Path('style.css'); s = f.read_text(encoding='utf-8')
assert 'patch318' not in s

# 1. la mise en page : textes en bas, fondu court
s = rep(s, """.mini.aurore .mini-dept{ color:rgba(255,255,255,.22); text-shadow:none; }
.mini.aurore .mini-infos{ background:linear-gradient(180deg, rgba(5,10,24,0), rgba(5,10,24,.8) 40%, rgba(5,10,24,.9)); }
.mini.aurore .mini-nom{ color:#fff; }
.mini.aurore .mini-num{ color:rgba(255,255,255,.7); }
.mini.aurore .mini-rarete{ color:#fff; }
""", """/* patch318 (idée de Maroli) : le nom en bas, puis n° à gauche et rareté à droite ; le fondu
   ne couvre plus que le bas de la carte. Si la ligne est trop étroite, la rareté passe dessous, à gauche. */
.mini.aurore .mini-dept{ color:rgba(255,255,255,.42); text-shadow:0 1px 2px rgba(0,0,0,.3); }
.mini.aurore .mini-infos{ flex-direction:row; flex-wrap:wrap; align-content:flex-end; align-items:baseline; justify-content:space-between; column-gap:4px;
  background:linear-gradient(180deg, rgba(5,10,24,0) 42%, rgba(5,10,24,.22) 53%, rgba(5,10,24,.56) 65%, rgba(5,10,24,.8) 78%, rgba(5,10,24,.9)); }
.mini.aurore .mini-nom{ color:#fff; flex-basis:100%; text-shadow:0 1px 6px rgba(0,0,0,.55); }
.mini.aurore .mini-num{ color:rgba(255,255,255,.7); min-width:0; }
.mini.aurore .mini-rarete{ color:color-mix(in srgb, var(--au-t) 45%, #fff); flex:none; margin:0; }
/* patch318 : le liseré aux couleurs de l'aurore */
.mini.aurore .mini-lisere{ background:linear-gradient(90deg, var(--au-a1), var(--au-a2) 50%, var(--au-a3)); box-shadow:0 0 8px color-mix(in srgb, var(--au-a2) 70%, transparent); }
.mini.aurore .mini-int .mini-lisere span:nth-child(n){ background:transparent; }
""")

# 3. la fiche : l'aurore s'anime (la règle qui coupe l'animation des petites cartes reste pour la grille)
s = rep(s, """.mini .au-voile i, .mini .au-etoiles i{ animation:none; }
""", """.mini .au-voile i, .mini .au-etoiles i{ animation:none; }
/* patch318 : sauf dans la fiche (une seule carte, en grand) : l'Aurore bouge comme au tirage,
   et son reflet suit l'inclinaison (entre 35 et 65 % : au-delà, le dégradé du reflet se casse) */
.c3d .mini.aurore .au-voile i:nth-child(1){ animation:auOndule1 9s ease-in-out infinite alternate; }
.c3d .mini.aurore .au-voile i:nth-child(2){ animation:auOndule2 12s ease-in-out infinite alternate; }
.c3d .mini.aurore .au-voile i:nth-child(3){ animation:auOndule3 15s ease-in-out infinite alternate; }
.c3d .mini.aurore .au-etoiles i{ animation:auScintille 3.2s ease-in-out infinite; }
.c3d .mini.aurore .au-reflet{ --hx:calc(35% + var(--gx, 50%) * .3); opacity:.42; }
""")

f.write_text(s, encoding='utf-8')
print('patch318 ok')
