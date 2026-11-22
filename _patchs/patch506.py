# patch506 : le « Lion dressé » (lion rampant) dans les animaux gratuits des motifs (demande d'ASMFCB, 23/11).
# Silhouette tirée d'une gravure de 1862 (Arthur Hall, The Manual of Heraldry, Londres : domaine public), envoyée
# par Nataël, simplifiée ici (intérieur plein, queue et œil redessinés). Va avec s3-57.
import os, sys, json
R = sys.argv[1] if len(sys.argv) > 1 else '.'
def rep(f, a, b, n=1):
    p = os.path.join(R, f); t = open(p, encoding='utf-8').read()
    if t.count(a) != n:
        if b in t: print(f'{f} : déjà fait'); return
        raise SystemExit(f'{f} : {t.count(a)} occurrence(s) pour {a[:80]!r}')
    open(p, 'w', encoding='utf-8').write(t.replace(a, b)); print(f'{f} : ok')
ICI = os.path.dirname(os.path.abspath(__file__))
lion = json.load(open(os.path.join(ICI, 'patch506-lion.json'), encoding='utf-8'))
p = os.path.join(R, 'motifs-formes.json'); fs = json.load(open(p, encoding='utf-8'))
if not any(f['id'] == lion['id'] for f in fs):
    i = next(k for k, f in enumerate(fs) if f['id'] == 'lion')
    fs.insert(i + 1, lion)
json.dump(fs, open(p, 'w', encoding='utf-8'), ensure_ascii=False, separators=(',', ':')); print('motifs-formes.json : ok')
rep('app.js', "Dessins : game-icons.net (Lorc, Delapouite et autres), licence CC BY 3.0.</small>",
              "Dessins : game-icons.net (Lorc, Delapouite et autres), licence CC BY 3.0. Lion dressé : gravure de 1862 (A. Hall), domaine public.</small>")
rep('mentions-legales.html', "sous licence <a href=\"https://creativecommons.org/licenses/by/3.0/\" rel=\"noopener\">CC BY 3.0</a>, mis à l'échelle pour le jeu.</p>",
    "sous licence <a href=\"https://creativecommons.org/licenses/by/3.0/\" rel=\"noopener\">CC BY 3.0</a>, mis à l'échelle pour le jeu. Le lion dressé est une silhouette tirée d'une gravure du <i>Manual of Heraldry</i> d'Arthur Hall (Londres, 1862), dans le domaine public.</p>")
p = os.path.join(R, 'data', 'nouveautes.json'); d = json.load(open(p, encoding='utf-8'))
e = max((x for x in d if x.get('date') in ('2026-11-22', '2026-11-23')), key=lambda x: x['date'])
l = "🦁 Motifs : le « Lion dressé » des blasons rejoint les animaux gratuits (demande d'ASMFCB)."
if l not in e['nouveautes']: e['nouveautes'].insert(0, l)
json.dump(d, open(p, 'w', encoding='utf-8'), ensure_ascii=False, indent=2); print('nouveautes.json : ok')
