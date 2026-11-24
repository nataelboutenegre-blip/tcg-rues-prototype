# patch526 : les textes suivent s3-66 (12 points par ⚡, pose à 1 ⚡). « Tout repousser » : 12 × 1,2 × 0,8 = 11,52 par ⚡.
import os, sys, json
R = sys.argv[1] if len(sys.argv) > 1 else '.'
def rep(f, a, b, n=1):
    p = os.path.join(R, f); t = open(p, encoding='utf-8').read()
    if t.count(a) != n:
        if b in t: print(f'{f} : déjà fait'); return
        raise SystemExit(f'{f} : {t.count(a)} occurrence(s) pour {a[:80]!r}')
    open(p, 'w', encoding='utf-8').write(t.replace(a, b)); print(f'{f} : ok')
rep('app.js', "function sgToutN(deg){ return Math.min(60, Math.max(1, Math.ceil((Number(deg) || 0) / 9.6))); }",
              "const SG_PIRE_RENFORT = 11.52;   // patch526 : 12 points × 1,2 (défenseur) × 0,8 (pire tirage)\nfunction sgToutN(deg){ return Math.min(60, Math.max(1, Math.ceil((Number(deg) || 0) / SG_PIRE_RENFORT))); }")
rep('app.js', "const txt = n >= 60 && deg / 9.6 > 60 ?", "const txt = n >= 60 && deg / SG_PIRE_RENFORT > 60 ?")
rep('app.js', "<li><b>Chaque énergie</b> fait 10 points sur la jauge, au hasard entre 8 et 12.</li>",
              "<li><b>Chaque énergie</b> fait 12 points sur la jauge, au hasard entre 10 et 14.</li>")
rep('app.js', "e - (neuf ? Number(a.pose) || 2 : 0)", "e - (neuf ? Number(a.pose) || 1 : 0)")
rep('app.js', "const pose = s ? 0 : (Number(a.pose) || 2);", "const pose = s ? 0 : (Number(a.pose) || 1);")
rep('index.html', "Poser coûte <b>2 ⚡</b>, en plus de ta première vague.", "Poser coûte <b>1 ⚡</b>, en plus de ta première vague.")
rep('index.html', "Chaque ⚡ fait environ <b>10 points de dégâts</b> (entre 8 et 12 au hasard), jusqu'à 60 ⚡ par vague.",
                  "Chaque ⚡ fait environ <b>12 points de dégâts</b> (entre 10 et 14 au hasard), jusqu'à 60 ⚡ par vague.")
rep('index.html', "Il faut donc environ <b>6 ⚡</b> pour une commune et <b>25 ⚡</b> pour une légendaire, plus les 2 ⚡ de la pose,",
                  "Il faut donc environ <b>5 ⚡</b> pour une commune et <b>21 ⚡</b> pour une légendaire, plus 1 ⚡ de pose,")
rep('index.html', "chaque ⚡ fait reculer la jauge d'environ <b>12 points</b> (×1,2 pour le défenseur).",
                  "chaque ⚡ fait reculer la jauge d'environ <b>14 points</b> (12 × 1,2 pour le défenseur).")
rep('index.html', "pose un siège (<b>2 énergie</b>), puis envoie des <b>vagues</b>", "pose un siège (<b>1 énergie</b>), puis envoie des <b>vagues</b>")
rep('index.html', "Chaque énergie fait <b>10 points de dégâts</b> (entre 8 et 12, au hasard).", "Chaque énergie fait <b>12 points de dégâts</b> (entre 10 et 14, au hasard).")
rep('index.html', "fait <b>reculer</b> sa jauge de 10 points, <b>+20 %</b> parce que tu es chez toi (12 en moyenne).",
                  "fait <b>reculer</b> sa jauge de 12 points, <b>+20 %</b> parce que tu es chez toi (14 en moyenne).")
p = os.path.join(R, 'data', 'nouveautes.json'); d = json.load(open(p, encoding='utf-8'))
if d[0].get('date') != '2026-11-24': d.insert(0, {'date': '2026-11-24', 'nouveautes': []})
e = d[0]; e.setdefault('nouveautes', [])
l = "⚡ Front : conquérir coûte moins cher. Chaque énergie fait 12 points au lieu de 10 (en attaque comme en renfort), et poser un siège coûte 1 ⚡ au lieu de 2."
if l not in e['nouveautes']: e['nouveautes'].insert(0, l)
json.dump(d, open(p, 'w', encoding='utf-8'), ensure_ascii=False, indent=2); print('nouveautes.json : ok')
