# patch549 : ordinateur sans pavé tactile : la molette fait défiler les rangées horizontales (catégories du motif, filtres, onglets),
# et une fine barre de défilement apparaît sous ces rangées.
import os, sys, json
R = sys.argv[1] if len(sys.argv) > 1 else '.'
D = os.path.dirname(os.path.abspath(__file__))
def ajouter(f, src, marque):
    p = os.path.join(R, f); t = open(p, encoding='utf-8').read()
    if marque in t: print(f'{f} : déjà ajouté'); return
    open(p, 'a', encoding='utf-8').write(open(os.path.join(D, src), encoding='utf-8').read()); print(f'{f} : ajouté')
ajouter('app.js', 'patch549-molette.js', 'patch549 : sur ordinateur, la molette')
ajouter('style.css', 'patch549.css', 'patch549 : sur ordinateur, une fine barre')
p = os.path.join(R, 'data/nouveautes.json'); d = json.load(open(p, encoding='utf-8'))
assert d[0]['date'] == '2026-11-26'
c1 = "Sur ordinateur avec une souris : la molette fait maintenant défiler les rangées qui glissent sur le côté (catégories du motif, filtres, onglets)."
if c1 not in d[0].setdefault('correctifs', []): d[0]['correctifs'].append(c1)
json.dump(d, open(p, 'w', encoding='utf-8'), ensure_ascii=False, indent=1); print('nouveautes : ok')
