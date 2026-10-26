#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
TerraFront — les contours manquants de la carte (26 octobre 2026)

Environ 160 communes n'ont pas de contour dans contours/XX.json (souvent de
petites communes, perdues à la simplification) : elles ne sont pas cliquables
sur la carte. Signalé pour Châteauneuf (71) par D.C.A.

Ce script télécharge leur vrai contour sur geo.api.gouv.fr (service public,
sans clé), le simplifie comme les autres et l'ajoute au bon fichier.

USAGE (depuis le dossier du jeu, sur le Mac : il faut internet)
    python3 _sql/contours-manquants.py            # simulation : liste ce qui manque
    python3 _sql/contours-manquants.py --ecrire   # télécharge et écrit les fichiers
Rejouable : une commune qui a déjà son contour est sautée.
Les arrondissements de Paris, Lyon et Marseille ont leurs propres contours.
"""
import json, os, sys, time, urllib.request, urllib.error

ICI = os.path.dirname(os.path.abspath(__file__))
JEU = os.path.dirname(ICI)
ECRIRE = '--ecrire' in sys.argv
TOL = 0.0008          # même simplification que les contours existants
UA = 'TerraFront/1.0 (https://terrafront.fr) python-urllib'

def arrondissement(code):
    return code.startswith('751') or code.startswith('6938') or code[:3] == '132'

def rdp(pts, tol):
    """Ramer-Douglas-Peucker sur une liste de points [x, y]."""
    if len(pts) < 3: return pts
    (x1, y1), (x2, y2) = pts[0], pts[-1]
    dx, dy = x2 - x1, y2 - y1
    n = (dx * dx + dy * dy) ** .5
    dmax, imax = 0, 0
    for i in range(1, len(pts) - 1):
        x, y = pts[i]
        d = abs(dy * x - dx * y + x2 * y1 - y2 * x1) / n if n else ((x - x1) ** 2 + (y - y1) ** 2) ** .5
        if d > dmax: dmax, imax = d, i
    if dmax <= tol: return [pts[0], pts[-1]]
    return rdp(pts[:imax + 1], tol)[:-1] + rdp(pts[imax:], tol)

def anneau(coords):
    pts = [[float(x), float(y)] for x, y in coords]
    if len(pts) > 1 and pts[0] == pts[-1]: pts = pts[:-1]
    s = rdp(pts + [pts[0]], TOL)[:-1]
    if len(s) < 3: s = pts                       # une toute petite commune : on garde tout
    out = []
    for x, y in s:
        p = [round(x, 4), round(y, 4)]
        if not out or out[-1] != p: out.append(p)
    return out if len(out) >= 3 else None

def anneaux(geom):
    polys = [geom['coordinates']] if geom['type'] == 'Polygon' else geom['coordinates']
    res = []
    for poly in polys:
        for ring in poly:                          # extérieur puis trous
            a = anneau(ring)
            if a: res.append(a)
    return res

def contour(code):
    url = 'https://geo.api.gouv.fr/communes/%s?fields=contour&format=json&geometry=contour' % code
    req = urllib.request.Request(url, headers={'User-Agent': UA})
    for essai in range(3):
        try:
            with urllib.request.urlopen(req, timeout=20) as r:
                d = json.load(r)
            g = d.get('contour')
            return anneaux(g) if g else None
        except urllib.error.HTTPError as e:
            if e.code == 404: return None
            time.sleep(1 + essai)
        except Exception:
            time.sleep(1 + essai)
    return None

communes = json.load(open(os.path.join(JEU, 'data', 'communes.json'), encoding='utf-8'))
par_dep = {}
for r in communes:
    par_dep.setdefault(r[1], []).append(r)

manquants = []
for dep in sorted(par_dep):
    f = os.path.join(JEU, 'contours', dep + '.json')
    if not os.path.exists(f): continue
    C = json.load(open(f, encoding='utf-8'))
    for r in par_dep[dep]:
        if r[-1] not in C and not arrondissement(r[-1]):
            manquants.append((dep, r[-1], r[0]))

print('%d communes sans contour sur la carte.' % len(manquants))
if not ECRIRE:
    for dep, code, nom in manquants[:200]: print('  %s  %s  %s' % (dep, code, nom))
    print('\nSimulation : rien n\'a changé. Pour télécharger et écrire : python3 _sql/contours-manquants.py --ecrire')
    sys.exit(0)

ajoutes, rates, fichiers = 0, [], {}
for i, (dep, code, nom) in enumerate(manquants, 1):
    a = contour(code)
    if not a:
        rates.append((code, nom)); print('  ✗ %s %s' % (code, nom)); continue
    if dep not in fichiers:
        fichiers[dep] = json.load(open(os.path.join(JEU, 'contours', dep + '.json'), encoding='utf-8'))
    fichiers[dep][code] = a
    ajoutes += 1
    print('  ✓ %s %s (%d points)' % (code, nom, sum(len(x) for x in a)))
    time.sleep(0.15)                               # on reste poli avec le service public
for dep, C in fichiers.items():
    json.dump(C, open(os.path.join(JEU, 'contours', dep + '.json'), 'w', encoding='utf-8'), separators=(',', ':'), ensure_ascii=False)
print('\n%d contours ajoutés dans %d fichiers, %d introuvables.' % (ajoutes, len(fichiers), len(rates)))
if rates: print('Introuvables :', ', '.join('%s %s' % r for r in rates))
print('Dis-le à Claude : il commitera les fichiers contours/ avec le patch208.')
