# patch302 : la fiche d'une commune ne défilait pas au doigt (1/11) — signalé par Arkhannou (Android, Chrome)
# La fiche (#mapPanneau) est posée dans le cadre de la carte, et le cadre bloque tout glissé du doigt
# (touchmove + preventDefault) pour déplacer la carte : glisser sur la fiche déplaçait la carte derrière
# au lieu de faire défiler la fiche. Visible depuis que la fiche est longue (garnison, Fonderie,
# bâtiments) : le bas (Forteresse, Centre de recherche) restait inaccessible.
# Correctif : les gestes commencés sur la fiche ou sur la légende ne sont plus pris par la carte.
import json, pathlib

def rep(s, a, b, n=1):
    assert s.count(a) == n, (s.count(a), a[:100])
    return s.replace(a, b)

f = pathlib.Path('app.js'); s = f.read_text(encoding='utf-8')
assert 'patch302' not in s
s = rep(s, """  // --- Tactile : un doigt = deplacer, deux doigts = pincer pour zoomer ---
  wrap.addEventListener('touchstart', (e) => {
    const rect = wrap.getBoundingClientRect();""",
"""  // --- Tactile : un doigt = deplacer, deux doigts = pincer pour zoomer ---
  // patch302 : un geste commencé sur la fiche ou la légende leur appartient (elles défilent)
  const gesteHorsCarte = (e) => !!(e.target && e.target.closest && e.target.closest('#mapPanneau, #mapLegende'));
  wrap.addEventListener('touchstart', (e) => {
    if(gesteHorsCarte(e)){ mapDragging = false; touchPinch = null; return; }   // patch302
    const rect = wrap.getBoundingClientRect();""")
s = rep(s, """  wrap.addEventListener('touchmove', (e) => {
    e.preventDefault();
    if(touchPinch && e.touches.length === 2){""",
"""  wrap.addEventListener('touchmove', (e) => {
    if(gesteHorsCarte(e)) return;   // patch302 : laisser défiler la fiche
    e.preventDefault();
    if(touchPinch && e.touches.length === 2){""")
s = rep(s, """  wrap.addEventListener('touchend', (e) => {
    if(e.touches.length === 1){""",
"""  wrap.addEventListener('touchend', (e) => {
    if(gesteHorsCarte(e)) return;   // patch302
    if(e.touches.length === 1){""")
f.write_text(s, encoding='utf-8')

f = pathlib.Path('style.css'); s = f.read_text(encoding='utf-8')
assert 'patch302' not in s
s = rep(s, "  .map-wrap.plein-ecran .pc{ max-height: calc(100% - 66px - env(safe-area-inset-top, 0px)); }\n}\n",
           "  .map-wrap.plein-ecran .pc{ max-height: calc(100% - 66px - env(safe-area-inset-top, 0px)); }\n}\n"
           "/* patch302 : la fiche défile au doigt sans entraîner la page */\n"
           ".pc{ overscroll-behavior:contain; -webkit-overflow-scrolling:touch; }\n")
f.write_text(s, encoding='utf-8')

f = pathlib.Path('data/nouveautes.json'); d = json.loads(f.read_text(encoding='utf-8'))
e = next(x for x in d if x['date'] == '2026-11-01')
e['correctifs'].insert(0, 'Sur téléphone, la fiche d’une commune défile de nouveau au doigt (le bas, avec les bâtiments, restait inaccessible)')
f.write_text(json.dumps(d, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
print('patch302 appliqué')
