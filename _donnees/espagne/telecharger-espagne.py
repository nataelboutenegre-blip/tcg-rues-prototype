#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
TerraFront — l'Espagne : téléchargement des données brutes.

CE QUE FAIT CE SCRIPT
  1. Les contours des municipios, provinces et communautés autonomes : IGN espagnol
     (Base de données des limites juridictionnelles, BDLJE), par son API
     « api-features.ign.es ». Licence CC BY 4.0 : usage commercial autorisé,
     à condition d'afficher « CC BY 4.0 ign.es » dans le jeu.
  2. La liste officielle des municipios et leurs codes (INE, au 1/1/2026) et la
     population officielle (INE). Réutilisation autorisée en citant l'INE.
  3. Wikidata (CC0) : noms français / espagnols / catalans / basques / galiciens,
     position, article Wikipédia, population et photo ; Commons : auteur et licence
     de chaque photo (attribution obligatoire).

  Il N'ÉCRIT RIEN dans la base et ne touche pas au jeu. Tout part dans
  _donnees/espagne/brut/ (ignoré par git : les contours pèsent plusieurs centaines de Mo).

USAGE (depuis le dossier du jeu, sur ton Mac)
    git pull
    python3 _donnees/espagne/telecharger-espagne.py

  Aucune dépendance. Long : environ 8 200 contours détaillés, compte 20 à 60 min
  selon ta connexion. Relançable : il reprend là où il s'est arrêté.
"""

import os, sys, time

ICI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(ICI))
from commun import (http, http_json, telecharger, ogc_collections, ogc_tout, wikidata_pays, fin)

BRUT = os.path.join(ICI, "brut")
IGN = "https://api-features.ign.es"
PAR_PAGE = int(os.environ.get("TF_PAR_PAGE", "200"))
DICTIONNAIRES = ["https://www.ine.es/daco/daco42/codmun/diccionario26.xlsx",
                 "https://www.ine.es/daco/daco42/codmun/diccionario25.xlsx"]
# Table INE « Cifras oficiales del padrón por municipio » (API Tempus), dernière année
POPULATION_INE = "https://servicios.ine.es/wstempus/js/ES/DATOS_TABLA/29005?nult=1"


def contours(resume, manque):
    try:
        cols = ogc_collections(IGN)
    except Exception as e:
        print("   ! %s" % e)
        manque.append(("les recintos municipales (BDLJE, shapefile ou GeoPackage)",
                       "https://centrodedescargas.cnig.es/CentroDescargas/ (Información geográfica de referencia › Líneas límite municipales)"))
        return
    resume["ign_collections"] = cols
    unites = [(i, t) for i, t in cols if "administrativeunit" in i.lower() and "boundary" not in i.lower()]
    print("   %d collections ; unités administratives : %s" % (len(cols), ", ".join(i for i, _ in unites) or "aucune"))
    if not unites:
        manque.append(("les recintos municipales (BDLJE)", "https://centrodedescargas.cnig.es/CentroDescargas/"))
        return
    for i, t in unites:
        print("   collection %s (%s), %d par page" % (i, t, PAR_PAGE))
        n = ogc_tout(IGN, i, os.path.join(BRUT, "ign--%s.geojson" % i), par_page=PAR_PAGE, max_pages=400)
        resume.setdefault("ign", {})[i] = n


def ine(resume, manque):
    for url in DICTIONNAIRES:
        try:
            print("   %s" % url.rsplit("/", 1)[-1])
            telecharger(url, os.path.join(BRUT, url.rsplit("/", 1)[-1]))
            resume["ine_codes"] = url
            break
        except Exception as e:
            print("   ! %s" % e)
    else:
        manque.append(("la « Relación de municipios y sus códigos » (xlsx)",
                       "https://www.ine.es/daco/daco42/codmun/codmun.htm"))
    try:
        print("   population officielle (API INE)")
        brut = http(POPULATION_INE, delai=300)
        with open(os.path.join(BRUT, "ine-population.json"), "wb") as fh:
            fh.write(brut)
        resume["ine_population"] = {"url": POPULATION_INE, "octets": len(brut)}
        print("   %.1f Mo" % (len(brut) / 1e6))
    except Exception as e:
        print("   ! %s (pas grave : Wikidata donne aussi la population)" % e)


# Q2074737 = municipio d'Espagne ; P772 = code INE du municipio (5 chiffres)
FILTRE = """
  ?c wdt:P772 ?code ;
     wdt:P31/wdt:P279* wd:Q2074737 .
  FILTER NOT EXISTS { ?c wdt:P576 ?fin }
"""


def main():
    os.makedirs(BRUT, exist_ok=True)
    resume, manque = {}, []
    print("1/3  INE (codes et population)")
    ine(resume, manque)
    print("\n2/3  Wikidata et Commons")
    # une tranche par province (2 premiers chiffres du code INE, 01 à 52) : en une fois, Wikidata coupait la réponse
    tranches = ['FILTER(STRSTARTS(?code, "%02d"))' % p for p in range(1, 53)]
    resume["wikidata"] = wikidata_pays(BRUT, "ES", FILTRE, ("fr", "es", "ca", "eu", "gl"), tranches=tranches)
    resume["wikidata"]["le"] = time.strftime("%Y-%m-%d %H:%M")
    print("\n3/3  IGN : contours (le plus long)")
    contours(resume, manque)
    fin(BRUT, resume, manque, "espagne")


if __name__ == "__main__":
    main()
