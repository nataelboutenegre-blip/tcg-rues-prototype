# patch509 : échanges de clan — la recherche accepte plusieurs départements séparés par des virgules (« 25, 90, 70, 39 »,
# « 2A, 2B »), un nom de département ou de région, comme la collection (correspondUnTerme, patch142). Idée d'Arkhannou.
# Avant : un seul département, tapé exactement, ou un morceau du nom de la commune.
import os, sys, json
R = sys.argv[1] if len(sys.argv) > 1 else '.'
def rep(f, a, b, n=1):
    p = os.path.join(R, f); t = open(p, encoding='utf-8').read()
    if t.count(a) != n:
        if b in t: print(f'{f} : déjà fait'); return
        raise SystemExit(f'{f} : {t.count(a)} occurrence(s) pour {a[:80]!r}')
    open(p, 'w', encoding='utf-8').write(t.replace(a, b)); print(f'{f} : ok')
rep('app.js', "  const l = liste.filter(c => !f || sansAccents(c.nom.toLowerCase()).includes(f) || String(c.departement).toLowerCase() === f);",
              "  const l = liste.filter(c => !f || correspondUnTerme(c.nom, c.departement, f));   // patch509 : « 25, 90, 70 »")
rep('app.js', 'placeholder="Une de tes communes…"', 'placeholder="Commune ou départements : 25, 90…"')
rep('app.js', 'placeholder="Une commune de ton coéquipier…"', 'placeholder="Commune ou départements : 2A, 2B…"')
p = os.path.join(R, 'data', 'nouveautes.json'); d = json.load(open(p, encoding='utf-8'))
e = d[0]; e.setdefault('nouveautes', [])
l = "🤝 Échanges de clan : la recherche accepte plusieurs départements à la fois (« 25, 90, 70, 39 »), un nom de département ou une région. Idée d'Arkhannou."
if l not in e['nouveautes']: e['nouveautes'].insert(0, l)
json.dump(d, open(p, 'w', encoding='utf-8'), ensure_ascii=False, indent=2); print('nouveautes.json : ok')
