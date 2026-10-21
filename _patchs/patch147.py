# -*- coding: utf-8 -*-
u"""
patch147 — nouveau logo : le T « Relief » (21 octobre).

Le T reste le même (mêmes lignes de niveau, même bleu nuit, même or), en
plus fort : bloc d'or en relief, contour sombre, épaisseur, lignes gravées
dans l'or. Le mot TerraFront ne change pas.

Les images sont remplacées à côté de ce patch (favicon.png,
apple-touch-icon.png, icon-192.png, icon-512.png, logo-terrafront.svg,
og-saison-2.png, og-terrafront.png) et deux fichiers arrivent :
- icon-maskable-512.png : Android découpe l'icône en rond ; le T y est à
  90 % pour ne jamais être rogné. Avant, la même image servait aux deux.
- badge-96.png : la petite icône des notifications Android. Le système
  n'en garde que la transparence ; avec icon-192 (carré plein), il
  affichait un carré blanc. C'est maintenant un T blanc sur fond transparent.

Ici : ?v=2 sur les adresses des icônes et de l'image de partage, pour que
les navigateurs et Discord reprennent les nouvelles images au lieu de
celles qu'ils ont gardées en mémoire. patch-jour-j.py remplace toujours
og-saison-2.png par og-terrafront.png (le ?v=2 suit).
"""
import io, os
ICI = os.path.dirname(os.path.abspath(__file__))
BASE = os.path.dirname(ICI) if os.path.basename(ICI) == '_patchs' else ICI
def lire(n):
    with io.open(os.path.join(BASE, n), encoding='utf-8') as f: return f.read()
def ecrire(n, s):
    with io.open(os.path.join(BASE, n), 'w', encoding='utf-8') as f: f.write(s)
def rempl(src, avant, apres, etiquette):
    n = src.count(avant)
    assert n == 1, u'%s : %d occurrences (attendu 1)' % (etiquette, n)
    return src.replace(avant, apres)

for f in ('icon-maskable-512.png', 'badge-96.png'):
    assert os.path.exists(os.path.join(BASE, f)), u'%s manquant : copier les images avant le patch' % f

h = lire('index.html')
assert 'favicon.png?v=' not in h, u'patch147 deja applique'
h = rempl(h, u'<link rel="apple-touch-icon" href="apple-touch-icon.png">',
             u'<link rel="apple-touch-icon" href="apple-touch-icon.png?v=2">', 'apple-touch')
h = rempl(h, u'<link rel="icon" type="image/png" href="favicon.png">',
             u'<link rel="icon" type="image/png" href="favicon.png?v=2">', 'favicon')
h = rempl(h, u'<meta property="og:image" content="https://terrafront.fr/og-saison-2.png">',
             u'<meta property="og:image" content="https://terrafront.fr/og-saison-2.png?v=2">', 'og:image')
h = rempl(h, u'<meta name="twitter:image" content="https://terrafront.fr/og-saison-2.png">',
             u'<meta name="twitter:image" content="https://terrafront.fr/og-saison-2.png?v=2">', 'twitter:image')
ecrire('index.html', h)

for page in ('cgu.html', 'mentions-legales.html', 'confidentialite.html'):
    p = lire(page)
    p = rempl(p, u'<link rel="icon" type="image/png" href="favicon.png">',
                 u'<link rel="icon" type="image/png" href="favicon.png?v=2">', page)
    ecrire(page, p)

m = lire('manifest.webmanifest')
m = rempl(m, u"""    { "src": "icon-192.png", "sizes": "192x192", "type": "image/png" },
    { "src": "icon-512.png", "sizes": "512x512", "type": "image/png" },
    { "src": "icon-512.png", "sizes": "512x512", "type": "image/png", "purpose": "maskable" }""",
             u"""    { "src": "icon-192.png?v=2", "sizes": "192x192", "type": "image/png" },
    { "src": "icon-512.png?v=2", "sizes": "512x512", "type": "image/png" },
    { "src": "icon-maskable-512.png?v=2", "sizes": "512x512", "type": "image/png", "purpose": "maskable" }""", 'manifest')
ecrire('manifest.webmanifest', m)

sw = lire('sw.js')
sw = rempl(sw, u"""    icon: 'icon-192.png',
    badge: 'icon-192.png',""",
               u"""    icon: 'icon-192.png?v=2',
    badge: 'badge-96.png',""", 'sw badge')
ecrire('sw.js', sw)

print(u'patch147 applique. Lancer : python3 maj-version.py')
