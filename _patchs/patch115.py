# -*- coding: utf-8 -*-
u"""
patch115 — Échange : chercher par joueur et combiner plusieurs critères
(idée de Wally).

Le champ « Tu reçois » accepte plusieurs critères séparés par des
virgules : « 16, 17, Maroli » = les communes de Maroli en Charente ou en
Charente-Maritime. Chaque nom de département est traduit en numéro avant
d'être envoyé au serveur, qui fait le reste (echange-recherche.sql).
À passer AVANT : _sql/echange-recherche.sql.
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

js = lire('app.js')
assert 'criteresEchange' not in js, u'patch115 deja applique'
js = rempl(js, u"    p_tier: echangeTier, p_recherche: codeDepartement(echangeRecherche) || echangeRecherche\n",
           u"    p_tier: echangeTier, p_recherche: criteresEchange(echangeRecherche)\n", 'appel')
js += u"""

// ---------- patch115 : plusieurs criteres dans la recherche d'echange ----------
// « 16, Charente-Maritime, Maroli » -> « 16, 17, Maroli » : chaque nom de
// departement devient son numero, le serveur reconnait les pseudos.
function criteresEchange(texte){
  return String(texte || '').split(/[,;]/).map(t => t.trim()).filter(Boolean)
    .map(t => codeDepartement(t) || t).join(', ');
}
"""
ecrire('app.js', js)

h = lire('index.html')
h = rempl(h, u"""<input type="text" id="echSearch" class="bourse-search" placeholder="Rechercher une commune ou un département…">""",
          u"""<input type="text" id="echSearch" class="bourse-search" placeholder="Commune, département ou joueur…">
        <p class="ech-astuce">Combine avec des virgules : <b>16, 17, Maroli</b></p>""", 'champ')
ecrire('index.html', h)

css = lire('style.css')
assert 'ech-astuce' not in css
css += u"""
/* patch115 : l'astuce sous la recherche d'echange */
.ech-astuce{ margin: -4px 0 10px; font-size: .74rem; color: var(--brume); }
.ech-astuce b{ color: var(--papier); font-weight: 600; }
"""
ecrire('style.css', css)
print(u'patch115 applique')
