# -*- coding: utf-8 -*-
u"""
patch144 — image de partage 1200x630 (Discord, réseaux) : og-saison-2.png
avec la date pour la semaine de promo, titre et description du lien au
texte de la saison 2. Le jour J, patch-jour-j.py passe à og-terrafront.png.
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
h = lire('index.html')
assert 'og-saison-2.png' not in h, u'patch144 deja applique'
h = rempl(h, u'<meta property="og:title" content="Ta ville n\'appartient qu\'à une seule personne.">',
             u'<meta property="og:title" content="TerraFront — Collectionne la France. Conquiers-la.">', 'titre')
h = rempl(h, u'<meta property="og:description" content="Jeu de collection sur la carte de France : 34 739 communes, une seule personne peut posséder chacune. Gratuit, dans le navigateur.">',
             u'<meta property="og:description" content="Les 35 000 communes du pays sont des cartes. Complète ta propre France en Terra et dispute la carte aux autres joueurs en Front. Gratuit, dans le navigateur.">', 'description')
h = rempl(h, u'<meta property="og:image" content="https://terrafront.fr/icon-512.png">',
             u'<meta property="og:image" content="https://terrafront.fr/og-saison-2.png">\n'
             u'<meta property="og:image:width" content="1200">\n'
             u'<meta property="og:image:height" content="630">\n'
             u'<meta property="og:image:alt" content="TerraFront : carte de France aux territoires colorés et trois cartes de communes. Collectionne la France. Conquiers-la.">', 'image')
h = rempl(h, u'<meta name="twitter:card" content="summary_large_image">',
             u'<meta name="twitter:card" content="summary_large_image">\n<meta name="twitter:image" content="https://terrafront.fr/og-saison-2.png">', 'twitter')
ecrire('index.html', h)
print(u'patch144 applique')
