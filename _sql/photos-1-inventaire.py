#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
TerraFront — photos des communes, etape 1 sur 3 : l'inventaire.

CE QUE FAIT CE SCRIPT
  Il interroge Wikidata et Wikimedia Commons, et ecrit un CSV.
  Il NE TELECHARGE AUCUNE IMAGE et N'ECRIT RIEN dans la base.
  On regarde le CSV, et seulement apres on passe a l'etape 2.

POURQUOI IL TOURNE CHEZ TOI ET PAS CHEZ MOI
  Le conteneur de Claude et le pont vers ton Mac passent tous les deux
  par un proxy qui refuse wikidata.org et commons.wikimedia.org. Ton
  Terminal, lui, y accede normalement. Je peux ecrire ce script, je ne
  peux pas le faire tourner : c'est pour ca qu'il est decoupe en trois
  etapes verifiables une par une, avec un mode d'essai.

USAGE
    python3 photos-1-inventaire.py --essai          # 2 departements, ~700 communes
    python3 photos-1-inventaire.py                  # les 101 departements

  Aucune dependance a installer : bibliotheque standard seulement.

CE QUI SORT
    photos-inventaire.csv   code_insee, fichier, auteur, licence, licence_url
    photos-manquantes.csv   les communes sans photo, pour savoir lesquelles

LES LICENCES NE SONT PAS UN DETAIL
  Les images de Commons sont majoritairement en CC-BY-SA : l'attribution
  est obligatoire (auteur, licence, lien). C'est pour ca que l'auteur et
  la licence sont recuperes des maintenant, en meme temps que le nom du
  fichier, et pas « plus tard ». Les recuperer apres coup sur 35 000
  images serait une deuxieme passe complete.
"""

import argparse, csv, json, re, sys, time, urllib.parse, urllib.request

UA = "TerraFront/1.0 (https://terrafront.fr; contact via Discord) python-urllib"
WDQS = "https://query.wikidata.org/sparql"
COMMONS = "https://commons.wikimedia.org/w/api.php"

# Les 101 departements, en prefixe de code INSEE. On interroge Wikidata
# departement par departement : une seule requete sur 40 000 lignes
# depasse le delai du service, 101 petites passent sans probleme et on
# voit l'avancement.
DEPARTEMENTS = (
    ["%02d" % d for d in range(1, 20)] + ["2A", "2B"] +
    ["%02d" % d for d in range(21, 96)] +
    ["971", "972", "973", "974", "976"]
)


def http_json(url, donnees=None, essais=4):
    """Un GET ou POST JSON, avec reprise sur erreur passagere."""
    for tentative in range(1, essais + 1):
        try:
            req = urllib.request.Request(url, data=donnees)
            req.add_header("User-Agent", UA)
            req.add_header("Accept", "application/json")
            with urllib.request.urlopen(req, timeout=120) as r:
                return json.loads(r.read().decode("utf-8"))
        except Exception as e:
            if tentative == essais:
                raise
            attente = 3 * tentative
            print("      ! %s — nouvel essai dans %ds" % (e, attente), file=sys.stderr)
            time.sleep(attente)


def communes_du_departement(prefixe):
    """[(code_insee, nom_de_fichier_ou_None)] pour un departement."""
    requete = """
SELECT ?insee ?nom (SAMPLE(?img) AS ?image) WHERE {
  ?c wdt:P31 wd:Q484170 ;
     wdt:P374 ?insee .
  OPTIONAL { ?c rdfs:label ?nom FILTER(LANG(?nom) = "fr") }
  OPTIONAL { ?c wdt:P18 ?img }
  FILTER(STRSTARTS(?insee, "%s"))
}
GROUP BY ?insee ?nom
""" % prefixe
    url = WDQS + "?" + urllib.parse.urlencode({"query": requete, "format": "json"})
    data = http_json(url)
    lignes = []
    for b in data["results"]["bindings"]:
        insee = b["insee"]["value"].strip()
        nom = b.get("nom", {}).get("value", "")
        img = b.get("image", {}).get("value")
        # l'URL est du type .../Special:FilePath/Mairie%20de%20X.jpg
        fichier = urllib.parse.unquote(img.rsplit("/", 1)[-1]) if img else None
        lignes.append((insee, nom, fichier))
    return lignes


def metadonnees(fichiers):
    """{nom_fichier: (auteur, licence, licence_url)} — par paquets de 50."""
    infos = {}
    paquets = [fichiers[i:i + 50] for i in range(0, len(fichiers), 50)]
    for n, paquet in enumerate(paquets, 1):
        titres = "|".join("File:" + f for f in paquet)
        corps = urllib.parse.urlencode({
            "action": "query", "format": "json", "prop": "imageinfo",
            "iiprop": "extmetadata", "iiextmetadatafilter":
                "Artist|LicenseShortName|LicenseUrl", "titles": titres,
        }).encode("utf-8")
        data = http_json(COMMONS, donnees=corps)
        for page in (data.get("query", {}).get("pages", {}) or {}).values():
            titre = page.get("title", "")[len("File:"):]
            ii = (page.get("imageinfo") or [{}])[0]
            meta = ii.get("extmetadata", {}) or {}
            lire = lambda c: (meta.get(c, {}) or {}).get("value", "") or ""
            # l'auteur arrive en HTML (souvent un lien) : on le degrossit
            auteur = re.sub(r"<[^>]+>", "", lire("Artist"))
            auteur = re.sub(r"\s+", " ", auteur).strip()
            infos[titre] = (auteur, lire("LicenseShortName"), lire("LicenseUrl"))
        print("   metadonnees %d/%d" % (n, len(paquets)))
        time.sleep(0.4)          # on reste poli avec l'API
    return infos


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--essai", action="store_true",
                    help="seulement la Charente (16) et la Gironde (33)")
    args = ap.parse_args()

    deps = ["16", "33"] if args.essai else DEPARTEMENTS
    print("Inventaire sur %d departement(s).\n" % len(deps))

    toutes = []
    for i, d in enumerate(deps, 1):
        lignes = communes_du_departement(d)
        avec = sum(1 for _, _, f in lignes if f)
        print("%3d/%d  dept %-3s  %5d communes, %5d avec photo"
              % (i, len(deps), d, len(lignes), avec))
        toutes.extend(lignes)
        time.sleep(0.5)

    avec_photo = [(c, n, f) for (c, n, f) in toutes if f]
    sans_photo = [(c, n) for (c, n, f) in toutes if not f]
    print("\n%d communes, %d avec photo (%.1f %%), %d sans."
          % (len(toutes), len(avec_photo),
             100.0 * len(avec_photo) / max(len(toutes), 1), len(sans_photo)))

    print("\nRecuperation des auteurs et des licences...")
    fichiers = sorted({f for (_, _, f) in avec_photo})
    infos = metadonnees(fichiers)

    with open("photos-inventaire.csv", "w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh)
        w.writerow(["code_insee", "nom", "fichier", "auteur", "licence", "licence_url"])
        for code, nom, fic in sorted(avec_photo):
            a, l, u = infos.get(fic, ("", "", ""))
            w.writerow([code, nom, fic, a, l, u])

    with open("photos-manquantes.csv", "w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh)
        w.writerow(["code_insee", "nom"])
        for code, nom in sorted(sans_photo):
            w.writerow([code, nom])

    licences = {}
    for fic in fichiers:
        l = infos.get(fic, ("", "", ""))[1] or "(inconnue)"
        licences[l] = licences.get(l, 0) + 1
    print("\nLicences rencontrees :")
    for l, n in sorted(licences.items(), key=lambda x: -x[1]):
        print("   %-28s %d" % (l, n))
    sans_auteur = sum(1 for f in fichiers if not infos.get(f, ("",))[0])
    if sans_auteur:
        print("\n%d image(s) sans auteur lisible : a ecarter ou a verifier "
              "a la main, l'attribution est obligatoire." % sans_auteur)

    print("\nEcrit : photos-inventaire.csv et photos-manquantes.csv")
    print("Rien n'a ete telecharge, rien n'a ete modifie en base.")


if __name__ == "__main__":
    main()
