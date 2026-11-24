# patch529 (idée d'Arkhannou) : le numéro de département à côté du nom dans « À défendre maintenant » et « Mes sièges » (QG).
import os, sys, json
R = sys.argv[1] if len(sys.argv) > 1 else '.'
def rep(f, a, b, n=1):
    p = os.path.join(R, f); t = open(p, encoding='utf-8').read()
    if t.count(a) != n:
        if b in t: print(f'{f} : déjà fait'); return
        raise SystemExit(f'{f} : {t.count(a)} occurrence(s) pour {a[:80]!r}')
    open(p, 'w', encoding='utf-8').write(t.replace(a, b)); print(f'{f} : ok')
rep('app.js', "return `<div class=\"mfo-l\"><div><b>${echapperTexte(m.nom || m.commune)}</b> · ${sgTier(m.tier).label.toLowerCase()}",
              "return `<div class=\"mfo-l\"><div><b>${echapperTexte(m.nom || m.commune)}</b>${badgeDept(m.dept)} · ${sgTier(m.tier).label.toLowerCase()}")
rep('app.js', "return `<div class=\"mfo-l\"><div><b>${echapperTexte(s.nom || s.commune)}</b><small>",
              "return `<div class=\"mfo-l\"><div><b>${echapperTexte(s.nom || s.commune)}</b>${badgeDept(s.dept)}<small>")
rep('style.css', ".ca-cible{ position:relative; }", ".ca-cible{ position:relative; }\n.mfo-l .dep{ margin-left:5px; vertical-align:1px; }   /* patch529 */")
p = os.path.join(R, 'data', 'nouveautes.json'); d = json.load(open(p, encoding='utf-8'))
e = d[0]; assert e['date'] == '2026-11-24'
l = "🔢 QG : le numéro de département s'affiche à côté du nom dans « À défendre maintenant » et « Mes sièges » (merci Arkhannou)."
if l not in e['nouveautes']: e['nouveautes'].insert(0, l)
json.dump(d, open(p, 'w', encoding='utf-8'), ensure_ascii=False, indent=2); print('nouveautes.json : ok')
