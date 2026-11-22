#!/usr/bin/env python3
# Construit la page « Bilan de la saison 2 » à partir de stats.txt et courbes.txt.
# usage : python3 gen.py <sortie.html> [prefixe-des-polices]
import json, sys, os
ICI = os.path.dirname(os.path.abspath(__file__))
sortie = sys.argv[1]
polices = sys.argv[2] if len(sys.argv) > 2 else 'fonts/polices.css'

courbes = {}
for p in open(os.path.join(ICI, 'courbes.txt')).read().strip().split(';'):
    r, v = p.split(':')
    courbes[int(r)] = [int(x) for x in v.split(',')]

cles = ['r', 'p', 'pts', 'c', 'leg', 'dep', 'acq', 'pr', 'pe', 'as', 'asg', 'ea', 'de', 'deg', 'ed',
        'bo', 'boc', 're', 'ec', 'jj', 'ba', 'ci', 'cin', 'bou', 'boun', 'dist']
joueurs = []
for l in open(os.path.join(ICI, 'stats.txt'), encoding='utf-8'):
    l = l.rstrip('\n')
    if not l:
        continue
    f = l.split('|')
    assert len(f) == len(cles), (len(f), l)
    j = {}
    for k, v in zip(cles, f):
        if k in ('p', 'ci', 'bou'):
            j[k] = v
        elif k == 'dist':
            j[k] = v.split() if v else []
        else:
            j[k] = int(v)
    k = courbes[j['r']][:]
    assert len(k) == 29
    k[-1] = j['c']          # dernier point = le classement final (10 h 03)
    j['k'] = k
    joueurs.append(j)
assert len(joueurs) == 101

data = json.dumps({'joueurs': joueurs}, ensure_ascii=False, separators=(',', ':'))
page = open(os.path.join(ICI, 'page.html'), encoding='utf-8').read()
assert page.count('__DATA__') == 1 and page.count('__POLICES__') == 1
page = page.replace('__DATA__', data).replace('__POLICES__', polices)
open(sortie, 'w', encoding='utf-8').write(page)
print('ok', sortie, len(page), 'octets')
