# Espagne : contours (communes, provinces, pays) et table des communes, au format du jeu.
# Entrées (dossier brut/ de telecharger-espagne.py) :
#   ign--administrativeunit.geojson  IGN España, unités administratives (CC BY 4.0 ign.es)
#   diccionario26.xlsx               INE, codes des municipios au 1/1/2026 (la liste de référence)
#   ine-population.json              INE, tableau 29005 : population au 1/1/2025 par municipio (série au nom de la commune)
#   wikidata-communes.csv, wikidata-population.csv, photos-inventaire.csv  (Wikidata CC0, Commons)
# Codes : communes « ES » + code INE à 5 chiffres (ES28079 = Madrid) ; provinces « E » + 2 chiffres (E28 = Madrid),
# car 01…52 sont pris par les départements français. Régions : les 17 communautés autonomes, plus Ceuta et Melilla.
# On ne garde que les municipios du dictionnaire INE : les « condominios » de l'IGN (terres partagées) sont écartés.
# Rareté : proportions de la France métropolitaine (comme la Belgique et le Luxembourg), classement par population.
# Noms : nom officiel INE, article remis devant (« Rozas de Madrid, Las » → « Las Rozas de Madrid ») ;
# nom français pour les villes de 20 000 habitants et plus quand Wikipédia en a un différent (Séville, Saragosse…).
# Usage : python3 espagne-jeu.py <dossier brut> <dossier de travail>
import csv, json, os, re, subprocess, sys, unicodedata, collections
import openpyxl
from shapely.geometry import shape
from shapely.ops import polylabel

BRUT, W = sys.argv[1], sys.argv[2]
ICI = os.path.dirname(os.path.abspath(__file__)); OUT = os.path.join(ICI, '..', 'jeu')
os.makedirs(W, exist_ok=True); os.makedirs(os.path.join(OUT, 'contours'), exist_ok=True)
SEUIL_NOM_FR = 20000
# libellés français de Wikidata qui n'en sont pas (asturien, castillan, traduction forcée) : on garde le nom officiel
PAS_FRANCAIS = {'Las Palmas de Gran Canaria', 'Langreo', 'Almassora', 'Vila-real', 'Valle de Egüés/Eguesibar',
                'Las Torres de Cotillas', 'Altea'}
# villes à double nom officiel connues en France sous un seul
NOM_FORCE = {'03014': 'Alicante', '03065': 'Elche', '12040': 'Castellón de la Plana'}

PROVINCES = {   # code INE -> nom français
 '01': 'Alava', '02': 'Albacete', '03': 'Alicante', '04': 'Almería', '05': 'Ávila', '06': 'Badajoz', '07': 'Îles Baléares',
 '08': 'Barcelone', '09': 'Burgos', '10': 'Cáceres', '11': 'Cadix', '12': 'Castellón', '13': 'Ciudad Real', '14': 'Cordoue',
 '15': 'La Corogne', '16': 'Cuenca', '17': 'Gérone', '18': 'Grenade', '19': 'Guadalajara', '20': 'Guipuscoa', '21': 'Huelva',
 '22': 'Huesca', '23': 'Jaén', '24': 'León', '25': 'Lérida', '26': 'La Rioja', '27': 'Lugo', '28': 'Madrid', '29': 'Malaga',
 '30': 'Murcie', '31': 'Navarre', '32': 'Ourense', '33': 'Asturies', '34': 'Palencia', '35': 'Las Palmas', '36': 'Pontevedra',
 '37': 'Salamanque', '38': 'Santa Cruz de Tenerife', '39': 'Cantabrie', '40': 'Ségovie', '41': 'Séville', '42': 'Soria',
 '43': 'Tarragone', '44': 'Teruel', '45': 'Tolède', '46': 'Valence', '47': 'Valladolid', '48': 'Biscaye', '49': 'Zamora',
 '50': 'Saragosse', '51': 'Ceuta', '52': 'Melilla'}
REGIONS = {   # CODAUTO INE -> nom français
 '01': 'Andalousie', '02': 'Aragon', '03': 'Asturies', '04': 'Îles Baléares', '05': 'Canaries', '06': 'Cantabrie',
 '07': 'Castille-et-León', '08': 'Castille-La Manche', '09': 'Catalogne', '10': 'Communauté valencienne', '11': 'Estrémadure',
 '12': 'Galice', '13': 'Communauté de Madrid', '14': 'Région de Murcie', '15': 'Navarre', '16': 'Pays basque', '17': 'La Rioja',
 '18': 'Ceuta', '19': 'Melilla'}

norm = lambda s: re.sub(r'[^a-z0-9]', '', unicodedata.normalize('NFKD', s or '').encode('ascii', 'ignore').decode().lower())

def article_devant(n):
    # « Rozas de Madrid, Las » → « Las Rozas de Madrid » ; « Palmas de Gran Canaria, Las » ; « Escala, L' » → « L'Escala »
    # les noms doubles « A/B » sont traités moitié par moitié
    def un(x):
        m = re.match(r"^(.*), (El|La|Los|Las|L'|Els|Les|Es|Sa|Ses|S'|O|A|Os|As|Lo)$", x.strip(), re.I)
        if not m: return x.strip()
        a = m.group(2)
        a = a[0].upper() + a[1:]
        return (a + m.group(1)) if a.endswith("'") else (a + ' ' + m.group(1))
    return '/'.join(un(p) for p in n.split('/'))

# 1. dictionnaire INE : la liste des communes
wb = openpyxl.load_workbook(os.path.join(BRUT, 'diccionario26.xlsx'), read_only=True)
dic = {}
for r in list(wb.active.iter_rows(values_only=True))[2:]:
    if not r or not r[1]: continue
    ca, pr, mu, _, nom = [str(x).strip() if x is not None else '' for x in r[:5]]
    dic[pr.zfill(2) + mu.zfill(3)] = {'nom_ine': nom, 'prov': pr.zfill(2), 'ca': ca.zfill(2)}
print('INE : %d municipios' % len(dic))

# 2. population INE 2025 (séries au nom de la commune ; 17 noms en double, départagés par Wikidata)
pop_wd = {}
for r in csv.DictReader(open(os.path.join(BRUT, 'wikidata-population.csv'), encoding='utf-8')):
    if r['population'] and (r['code'] not in pop_wd or r['date'] > pop_wd[r['code']][1]):
        try: pop_wd[r['code']] = (int(float(r['population'])), r['date'])
        except ValueError: pass
par_nom = collections.defaultdict(list)
for s in json.load(open(os.path.join(BRUT, 'ine-population.json'))):
    if '. Total. Total habitantes' not in s['Nombre']: continue
    v = [x['Valor'] for x in s['Data'] if x.get('Valor') is not None]
    if v: par_nom[norm(s['Nombre'].split('. Total. Total habitantes')[0])].append(int(v[0]))
pop, sources = {}, collections.Counter()
for code, x in dic.items():
    cand = par_nom.get(norm(x['nom_ine']), [])
    if len(cand) == 1:
        pop[code] = cand[0]; sources['ine'] += 1
    elif len(cand) > 1 and code in pop_wd:
        pop[code] = min(cand, key=lambda p: abs(p - pop_wd[code][0])); sources['ine (homonyme, départagé)'] += 1
    elif code in pop_wd:
        pop[code] = pop_wd[code][0]; sources['wikidata (%s)' % pop_wd[code][1][:4]] += 1
    else:
        pop[code] = 0; sources['aucune'] += 1
print('population :', dict(sources))

# 3. contours IGN : municipios du dictionnaire seulement
d = json.load(open(os.path.join(BRUT, 'ign--administrativeunit.geojson')))
feats, ecartes = [], []
for f in d['features']:
    p = f['properties']
    if p.get('nationallevelname') != 'Municipio': continue
    code = p['nationalcode'][-5:]
    if code not in dic: ecartes.append((code, p['nameunit'])); continue
    feats.append({'type': 'Feature', 'geometry': f['geometry'],
                  'properties': {'code': 'ES' + code, 'prov': 'E' + dic[code]['prov'], 'ign': p['nameunit']}})
del d
manquent = sorted(set(dic) - {f['properties']['code'][2:] for f in feats})
print('IGN : %d municipios gardés, %d écartés (pas dans l\'INE), %d de l\'INE sans contour' % (len(feats), len(ecartes), len(manquent)))
if manquent: print('   sans contour :', ', '.join('%s %s' % (c, dic[c]['nom_ine']) for c in manquent[:20]))
json.dump({'type': 'FeatureCollection', 'features': feats}, open(os.path.join(W, 'communes-codes.json'), 'w'))
del feats

def ms(*a): subprocess.run(['mapshaper', '-quiet', *a], check=True)
# communes espagnoles ≈ 62 km² (France 16, Belgique 53) : on vise ≈ 30 points par commune, comme la Belgique
ms('-i', os.path.join(W, 'communes-codes.json'), 'name=communes', '-simplify', os.environ.get('ES_SIMPLE', '3%'), 'weighted', 'keep-shapes',
   '-clean', '-o', os.path.join(W, 'communes.json'), 'format=geojson',
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
par, base, points = {}, {}, 0
for f in com['features']:
    p = f['properties']
    if not f['geometry']: print('   ! géométrie vide après simplification :', p['code']); continue
    a = anneaux(f['geometry']); points += sum(len(r) for r in a)
    par.setdefault(p['prov'], {})[p['code']] = a
    g = shape(f['geometry']); gros = max(getattr(g, 'geoms', [g]), key=lambda x: x.area)
    try: c = polylabel(gros.buffer(0), tolerance=0.001)
    except Exception: c = gros.representative_point()
    if not gros.contains(c): c = gros.representative_point()
    base[p['code']] = {'prov': p['prov'], 'lat': round(c.y, 4), 'lon': round(c.x, 4)}
tailles = {}
for k, v in par.items():
    t = json.dumps(v, separators=(',', ':')); open(os.path.join(OUT, 'contours', k + '.json'), 'w').write(t); tailles[k] = len(t)
prov = {f['properties']['prov']: anneaux(f['geometry'], False) for f in json.load(open(os.path.join(W, 'provinces.json')))['features']}
json.dump(prov, open(os.path.join(OUT, 'provinces.json'), 'w'), separators=(',', ':'))
P = json.load(open(os.path.join(W, 'pays.json')))
pays = [r for g in (P.get('geometries') or [f['geometry'] for f in P.get('features', [])]) if g for r in anneaux(g, False)]
json.dump(pays, open(os.path.join(OUT, 'espagne-contour.json'), 'w'), separators=(',', ':'))

# 4. noms, raretés, photos
wd = {}
for r in csv.DictReader(open(os.path.join(BRUT, 'wikidata-communes.csv'), encoding='utf-8')):
    wd.setdefault(r['code'], r)   # doublons d'entités : la première
ph = {r['code']: r for r in csv.DictReader(open(os.path.join(BRUT, 'photos-inventaire.csv'), encoding='utf-8'))}
def photo(k):
    r = ph.get(k)
    return r['fichier'] if r and (r['auteur'] or r['licence'] in ('Public domain', 'CC0')) else ''
PARTS = [('legendaire', 0.0087), ('epique', 0.0292), ('rare', 0.0980), ('peucommun', 0.3696)]
codes = sorted(base, key=lambda k: (-pop[k[2:]], k)); n = len(codes); bornes, cumul = [], 0.0
for t, p in PARTS:
    cumul += p; bornes.append((t, round(cumul * n)))
def tier(rang):
    for t, b in bornes:
        if rang <= b: return t
    return 'commun'
lignes, francises = [], []
for rang, k in enumerate(codes, 1):
    c5, b = k[2:], base[k]; w = wd.get(c5) or {}
    officiel = article_devant(dic[c5]['nom_ine'])
    nom = officiel
    fr = (w.get('nom_fr') or '').strip()
    if c5 in NOM_FORCE:
        nom = NOM_FORCE[c5]; francises.append((officiel, nom, pop[c5]))
    elif pop[c5] >= SEUIL_NOM_FR and fr and officiel not in PAS_FRANCAIS and norm(fr) != norm(officiel) \
         and not any(norm(fr) == norm(x) for x in officiel.split('/')):
        nom = fr; francises.append((officiel, fr, pop[c5]))
    lignes.append({'code': k, 'nom': nom, 'departement': b['prov'], 'region': REGIONS[dic[c5]['ca']], 'population': pop[c5],
                   'latitude': b['lat'], 'longitude': b['lon'], 'tier': tier(rang), 'rang': rang, 'nom_officiel': officiel,
                   'nom_es': w.get('nom_es', ''), 'nom_ca': w.get('nom_ca', ''), 'nom_eu': w.get('nom_eu', ''), 'nom_gl': w.get('nom_gl', ''),
                   'wikidata': w.get('wikidata', ''), 'article_fr': w.get('article_fr', ''), 'photo': photo(k)})
with open(os.path.join(OUT, 'communes-espagne.csv'), 'w', newline='', encoding='utf-8') as fh:
    wr = csv.DictWriter(fh, fieldnames=list(lignes[0].keys())); wr.writeheader(); wr.writerows(sorted(lignes, key=lambda l: l['code']))
json.dump({'E' + k: v for k, v in PROVINCES.items()}, open(os.path.join(OUT, 'provinces-noms.json'), 'w'), ensure_ascii=False, indent=0)

print('\ncommunes %d, provinces %d, population %d, %.1f points par commune, contours %.1f Mo, pays %d anneaux'
      % (n, len(prov), sum(pop[k[2:]] for k in codes), points / max(1, n), sum(tailles.values()) / 1e6, len(pays)))
print('plus gros fichier de province : %s (%.0f Ko)' % max(((k, v / 1e3) for k, v in tailles.items()), key=lambda x: x[1]))
print('raretés :', collections.Counter(l['tier'] for l in lignes).most_common())
for t in ('legendaire', 'epique'):
    print('%s : %s' % (t, ', '.join('%s (%d)' % (l['nom'], l['population']) for l in sorted(lignes, key=lambda l: l['rang']) if l['tier'] == t)))
print('noms français (%d) : %s' % (len(francises), '; '.join('%s → %s' % (a, b) for a, b, _ in sorted(francises, key=lambda x: -x[2]))))
print('photos : %d ; articles fr : %d ; wikidata : %d' % (sum(1 for l in lignes if l['photo']), sum(1 for l in lignes if l['article_fr']), sum(1 for l in lignes if l['wikidata'])))
print('écartés IGN :', ', '.join('%s %s' % x for x in ecartes[:12]), '…' if len(ecartes) > 12 else '')
