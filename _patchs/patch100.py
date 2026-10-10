# -*- coding: utf-8 -*-
u"""
patch100 — épique dans les filtres + recharge de garnison offerte.
SQL : _sql/s2-11-garnison-recharge.sql (sans effet en saison 1).

- Filtre « Épique » dans Combat, dans « Vendre une commune » (Bourse) et
  dans « Proposer un échange » : caché tant que EPIQUE_VISIBLE = false.
  (Sans lui, on ne pouvait pas proposer d'échange d'épiques en Terra.)
- Défendre en saison 2 : le bouton annonce « 1 énergie » (le vrai coût d'une
  défense ; patch99 affichait le coût d'un assaut).
- Défense réussie sur une commune en garnison : « +3 énergie dans la
  garnison » dans la notification, garnisons rechargées.
- Réveil de Défendre en saison 2 : « mets-la en garnison » au lieu de
  « pose un bouclier ».
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

def rempl(src, avant, apres, etiquette, n_attendu=1):
    n = src.count(avant)
    assert n == n_attendu, u'%s : %d occurrences (attendu %d)' % (etiquette, n, n_attendu)
    return src.replace(avant, apres)

EPI = u'<button class="filter-pill" data-tier="epique" data-epique hidden><span class="pill-point" style="background:#9B5CF6"></span>Épique</button>'

html = lire('index.html')
assert 'data-epique' not in html, u'patch100 deja applique'
# Combat et Vendre : Legendaire, puis Epique, puis Rare
html = rempl(html, u"""<button class="filter-pill" data-tier="legendaire"><span class="pill-point" style="background:#F0B429"></span>Légendaire</button>
          <button class="filter-pill" data-tier="rare">""",
             u"""<button class="filter-pill" data-tier="legendaire"><span class="pill-point" style="background:#F0B429"></span>Légendaire</button>
          """ + EPI + u"""
          <button class="filter-pill" data-tier="rare">""", 'vendre')
html = rempl(html, u"""<button class="filter-pill" data-tier="legendaire"><span class="pill-point" style="background:#F0B429"></span>Légendaire</button>
        <button class="filter-pill" data-tier="rare">""",
             u"""<button class="filter-pill" data-tier="legendaire"><span class="pill-point" style="background:#F0B429"></span>Légendaire</button>
        """ + EPI + u"""
        <button class="filter-pill" data-tier="rare">""", 'combat')
# Echange : ordre croissant, l'epique entre rare et legendaire
html = rempl(html, u"""          <button class="filter-pill" data-tier="rare"><span class="pill-point" style="background:#2F7CF6"></span>Rare</button>
          <button class="filter-pill" data-tier="legendaire"><span class="pill-point" style="background:#F0B429"></span>Légendaire</button>
        </div>""", u"""          <button class="filter-pill" data-tier="rare"><span class="pill-point" style="background:#2F7CF6"></span>Rare</button>
          """ + EPI + u"""
          <button class="filter-pill" data-tier="legendaire"><span class="pill-point" style="background:#F0B429"></span>Légendaire</button>
        </div>""", 'echange')
ecrire('index.html', html)

js = lire('app.js')
assert 'patch100' not in js
js = rempl(js, u"""document.getElementById('combatFilters').addEventListener('click', (e) => {""",
           u"""// patch100 : les filtres Epique n'apparaissent qu'avec la saison 2
if(EPIQUE_VISIBLE) document.querySelectorAll('[data-epique]').forEach(b => { b.hidden = false; });

document.getElementById('combatFilters').addEventListener('click', (e) => {""", 'epique')

# Defendre : le vrai cout d'une defense en saison 2
js = rempl(js, u"""${ICONE_BOUCLIER}${coutTexte(coutIntensite(g.tier))}</button>""",
           u"""${ICONE_BOUCLIER}${coutTexte(SAISON2 ? 1 : coutIntensite(g.tier))}</button>""", 'cout defense')

# recharge de garnison offerte
js = rempl(js, u"""  const btn = e.target.closest('.menace-defendre');
  if(!btn || btn.disabled) return;
  btn.disabled = true;""", u"""  const btn = e.target.closest('.menace-defendre');
  if(!btn || btn.disabled) return;
  btn.disabled = true;
  const gn = SAISON2 ? garnisonsMoi.get(btn.dataset.commune) : null;
  const recharge = gn ? Math.min(3, 10 - gn.energie) : 0;""", 'recharge 1')
js = rempl(js, u"""        texte: r.victoires_restantes > 0 ? `L'attaquant perd une victoire (plus que ${r.victoires_restantes} sur 3).` : 'L\\'attaquant perd sa victoire : son attaque repart de zéro.',""",
           u"""        texte: (r.victoires_restantes > 0 ? `L'attaquant perd une victoire (plus que ${r.victoires_restantes} sur 3).` : 'L\\'attaquant perd sa victoire : son attaque repart de zéro.')
          + (recharge > 0 ? ` +${recharge} énergie dans la garnison.` : ''),""", 'recharge 2')
js = rempl(js, u"""    await loadMenaces();
    loadPackStatus();
    if(SAISON2) majEnergie();""", u"""    await loadMenaces();
    loadPackStatus();
    if(SAISON2){ majEnergie(); if(gn) chargerGarnisons(); }""", 'recharge 3')
# saison 2 : plus de boucliers, le reveil parle de garnison
js = rempl(js, u"""</b>')}. Pose un bouclier ou défends-la.</p>""",
           u"""</b>')}. ${SAISON2 ? 'Défends-la ou mets-la en garnison.' : 'Pose un bouclier ou défends-la.'}</p>""", 'reveil')
ecrire('app.js', js)

css = lire('style.css')
assert '.filter-pill[data-epique][hidden]' not in css
css += u"""
/* patch100 */
.filter-pill[data-epique][hidden]{ display:none; }
"""
ecrire('style.css', css)
print(u'patch100 applique')
