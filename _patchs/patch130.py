# -*- coding: utf-8 -*-
u"""
patch130 — deux corrections signalées par Maroli.
1. Rafale, entraînement : Paris, Lyon et Marseille reconnues (le jeu les
   découpe en arrondissements ; le serveur est corrigé par rafale-2).
2. Carte : les communes nouvelles couvrent tout leur territoire. Les contours
   venaient d'un découpage plus ancien : Montaigu-Vendée n'avait que
   l'ancienne Montaigu, et Boufféré, Saint-Georges-de-Montaigu, etc.
   restaient à part, sans carte. 485 anciennes communes ont été fondues
   dans leur commune actuelle (315 communes agrandies, 76 départements).
   Les fichiers contours/ changent : CONTOURS_V passe à 3 pour que les
   navigateurs les rechargent.
"""
import io, os
ICI = os.path.dirname(os.path.abspath(__file__))
BASE = os.path.dirname(ICI) if os.path.basename(ICI) == '_patchs' else ICI
def lire(n):
    with io.open(os.path.join(BASE, n), encoding='utf-8') as f: return f.read()
def ecrire(n, s):
    with io.open(os.path.join(BASE, n), 'w', encoding='utf-8') as f: f.write(s)
def rempl(src, avant, apres, etiquette, n_attendu=1):
    n = src.count(avant)
    assert n == n_attendu, u'%s : %d occurrences (attendu %d)' % (etiquette, n, n_attendu)
    return src.replace(avant, apres)
js = lire('app.js')
assert "rafaleNoms.set('PARIS'" not in js, u'patch130 deja applique'
js = rempl(js, u"""      .then(l => { rafaleNoms = new Map(); for(const [nom, dept] of l){ const k = rafaleNorm(nom); if(k && !rafaleNoms.has(k)) rafaleNoms.set(k, [nom, dept]); } return rafaleNoms; })""",
u"""      .then(l => { rafaleNoms = new Map(); for(const [nom, dept] of l){ const k = rafaleNorm(nom); if(k && !rafaleNoms.has(k)) rafaleNoms.set(k, [nom, dept]); }
        // patch130 : les trois villes a arrondissements
        rafaleNoms.set('PARIS', ['Paris', '75']); rafaleNoms.set('MARSEILLE', ['Marseille', '13']); rafaleNoms.set('LYON', ['Lyon', '69']);
        return rafaleNoms; })""", u'entrainement')
js = rempl(js, u"const CONTOURS_V = '2';", u"const CONTOURS_V = '3';   // patch130 : communes nouvelles", u'contours v')
ecrire('app.js', js)
print(u'patch130 applique')
