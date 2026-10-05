# -*- coding: utf-8 -*-
u"""
patch71 — Place du QG.

Demande de Natael (5 octobre) :
  - ordinateur : QG juste au-dessus de Combat dans la colonne ;
  - telephone : la barre devient Tirage · Territoire · QG · Combat (+ Plus).
    Collection passe dans le menu Plus.

Sur ordinateur, QG et Combat forment un seul groupe entre deux
separateurs (la respiration passe de Combat a QG).

La pastille du bouton Plus ne compte plus le QG sur telephone, puisqu'il
est dans la barre avec sa propre pastille.
"""
import io, os

ICI = os.path.dirname(os.path.abspath(__file__))
BASE = os.path.dirname(ICI) if os.path.basename(ICI) == '_patchs' else ICI

def lire(n):
    with io.open(os.path.join(BASE, n), encoding='utf-8') as f:
        return f.read()

def ecrire(n, s):
    with io.open(os.path.join(BASE, n), 'w', encoding='utf-8') as f:
        f.write(s)

def rempl(src, avant, apres, etiquette):
    n = src.count(avant)
    assert n == 1, u'%s : %d occurrences (attendu 1)' % (etiquette, n)
    return src.replace(avant, apres)

html = lire('index.html')
debut = u'      <div class="tab" data-tab="qg">'
fin = u'      <div class="tab" data-tab="monuments">'
combat = u'      <div class="tab" data-tab="combat">'
assert html.count(debut) == 1 and html.count(fin) == 1 and html.count(combat) == 1
i, j = html.index(debut), html.index(fin)
assert i < j < html.index(combat)
bloc = html[i:j]                       # les onglets qg, cdj et radar
html = html[:i] + html[j:]
html = rempl(html, combat, bloc + combat, 'avant combat')
ecrire('index.html', html)

js = lire('app.js')
js = rempl(js,
u"""const ONGLETS_BARRE = ['tirage', 'territoire', 'collection', 'combat'];""",
u"""const ONGLETS_BARRE = ['tirage', 'territoire', 'qg', 'combat'];""", 'barre')
js = rempl(js,
u"""  const cdjAJouer = surTelephone() && cdj && !cdj.hidden;""",
u"""  const cdjAJouer = surTelephone() && ONGLETS_MENU.includes('qg') && cdj && !cdj.hidden;""", 'pastille plus')
ecrire('app.js', js)

# la respiration de la colonne passe de Combat a QG : QG et Combat forment
# un seul groupe (« on se bat »), entre deux separateurs
css = lire('style.css')
css = rempl(css,
u"""    .tab[data-tab="combat"],
    .tab[data-tab="contrat"],
    .tab[data-tab="profil"]{ margin-top: 14px; }""",
u"""    .tab[data-tab="qg"],
    .tab[data-tab="contrat"],
    .tab[data-tab="profil"]{ margin-top: 14px; }""", 'groupes colonne')
ecrire('style.css', css)

print(u'patch71 applique : index.html, app.js, style.css')
