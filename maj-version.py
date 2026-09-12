#!/usr/bin/env python3
"""
Met a jour la version du jeu.

A lancer APRES avoir modifie index.html, style.css, app.js ou sw.js,
et AVANT d'envoyer les fichiers sur GitHub :

    python3 maj-version.py

Le script calcule une empreinte des fichiers, l'ecrit dans app.js et dans
version.json. Au demarrage, le jeu compare sa propre empreinte a celle de
version.json : si elles different, il se recharge tout seul.
"""
import hashlib
import json
import re
import sys
from pathlib import Path

DOSSIER = Path(__file__).resolve().parent
FICHIERS = ['index.html', 'style.css', 'sw.js', 'app.js']


def main():
    manquants = [f for f in FICHIERS if not (DOSSIER / f).exists()]
    if manquants:
        sys.exit("Fichier(s) introuvable(s) : " + ", ".join(manquants) +
                 "\nPlace ce script dans le meme dossier que le site.")

    app = (DOSSIER / 'app.js').read_text(encoding='utf-8')
    if not re.search(r"const VERSION_JEU = '[^']*';", app):
        sys.exit("La ligne VERSION_JEU est introuvable dans app.js.")

    # on neutralise la version actuelle pour que l'empreinte ne depende pas d'elle
    app_neutre = re.sub(r"const VERSION_JEU = '[^']*';", "const VERSION_JEU = '';", app)

    h = hashlib.sha256()
    for nom in FICHIERS:
        h.update((DOSSIER / nom).read_bytes() if nom != 'app.js' else app_neutre.encode('utf-8'))
    version = h.hexdigest()[:12]

    ancienne = re.search(r"const VERSION_JEU = '([^']*)';", app).group(1)
    if ancienne == version:
        print(f"Version inchangee ({version}) : rien a faire.")
        return

    (DOSSIER / 'app.js').write_text(
        re.sub(r"const VERSION_JEU = '[^']*';", f"const VERSION_JEU = '{version}';", app),
        encoding='utf-8')
    (DOSSIER / 'version.json').write_text(
        json.dumps({'version': version}, ensure_ascii=False) + '\n', encoding='utf-8')

    print(f"Version : {ancienne or '(vide)'} -> {version}")
    print("Envoie maintenant app.js et version.json sur GitHub, avec tes autres fichiers modifies.")


if __name__ == '__main__':
    main()
