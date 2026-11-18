# Belgique : contours des communes (secteurs Statbel 2025 regroupés), des provinces et du pays, au format du jeu.
# Entrée : sh_statbel_statistical_sectors_3812_20250101.geojson (Statbel, CC BY 4.0).
# Étapes (mapshaper) : passage en WGS84, regroupement des secteurs par commune (code INS), simplification 1 % pondérée
# (≈ 31 points par commune ; communes belges ≈ 53 km², 3 fois la Suisse), provinces et pays tirés de la même topologie.
import json, os, subprocess, sys
from shapely.geometry import shape
from shapely.ops import polylabel
SRC = sys.argv[1]; W = sys.argv[2]; OUT = sys.argv[3]
os.makedirs(W, exist_ok=True); os.makedirs(os.path.join(OUT, 'contours'), exist_ok=True)
# code INS de la province → code du jeu (ISO 3166-2:BE sans « BE- » ; trois lettres : jamais pris pour un canton suisse)
PROV = {'10000': 'VAN', '20001': 'VBR', '20002': 'WBR', '30000': 'VWV', '40000': 'VOV', '50000': 'WHT',
        '60000': 'WLG', '70000': 'VLI', '80000': 'WLX', '90000': 'WNA', None: 'BRU', '': 'BRU'}
def ms(*a): subprocess.run(['mapshaper', *a], check=True, stderr=subprocess.DEVNULL)
brut = os.path.join(W, 'communes-brut.json')
if not os.path.exists(brut):
    ms('-i', SRC, '-proj', 'init=EPSG:3812', 'wgs84', '-dissolve', 'cd_munty_refnis',
       'copy-fields=tx_munty_descr_fr,tx_munty_descr_nl,tx_munty_descr_de,cd_prov_refnis,cd_rgn_refnis', '-o', brut, 'format=geojson')
d = json.load(open(brut))
for f in d['features']:
    p = f['properties']; p['code'] = 'BE' + p['cd_munty_refnis']; p['prov'] = PROV[p.get('cd_prov_refnis')]
json.dump(d, open(os.path.join(W, 'communes-codes.json'), 'w'))
ms('-i', os.path.join(W, 'communes-codes.json'), 'name=communes', '-simplify', '1%', 'weighted', 'keep-shapes',
   '-o', os.path.join(W, 'communes.json'), 'format=geojson',
   '-dissolve', 'prov', '+', 'name=provinces', '-o', os.path.join(W, 'provinces.json'), 'format=geojson', 'target=provinces',
   '-dissolve', 'target=communes', '+', 'name=pays', '-o', os.path.join(W, 'pays.json'), 'format=geojson', 'target=pays')
def anneaux(g, avec_trous=True):
    polys = g['coordinates'] if g['type'] == 'MultiPolygon' else [g['coordinates']]
    out = []
    for p in polys:
        for i, r in enumerate(p):
            if i and not avec_trous: break
            out.append([[round(x, 4), round(y, 4)] for x, y in r])
    return out
com = json.load(open(os.path.join(W, 'communes.json')))
par, centres, noms = {}, {}, {}
for f in com['features']:
    p = f['properties']
    par.setdefault(p['prov'], {})[p['code']] = anneaux(f['geometry'])
    g = shape(f['geometry']); gros = max(getattr(g, 'geoms', [g]), key=lambda x: x.area)
    try: c = polylabel(gros.buffer(0), tolerance=0.0002)
    except Exception: c = gros.representative_point()
    if not gros.contains(c): c = gros.representative_point()
    centres[p['code']] = (round(c.y, 4), round(c.x, 4))
    noms[p['code']] = (p['tx_munty_descr_fr'], p['tx_munty_descr_nl'], p['tx_munty_descr_de'], p['prov'], p['cd_rgn_refnis'])
tailles = {}
for k, v in par.items():
    t = json.dumps(v, separators=(',', ':')); open(os.path.join(OUT, 'contours', k + '.json'), 'w').write(t); tailles[k] = len(t)
prov = {f['properties']['prov']: anneaux(f['geometry'], False) for f in json.load(open(os.path.join(W, 'provinces.json')))['features']}
json.dump(prov, open(os.path.join(OUT, 'provinces.json'), 'w'), separators=(',', ':'))
P = json.load(open(os.path.join(W, 'pays.json')))
pays = [r for g in (P.get('geometries') or [f['geometry'] for f in P.get('features', [])]) if g for r in anneaux(g, False)]
json.dump(pays, open(os.path.join(OUT, 'belgique-contour.json'), 'w'), separators=(',', ':'))
json.dump({k: {'lat': centres[k][0], 'lon': centres[k][1], 'fr': n[0], 'nl': n[1], 'de': n[2], 'prov': n[3], 'region': n[4]}
           for k, n in noms.items()}, open(os.path.join(W, 'communes-base.json'), 'w'), ensure_ascii=False, indent=0)
print('communes %d, provinces %d, contours %.0f Ko (plus gros %s %.0f Ko), pays %d anneaux' % (
    len(noms), len(prov), sum(tailles.values()) / 1e3, max(tailles, key=tailles.get), max(tailles.values()) / 1e3, len(pays)))
