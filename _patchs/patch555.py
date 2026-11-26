# patch555 (s3-87) : améliorer les bâtiments (niveaux 2 et 3) dans QG › Bâtiments ; portées et réserve de Banque selon le niveau.
import os, sys, json
R = sys.argv[1] if len(sys.argv) > 1 else '.'
D = os.path.dirname(os.path.abspath(__file__))
def rep(f, a, b, n=1):
    p = os.path.join(R, f); t = open(p, encoding='utf-8').read()
    if t.count(a) != n:
        if b in t: print(f'{f} : déjà fait'); return
        raise SystemExit(f'{f} : {t.count(a)} occurrence(s) pour {a[:80]!r}')
    open(p, 'w', encoding='utf-8').write(t.replace(a, b)); print(f'{f} : ok')
def ajouter(f, src, marque):
    p = os.path.join(R, f); t = open(p, encoding='utf-8').read()
    if marque in t: print(f'{f} : déjà ajouté'); return
    open(p, 'a', encoding='utf-8').write(open(os.path.join(D, src), encoding='utf-8').read()); print(f'{f} : ajouté')
rep('app.js', "    BATIMENTS = m.data;\n    batimentsLu = Date.now();\n", "    BATIMENTS = m.data;\n    batimentsLu = Date.now();\n    btNivCharger();   // patch555 : les niveaux\n")
rep('app.js', "  const res = Number(bqReglage('reserve', 60)) || 60, dedans = Math.min(res, Number(bq.contenu) || 0);",
    "  const res = Number((btNiv('banque', bq.code) || {}).val) || Number(bqReglage('reserve', 60)) || 60, dedans = Math.min(res, Number(bq.contenu) || 0);   // patch555 : selon le niveau")
rep('app.js', "nv = (rd.voit || []).length + (rd.voit_banques || []).length, po = rdReglage('portee_km', 50);", "nv = (rd.voit || []).length + (rd.voit_banques || []).length, po = Number(rd.portee_km) || rdReglage('portee_km', 50);   // patch555")
rep('app.js', "  const r = B.radar, prix = rdReglage('prix', 30), po = rdReglage('portee_km', 50);", "  const r = B.radar, prix = rdReglage('prix', 30), po = Number(r && r.portee_km) || rdReglage('portee_km', 50);   // patch555")
rep('app.js', "  const A = BATIMENTS.artillerie, prix = s3ArtR('prix', 20), po = s3ArtR('portee_km', 50);", "  const A = BATIMENTS.artillerie, prix = s3ArtR('prix', 20), po = Number(A && A.portee_km) || s3ArtR('portee_km', 50);   // patch555")
ajouter('app.js', 'patch555-niveaux.js', 'patch555 (s3-87) : améliorer les bâtiments')
ajouter('style.css', 'patch555.css', 'patch555 : améliorer les bâtiments')
rep('index.html', """            <p><b>Radar</b> : avec une Fonderie, construis un <b>Radar</b>""", """            <p><b>Améliorer un bâtiment</b> : dans QG › Bâtiments, chaque Fonderie, Forteresse, Banque, Radar et Artillerie monte jusqu'au <b>niveau 3</b>, contre des lingots, en <b>6 h</b> de chantier (le bâtiment marche à son niveau actuel pendant les travaux). Fonderie : réserve <b>+10</b> par niveau (15 puis 30 lingots). Banque : réserve <b>60 → 90 → 120</b> (15 puis 30). Radar : vue <b>50 → 70 → 90 km</b> (20 puis 35). Artillerie : portée <b>50 → 65 → 80 km</b> (20 puis 35). Forteresse : appui <b>20 → 25 → 30 km</b> (15 puis 30). <b>+20</b> au classement par niveau. Si la commune est prise, le bâtiment est perdu avec ses niveaux.</p>
            <p><b>Radar</b> : avec une Fonderie, construis un <b>Radar</b>""")
p = os.path.join(R, 'data/nouveautes.json'); d = json.load(open(p, encoding='utf-8'))
n1 = "🏗️ Améliorer ses bâtiments : dans QG › Bâtiments, Fonderie, Forteresse, Banque, Radar et Artillerie montent jusqu'au niveau 3 contre des lingots (6 h de chantier). Plus de réserve, plus de portée, +20 au classement par niveau. Idée de Bonjean."
if n1 not in d[0]['nouveautes']: d[0]['nouveautes'].append(n1)
json.dump(d, open(p, 'w', encoding='utf-8'), ensure_ascii=False, indent=1); print('nouveautes : ok')
