# -*- coding: utf-8 -*-
u"""
patch73 — Radar sans limite de duels.

Decide le 6 octobre : plus de limite par jour (corrections-6-octobre.sql).
Le serveur renvoie alors restants = null. Le QG n'affiche plus de compteur
(l'etiquette disparait), et le bouton « Lancer un duel » n'est plus jamais
grise pour cette raison. Si une limite revient un jour, l'affichage
d'avant revient tout seul.
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

js = lire('app.js')
js = rempl(js,
u"""  document.getElementById('qgRestants').textContent = r.en_cours ? 'partie en cours'
    : (r.restants > 0 ? `${r.restants} duel${r.restants > 1 ? 's' : ''} aujourd’hui` : 'reviens demain');""",
u"""  // restants null : pas de limite, pas de compteur (l'etiquette vide est cachee)
  const sansLimite = r.restants === null || r.restants === undefined;
  document.getElementById('qgRestants').textContent = r.en_cours ? 'partie en cours'
    : sansLimite ? ''
    : (r.restants > 0 ? `${r.restants} duel${r.restants > 1 ? 's' : ''} aujourd’hui` : 'reviens demain');""", 'compteur')
js = rempl(js,
u"""  lancer.disabled = !r.en_cours && r.restants <= 0;""",
u"""  lancer.disabled = !r.en_cours && !sansLimite && r.restants <= 0;""", 'bouton')
ecrire('app.js', js)
print(u'patch73 applique : app.js')
