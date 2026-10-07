# -*- coding: utf-8 -*-
u"""
patch80 — bulle de la carte plus compacte sur téléphone (7 octobre).
Marges, titre et lignes resserrés ; les boutons d'action passent sur deux
colonnes. Rien ne change sur ordinateur.
"""
import io, os
ICI = os.path.dirname(os.path.abspath(__file__))
BASE = os.path.dirname(ICI) if os.path.basename(ICI) == '_patchs' else ICI
p = os.path.join(BASE, 'style.css')
css = io.open(p, encoding='utf-8').read()
MARQUE = u'/* ---------- Bulle de la carte compacte sur téléphone (patch80) ---------- */'
assert MARQUE not in css, u'patch80 déjà passé'
css = css.rstrip('\n') + u'\n\n' + MARQUE + u'''
@media (max-width: 720px){
  .pc{ padding:16px 11px 9px; left:6px; right:6px; bottom:6px; border-radius:12px; }
  .pc::before{ top:5px; width:30px; }
  .pc-titre b{ font-size:1.2rem; }
  .pc-dep{ font-size:0.7rem; margin-top:1px; }
  .pc-lignes{ margin-top:7px; padding-top:5px; }
  .pc-ligne{ font-size:0.74rem; padding:1px 0; }
  .pc-note{ margin-top:6px; font-size:0.7rem; }
  .pc-propose, .pc-alerte{ margin-top:7px; font-size:0.74rem; }
  .pc-actions{ display:grid; grid-template-columns:1fr 1fr; gap:5px; margin-top:8px; }
  .pc-action{ padding:7px 8px; font-size:0.74rem; gap:5px; border-radius:8px; white-space:nowrap; overflow:hidden; text-overflow:ellipsis; min-width:0; }
  .pc-action svg{ width:15px; height:15px; }
  /* un bouton seul sur sa ligne prend toute la largeur */
  .pc-actions .pc-action:last-child:nth-child(odd){ grid-column:1 / -1; }
}
'''
io.open(p, 'w', encoding='utf-8').write(css)
print(u'patch80 : OK')
