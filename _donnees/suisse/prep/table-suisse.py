# Table des communes suisses pour le jeu : code, nom (français si Wikipédia en a un), canton, population, rareté.
import csv, json, re, collections
B = '/mnt/user-data/uploads/tcg-rues-prototype/_donnees/suisse/brut/'
geo = json.load(open('/home/claude/s3/ch/jeu/communes-wgs84.geojson'))
wd = {}
for l in csv.DictReader(open(B + 'wikidata-communes.csv', encoding='utf-8')):
    wd.setdefault(l['ofs'], []).append(l)
pops = collections.defaultdict(list)
for l in csv.DictReader(open(B + 'wikidata-population.csv', encoding='utf-8')):
    pops[l['ofs']].append((l['date'], int(float(l['population']))))
photos = {l['code']: l for l in csv.DictReader(open(B + 'photos-inventaire-suisse.csv', encoding='utf-8'))}
CHEFS_LIEUX = {'Zürich','Bern','Luzern','Altdorf','Schwyz','Sarnen','Stans','Glarus','Zug','Fribourg','Solothurn','Basel','Liestal','Schaffhausen','Herisau','Appenzell','St. Gallen','Chur','Aarau','Frauenfeld','Bellinzona','Lausanne','Sion','Neuchâtel','Genève','Delémont'}
SEUILS = [(30000, 'legendaire'), (8000, 'epique'), (2300, 'rare'), (450, 'peucommun'), (0, 'commun')]
sans_suffixe = lambda n: re.sub(r'\s*\([^)]*\)\s*$', '', n or '').strip()
lignes, sources, ecarts = [], collections.Counter(), []
for f in geo['features']:
    p = f['properties']; ofs = p['code'][2:]
    w = wd.get(ofs, [])
    fr = next((x['nom_fr'] for x in w if x['nom_fr']), '')
    officiel = sans_suffixe(p['nom_officiel'])
    # nom français seulement pour les villes connues (≥ 30 000 hab. ou chef-lieu) : ailleurs, « Perles »
    # pour Pieterlen ou « Bâche » pour Bettlach dérouteraient plus qu'ils n'aident
    connue = (p['pop'] or 0) >= 30000 or sans_suffixe(p['nom_officiel']) in CHEFS_LIEUX
    nom = sans_suffixe(fr) if (fr and connue) else officiel
    sources['nom français' if nom != officiel else 'officiel'] += 1
    if nom != officiel: ecarts.append((officiel, nom, p['canton']))
    pop = p['pop'] or 0
    tier = next(t for s, t in SEUILS if pop >= s)
    wdpop = max(pops.get(ofs, [('', None)]))[1]
    lignes.append({'code': p['code'], 'nom': nom, 'nom_officiel': p['nom_officiel'], 'canton': p['canton'], 'population': pop,
                   'pop_wikidata': wdpop, 'tier': tier, 'wikidata': w[0]['wikidata'] if w else '', 'article_fr': next((x['article_fr'] for x in w if x['article_fr']), ''),
                   'photo': photos.get(p['code'], {}).get('fichier', '')})
json.dump(lignes, open('/home/claude/s3/ch/jeu/table-suisse.json', 'w'), ensure_ascii=False)
print(len(lignes), 'communes ; noms :', dict(sources))
print('raretés :', collections.Counter(l['tier'] for l in lignes).most_common())
print('sans population :', sum(1 for l in lignes if not l['population']), '; sans Wikidata :', sum(1 for l in lignes if not l['wikidata']),
      '; sans photo :', sum(1 for l in lignes if not l['photo']), '; sans article fr :', sum(1 for l in lignes if not l['article_fr']))
print('noms français différents du nom officiel :', len(ecarts))
print('chefs-lieux trouvés :', sorted({sans_suffixe(f['properties']['nom_officiel']) for f in geo['features']} & CHEFS_LIEUX).__len__(), '/ 26')
for e in sorted(ecarts, key=lambda e: e[2])[:60]: print('   ', e)
dup = collections.Counter((l['nom'], l['canton']) for l in lignes); print('doublons nom+canton :', [k for k, v in dup.items() if v > 1])
dupn = collections.Counter(l['nom'] for l in lignes); print('homonymes (cantons différents) :', sum(1 for v in dupn.values() if v > 1))
big = sorted(lignes, key=lambda l: -l['population'])[:12]; print([ (l['nom'], l['population'], l['pop_wikidata']) for l in big])
d = [abs(l['population'] - l['pop_wikidata']) / max(l['population'], 1) for l in lignes if l['pop_wikidata']]
print('écart pop swisstopo / wikidata > 10 % :', sum(1 for x in d if x > 0.1), 'sur', len(d))
