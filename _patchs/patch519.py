# patch519 : Défendre — la liste des sièges disparaissait puis revenait chaque minute (signalé par Bonjean, 23/11).
# Cause : le minuteur de 30 s du panneau Défense appelait renderMenaces(), l'affichage de la saison 2 (attaques aux dés),
# qui ne voit aucune attaque en saison 3 et cachait le bloc ; loadMenaces (60 s) le réaffichait.
# Correction : en saison 3 (SIEGE), renderMenaces() redessine la liste des sièges.
import os, sys, json
R = sys.argv[1] if len(sys.argv) > 1 else '.'
def rep(f, a, b, n=1):
    p = os.path.join(R, f); t = open(p, encoding='utf-8').read()
    if t.count(a) != n:
        if b in t: print(f'{f} : déjà fait'); return
        raise SystemExit(f'{f} : {t.count(a)} occurrence(s) pour {a[:80]!r}')
    open(p, 'w', encoding='utf-8').write(t.replace(a, b)); print(f'{f} : ok')
rep('app.js', "function renderMenaces(){\n  const enDanger = menaces.filter(m => m.victoires_consecutives > 0);",
              "function renderMenaces(){\n  if(SIEGE){ renderMenacesSiege(); return; }   // patch519 : en saison 3, la liste des sièges (sinon elle disparaissait toutes les 30 s)\n  const enDanger = menaces.filter(m => m.victoires_consecutives > 0);")
p = os.path.join(R, 'data', 'nouveautes.json'); d = json.load(open(p, encoding='utf-8'))
if d[0].get('date') != '2026-11-23': d.insert(0, {'date': '2026-11-23', 'nouveautes': []})
e = d[0]; e.setdefault('correctifs', [])
l = "Défendre : la liste de tes communes assiégées ne disparaît plus toutes les 30 secondes (signalé par Bonjean)."
if l not in e['correctifs']: e['correctifs'].insert(0, l)
json.dump(d, open(p, 'w', encoding='utf-8'), ensure_ascii=False, indent=2); print('nouveautes.json : ok')
