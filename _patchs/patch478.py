# patch478 : la jauge de l'assaut suit le pourcentage affiché quand une garnison défend (signalé par ASMFCB, 20/11).
# Avant : la zone verte faisait 70 % (les dés) alors que « Tes chances » disait 35 %.
# Maintenant : vert plein = les vraies chances (35 %), hachuré ambre = victoires aux dés que la garnison annule (35 à 70 %),
# rouge = défaite. L'aiguille se pose dans la bonne zone.
import os, sys
R = sys.argv[1] if len(sys.argv) > 1 else '.'
def rep(f, a, b, n=1):
    p = os.path.join(R, f); t = open(p, encoding='utf-8').read()
    if t.count(a) != n:
        if b in t: print(f'{f} : déjà fait ({a[:50]!r})'); return
        raise SystemExit(f'{f} : {t.count(a)} occurrence(s) au lieu de {n} pour {a[:80]!r}')
    open(p, 'w', encoding='utf-8').write(t.replace(a, b)); print(f'{f} : ok ({a[:50]!r})')
A = 'app.js'
rep(A, """  const arret = res === 'ko' && !parGarnison ? chances + (100 - chances) * (0.25 + Math.random() * 0.6)   // patch393
                             : chances * (0.15 + Math.random() * 0.7);""",
"""  const arret = res === 'ko' && !parGarnison ? chances + (100 - chances) * (0.25 + Math.random() * 0.6)   // patch393
                             : !garn ? chances * (0.15 + Math.random() * 0.7)
                             : parGarnison ? chances * (0.58 + Math.random() * 0.34)   // patch478 : dans le hachuré
                             : chances * (0.08 + Math.random() * 0.34);   // patch478 : dans le vert plein""")
rep(A, """<div class="as-cadran"><div class="as-zone" style="width:${chances}%"></div><div class="as-aiguille"></div></div>""",
"""<div class="as-cadran">${garn ? `<div class="as-zone-garn" style="left:${chances / 2}%;width:${chances / 2}%"></div><div class="as-zone" style="width:${chances / 2}%"></div>` : `<div class="as-zone" style="width:${chances}%"></div>`}<div class="as-aiguille"></div></div>""")
rep('style.css', ".as-aiguille{ position:absolute;",
""".as-zone-garn{ position:absolute; top:0; bottom:0; background: repeating-linear-gradient(-45deg, rgba(240,180,41,.55) 0 5px, rgba(240,180,41,.22) 5px 10px); }   /* patch478 */
.as-aiguille{ position:absolute;""")
print('patch478 : fini')
