# Luxembourg : contours (communes, cantons, pays) et table des 100 communes, au format du jeu.
# Entrées : communes4326.geojson (ACT, data.public.lu, CC0), rnpp-population-communes.csv (RNPP « Population par
# commune », CTIE, data.public.lu, mis à jour le 2/10/2026), wikidata-communes.csv et photos-inventaire.csv (Wikidata CC0, Commons).
# Codes : communes « LU » + code LAU (= Wikidata) ; cantons en 3 lettres « L.. » (les codes à 2 lettres CA, LU, VD, GR…
# sont pris par des cantons suisses). Région unique « Luxembourg ».
# Rareté : proportions de la France métropolitaine (comme la Belgique), classement par population au Luxembourg.
# Noms : nom officiel de l'ACT (français ou luxembourgeois officiel, ex. Käerjeng, Habscht).
# Usage : python3 luxembourg-jeu.py <communes4326.geojson> <dossier de travail>
import csv, json, os, subprocess, sys, unicodedata, collections
from shapely.geometry import shape
from shapely.ops import polylabel
SRC, W = sys.argv[1], sys.argv[2]
ICI = os.path.dirname(os.path.abspath(__file__)); OUT = os.path.join(ICI, '..', 'jeu')
os.makedirs(W, exist_ok=True); os.makedirs(os.path.join(OUT, 'contours'), exist_ok=True)
CANTONS = {'Capellen': 'LCA', 'Clervaux': 'LCL', 'Diekirch': 'LDI', 'Echternach': 'LEC', 'Esch-sur-Alzette': 'LES',
           'Grevenmacher': 'LGR', 'Luxembourg': 'LLU', 'Mersch': 'LME', 'Redange': 'LRE', 'Remich': 'LRM',
           'Vianden': 'LVI', 'Wiltz': 'LWI'}
def ms(*a): subprocess.run(['mapshaper', *a], check=True, stderr=subprocess.DEVNULL)
d = json.load(open(SRC))
for f in d['features']:
    p = f['properties']; p['code'] = 'LU' + p['LAU2']; p['prov'] = CANTONS[p['CANTON']]
json.dump(d, open(os.path.join(W, 'communes-codes.json'), 'w'))
# communes luxembourgeoises ≈ 26 km² (France 16, Belgique 53). La source est déjà simplifiée (≈ 250 points par commune) :
# 11 % pondérée → ≈ 25 à 30 points par commune, comme la Belgique (31)
ms('-i', os.path.join(W, 'communes-codes.json'), 'name=communes', '-simplify', '11%', 'weighted', 'keep-shapes',
   '-o', os.path.join(W, 'communes.json'), 'format=geojson',
   '-dissolve', 'prov', '+', 'name=cantons', '-o', os.path.join(W, 'cantons.json'), 'format=geojson', 'target=cantons',
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
par, base = {}, {}
for f in com['features']:
    p = f['properties']
    par.setdefault(p['prov'], {})[p['code']] = anneaux(f['geometry'])
    g = shape(f['geometry']); gros = max(getattr(g, 'geoms', [g]), key=lambda x: x.area)
    try: c = polylabel(gros.buffer(0), tolerance=0.0002)
    except Exception: c = gros.representative_point()
    if not gros.contains(c): c = gros.representative_point()
    base[p['code']] = {'nom': p['COMMUNE'], 'prov': p['prov'], 'lat': round(c.y, 4), 'lon': round(c.x, 4)}
tailles = {}
for k, v in par.items():
    t = json.dumps(v, separators=(',', ':')); open(os.path.join(OUT, 'contours', k + '.json'), 'w').write(t); tailles[k] = len(t)
cant = {f['properties']['prov']: anneaux(f['geometry'], False) for f in json.load(open(os.path.join(W, 'cantons.json')))['features']}
json.dump(cant, open(os.path.join(OUT, 'cantons.json'), 'w'), separators=(',', ':'))
P = json.load(open(os.path.join(W, 'pays.json')))
pays = [r for g in (P.get('geometries') or [f['geometry'] for f in P.get('features', [])]) if g for r in anneaux(g, False)]
json.dump(pays, open(os.path.join(OUT, 'luxembourg-contour.json'), 'w'), separators=(',', ':'))

norm = lambda s: unicodedata.normalize('NFKD', s).encode('ascii', 'ignore').decode().lower()
pop_nom = {norm(r['COMMUNE_NOM']): sum(int(r[k]) for k in ('FEMMES_MINEURES', 'HOMMES_MINEURS', 'FEMMES_MAJEURES', 'HOMMES_MAJEURS'))
           for r in csv.DictReader(open(os.path.join(ICI, 'rnpp-population-communes.csv'), encoding='utf-8'))}
pop = {k: pop_nom[norm(b['nom'])] for k, b in base.items()}
wd = {r['code']: r for r in csv.DictReader(open(os.path.join(ICI, 'wikidata-communes.csv'), encoding='utf-8'))}
ph = {r['code']: r for r in csv.DictReader(open(os.path.join(ICI, 'photos-inventaire-luxembourg.csv'), encoding='utf-8'))}
def photo(k):
    r = ph.get(k)
    return r['fichier'] if r and (r['auteur'] or r['licence'] in ('Public domain', 'CC0')) else ''
PARTS = [('legendaire', 0.0087), ('epique', 0.0292), ('rare', 0.0980), ('peucommun', 0.3696)]
codes = sorted(base, key=lambda k: (-pop[k], k)); n = len(codes); bornes, cumul = [], 0.0
for t, p in PARTS:
    cumul += p; bornes.append((t, round(cumul * n)))
def tier(rang):
    for t, b in bornes:
        if rang <= b: return t
    return 'commun'
lignes = []
for rang, k in enumerate(codes, 1):
    b, w = base[k], wd.get(k) or {}
    lignes.append({'code': k, 'nom': b['nom'], 'departement': b['prov'], 'population': pop[k], 'latitude': b['lat'], 'longitude': b['lon'],
                   'tier': tier(rang), 'rang': rang, 'nom_officiel': b['nom'], 'nom_lb': w.get('nom_lb', ''), 'nom_de': w.get('nom_de', ''),
                   'wikidata': w.get('wikidata', ''), 'article_fr': w.get('article_fr', ''), 'photo': photo(k)})
with open(os.path.join(OUT, 'communes-luxembourg.csv'), 'w', newline='', encoding='utf-8') as fh:
    wr = csv.DictWriter(fh, fieldnames=list(lignes[0].keys())); wr.writeheader(); wr.writerows(sorted(lignes, key=lambda l: l['code']))
print('communes %d, cantons %d, population %d, contours %.0f Ko, pays %d anneaux' % (n, len(cant), sum(pop.values()), sum(tailles.values()) / 1e3, len(pays)))
print('raretés :', collections.Counter(l['tier'] for l in lignes).most_common())
for t in ('legendaire', 'epique', 'rare'):
    print('%s : %s' % (t, ', '.join('%s (%d)' % (l['nom'], l['population']) for l in sorted(lignes, key=lambda l: l['rang']) if l['tier'] == t)))
print('par canton :', dict(collections.Counter(l['departement'] for l in lignes)))
print('photos : %d ; articles : %d ; wikidata : %d' % (sum(1 for l in lignes if l['photo']), sum(1 for l in lignes if l['article_fr']), sum(1 for l in lignes if l['wikidata'])))
