# patch501 : va avec s3-54. Commune 5 min, peu commune 10 min en siège éclair : les textes suivent.
import os, sys, json
R = sys.argv[1] if len(sys.argv) > 1 else '.'
def rep(f, a, b, n=1):
    p = os.path.join(R, f); t = open(p, encoding='utf-8').read()
    if t.count(a) != n:
        if b in t: print(f'{f} : déjà fait'); return
        raise SystemExit(f'{f} : {t.count(a)} occurrence(s) pour {a[:80]!r}')
    open(p, 'w', encoding='utf-8').write(t.replace(a, b)); print(f'{f} : ok')
rep('app.js', "function sgEclairTxt(tier){ return tier === 'rare' ? 'elle peut tomber 20 min après le début' : tier === 'epique' ? 'elle peut tomber 1 h après le début' : 'elle peut tomber d\\'un coup'; }",
    "const SG_ECLAIR_MIN = { commun: 5, peucommun: 10, rare: 20, epique: 60 };   // patch501 (s3-54)\n"
    "function sgEclairTxt(tier){ const m = SG_ECLAIR_MIN[tier]; return m ? 'elle peut tomber ' + sgDuree(m) + ' après le début' : 'elle peut tomber d\\'un coup'; }")
p = os.path.join(R, 'data', 'nouveautes.json'); d = json.load(open(p, encoding='utf-8'))
e = next(x for x in d if x.get('date') == '2026-11-22')
l = "⏱️ Sièges éclair : une commune ne tombe plus d'un coup. Il faut au moins 5 min pour une commune et 10 min pour une peu commune, le temps pour le propriétaire de défendre."
if l not in e['nouveautes']: e['nouveautes'].insert(0, l)
json.dump(d, open(p, 'w', encoding='utf-8'), ensure_ascii=False, indent=2); print('nouveautes.json : ok')
