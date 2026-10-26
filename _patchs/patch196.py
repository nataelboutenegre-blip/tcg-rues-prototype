# -*- coding: utf-8 -*-
u"""
patch196 — correctif de patch193 : sur telephone, le QG gardait « Tes dernieres
parties » en colonne 2, ce qui creait une deuxieme colonne et ecrasait la
carte du jeu (texte sur un mot par ligne). Sur telephone, tout repasse sur
une seule colonne. Aucun SQL.
"""
import io, os
ICI = os.path.dirname(os.path.abspath(__file__))
BASE = os.path.dirname(ICI) if os.path.basename(ICI) == '_patchs' else ICI
def lire(n):
    with io.open(os.path.join(BASE, n), encoding='utf-8') as f: return f.read()
def ecrire(n, s):
    with io.open(os.path.join(BASE, n), 'w', encoding='utf-8') as f: f.write(s)
css = lire('style.css')
assert 'patch196' not in css
css += u"""

/* ---------- patch196 : le QG sur telephone, une seule colonne ---------- */
@media (max-width: 900px){
  .qg-choix-actif .qg-grille{ grid-template-columns:minmax(0,1fr); }
  .qg-choix-actif .qg-jeux, .qg-choix-actif #qgDefisBloc, .qg-choix-actif #qgDerniersBloc,
  .qg-choix-actif #qgClassementBloc, .qg-choix-actif #qgCdjNote{ grid-column:1; grid-row:auto; }
}
"""
ecrire('style.css', css)
print(u'patch196 applique. Lancer : python3 maj-version.py')
