# patch554 : une forme « Rectangle » (2 × 1, à tourner de 90° pour la mettre debout) dans Formes, juste après Carré.
# Serveur : insert into motif_formes (id, pack) values ('rectangle', null) — fait le 26/11.
import os, sys, json
R = sys.argv[1] if len(sys.argv) > 1 else '.'
p = os.path.join(R, 'motifs-formes.json'); brut = open(p, encoding='utf-8').read(); l = json.loads(brut)
if not any(f['id'] == 'rectangle' for f in l):
    i = next(i for i, f in enumerate(l) if f['id'] == 'carre')
    l.insert(i + 1, {"id": "rectangle", "nom": "Rectangle", "cat": "Formes", "pack": None, "type": "forme", "d": "M4 27L96 27L96 73L4 73Z"})
    compact = '\n' not in brut.strip()
    open(p, 'w', encoding='utf-8').write(json.dumps(l, ensure_ascii=False, separators=(',', ':')) if compact else json.dumps(l, ensure_ascii=False, indent=1))
    print('motifs-formes.json : ok', len(l))
else: print('motifs-formes.json : déjà fait')
p = os.path.join(R, 'data/nouveautes.json'); d = json.load(open(p, encoding='utf-8'))
n1 = "▭ Motif de territoire : nouvelle forme « Rectangle » (dans Formes). Tourne-la de 90° pour la mettre debout."
if n1 not in d[0]['nouveautes']: d[0]['nouveautes'].append(n1)
json.dump(d, open(p, 'w', encoding='utf-8'), ensure_ascii=False, indent=1); print('nouveautes : ok')
