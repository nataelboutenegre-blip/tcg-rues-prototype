# patch496 : la cloche de l'attaquant dit « il manque ≈ N ⚡ » quand une défense a fait que l'énergie qui attend
# dans son siège ne suffit plus (s3-50, question de Cairnan217). Le serveur envoie aussi une notification à ce moment-là.
import os, sys, json
R = sys.argv[1] if len(sys.argv) > 1 else '.'
def rep(f, a, b, n=1):
    p = os.path.join(R, f); t = open(p, encoding='utf-8').read()
    if t.count(a) != n:
        if b in t: print(f'{f} : déjà fait ({a[:50]!r})'); return
        raise SystemExit(f'{f} : {t.count(a)} occurrence(s) au lieu de {n} pour {a[:80]!r}')
    open(p, 'w', encoding='utf-8').write(t.replace(a, b)); print(f'{f} : ok ({a[:50]!r})')
A = 'app.js'
rep(A, "s: `−${fr(a.recul)} sur ta jauge${jauge}${a.devient_long ? ' · le siège devient long' : ''} · ${ilYA(a.le)}`,",
       "s: `−${fr(a.recul)} sur ta jauge${jauge}${a.devient_long ? ' · le siège devient long' : ''}${a.manque && a.ouvert ? ` · <b>il manquait ≈ ${fr(a.manque)} ⚡</b> pour finir` : ''} · ${ilYA(a.le)}`,   // patch496")
p = os.path.join(R, 'data', 'nouveautes.json'); d = json.load(open(p, encoding='utf-8'))
e = next(x for x in d if x.get('date') == '2026-11-22')
l = "🔔 Siège : si une défense fait que ton énergie en attente ne suffit plus pour finir, tu reçois une notification (« il manque ≈ N ⚡ »), et la cloche le garde (question de Cairnan217)."
if l not in e['nouveautes']: e['nouveautes'].insert(0, l)
json.dump(d, open(p, 'w', encoding='utf-8'), ensure_ascii=False, indent=2); print('nouveautes.json : ok')
