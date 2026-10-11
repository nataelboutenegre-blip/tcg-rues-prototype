# -*- coding: utf-8 -*-
u"""
Télécharge les contours officiels des arrondissements de Paris, Lyon et
Marseille (data.gouv.fr, jeu « Contours administratifs », Etalab, Licence
Ouverte) dans _sql/arrondissements-municipaux.geojson.

    cd ~/Code/tcg-rues-prototype && python3 _sql/arrondissements-telecharger.py

Il demande à data.gouv.fr la liste des fichiers du jeu, prend le plus récent
des arrondissements municipaux au niveau de détail 50 m (sinon 100 m), et le
décompresse s'il le faut. Rien d'autre n'est modifié.
"""
import gzip, io, json, os, re, urllib.request

ICI = os.path.dirname(os.path.abspath(__file__))
SORTIE = os.path.join(ICI, 'arrondissements-municipaux.geojson')
UA = {'User-Agent': 'TerraFront/1.0 (https://terrafront.fr)'}

def lire(url):
    with urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=120) as r:
        return r.read()

meta = json.loads(lire('https://www.data.gouv.fr/api/1/datasets/contours-administratifs/'))
candidats = []
for r in meta.get('resources', []):
    texte = (r.get('title', '') + ' ' + r.get('url', '')).lower()
    if 'arrondissements-municipaux' not in texte and 'arrondissements municipaux' not in texte:
        continue
    if 'geojson' not in texte:
        continue
    niveau = 0 if '50m' in texte else 1 if '100m' in texte else 9
    annee = max([int(a) for a in re.findall(r'20\d\d', texte)] or [0])
    candidats.append((niveau, -annee, r['url'], r.get('title', '')))

if not candidats:
    print('Aucun fichier « arrondissements municipaux » trouvé. Fichiers du jeu :')
    for r in meta.get('resources', [])[:80]:
        print('  ', r.get('title'), '|', r.get('url'))
    raise SystemExit(1)

candidats.sort()
niveau, annee, url, titre = candidats[0]
print('Téléchargement :', titre, '\n  ', url)
octets = lire(url)
if octets[:2] == b'\x1f\x8b':
    octets = gzip.decompress(octets)
d = json.loads(octets)
codes = sorted(f['properties'].get('code', '') for f in d.get('features', []))
with open(SORTIE, 'wb') as f:
    f.write(octets)
print('%d arrondissements enregistrés dans _sql/arrondissements-municipaux.geojson' % len(codes))
print('  ', ' '.join(codes))
