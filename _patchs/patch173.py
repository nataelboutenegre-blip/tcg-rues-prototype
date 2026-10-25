# -*- coding: utf-8 -*-
u"""
patch173 — ouverture des clans (CLANS = true), 6 membres au plus.
SQL : _sql/clans-ouverture.sql (AVANT le push : sinon l'onglet affiche
« Les clans ouvrent bientot »). Sur telephone, la ligne d'invitation passe
les boutons a la ligne.
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
js = lire('app.js')
js = rempl(js, u"const CLANS = false;", u"const CLANS = true;   // patch173 : ouverts le 25 octobre", 'interrupteur')
js = rempl(js, u"[/Le clan est complet/i, 'Le clan est complet (5 membres).'],", u"[/Le clan est complet/i, 'Le clan est complet (6 membres).'],", 'message')
js = rempl(js, u"${n} membre${n > 1 ? 's' : ''} sur 5${n < 3", u"${n} membre${n > 1 ? 's' : ''} sur 6${n < 3", 'sur6')
js = rempl(js, u"${c.chef && n < 5 ? `<div class=\"clan-inviter\">", u"${c.chef && n < 6 ? `<div class=\"clan-inviter\">", 'inviter')
ecrire('app.js', js)
h = lire('index.html')
h = rempl(h, u'<div class="sub">3 à 5 joueurs. En Front', u'<div class="sub">3 à 6 joueurs, comme les côtés de l’Hexagone. En Front', 'texte')
ecrire('index.html', h)
css = lire('style.css')
css = rempl(css, u".clan-invit{ grid-template-columns:64px minmax(0,1fr) auto auto; }", u""".clan-invit{ grid-template-columns:64px minmax(0,1fr) auto auto; }
@media (max-width:560px){   /* patch173 : les boutons passent sous le nom */
  .clan-invit{ grid-template-columns:52px minmax(0,1fr) auto; }
  .clan-invit .blason{ grid-row:span 2; }
  .clan-invit > div{ grid-column:2 / -1; }
  .clan-invit [data-clan-oui]{ grid-column:2; justify-self:start; }
  .clan-invit [data-clan-non]{ grid-column:3; }
}""", 'css')
ecrire('style.css', css)
print(u'patch173 applique. Lancer : python3 maj-version.py')
