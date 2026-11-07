# patch370 (7/11/2026) : les textes des bombes plus grosses (s2-114), et les
# nouveautés du 7/11 dans la cloche.
#
# s2-114 : 15 km à 24 h, 20 km à 36 h, 25 km à 48 h ; Centre visible à 36 h ;
# 30 km d'écart entre deux bombes. Le jeu lit déjà ces réglages du serveur
# (mes_batiments : bombe_heures, bombe_rayons, bombe_devoile_h, bombe_ecart_km) ;
# restent les textes écrits en dur (règles, fiche du Centre) et les valeurs de
# repli.
import json, pathlib

def rep(s, avant, apres, n=1):
    c = s.count(avant)
    assert c == n, f'{c} fois au lieu de {n} : {avant[:70]!r}'
    return s.replace(avant, apres)

F = pathlib.Path('app.js'); s = F.read_text(encoding='utf-8')
assert 'patch370' not in s, 'patch370 déjà appliqué'
s = rep(s, """// Le centre est secret (dévoilé à partir de 48 h de préparation et 24 h après
// le lâcher). « Préparer une bombe » coûte 45 lingots ; la bombe grossit avec
// le temps (10, 15, 20 km). On la lâche depuis la mallette de frappe.""",
"""// Le centre est secret (dévoilé à partir de 36 h de préparation et 24 h après
// le lâcher). « Préparer une bombe » coûte 45 lingots ; la bombe grossit avec
// le temps (15, 20, 25 km à 24, 36, 48 h, patch370). On la lâche depuis la mallette de frappe.""")
s = rep(s, "const H = btReglage('bombe_heures', [24, 48, 72]), R = btReglage('bombe_rayons', [10, 15, 20]);",
           "const H = btReglage('bombe_heures', [24, 36, 48]), R = btReglage('bombe_rayons', [15, 20, 25]);   // patch370")
s = rep(s, "dv = btReglage('bombe_devoile_h', 48);", "dv = btReglage('bombe_devoile_h', 36);   // patch370")
s = rep(s, "btReglage('bombe_ecart_km', 20)", "btReglage('bombe_ecart_km', 30)")
s = rep(s, "'Il est secret, mais apparaît sur la carte après <b>48 h</b> de préparation, et reste visible 24 h après l’impact.',",
           "'Il est secret, mais apparaît sur la carte après <b>36 h</b> de préparation, et reste visible 24 h après l’impact.',   // patch370")
s = rep(s, "dans sa zone (jusqu’à 20 km), et tout le monde",
           "dans sa zone (jusqu’à 25 km), et tout le monde")
F.write_text(s, encoding='utf-8')

H = pathlib.Path('index.html'); h = H.read_text(encoding='utf-8')
assert 'patch370' not in h
h = rep(h, """La bombe est prête en 24 h (rayon 10 km), puis grossit : 15 km à 48 h, 20 km à 72 h. À partir de 48 h de préparation, ton centre apparaît sur la carte""",
"""La bombe est prête en 24 h (rayon 15 km), puis grossit : 20 km à 36 h, 25 km à 48 h. À partir de 36 h de préparation, ton centre apparaît sur la carte""")
h = rep(h, """Pas de bombe à moins de 20 km d'une zone encore active.</p>""",
"""Pas de bombe à moins de 30 km d'une zone encore active.</p><!-- patch370 -->""")
H.write_text(h, encoding='utf-8')

N = pathlib.Path('data/nouveautes.json'); L = json.loads(N.read_text(encoding='utf-8'))
assert L[0]['date'] != '2026-11-07', 'nouveautés du 7/11 déjà là'
L.insert(0, {
  "date": "2026-11-07",
  "nouveautes": [
    "💣 Bombes plus grosses et plus rapides : 15 km de rayon à 24 h, 20 km à 36 h, 25 km à 48 h (au lieu de 10, 15 et 20 km à 24, 48 et 72 h). Le Centre apparaît sur la carte à 36 h de préparation. Pas de 2e bombe à moins de 30 km d’une zone encore active",
    "🍀 Série noire : après 2 assauts perdus d’affilée sur une même commune, les suivants ont +15 % jusqu’à ta prochaine victoire dessus (90 % au plus, pas contre une garnison)",
    "🌱 Bonus de débutant : pendant tes 7 premiers jours et jusqu’à ta première conquête, au moins 85 % par assaut, même loin de chez toi (pas contre une garnison). Sans commune, « Choisir sur la carte » te propose une cible près de chez toi",
    "🏗 Bâtiments en pixel art : une case « Mes bâtiments » dans Mon front, avec ceux des autres joueurs (recherche, région, type). Choisis le style de chaque bâtiment quand tu le construis",
    "🔎 Recherche par région : « bretagne », « grand est », « idf », « paca »… dans Combat, la Collection, l’Échange et les exclusions"
  ],
  "correctifs": [
    "La recherche « corse » trouve la Corse-du-Sud et la Haute-Corse (Combat ne montrait que le 2A)"
  ]
})
N.write_text(json.dumps(L, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
print('patch370 appliqué')
