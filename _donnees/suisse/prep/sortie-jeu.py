# Fichiers au format du jeu : contours par canton, cantons, contour du pays, lacs, table des communes.
import json, os, csv
from shapely.geometry import shape
from shapely.ops import polylabel
M = '/home/claude/s3/ch/jeu/ms/'; S = '/home/claude/s3/ch/jeu/sortie/'
os.makedirs(S + 'contours', exist_ok=True)
def anneaux(g, avec_trous=True):
    polys = g['coordinates'] if g['type'] == 'MultiPolygon' else [g['coordinates']]
    out = []
    for p in polys:
        for i, r in enumerate(p):
            if i and not avec_trous: break
            out.append([[round(x, 4), round(y, 4)] for x, y in r])
    return out
com = json.load(open(M + 'communes-wgs84.json'))
par_canton, centres = {}, {}
for f in com['features']:
    p = f['properties']
    par_canton.setdefault(p['canton'], {})[p['code']] = anneaux(f['geometry'])
    g = shape(f['geometry'])
    gros = max(getattr(g, 'geoms', [g]), key=lambda x: x.area)
    try: c = polylabel(gros.buffer(0), tolerance=0.0002)
    except Exception: c = gros.representative_point()
    if not gros.contains(c): c = gros.representative_point()
    centres[p['code']] = (round(c.y, 4), round(c.x, 4))
tailles = {}
for k, d in par_canton.items():
    t = json.dumps(d, separators=(',', ':'))
    open(S + 'contours/%s.json' % k, 'w').write(t); tailles[k] = len(t)
cant = {f['properties']['canton']: anneaux(f['geometry'], False) for f in json.load(open(M + 'cantons.json'))['features']}
json.dump(cant, open(S + 'cantons.json', 'w'), separators=(',', ':'))
pays = anneaux(json.load(open(M + 'suisse.json'))['geometries'][0], False)
json.dump(pays, open(S + 'suisse-contour.json', 'w'), separators=(',', ':'))
L = json.load(open(M + 'lacs-wgs84.json'))
lacs = [r for g in (L.get('geometries') or [f['geometry'] for f in L.get('features', [])]) if g for r in anneaux(g, False)]
json.dump(lacs, open(S + 'lacs.json', 'w'), separators=(',', ':'))
table = json.load(open('/home/claude/s3/ch/jeu/table-suisse.json'))
with open(S + 'communes-suisse.csv', 'w', newline='', encoding='utf-8') as fh:
    w = csv.writer(fh)
    w.writerow(['code', 'nom', 'departement', 'population', 'latitude', 'longitude', 'tier', 'nom_officiel', 'wikidata', 'article_fr', 'photo'])
    for l in sorted(table, key=lambda l: l['code']):
        la, lo = centres[l['code']]
        w.writerow([l['code'], l['nom'], l['canton'], l['population'], la, lo, l['tier'], l['nom_officiel'], l['wikidata'], l['article_fr'], l['photo']])
tot = sum(tailles.values())
print('contours : %d cantons, %.0f Ko au total, plus gros %s (%.0f Ko)' % (len(tailles), tot / 1e3, max(tailles, key=tailles.get), max(tailles.values()) / 1e3))
for f in ['cantons.json', 'suisse-contour.json', 'lacs.json', 'communes-suisse.csv']: print(f, round(os.path.getsize(S + f) / 1e3), 'Ko')
lons = [p[0] for r in pays for p in r]; print('Suisse de', min(lons), 'à', max(lons), '°E')
