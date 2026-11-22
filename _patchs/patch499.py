# patch499 : les skins passent aux cartes v2 (signalé par Maroli, « let's go » de Nataël 22/11 19 h 44).
# - Le dessin du skin (WebGL) agrandit la photo comme les cartes v2 : 64 % de la hauteur au lieu de 41 %
#   (photoRect 116 → 182 sur H = 285). Chaque skin dessine autour de ce rectangle : rien d'autre à changer.
#   Seulement quand les cartes v2 sont allumées (html.topo sans .sans-cartes) ; sinon l'ancien dessin.
# - Le nom passe en bas de la photo, le numéro du département dans une petite plaque en haut à droite,
#   la rareté avec sa pastille de couleur. La typographie propre à chaque skin (Néon, Gravure, Or fondu…) est gardée.
import os, sys, json
R = sys.argv[1] if len(sys.argv) > 1 else '.'
ICI = os.path.dirname(os.path.abspath(__file__))
def rep(f, a, b, n=1):
    p = os.path.join(R, f); t = open(p, encoding='utf-8').read()
    if t.count(a) != n:
        if b in t: print(f'{f} : déjà fait ({a[:50]!r})'); return
        raise SystemExit(f'{f} : {t.count(a)} occurrence(s) au lieu de {n} pour {a[:80]!r}')
    open(p, 'w', encoding='utf-8').write(t.replace(a, b)); print(f'{f} : ok ({a[:50]!r})')
A = 'app.js'
rep(A, "gl.shaderSource(fs, SKIN_GLSL_COMMUN + (v2 ? SKIN_GLSL_V2[k] : SKIN_GLSL[k]) + SKIN_GLSL_FIN);",
       "gl.shaderSource(fs, skinCommun() + (v2 ? SKIN_GLSL_V2[k] : SKIN_GLSL[k]) + SKIN_GLSL_FIN);   // patch499")
rep(A, "const SKIN_GLSL_COMMUN = DOS_GLSL_COMMUN",
       "// patch499 : avec les cartes v2, la photo du skin prend 64 % de la hauteur (182 sur 285), comme les autres cartes\n"
       "function skinCommun(){ const h = document.documentElement.classList; return h.contains('topo') && !h.contains('sans-cartes')\n"
       "  ? SKIN_GLSL_COMMUN.replace('vec4 photoRect(float b){ return vec4(5.2,5.2,W-5.2,116.); }', 'vec4 photoRect(float b){ return vec4(5.2,5.2,W-5.2,182.); }') : SKIN_GLSL_COMMUN; }\n"
       "const SKIN_GLSL_COMMUN = DOS_GLSL_COMMUN")
p = os.path.join(R, 'style.css'); t = open(p, encoding='utf-8').read()
css = open(os.path.join(ICI, 'patch499-style.css'), encoding='utf-8').read()
if css.split('\n')[0] in t: print('style.css : déjà fait')
else: open(p, 'w', encoding='utf-8').write(t.rstrip('\n') + '\n\n' + css); print('style.css : ok')
p = os.path.join(R, 'data', 'nouveautes.json'); d = json.load(open(p, encoding='utf-8'))
e = next(x for x in d if x.get('date') == '2026-11-22')
for l in ["🎨 Les skins passent au nouveau design des cartes : grande photo, nom posé dessus, département en haut à droite (signalé par Maroli).",
          "🎮 Duels classés (Plus ou moins, Rafale, Radar) : une égalité ne change plus l'Elo (idée de Maroli)."]:
    if l not in e['nouveautes']: e['nouveautes'].insert(0, l)
json.dump(d, open(p, 'w', encoding='utf-8'), ensure_ascii=False, indent=2); print('nouveautes.json : ok')
