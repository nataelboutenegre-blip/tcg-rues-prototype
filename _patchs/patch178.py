# -*- coding: utf-8 -*-
u"""
patch178 — la Boutique aussi en Front (demande de Nataël, 25 octobre),
sans les paquets : en Front on garde les dos de cartes (en points) et les
objets TerraFront (euros). Les paquets de boutique restent en Terra.
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
assert 'patch178' not in js
js = rempl(js, u"""           propres: ['tirage', 'territoire', 'qg', 'combat', 'collection'] },""",
u"""           propres: ['tirage', 'territoire', 'qg', 'combat', 'collection', 'boutique'] },   // patch178 : boutique sans paquets""", 'front')
js = rempl(js, u"""+ `<span class="puce">Paquets de boutique aujourd'hui <b>${b.paquets_du_jour} sur ${b.paquets_max}</b></span>`;""",
u"""+ `<span class="puce bq-terra-seul">Paquets de boutique aujourd'hui <b>${b.paquets_du_jour} sur ${b.paquets_max}</b></span>`;""", 'puce')
ecrire('app.js', js)
html = lire('index.html')
html = rempl(html, u"""      <div class="bourse-section bq-section">
        <h2>Paquets</h2>""", u"""      <div class="bourse-section bq-section bq-terra-seul">
        <h2>Paquets</h2>""", 'section paquets')
html = rempl(html, u"""      <div class="note">3 paquets de boutique par jour au maximum. Ils ne comptent pas pour les quêtes. Un dos de carte""",
u"""      <div class="note"><span class="bq-terra-seul">3 paquets de boutique par jour au maximum. Ils ne comptent pas pour les quêtes. </span>Un dos de carte""", 'note')
ecrire('index.html', html)
css = lire('style.css')
css += u"""

/* ---------- patch178 : en Front, la boutique sans les paquets ---------- */
body.mode-front .bq-terra-seul{ display: none !important; }
"""
ecrire('style.css', css)
print(u'patch178 applique')
