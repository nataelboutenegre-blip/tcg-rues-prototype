# -*- coding: utf-8 -*-
u"""
patch162 — Plus ou moins : plus d'air dans la fenetre (retour de Nataël le
25 octobre : « un peu trop serre »). Les elements du jeu n'avaient aucun
espacement entre eux (#pomCorps n'etait pas une grille) ; fenetre plus
large (760 px), marges et ecarts agrandis, question equilibree sur mobile.
Modification appliquee directement dans style.css (bloc patch160) ; ce
fichier sert de trace.
"""
import io, os
ICI = os.path.dirname(os.path.abspath(__file__))
BASE = os.path.dirname(ICI) if os.path.basename(ICI) == '_patchs' else ICI
with io.open(os.path.join(BASE, 'style.css'), encoding='utf-8') as f: css = f.read()
assert '#pomCorps{ display:grid; gap:22px; }' in css, u'patch162 absent de style.css'
print(u'patch162 deja en place.')
