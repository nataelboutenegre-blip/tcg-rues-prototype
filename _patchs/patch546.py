# patch546 : légendaires (s3-83) : l'assaut final ne s'annule que sous la moitié de la jauge ; renfort du propriétaire × 1 (au lieu de × 1,2).
# Petits lauriers : correctif dans les nouveautés.
import os, sys, json
R = sys.argv[1] if len(sys.argv) > 1 else '.'
def rep(f, a, b, n=1):
    p = os.path.join(R, f); t = open(p, encoding='utf-8').read()
    if t.count(a) != n:
        if b in t: print(f'{f} : déjà fait'); return
        raise SystemExit(f'{f} : {t.count(a)} occurrence(s) pour {a[:80]!r}')
    open(p, 'w', encoding='utf-8').write(t.replace(a, b)); print(f'{f} : ok')
# Défendre : l'alerte d'assaut final suit le seuil de la rareté
rep('app.js', """    const n = Math.max(1, Math.ceil((deg - res * 2 / 3 + 1) / sgPireRecul()));
    return `<p class="sg-chute alerte"><b>🚨 Assaut final</b> : elle tombe à <b>${sgHeure(m.assaut_le)}</b> (dans ${am} min) si tu ne repousses pas la jauge sous les deux tiers, ≈""",
"""    const leg = m.tier === 'legendaire';   // patch546 (s3-83) : sur une légendaire, sous la moitié et renfort × 1
    const n = Math.max(1, Math.ceil((deg - res * (leg ? 1 / 2 : 2 / 3) + 1) / (leg ? 9.6 : sgPireRecul())));
    return `<p class="sg-chute alerte"><b>🚨 Assaut final</b> : elle tombe à <b>${sgHeure(m.assaut_le)}</b> (dans ${am} min) si tu ne repousses pas la jauge sous ${leg ? 'la moitié' : 'les deux tiers'}, ≈""")
rep('app.js', "chaque énergie fait reculer sa jauge, avec 20 % de bonus à domicile.", "chaque énergie fait reculer sa jauge, avec 20 % de bonus à domicile (sauf sur une légendaire).")
rep('app.js', "(× 1 pour toi, × 1,2 pour le propriétaire)", "(× 1 pour toi, × 1,2 pour le propriétaire, × 1 sur une légendaire)")
rep('app.js', "<li><b>Renfort</b> : chaque énergie du propriétaire fait reculer ta jauge de 12 points en moyenne, et rend le siège long.</li>",
    "<li><b>Renfort</b> : chaque énergie du propriétaire fait reculer ta jauge d'environ 14 points (12 sur une légendaire), et rend le siège long. Sur une légendaire, l'assaut final ne s'annule que si ta jauge repasse sous la moitié.</li>")
# Règles
rep('index.html', "elle tombe <b>30 min</b> plus tard s'il ne repousse pas ta jauge sous les deux tiers.</p>",
    "elle tombe <b>30 min</b> plus tard s'il ne repousse pas ta jauge sous les deux tiers (<b>sous la moitié</b> pour une légendaire).</p>")
rep('index.html', "<b>+20 %</b> parce que tu es chez toi (14 en moyenne).", "<b>+20 %</b> parce que tu es chez toi (14 en moyenne). Pas de bonus sur une <b>légendaire</b> : 12 par énergie.")
rep('index.html', "<b>× 1</b> par énergie (le propriétaire, lui, × 1,2)", "<b>× 1</b> par énergie (le propriétaire, lui, × 1,2, et × 1 sur une légendaire)")
# Nouveautés
p = os.path.join(R, 'data/nouveautes.json'); d = json.load(open(p, encoding='utf-8'))
assert d[0]['date'] == '2026-11-26'
n1 = "⚔️ Sièges de légendaires : un défenseur actif gagnait presque à coup sûr (5 % de prises avec garnison). Sur une légendaire, le renfort du propriétaire vaut maintenant 12 par énergie (au lieu de 14), et l'assaut final ne s'annule que si la jauge repasse sous la moitié (au lieu des deux tiers). On suit les chiffres de près et on ajustera."
c1 = "Les petits lauriers du classement : la feuille du bout de branche ne flotte plus au-dessus du blason."
if n1 not in d[0]['nouveautes']: d[0]['nouveautes'].append(n1)
if c1 not in d[0].setdefault('correctifs', []): d[0]['correctifs'].append(c1)
json.dump(d, open(p, 'w', encoding='utf-8'), ensure_ascii=False, indent=1); print('nouveautes : ok')
