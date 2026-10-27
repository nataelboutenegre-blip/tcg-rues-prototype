# -*- coding: utf-8 -*-
u"""
patch225 — nouvel écran de démarrage : la France coupée entre Terra et Front
(version 2 de l'aperçu, choisie par Nataël le 27/10).

- index.html : le dessin (contour de la France, moitié Terra en courbes de
  niveau, moitié Front en hachures, ligne de partage dorée, Terra | Front).
  Il s'anime dès l'ouverture, avant le téléchargement de app.js.
- style.css : remplace le bloc patch122.
- app.js : le contour doré suit le chargement ; à l'arrivée dans le jeu, le
  dernier mode joué recouvre la France puis le jeu apparaît (environ 1 s).
  Accueil, connexion, bouton Animation coupé ou mouvements réduits : fondu.
  Une astuce au hasard parmi 8.
"""
import io, os
ICI = os.path.dirname(os.path.abspath(__file__))
BASE = os.path.dirname(ICI) if os.path.basename(ICI) == '_patchs' else ICI
def lire(n):
    with io.open(os.path.join(BASE, n), encoding='utf-8') as f: return f.read()
def ecrire(n, s):
    with io.open(os.path.join(BASE, n), 'w', encoding='utf-8') as f: f.write(s)
def rep(s, a, b, n=1):
    c = s.count(a); assert c == n, ('MATCH', a[:70], 'trouve', c, 'attendu', n); return s.replace(a, b)
def tranche(s, debut, fin, nouveau):
    assert s.count(debut) == 1, ('DEBUT', debut[:60], s.count(debut))
    i = s.index(debut); j = s.index(fin, i); assert j > i, 'FIN'
    return s[:i] + nouveau + s[j + len(fin):]

# 1. index.html
h = lire('index.html')
assert 'dmPolyT' not in h, 'patch225 deja passe'
h = tranche(h, '<div class="demarrage" id="demarrage" role="status" aria-live="polite">', '</div>\n\n<svg id="fondTopo"',
            lire('_patchs/patch225-ecran.html') + '\n<svg id="fondTopo"')
ecrire('index.html', h)

# 2. style.css
c = lire('style.css')
c = tranche(c, '/* ---------- patch122 : ecran de chargement ---------- */',
            '@media (prefers-reduced-motion:reduce){ .dm-anneau{ animation:none; stroke-dashoffset:0; } .dm-epingle{ animation:none; } }\n',
            lire('_patchs/patch225.css'))
ecrire('style.css', c)

# 3. app.js
s = lire('app.js')
s = tranche(s, '// ---------- patch122 : ecran de chargement ----------\n', '// jamais bloque derriere l\'ecran : 15 s au plus\nsetTimeout(dmFin, 15000);\n',
            lire('_patchs/patch225-js.js'))
s = rep(s, "  await loadPackStatus();\n  dmMesure('paquets');\n  dmFin();", "  await loadPackStatus();\n  dmMesure('paquets');\n  dmFin(true);   // patch225 : on arrive dans le jeu")
ecrire('app.js', s)
print('patch225 ok')
