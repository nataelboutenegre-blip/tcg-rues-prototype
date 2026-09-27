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

# GitHub Pages envoie tout avec max-age=600. Sans numero de version dans
# l'adresse, le navigateur peut resservir l'ancien app.js pendant dix
# minutes apres un deploiement -- et le rechargement automatique du jeu
# tourne alors en rond, puisqu'il redemande exactement la meme adresse.
RE_APPEL = re.compile(r'''(href|src)=(["'])(app\.js|style\.css)(\?v=[^"']*)?\2''')


def appels_neutres(html):
    """index.html sans les ?v=, pour que l'empreinte ne depende pas d'elle-meme."""
    return RE_APPEL.sub(lambda m: '%s=%s%s%s' % (m.group(1), m.group(2), m.group(3), m.group(2)),
                        html)


def ecrire_appels(html, version):
    return RE_APPEL.sub(lambda m: '%s=%s%s?v=%s%s' % (m.group(1), m.group(2), m.group(3),
                                                      version, m.group(2)),
                        html)


def main():
    manquants = [f for f in FICHIERS if not (DOSSIER / f).exists()]
    if manquants:
        sys.exit("Fichier(s) introuvable(s) : " + ", ".join(manquants) +
                 "\nPlace ce script dans le meme dossier que le site.")

    app = (DOSSIER / 'app.js').read_text(encoding='utf-8')
    if not re.search(r"const VERSION_JEU = '[^']*';", app):
        sys.exit("La ligne VERSION_JEU est introuvable dans app.js.")

    html = (DOSSIER / 'index.html').read_text(encoding='utf-8')
    attendus = {'app.js', 'style.css'}
    trouves = {m.group(3) for m in RE_APPEL.finditer(html)}
    if trouves != attendus:
        sys.exit("index.html doit appeler app.js et style.css une fois chacun "
                 "(trouve : " + (", ".join(sorted(trouves)) or "rien") + ").\n"
                 "Sans ca le navigateur peut resservir un ancien fichier "
                 "pendant dix minutes.")
    html_neutre = appels_neutres(html)

    # on neutralise la version actuelle pour que l'empreinte ne depende pas d'elle
    app_neutre = re.sub(r"const VERSION_JEU = '[^']*';", "const VERSION_JEU = '';", app)

    neutres = {'app.js': app_neutre, 'index.html': html_neutre}
    h = hashlib.sha256()
    for nom in FICHIERS:
        contenu = neutres.get(nom)
        h.update(contenu.encode('utf-8') if contenu is not None
                 else (DOSSIER / nom).read_bytes())
    version = h.hexdigest()[:12]

    html_a_jour = ecrire_appels(html_neutre, version)
    if html_a_jour != html:
        (DOSSIER / 'index.html').write_text(html_a_jour, encoding='utf-8')

    ancienne = re.search(r"const VERSION_JEU = '([^']*)';", app).group(1)
    if ancienne == version:
        if html_a_jour != html:
            print(f"Version inchangee ({version}), appels d'index.html remis d'aplomb.")
        else:
            print(f"Version inchangee ({version}) : rien a faire.")
        return

    (DOSSIER / 'app.js').write_text(
        re.sub(r"const VERSION_JEU = '[^']*';", f"const VERSION_JEU = '{version}';", app),
        encoding='utf-8')
    (DOSSIER / 'version.json').write_text(
        json.dumps({'version': version}, ensure_ascii=False) + '\n', encoding='utf-8')

    print(f"Version : {ancienne or '(vide)'} -> {version}")
    print("Envoie maintenant app.js, index.html et version.json sur GitHub, "
          "avec tes autres fichiers modifies.")


if __name__ == '__main__':
    main()
