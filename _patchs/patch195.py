# -*- coding: utf-8 -*-
u"""
patch195 — rail PC : le Tirage n'est plus un gros rond dore ; c'est un onglet
comme les autres (icone + « Tirage » dessous), a la couleur du mode quand il
est actif. Aucun SQL.
"""
import io, os
ICI = os.path.dirname(os.path.abspath(__file__))
BASE = os.path.dirname(ICI) if os.path.basename(ICI) == '_patchs' else ICI
def lire(n):
    with io.open(os.path.join(BASE, n), encoding='utf-8') as f: return f.read()
def ecrire(n, s):
    with io.open(os.path.join(BASE, n), 'w', encoding='utf-8') as f: f.write(s)
css = lire('style.css')
assert 'patch195' not in css
css += u"""

/* ---------- patch195 : le Tirage, un onglet comme les autres sur PC ---------- */
@media (min-width: 721px) and (hover: hover){
  .tab[data-tab="tirage"], .sidebar:hover .tab[data-tab="tirage"], .sidebar:focus-within .tab[data-tab="tirage"]{
    width:68px; height:auto; margin:0; padding:7px 2px 6px; border:0; border-radius:10px; background:none; box-shadow:none; overflow:visible;
    flex-direction:column; align-items:center; justify-content:center; gap:3px;
    font-size:.62rem; font-weight:600; line-height:1.1; white-space:normal; text-align:center; color: var(--brume); }
  .tab[data-tab="tirage"]::after, .sidebar:hover .tab[data-tab="tirage"]::after, .sidebar:focus-within .tab[data-tab="tirage"]::after{ content:none; }
  .tab[data-tab="tirage"] .icon, .tab[data-tab="tirage"] .icon svg{ width:22px; height:22px; color: inherit; }
  .tab[data-tab="tirage"]:hover{ background: rgba(169,188,212,0.08); color:#fff; }
  .tab[data-tab="tirage"].active{ box-shadow:none; color: var(--c-legendaire); }
  .tab[data-tab="tirage"].active::before{ left:2px; }
}
"""
ecrire('style.css', css)
print(u'patch195 applique. Lancer : python3 maj-version.py')
