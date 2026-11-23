# patch521 : Défendre — « au plus X points par heure » devient « se remplit en 15 h au plus vite » (question de Cairnan217).
# Les points par heure trompaient : avec une Forteresse (résistance ×1,5), la jauge avance de plus de points par heure
# mais en a plus à remplir ; la durée, elle, ne change pas.
import os, sys, json
R = sys.argv[1] if len(sys.argv) > 1 else '.'
def rep(f, a, b, n=1):
    p = os.path.join(R, f); t = open(p, encoding='utf-8').read()
    if t.count(a) != n:
        if b in t: print(f'{f} : déjà fait'); return
        raise SystemExit(f'{f} : {t.count(a)} occurrence(s) pour {a[:80]!r}')
    open(p, 'w', encoding='utf-8').write(t.replace(a, b)); print(f'{f} : ok')
rep('app.js', "const etat = m.long ? `<b class=\"sg-long\">Siège long</b> · au plus ${sgNb(m.rythme_h)} points par heure`",
              "const etat = m.long ? `<b class=\"sg-long\">Siège long</b> · ${Number(m.rythme_h) > 0 && res > 0 ? `se remplit en ${sgDuree(Math.round(res / Number(m.rythme_h) * 60))} au plus vite` : 'se remplit lentement'}`")
p = os.path.join(R, 'data', 'nouveautes.json'); d = json.load(open(p, encoding='utf-8'))
e = d[0]; e.setdefault('correctifs', [])
l = "Défendre : un siège long affiche sa durée (« se remplit en 15 h au plus vite ») au lieu de points par heure, qui faisaient croire qu'une Forteresse accélérait le siège (signalé par Cairnan217)."
if l not in e['correctifs']: e['correctifs'].insert(0, l)
json.dump(d, open(p, 'w', encoding='utf-8'), ensure_ascii=False, indent=2); print('nouveautes.json : ok')
