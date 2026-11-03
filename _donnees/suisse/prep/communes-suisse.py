# swissBOUNDARIES3D (communes) moins les lacs de swissTLMRegio, en WGS84. Sources swisstopo, usage commercial
# autorisé avec mention (« © swisstopo »).
import json, shapefile
from pyproj import Transformer
from shapely.geometry import shape, mapping
from shapely.ops import transform, unary_union
from shapely import force_2d
from shapely.strtree import STRtree
T = Transformer.from_crs(2056, 4326, always_xy=True)
SB = '/home/claude/s3/ch/sb3d/swissBOUNDARIES3D_1_5_TLM_'
CANT = ['','ZH','BE','LU','UR','SZ','OW','NW','GL','ZG','FR','SO','BS','BL','SH','AR','AI','SG','GR','AG','TG','TI','VD','VS','NE','GE','JU']
wgs = lambda g: transform(lambda x, y, z=None: T.transform(x, y), g)
communes = []
for sr in shapefile.Reader(SB + 'HOHEITSGEBIET', encoding='utf-8').iterShapeRecords():
    d = sr.record.as_dict()
    if d['ICC'] == 'CH' and d['OBJEKTART'] == 'Gemeindegebiet':
        communes.append((d, force_2d(shape(sr.shape.__geo_interface__)).buffer(0)))
pays = unary_union([force_2d(shape(s.__geo_interface__)).buffer(0) for s, r in
                    zip(shapefile.Reader(SB + 'LANDESGEBIET').shapes(), shapefile.Reader(SB + 'LANDESGEBIET').records()) if r['ICC'] == 'CH'])
# lacs de plus de 0,3 km² qui touchent la Suisse (Léman, Constance, Majeur, Lugano compris en entier)
lacs = [shape(s.__geo_interface__).buffer(0) for s in shapefile.Reader('/home/claude/s3/ch/regio/swissTLMRegio_Lake').shapes()]
lacs = [g for g in lacs if g.area > 3e5 and g.intersects(pays)]
arbre = STRtree(lacs)
sortie, coupees, perdu = [], 0, []
for d, g in communes:
    proches = [lacs[i] for i in arbre.query(g)]
    g2 = g.difference(unary_union(proches)) if proches else g
    if g2.area < g.area * 0.995: coupees += 1
    if g2.area < g.area * 0.2: perdu.append((d['NAME'], round(g2.area / g.area, 2)))
    sortie.append({'type': 'Feature', 'properties': {'code': 'CH%d' % d['BFS_NUMMER'], 'canton': CANT[d['KANTONSNUM']],
                   'nom_officiel': d['NAME'], 'pop': d['EINWOHNERZ'], 'ha': d['GEM_FLAECH'], 'lac_ha': d['SEE_FLAECH']},
                   'geometry': mapping(wgs(g2))})
json.dump({'type': 'FeatureCollection', 'features': sortie}, open('/home/claude/s3/ch/jeu/communes-wgs84.geojson', 'w'))
json.dump({'type': 'FeatureCollection', 'features': [{'type': 'Feature', 'properties': {}, 'geometry': mapping(wgs(g))} for g in lacs]},
          open('/home/claude/s3/ch/jeu/lacs-wgs84.geojson', 'w'))
json.dump({'type': 'FeatureCollection', 'features': [{'type': 'Feature', 'properties': {}, 'geometry': mapping(wgs(pays))}]},
          open('/home/claude/s3/ch/jeu/suisse-wgs84.geojson', 'w'))
print(len(sortie), 'communes ;', coupees, 'découpées par un lac ;', len(lacs), 'lacs ; communes réduites à moins de 20 % :', perdu)
