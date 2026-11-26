# patch551 (s3-84) : les formes du motif de territoire sont toutes gratuites : plus de « à toi » ni de prix dans l'éditeur.
import os, sys, json
R = sys.argv[1] if len(sys.argv) > 1 else '.'
def rep(f, a, b, n=1):
    p = os.path.join(R, f); t = open(p, encoding='utf-8').read()
    if t.count(a) != n:
        if b in t: print(f'{f} : déjà fait'); return
        raise SystemExit(f'{f} : {t.count(a)} occurrence(s) pour {a[:80]!r}')
    open(p, 'w', encoding='utf-8').write(t.replace(a, b)); print(f'{f} : ok')
rep('app.js', "  pk.innerHTML = packs.length ? packs.map(p => motPossede({ pack: p })", "  pk.innerHTML = packs.some(p => !motPossede({ pack: p })) ? packs.map(p => motPossede({ pack: p })")   # patch551 : tout possédé → « Gratuit pour tous. »
rep('app.js', "(motPossede(f) ? 'À toi' : MOT_PACKS[f.pack]", "(motPossede(f) ? 'Changer ›' : MOT_PACKS[f.pack]")
p = os.path.join(R, 'data/nouveautes.json'); d = json.load(open(p, encoding='utf-8'))
assert d[0]['date'] == '2026-11-26'
n1 = "🖌️ Motif de territoire : toutes les formes sont maintenant gratuites, pour tout le monde (Héraldique, Nature, Cartographe, Tissus compris)."
if n1 not in d[0]['nouveautes']: d[0]['nouveautes'].append(n1)
json.dump(d, open(p, 'w', encoding='utf-8'), ensure_ascii=False, indent=1); print('nouveautes : ok')
