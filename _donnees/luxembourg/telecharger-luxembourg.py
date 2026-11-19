#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
TerraFront — le Luxembourg : téléchargement des données brutes.

CE QUE FAIT CE SCRIPT
  1. Les contours des 100 communes et des 12 cantons : Administration du cadastre
     et de la topographie (ACT), sur data.public.lu et geoportail.lu.
     Licence CC0 (domaine public) : aucune condition, on citera quand même la source.
  2. La population par commune : STATEC, sur data.public.lu.
  3. Wikidata (CC0) : noms français / luxembourgeois / allemands, position, article
     Wikipédia, population et photo de chaque commune ; Commons : auteur et licence
     de chaque photo (attribution obligatoire).

  Il N'ÉCRIT RIEN dans la base et ne touche pas au jeu. Tout part dans
  _donnees/luxembourg/brut/ (ignoré par git).

USAGE (depuis le dossier du jeu, sur ton Mac)
    git pull
    python3 _donnees/luxembourg/telecharger-luxembourg.py

  Aucune dépendance. Relançable. Quelques minutes.
"""

import os, sys, time, urllib.parse

ICI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(ICI))
from commun import (http_json, telecharger, nom_fichier, ogc_collections, ogc_tout,
                    wikidata_pays, fin)

BRUT = os.path.join(ICI, "brut")
API = "https://data.public.lu/api/1/datasets/"
OGC = "https://wms.inspire.geoportail.lu/geoserver/ogc/features/v1"

# Recherches sur data.public.lu : (quoi, mots, organisation attendue dans le nom, formats voulus)
RECHERCHES = [
    ("contours", "limites administratives", "cadastre", ("geojson", "json", "zip", "shp", "gpkg", "gml")),
    ("population", "population communes", "statec", ("csv", "xlsx", "xls", "json")),
]


def chercher(mots):
    data = http_json(API + "?" + urllib.parse.urlencode({"q": mots, "page_size": 20}))
    return data.get("data", [])


def data_public(resume, manque):
    for quoi, mots, orga, formats in RECHERCHES:
        print("   data.public.lu : %s (« %s »)" % (quoi, mots))
        try:
            jeux = chercher(mots)
        except Exception as e:
            print("   ! %s" % e)
            manque.append((quoi, "https://data.public.lu/fr/datasets/?q=" + urllib.parse.quote(mots)))
            continue
        jeux = [j for j in jeux if orga in ((j.get("organization") or {}).get("name", "") or "").lower()] or jeux
        pris = []
        for j in jeux[:3]:
            print("     jeu : %s (%s)" % (j.get("title"), (j.get("organization") or {}).get("name", "?")))
            for r in j.get("resources", []):
                fmt = (r.get("format") or "").lower()
                taille = r.get("filesize") or 0
                if fmt not in formats or (taille and taille > 400e6):
                    continue
                url = r.get("url") or ""
                nom = "%s--%s" % (quoi, nom_fichier(url))
                print("     → %s (%s, %.1f Mo)" % (r.get("title"), fmt, (taille or 0) / 1e6))
                try:
                    telecharger(url, os.path.join(BRUT, nom))
                    pris.append({"jeu": j.get("title"), "page": j.get("page"), "licence": j.get("license"),
                                 "ressource": r.get("title"), "url": url, "fichier": nom})
                except Exception as e:
                    print("     ! %s" % e)
        resume[quoi] = pris
        if not pris:
            manque.append((quoi, "https://data.public.lu/fr/datasets/?q=" + urllib.parse.quote(mots)))


def geoportail(resume):
    """Les unités administratives INSPIRE en GeoJSON (secours si data.public.lu n'a que du GML)."""
    try:
        cols = ogc_collections(OGC)
    except Exception as e:
        print("   ! geoportail.lu : %s" % e)
        return
    au = [(i, t) for i, t in cols if "administrativeunit" in i.lower() or "administrative unit" in t.lower()]
    print("   %d collections, dont %d « unités administratives »" % (len(cols), len(au)))
    resume["geoportail_collections"] = cols
    for i, t in au[:4]:
        print("   collection %s (%s)" % (i, t))
        try:
            ogc_tout(OGC, i, os.path.join(BRUT, "geoportail--%s.geojson" % i.replace(":", "_")), par_page=500)
        except Exception as e:
            print("   ! %s" % e)


# Q2919801 = commune du Luxembourg ; P782 = code LAU
FILTRE = """
  ?c wdt:P31/wdt:P279* wd:Q2919801 .
  FILTER NOT EXISTS { ?c wdt:P576 ?fin }
  OPTIONAL { ?c wdt:P782 ?lau }
  BIND(COALESCE(?lau, STRAFTER(STR(?c), "entity/")) AS ?code)
"""


def main():
    os.makedirs(BRUT, exist_ok=True)
    resume, manque = {}, []
    print("1/3  data.public.lu (contours ACT, population STATEC)")
    data_public(resume, manque)
    print("\n2/3  geoportail.lu (unités administratives en GeoJSON)")
    geoportail(resume)
    print("\n3/3  Wikidata et Commons")
    resume["wikidata"] = wikidata_pays(BRUT, "LU", FILTRE, ("fr", "lb", "de"))
    resume["wikidata"]["le"] = time.strftime("%Y-%m-%d %H:%M")
    if not 95 <= resume["wikidata"]["communes"] <= 105:
        print("   ATTENTION : %d communes au lieu de 100 — dis-le à Claude, rien de grave." % resume["wikidata"]["communes"])
    fin(BRUT, resume, manque, "luxembourg")


if __name__ == "__main__":
    main()
