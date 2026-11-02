#!/usr/bin/env python3
"""
Grands chantiers : assemble le moteur et les dessins en un seul fichier pour le jeu.

    python3 _chantiers/construire.py

Lit _chantiers/moteur.js et _chantiers/dessins.js (les sources, celles de
l'aperçu) et écrit chantiers/chantiers.js, servi par le site. Le tout est
enfermé dans une fonction : les noms du moteur (code, rgb, sprite…) ne
peuvent pas entrer en conflit avec ceux d'app.js. Le jeu n'en voit que
window.TF_CHANTIERS.

À relancer après chaque retouche d'un dessin, puis maj-version.py comme
d'habitude (le jeu charge chantiers.js avec le numéro de version).
"""
import pathlib

ICI = pathlib.Path(__file__).resolve().parent
RACINE = ICI.parent

moteur = (ICI / 'moteur.js').read_text(encoding='utf-8')
dessins = (ICI / 'dessins.js').read_text(encoding='utf-8')

sortie = RACINE / 'chantiers' / 'chantiers.js'
sortie.parent.mkdir(exist_ok=True)
sortie.write_text(
    '/* TerraFront — grands chantiers : moteur et dessins en pixel art.\n'
    '   Fichier assemblé par _chantiers/construire.py depuis _chantiers/moteur.js\n'
    '   et _chantiers/dessins.js : ne pas le modifier à la main. */\n'
    '(function () {\n'
    + moteur.rstrip() + '\n\n'
    + dessins.rstrip() + '\n\n'
    'window.TF_CHANTIERS = { PW: PW, PH: PH, DESSINS: DESSINS, creerScene: creerScene,\n'
    '  ORDRE_TYPES: ORDRE_TYPES, ORDRE_MERVEILLES: ORDRE_MERVEILLES };\n'
    '})();\n',
    encoding='utf-8')
print('écrit :', sortie.relative_to(RACINE), sortie.stat().st_size, 'octets')
