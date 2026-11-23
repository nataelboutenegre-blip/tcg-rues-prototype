# patch516 : les motifs ne s'effacent plus quand on dézoome (signalé par ASMFCB, 23/11).
# Avant : invisibles sous 3 px/km, entiers à 8 px/km (sur téléphone : rien avant ×10 environ, entier vers ×28).
# Depuis patch512 les départements montrent déjà le motif de loin : on le garde donc presque à tout zoom
# (entier dès 1 px/km, soit ×3,5 environ sur téléphone ; un peu plus pâle juste au passage départements → communes).
import os, sys, json
R = sys.argv[1] if len(sys.argv) > 1 else '.'
def rep(f, a, b, n=1):
    p = os.path.join(R, f); t = open(p, encoding='utf-8').read()
    if t.count(a) != n:
        if b in t: print(f'{f} : déjà fait'); return
        raise SystemExit(f'{f} : {t.count(a)} occurrence(s) pour {a[:80]!r}')
    open(p, 'w', encoding='utf-8').write(t.replace(a, b)); print(f'{f} : ok')
rep('app.js', "const MOT_VIS_DEBUT = 3, MOT_VIS_PLEIN = 8;   // en pixels par kilomètre : en dessous le motif est caché, au-dessus il est entier",
              "const MOT_VIS_DEBUT = 0, MOT_VIS_PLEIN = 1;   // en pixels par kilomètre ; patch516 : visible presque à tout zoom (avant 3 et 8)")
rep('app.js', "De loin, le motif s'efface pour que les raretés, les clans et les bâtiments restent lisibles.</p>",
              "Il se voit à tous les niveaux de zoom ; de loin, il couvre les départements où tu es en tête.</p>")
p = os.path.join(R, 'data', 'nouveautes.json'); d = json.load(open(p, encoding='utf-8'))
if d[0].get('date') != '2026-11-23': d.insert(0, {'date': '2026-11-23', 'nouveautes': []})
e = d[0]; e.setdefault('correctifs', [])
l = "Motifs : ils ne s'effacent plus quand on dézoome la carte (signalé par ASMFCB)."
if l not in e['correctifs']: e['correctifs'].insert(0, l)
json.dump(d, open(p, 'w', encoding='utf-8'), ensure_ascii=False, indent=2); print('nouveautes.json : ok')
