# Belgique : la table des 565 communes pour le jeu.
# Population : Statbel, population par secteur statistique au 1/1/2025 (nouveau découpage), sommée par commune.
# Rareté (décision de Nataël, 18/11 23 h 10) : classement par population en Belgique avec les proportions de la France
# métropolitaine (0,87 / 2,92 / 9,80 / 36,96 / 49,45 %) → 5 légendaires, 17 épiques, 55 rares, 209 peu communes, 279 communes.
# Noms (règle des grandes villes, 18/11 22 h 25) : nom français (Statbel) pour les communes de 30 000 hab. ou plus et les
# chefs-lieux de province ; ailleurs le nom officiel : néerlandais en Flandre, français en Wallonie et à Bruxelles,
# allemand dans les 9 communes germanophones.
import csv, json, os, collections
ICI = os.path.dirname(os.path.abspath(__file__))
base = json.load(open(os.path.join(ICI, 'communes-base.json')))
pop = json.load(open(os.path.join(ICI, 'population-statbel-2025.json')))
CHEFS_LIEUX = {'11002', '24062', '25112', '31005', '44021', '53053', '62063', '71022', '81001', '92094', '21004'}   # Anvers, Louvain, Wavre, Bruges, Gand, Mons, Liège, Hasselt, Arlon, Namur, Bruxelles
GERMANOPHONES = {'63001', '63012', '63013', '63023', '63040', '63048', '63061', '63067', '63087'}
PARTS = [('legendaire', 0.0087), ('epique', 0.0292), ('rare', 0.0980), ('peucommun', 0.3696)]
codes = sorted(base, key=lambda k: (-pop[k[2:]], k))
n = len(codes); bornes, cumul = [], 0.0
for t, p in PARTS:
    cumul += p; bornes.append((t, round(cumul * n)))
def tier(rang):
    for t, b in bornes:
        if rang <= b: return t
    return 'commun'
lignes = []
for rang, k in enumerate(codes, 1):
    b, nis = base[k], k[2:]
    officiel = b['de'] if nis in GERMANOPHONES else b['nl'] if b['region'] == '02000' else b['fr']
    nom = b['fr'] if (pop[nis] >= 30000 or nis in CHEFS_LIEUX) else officiel
    lignes.append({'code': k, 'nom': nom, 'departement': b['prov'], 'population': pop[nis], 'latitude': b['lat'], 'longitude': b['lon'],
                   'tier': tier(rang), 'rang': rang, 'nom_officiel': officiel, 'nom_fr': b['fr'], 'nom_nl': b['nl'], 'nom_de': b['de']})
os.makedirs(os.path.join(ICI, '..', 'jeu'), exist_ok=True)
with open(os.path.join(ICI, '..', 'jeu', 'communes-belgique.csv'), 'w', newline='', encoding='utf-8') as fh:
    w = csv.DictWriter(fh, fieldnames=list(lignes[0].keys())); w.writeheader(); w.writerows(sorted(lignes, key=lambda l: l['code']))
print('raretés :', collections.Counter(l['tier'] for l in lignes).most_common())
print('légendaires :', ', '.join(l['nom'] for l in lignes if l['tier'] == 'legendaire'))
print('épiques :', ', '.join(l['nom'] for l in lignes if l['tier'] == 'epique'))
print('seuils de population : ' + ', '.join('%s ≥ %d' % (t, min(l['population'] for l in lignes if l['tier'] == t)) for t, _ in PARTS + [('commun', 0)]))
print('noms français ≠ officiels :', sum(1 for l in lignes if l['nom'] != l['nom_officiel']))
