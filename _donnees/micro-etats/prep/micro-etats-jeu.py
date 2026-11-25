# Andorre (7 paroisses) et Monaco (1 commune) : contours et table au format du jeu.
# Entrée : brut/ de telecharger-andorre-monaco.py (Wikidata CC0 ; contours OpenStreetMap, ODbL, via Commons et Nominatim).
# Codes : communes « AD » + numéro ISO de paroisse (AD07 = Andorre-la-Vieille), « MC00 » pour Monaco ;
# « départements » AND et MCO (3 lettres, comme la Belgique et le Luxembourg). Régions : « Andorre », « Monaco ».
# Rareté : seuils de population de la France (légendaire ≥ 30 000, épique ≥ 8 000, rare ≥ 2 300, peu commune ≥ 450),
# car 8 communes ne permettent pas de proportions.
# Usage : python3 micro-etats-jeu.py <dossier brut> <dossier de travail>
import csv, json, os, subprocess, sys
from shapely.geometry import shape
from shapely.ops import polylabel
BRUT, W = sys.argv[1], sys.argv[2]
ICI = os.path.dirname(os.path.abspath(__file__)); OUT = os.path.join(ICI, '..', 'jeu')
os.makedirs(W, exist_ok=True); os.makedirs(os.path.join(OUT, 'contours'), exist_ok=True)
NOMS = {'AD-02': 'Canillo', 'AD-03': 'Encamp', 'AD-04': 'La Massana', 'AD-05': 'Ordino', 'AD-06': 'Sant Julià de Lòria',
        'AD-07': 'Andorre-la-Vieille', 'AD-08': 'Escaldes-Engordany'}
def tier(p):
    return 'legendaire' if p >= 30000 else 'epique' if p >= 8000 else 'rare' if p >= 2300 else 'peucommun' if p >= 450 else 'commun'
ent = json.load(open(os.path.join(BRUT, 'communes.json'), encoding='utf-8'))
feats, lignes = [], []
for e in ent:
    iso = e.get('iso') or ''
    code, dep, region = ('AD' + iso[3:], 'AND', 'Andorre') if iso.startswith('AD-') else ('MC00', 'MCO', 'Monaco')
    d = json.load(open(os.path.join(BRUT, e['contour_fichier'])))
    fs = d['features'] if d.get('type') == 'FeatureCollection' else [d]
    for f in fs:
        if f.get('geometry'): feats.append({'type': 'Feature', 'geometry': f['geometry'], 'properties': {'code': code, 'prov': dep}})
    lignes.append({'code': code, 'nom': NOMS.get(iso, e['nom']), 'departement': dep, 'region': region, 'population': e['pop'],
                   'tier': tier(e['pop']), 'wikidata': e['wikidata'], 'article_fr': (e.get('article') or '').rsplit('/', 1)[-1],
                   'photo': e.get('photo', '') if (e.get('photo_auteur') or e.get('photo_licence') in ('Public domain', 'CC0')) else '',
                   'contour': 'OpenStreetMap (ODbL)'})
json.dump({'type': 'FeatureCollection', 'features': feats}, open(os.path.join(W, 'brut.json'), 'w'))
# -dissolve par code (Monaco arrive en plusieurs morceaux), -clean pour supprimer les chevauchements entre paroisses
subprocess.run(['mapshaper', '-quiet', '-i', os.path.join(W, 'brut.json'), '-dissolve', 'code', 'copy-fields=prov', '-clean',
                '-simplify', '25%', 'weighted', 'keep-shapes', '-o', os.path.join(W, 'communes.json'), 'format=geojson'], check=True)
def anneaux(g):
    polys = g['coordinates'] if g['type'] == 'MultiPolygon' else [g['coordinates']]
    return [[[round(x, 4), round(y, 4)] for x, y in r] for p in polys for r in p]
par, pts, centre = {}, 0, {}
for f in json.load(open(os.path.join(W, 'communes.json')))['features']:
    p = f['properties']; a = anneaux(f['geometry']); pts += sum(len(r) for r in a)
    par.setdefault(p['prov'], {})[p['code']] = a
    g = shape(f['geometry']); gros = max(getattr(g, 'geoms', [g]), key=lambda x: x.area)
    c = polylabel(gros.buffer(0), tolerance=0.0002)
    if not gros.contains(c): c = gros.representative_point()
    centre[p['code']] = (round(c.y, 4), round(c.x, 4))
for k, v in par.items():
    open(os.path.join(OUT, 'contours', k + '.json'), 'w').write(json.dumps(v, separators=(',', ':')))
for l in lignes:
    l['latitude'], l['longitude'] = centre[l['code']]
with open(os.path.join(OUT, 'communes-andorre-monaco.csv'), 'w', newline='', encoding='utf-8') as fh:
    wr = csv.DictWriter(fh, fieldnames=['code', 'nom', 'departement', 'region', 'population', 'latitude', 'longitude', 'tier',
                                        'wikidata', 'article_fr', 'photo', 'contour'])
    wr.writeheader(); wr.writerows(sorted(lignes, key=lambda l: l['code']))
print('%d communes, %d points en tout' % (len(lignes), pts))
for l in sorted(lignes, key=lambda l: -l['population']): print('  %s %-22s %6d %s %s' % (l['code'], l['nom'], l['population'], l['tier'], l['photo'][:30]))
