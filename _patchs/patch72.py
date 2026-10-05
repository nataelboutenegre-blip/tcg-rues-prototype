# -*- coding: utf-8 -*-
u"""
patch72 — Radar : la carte prend la place sur ordinateur.

Remarque de Natael (5 octobre, capture a l'appui) : sur ordinateur, la
carte de Radar etait trop petite. L'ecran etait limite a 640 px de large,
alors que viser demande de la precision.

Sur ordinateur, la carte se regle maintenant sur la hauteur de la fenetre
(tout reste visible sans defiler : nom, chrono, carte, bouton) et peut
aller jusqu'a 1 000 px de large. Telephone : rien ne change.
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

css = lire('style.css')
assert '.rd-ecran{ display:flex;' in css
css += u"""

/* ---------- Radar : grande carte sur ordinateur (patch72) ---------- */
@media (min-width: 721px){
  #rdManche{ max-width: 1000px; }
  #rdManche .rd-carte{ display:flex; justify-content:center; }
  /* la hauteur de la fenetre, moins le titre, le nom, le verdict et le bouton */
  #rdManche .rd-carte svg{ width:auto; height: calc(100vh - 345px); min-height: 420px; max-width:100%; }
}
"""
ecrire('style.css', css)
print(u'patch72 applique : style.css')
