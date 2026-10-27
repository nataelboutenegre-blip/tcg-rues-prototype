# -*- coding: utf-8 -*-
u"""
patch216 — héberger supabase-js et d3 dans le dépôt au lieu du CDN (audit 26-27 oct).
Supprime la dépendance aux CDN jsDelivr/cdnjs : un CDN compromis ne peut plus
voler la session des joueurs (gardée dans le localStorage), et plus de fuite
d'IP vers ces CDN. Fichiers ajoutés : lib/supabase-js-2.117.2.umd.js (identique
au build npm 2.117.2) et lib/d3-7.8.5.min.js (d3 7.8.5). Vérifiés : ils
exposent bien supabase.createClient, d3.select et d3.Delaunay.
Aucun changement de comportement du jeu. Sans SQL.
"""
import io, os
ICI = os.path.dirname(os.path.abspath(__file__))
BASE = os.path.dirname(ICI) if os.path.basename(ICI) == '_patchs' else ICI
def lire(n):
    with io.open(os.path.join(BASE, n), encoding='utf-8') as f: return f.read()
def ecrire(n, s):
    with io.open(os.path.join(BASE, n), 'w', encoding='utf-8') as f: f.write(s)
def rep(s, a, b, n=1):
    c = s.count(a); assert c == n, (a[:80], c, n); return s.replace(a, b)

for f in ('lib/supabase-js-2.117.2.umd.js', 'lib/d3-7.8.5.min.js'):
    assert os.path.exists(os.path.join(BASE, f)), 'manque ' + f

h = lire('index.html')
assert 'lib/supabase-js' not in h, 'patch216 deja applique'
h = rep(h,
  u'<script defer src="https://cdn.jsdelivr.net/npm/@supabase/supabase-js@2.117.2/dist/umd/supabase.js"></script>',
  u'<script defer src="lib/supabase-js-2.117.2.umd.js"></script>')
h = rep(h,
  u'<script defer src="https://cdnjs.cloudflare.com/ajax/libs/d3/7.8.5/d3.min.js"></script>',
  u'<script defer src="lib/d3-7.8.5.min.js"></script>')
ecrire('index.html', h)
print('patch216 ok')
