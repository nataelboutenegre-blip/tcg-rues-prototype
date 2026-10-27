# -*- coding: utf-8 -*-
u"""
patch226 — les cartes de la vitrine ne s'étirent plus (bug signalé par
LeoLesel le 27/10 sur iPhone : « Ma vitrine Front » avec des cartes géantes,
impossible d'en sortir).

Cause pas reproduite (pas de Safari sur le banc). Ce qui colle à sa capture :
le dessin du skin (un canvas) qui se retrouve DANS la carte au lieu d'être
posé dessus ; la carte (format 2/3) grandit alors pour le contenir. Sur le
banc, ça donne exactement des cartes hautes avec le skin en haut.
Correctif défensif, sans effet visible en temps normal :
- le canvas du skin est toujours posé par-dessus la carte ;
- dans la vitrine (bande, grille, étagère du profil), une carte garde son
  format quoi qu'il arrive.
"""
import io, os
ICI = os.path.dirname(os.path.abspath(__file__))
BASE = os.path.dirname(ICI) if os.path.basename(ICI) == '_patchs' else ICI
def lire(n):
    with io.open(os.path.join(BASE, n), encoding='utf-8') as f: return f.read()
def ecrire(n, s):
    with io.open(os.path.join(BASE, n), 'w', encoding='utf-8') as f: f.write(s)
c = lire('style.css')
assert 'patch226' not in c
c = c.rstrip('\n') + u'''

/* ---------- patch226 : une carte de vitrine ne s'étire jamais ---------- */
.mini-int > canvas.skin-gl{ position:absolute; inset:0; width:100%; height:100%; display:block; pointer-events:none; }
.vt-bande .mini, .vt-grille .mini, .vt-etagere .mini{ min-height:0; overflow:hidden; }
'''
ecrire('style.css', c)
print('patch226 ok')
