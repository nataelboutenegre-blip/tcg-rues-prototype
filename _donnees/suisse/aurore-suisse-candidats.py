#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
TerraFront — saison 3 : les candidates Aurore suisses.

Comme pour la France : une Aurore est une photo pleine carte, donc une photo
EN HAUTEUR. Ce script cherche, parmi les communes suisses rares, épiques et
légendaires, celles dont la photo Wikidata est en hauteur, et en télécharge
une version de 600 px de large (la taille des Aurore françaises).

Il n'écrit rien en base et ne touche pas au jeu. Il dépose les images dans
_prochain-patch/aurore-suisse/ (dossier que Claude peut lire) avec
candidats.csv (auteur et licence de chaque photo). Claude en fait ensuite une
page de tri ; tu choisis ; Claude met les gagnantes dans le jeu.

POURQUOI SUR TON MAC : le conteneur de Claude n'a pas accès à Wikimedia.

USAGE (depuis le dossier du jeu, aucune clé nécessaire)
    python3 _donnees/suisse/aurore-suisse-candidats.py
  Environ 5 minutes. Rejouable : une image déjà là n'est pas retéléchargée.
"""

import csv, json, os, re, sys, time
import urllib.parse, urllib.request, urllib.error

ICI = os.path.dirname(os.path.abspath(__file__))
RACINE = os.path.dirname(os.path.dirname(ICI))
COMMUNES = os.path.join(ICI, "jeu", "communes-suisse.csv")
SORTIE = os.path.join(RACINE, "_prochain-patch", "aurore-suisse")
COMMONS = "https://commons.wikimedia.org/w/api.php"
UA = "TerraFront/1.0 (https://terrafront.fr) python-urllib"
LARGEUR = 600
RAPPORT_MIN = 1.05     # hauteur / largeur : en dessous, la photo n'est pas en hauteur
PALIERS = ("legendaire", "epique", "rare")


def http(url, donnees=None, brut=False, essais=4):
    for n in range(1, essais + 1):
        try:
            req = urllib.request.Request(url, data=donnees)
            req.add_header("User-Agent", UA)
            with urllib.request.urlopen(req, timeout=120) as r:
                recu = r.read()
                return recu if brut else json.loads(recu.decode("utf-8"))
        except urllib.error.HTTPError as e:
            if e.code in (400, 403, 404) or n == essais:
                raise
            time.sleep(3 * n)
        except Exception:
            if n == essais:
                raise
            time.sleep(3 * n)


def main():
    os.makedirs(SORTIE, exist_ok=True)
    communes = [c for c in csv.DictReader(open(COMMUNES, encoding="utf-8"))
                if c["tier"] in PALIERS and c.get("photo")]
    print("%d communes rares, épiques ou légendaires avec une photo." % len(communes))
    par_fichier = {}
    for c in communes:
        par_fichier.setdefault(c["photo"].replace("_", " "), []).append(c)

    # 1. tailles, auteurs, licences, adresse de la version 600 px (par 50)
    infos = {}
    fichiers = sorted(par_fichier)
    for i in range(0, len(fichiers), 50):
        corps = urllib.parse.urlencode({
            "action": "query", "format": "json", "prop": "imageinfo",
            "iiprop": "size|url|extmetadata", "iiurlwidth": LARGEUR,
            "iiextmetadatafilter": "Artist|LicenseShortName|LicenseUrl",
            "titles": "|".join("File:" + f for f in fichiers[i:i + 50]),
        }).encode("utf-8")
        data = http(COMMONS, donnees=corps)
        normal = {x["to"]: x["from"] for x in (data.get("query", {}).get("normalized") or [])}
        for page in (data.get("query", {}).get("pages", {}) or {}).values():
            titre = normal.get(page.get("title", ""), page.get("title", ""))[len("File:"):].replace("_", " ")
            ii = (page.get("imageinfo") or [{}])[0]
            meta = ii.get("extmetadata") or {}
            lire = lambda k: (meta.get(k) or {}).get("value", "") or ""
            infos[titre] = {
                "l": ii.get("width") or 0, "h": ii.get("height") or 0,
                "vignette": ii.get("thumburl") or "", "page": ii.get("descriptionurl") or "",
                "auteur": re.sub(r"\s+", " ", re.sub(r"<[^>]+>", "", lire("Artist"))).strip(),
                "licence": lire("LicenseShortName"), "licence_url": lire("LicenseUrl"),
            }
        print("   Commons %d/%d" % (min(i + 50, len(fichiers)), len(fichiers)))
        time.sleep(0.4)

    # 2. on garde les photos en hauteur, assez grandes, avec un auteur
    garder = []
    for f, cs in par_fichier.items():
        x = infos.get(f)
        if not x or not x["l"] or not x["vignette"]:
            continue
        if x["h"] / x["l"] < RAPPORT_MIN or x["l"] < LARGEUR or not x["auteur"]:
            continue
        for c in cs:
            garder.append((c, f, x))
    ordre = {p: i for i, p in enumerate(PALIERS)}
    garder.sort(key=lambda t: (ordre[t[0]["tier"]], -int(t[0]["population"] or 0)))
    print("\n%d photos en hauteur (sur %d communes)." % (len(garder), len(communes)))

    # 3. les images (600 px de large) + candidats.csv
    lignes, rates = [], 0
    for n, (c, f, x) in enumerate(garder, 1):
        dest = os.path.join(SORTIE, c["code"] + ".jpg")
        try:
            if not (os.path.exists(dest) and os.path.getsize(dest) > 15000):
                image = http(x["vignette"], brut=True)
                if len(image) < 15000:
                    raise ValueError("image trop petite (%d octets)" % len(image))
                open(dest, "wb").write(image)
                time.sleep(0.25)
            lignes.append([c["code"], c["nom"], c["departement"], c["tier"], c["population"], f,
                           x["l"], x["h"], x["auteur"], x["licence"], x["licence_url"], x["page"]])
        except Exception as e:
            rates += 1
            print("   %s %s : ÉCHEC %s" % (c["code"], c["nom"], e))
        if n % 25 == 0:
            print("   images %d/%d" % (n, len(garder)))
    with open(os.path.join(SORTIE, "candidats.csv"), "w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh)
        w.writerow(["code", "nom", "canton", "tier", "population", "fichier", "largeur", "hauteur",
                    "auteur", "licence", "licence_url", "page"])
        w.writerows(lignes)
    print("\nFini : %d candidates dans _prochain-patch/aurore-suisse/ (%d échecs)." % (len(lignes), rates))
    print("Dis à Claude que c'est prêt.")


if __name__ == "__main__":
    main()
