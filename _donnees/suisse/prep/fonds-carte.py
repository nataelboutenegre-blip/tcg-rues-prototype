# Fond de carte de la saison 3 : voisins (Natural Earth, domaine public, via world-atlas),
# terre suisse avec une couture vers la France, lacs, frontière. Format du jeu : anneaux [lon, lat].
import json, subprocess
from shapely.geometry import shape, Polygon, MultiPolygon, box, mapping
from shapely.ops import unary_union
S = '/home/claude/s3/ch/jeu/sortie/'; O = '/home/claude/s3/ch/jeu/site/'
import os; os.makedirs(O + 'data', exist_ok=True)
anneaux_poly = lambda rings: unary_union([Polygon(r).buffer(0) for r in rings])
def vers_anneaux(g, tol=None, prec=4, aire_min=0):
    if tol: g = g.simplify(tol, preserve_topology=True)
    out = []
    for p in getattr(g, 'geoms', [g]):
        if p.geom_type != 'Polygon' or p.area <= aire_min: continue
        out.append([[round(x, prec), round(y, prec)] for x, y in p.exterior.coords])
    return out
france = anneaux_poly(json.load(open('/mnt/user-data/uploads/tcg-rues-prototype/data/france-outline.json')))
suisse = anneaux_poly(json.load(open(S + 'suisse-contour.json')))
jouable = unary_union([france, suisse])
# terre suisse + couture : ce qui sépare les contours de la France (IGN, simplifiés) et de la Suisse
couture = suisse.buffer(0.02).intersection(france.buffer(0.02))
terre = unary_union([suisse, couture])
json.dump(vers_anneaux(terre, aire_min=1e-6), open(O + 'data/suisse-terre.json', 'w'), separators=(',', ':'))
# voisins
pays = json.loads(subprocess.check_output(['node', '-e', """
const topo = require('/home/claude/s3/npm/node_modules/world-atlas/countries-10m.json');
const { feature } = require('/home/claude/s3/npm/node_modules/topojson-client');
const ids = {'056':'BELGIQUE','442':'LUX.','276':'ALLEMAGNE','380':'ITALIE','724':'ESPAGNE','020':'ANDORRE','492':'MONACO','826':'ROYAUME-UNI','040':'AUTRICHE','438':'LIECHT.','528':'PAYS-BAS','674':'SAINT-MARIN','336':'VATICAN','208':'DANEMARK','203':'TCHÉQUIE','705':'SLOVÉNIE','191':'CROATIE','372':'IRLANDE','620':'PORTUGAL','012':'ALGÉRIE','788':'TUNISIE','504':'MAROC'};
process.stdout.write(JSON.stringify(feature(topo, topo.objects.countries).features.filter(f => ids[f.id]).map(f => ({ nom: ids[f.id], g: f.geometry }))));
"""]))
cadre = box(-8.5, 39.5, 13.5, 53.5)
ETIQ = {'ALLEMAGNE': [9.4, 49.9], 'BELGIQUE': [4.6, 50.6], 'LUX.': [6.1, 49.78], 'ITALIE': [9.9, 44.6], 'ESPAGNE': [-2.4, 41.6],
        'ROYAUME-UNI': [-3.4, 51.2], 'AUTRICHE': [11.6, 47.25], 'ANDORRE': [1.55, 42.38], 'PAYS-BAS': [5.6, 51.6]}
zone_couture = jouable.buffer(0.06).difference(jouable)
voisins = []
for p in pays:
    g = shape(p['g']).buffer(0).intersection(cadre)
    if g.is_empty: continue
    g = unary_union([g, zone_couture.intersection(g.buffer(0.06))]).difference(jouable)
    a = vers_anneaux(g, tol=0.006, prec=3, aire_min=2e-4)
    if a: voisins.append({'nom': p['nom'], 'a': a, 'e': ETIQ.get(p['nom'])})
json.dump(voisins, open(O + 'data/voisins.json', 'w'), separators=(',', ':'), ensure_ascii=False)
for f, n in [('suisse-frontiere.json', 'suisse-frontiere.json'), ('lacs.json', 'lacs-suisse.json'), ('cantons.json', 'contours-cantons.json')]:
    open(O + 'data/' + n, 'w').write(open(S + f).read())
os.makedirs(O + 'contours', exist_ok=True)
for f in os.listdir(S + 'contours'): open(O + 'contours/' + f, 'w').write(open(S + 'contours/' + f).read())
for f in sorted(os.listdir(O + 'data')): print(f, round(os.path.getsize(O + 'data/' + f) / 1e3, 1), 'Ko')
print([v['nom'] for v in voisins])
