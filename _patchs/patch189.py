# -*- coding: utf-8 -*-
u"""
patch189 — correctif de patch188 : dans Ma collection, l'en-tete collant
(fond opaque) cachait la lueur du mode et dessinait un rectangle sombre.
Il porte maintenant la meme lueur, placee au meme endroit. Le surtitre
« Mode … » s'affiche aussi sur Ma collection et sur les Regles (titres
ranges dans un bloc). Aucun SQL.
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
css = lire('style.css')
assert 'patch189' not in css, u'patch189 deja applique'
# le surtitre : aussi les titres ranges dans un bloc
for avant, apres in [
  (u"""body.mode-terra .tab-panel > h1::before, body.mode-front .tab-panel > h1::before{""",
   u"""body.mode-terra .tab-panel > h1::before, body.mode-front .tab-panel > h1::before,
body.mode-terra .coll-ligne-titre > h1::before, body.mode-front .coll-ligne-titre > h1::before,
body.mode-terra .regles > h1::before, body.mode-front .regles > h1::before{"""),
  (u"""body.mode-terra .tab-panel > h1::before{ content:"Mode Terra · ta collection"; }""",
   u"""body.mode-terra .tab-panel > h1::before, body.mode-terra .coll-ligne-titre > h1::before, body.mode-terra .regles > h1::before{ content:"Mode Terra · ta collection"; }"""),
  (u"""body.mode-front .tab-panel > h1::before{ content:"Mode Front · la conquête"; }""",
   u"""body.mode-front .tab-panel > h1::before, body.mode-front .coll-ligne-titre > h1::before, body.mode-front .regles > h1::before{ content:"Mode Front · la conquête"; }""")]:
    css = rempl(css, avant, apres, 'surtitre')
css += u"""

/* ---------- patch189 : l'en-tete collant de Ma collection porte la lueur ---------- */
body.mode-terra .coll-entete, body.mode-front .coll-entete{
  background:
    radial-gradient(110% 420px at 55% -60px, var(--mode-lueur), transparent 72%) no-repeat,
    linear-gradient(180deg, var(--nuit) 78%, rgba(15,31,56,0)); }
"""
ecrire('style.css', css)
print(u'patch189 applique. Lancer : python3 maj-version.py')
