# patch547 : Espagne (test) : trois petits trous entre communes au sud de Burgos (terres sans commune) étaient dessinés comme une côte.
# On retire ces anneaux de espagne-terre.json et espagne-frontiere.json (îles, Llívia et îlots gardés) ; fichiers en ?v=2.
import os, sys, json
R = sys.argv[1] if len(sys.argv) > 1 else '.'
def rep(f, a, b, n=1):
    p = os.path.join(R, f); t = open(p, encoding='utf-8').read()
    if t.count(a) != n:
        if b in t: print(f'{f} : déjà fait'); return
        raise SystemExit(f'{f} : {t.count(a)} occurrence(s) pour {a[:80]!r}')
    open(p, 'w', encoding='utf-8').write(t.replace(a, b)); print(f'{f} : ok')
def trou(r):   # les trois anneaux entre -3.35 et -3.10 de longitude, 41.9 et 42.1 de latitude
    cx = sum(p[0] for p in r) / len(r); cy = sum(p[1] for p in r) / len(r)
    return -3.35 < cx < -3.10 and 41.9 < cy < 42.1 and len(r) < 20
for f in ['data/espagne-terre.json', 'data/espagne-frontiere.json']:
    p = os.path.join(R, f); d = json.load(open(p))
    e = [r for r in d if not trou(r)]
    if len(d) - len(e) not in (0, 3): raise SystemExit(f'{f} : {len(d) - len(e)} anneaux retirés, 3 attendus')
    json.dump(e, open(p, 'w'), separators=(',', ':')); print(f, len(d), '->', len(e))
rep('app.js', "const lire = (f) => fetch('data/' + f + (f === 'voisins.json' ? '?v=2' : '?v=1'), { cache: 'force-cache' })",
    "const lire = (f) => fetch('data/' + f + (['voisins.json', 'espagne-terre.json', 'espagne-frontiere.json'].includes(f) ? '?v=2' : '?v=1'), { cache: 'force-cache' })   /* patch547 */")
