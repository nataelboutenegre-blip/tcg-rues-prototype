#!/usr/bin/env python3
# -*- coding: utf-8 -*-
u"""
TerraFront — Les monuments, etape 1 : l'inventaire.

CE QUE FAIT CE SCRIPT
  Il interroge Wikidata et ecrit deux CSV. Il NE TELECHARGE AUCUNE IMAGE et
  N'ECRIT RIEN dans la base. On regarde les chiffres, et seulement apres on
  decide s'il y a une fonctionnalite ou pas.

POURQUOI IL TOURNE CHEZ TOI ET PAS CHEZ MOI
  Le conteneur de Claude passe par un proxy qui refuse wikidata.org. Je peux
  ecrire le script, je ne peux pas le lancer.

LA QUESTION A LAQUELLE IL REPOND
  Combien de lieux VRAIMENT connus peut-on rattacher a une commune francaise ?
  Si on trouve 200 a 500 noms que n'importe qui reconnait, ca vaut une page
  entiere du jeu. Si on ne trouve que des chapelles de village, mieux vaut une
  liste ecrite a la main.

COMMENT ON MESURE « CONNU », ET POURQUOI C'EST LE POINT DELICAT
  Il n'existe pas de liste des monuments celebres. La base Merimee en recense
  45 000, en majorite des edifices que personne ne connait — elle ne distingue
  pas la tour Eiffel d'une grange classee.

  On utilise donc un indicateur detourne mais tres fiable : le NOMBRE DE
  VERSIONS LINGUISTIQUES de la page Wikipedia. Le Mont-Saint-Michel existe en
  plus de cent langues, une eglise de village en une seule. C'est a peu pres
  la definition operatoire de « tout le monde connait ».

  Le script ne choisit pas le seuil : il sort la repartition par tranche, et
  c'est toi qui tranches en voyant les noms.

CE QU'ON EXCLUT, ET POURQUOI
  — les personnes : une statue est un lieu, un sculpteur non
  — les communes elles-memes : elles sont deja le jeu
  — tout ce qui n'a pas de coordonnees : un lieu se trouve sur une carte,
    une entreprise ou un evenement non

USAGE
    python3 monuments-1-inventaire.py --essai     # 3 departements, pour voir
    python3 monuments-1-inventaire.py             # les 101

  Aucune dependance a installer : bibliotheque standard seulement.

CE QUI SORT
    monuments-inventaire.csv   code_insee, commune, monument, type, langues,
                               image, wikidata
    monuments-tranches.csv     combien de lieux par tranche de notoriete
"""

import argparse, csv, json, sys, time, urllib.parse, urllib.request
from collections import Counter

UA = "TerraFront/1.0 (https://terrafront.fr) python-urllib"
WDQS = "https://query.wikidata.org/sparql"

# Un lieu present dans au moins 4 langues. Volontairement bas : on veut VOIR
# la repartition avant de couper. Couper trop haut au depart, c'est decider
# sans avoir regarde.
LANGUES_MINI = 4

DEPARTEMENTS = (
    ["%02d" % d for d in range(1, 20)] + ["2A", "2B"] +
    ["%02d" % d for d in range(21, 96)] +
    ["971", "972", "973", "974", "976"]
)

REQUETE = u"""
SELECT ?item ?itemLabel ?insee ?communeLabel ?langues ?image ?typeLabel WHERE {
  ?item wikibase:sitelinks ?langues .
  FILTER(?langues >= %d)
  ?item wdt:P625 ?coord .
  ?item wdt:P131 ?commune .
  ?commune wdt:P374 ?insee .
  FILTER(STRSTARTS(?insee, "%s"))
  FILTER NOT EXISTS { ?item wdt:P31 wd:Q5 }
  FILTER NOT EXISTS { ?item wdt:P31 wd:Q484170 }
  OPTIONAL { ?item wdt:P18 ?image }
  OPTIONAL { ?item wdt:P31 ?type }
  SERVICE wikibase:label { bd:serviceParam wikibase:language "fr,en". }
}
"""


def http_json(url, essais=4):
    for n in range(1, essais + 1):
        try:
            req = urllib.request.Request(url)
            req.add_header("User-Agent", UA)
            req.add_header("Accept", "application/json")
            with urllib.request.urlopen(req, timeout=180) as r:
                return json.loads(r.read().decode("utf-8"))
        except Exception as e:
            if n == essais:
                raise
            attente = 4 * n
            print("      ! %s — nouvel essai dans %ds" % (e, attente), file=sys.stderr)
            time.sleep(attente)


def lieux_du_departement(prefixe):
    url = WDQS + "?" + urllib.parse.urlencode({
        "query": REQUETE % (LANGUES_MINI, prefixe), "format": "json"})
    data = http_json(url)
    vus, lignes = set(), []
    for b in data["results"]["bindings"]:
        qid = b["item"]["value"].rsplit("/", 1)[-1]
        if qid in vus:          # plusieurs types pour un meme lieu
            continue
        vus.add(qid)
        lignes.append({
            "code_insee": b["insee"]["value"].strip(),
            "commune": b.get("communeLabel", {}).get("value", ""),
            "monument": b.get("itemLabel", {}).get("value", ""),
            "type": b.get("typeLabel", {}).get("value", ""),
            "langues": int(b["langues"]["value"]),
            "image": urllib.parse.unquote(b["image"]["value"].rsplit("/", 1)[-1])
                     if b.get("image") else "",
            "wikidata": qid,
        })
    return lignes


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--essai", action="store_true",
                    help="Paris (75), Bouches-du-Rhone (13) et Aveyron (12)")
    args = ap.parse_args()

    deps = ["75", "13", "12"] if args.essai else DEPARTEMENTS
    print("Inventaire sur %d departement(s), lieux presents dans au moins "
          "%d langues.\n" % (len(deps), LANGUES_MINI))

    tout = []
    for i, d in enumerate(deps, 1):
        lignes = lieux_du_departement(d)
        celebres = sum(1 for l in lignes if l["langues"] >= 15)
        print("%3d/%d  dept %-3s  %4d lieux, dont %3d en 15 langues et plus"
              % (i, len(deps), d, len(lignes), celebres))
        tout.extend(lignes)
        time.sleep(0.6)

    tout.sort(key=lambda l: (-l["langues"], l["code_insee"]))

    with open("monuments-inventaire.csv", "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=["code_insee", "commune", "monument",
                                           "type", "langues", "image", "wikidata"])
        w.writeheader()
        w.writerows(tout)

    # --- la repartition : c'est elle qui sert a choisir le seuil ------------
    TRANCHES = [(100, 10**9, "100 langues et plus — connu dans le monde entier"),
                (50, 100,  "50 a 99 — connu bien au-dela de la France"),
                (30, 50,   "30 a 49 — connu de tous les Francais"),
                (20, 30,   "20 a 29 — connu"),
                (15, 20,   "15 a 19 — connu des amateurs"),
                (10, 15,   "10 a 14 — limite basse"),
                (4,  10,   "4 a 9 — local")]
    with open("monuments-tranches.csv", "w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh)
        w.writerow(["tranche", "lieux", "communes concernees", "exemples"])
        print("\nRepartition :")
        for bas, haut, libelle in TRANCHES:
            dedans = [l for l in tout if bas <= l["langues"] < haut]
            communes = len({l["code_insee"] for l in dedans})
            ex = " · ".join(l["monument"] for l in dedans[:4])
            w.writerow([libelle, len(dedans), communes, ex])
            print("   %-46s %5d lieux, %5d communes" % (libelle, len(dedans), communes))
            if ex:
                print("      %s" % ex)

    # --- le chiffre qui decide ---------------------------------------------
    for seuil in (15, 20, 30):
        gardes = [l for l in tout if l["langues"] >= seuil]
        communes = len({l["code_insee"] for l in gardes})
        avec_image = sum(1 for l in gardes if l["image"])
        print("\nA partir de %d langues : %d lieux dans %d communes, "
              "%d avec une image (%.0f %%)"
              % (seuil, len(gardes), communes, avec_image,
                 100.0 * avec_image / max(len(gardes), 1)))

    print("\nEcrit : monuments-inventaire.csv et monuments-tranches.csv")
    print("Rien n'a ete telecharge, rien n'a ete modifie en base.")


if __name__ == "__main__":
    main()
