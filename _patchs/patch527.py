# patch527 : bouclier de garnison 12 points par ⚡ (s3-66, partie 3).
import os, sys, json
R = sys.argv[1] if len(sys.argv) > 1 else '.'
def rep(f, a, b, n=1):
    p = os.path.join(R, f); t = open(p, encoding='utf-8').read()
    if t.count(a) != n:
        if b in t: print(f'{f} : déjà fait'); return
        raise SystemExit(f'{f} : {t.count(a)} occurrence(s) pour {a[:80]!r}')
    open(p, 'w', encoding='utf-8').write(t.replace(a, b)); print(f'{f} : ok')
rep('app.js', "fait un bouclier de 10 points, à casser avant la jauge.", "fait un bouclier de 12 points, à casser avant la jauge.")
rep('index.html', "(1 ⚡ de garnison arrête 10 points de dégâts)", "(1 ⚡ de garnison arrête 12 points de dégâts)")
rep('index.html', "de <b>10 points par énergie</b> (100 au plus)", "de <b>12 points par énergie</b> (120 au plus)")
p = os.path.join(R, 'data', 'nouveautes.json'); d = json.load(open(p, encoding='utf-8'))
l = d[0]['nouveautes']
a = "⚡ Front : conquérir coûte moins cher. Chaque énergie fait 12 points au lieu de 10 (en attaque comme en renfort), et poser un siège coûte 1 ⚡ au lieu de 2."
b = "⚡ Front : conquérir coûte moins cher. Chaque énergie fait 12 points au lieu de 10 (en attaque, en renfort et en garnison), et poser un siège coûte 1 ⚡ au lieu de 2."
if a in l: l[l.index(a)] = b
json.dump(d, open(p, 'w', encoding='utf-8'), ensure_ascii=False, indent=2); print('nouveautes.json : ok')
