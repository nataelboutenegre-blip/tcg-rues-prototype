#!/usr/bin/env python3
# -*- coding: utf-8 -*-
u"""
TerraFront — Les villages remarquables, etape 1 : l'inventaire.

CE QUE FAIT CE SCRIPT
  Il demande a Wikidata la liste des communes membres de l'association « Les
  Plus Beaux Villages de France », et ecrit un CSV. Il NE TOUCHE A RIEN :
  ni la base, ni le stockage, ni le jeu.

POURQUOI IL TOURNE CHEZ TOI
  Mon conteneur ne peut pas joindre wikidata.org. Je peux ecrire le script,
  pas le lancer.

LE NOM
  « Les Plus Beaux Villages de France » est une marque deposee, et tu as
  verifie toi-meme que l'association defend son nom. La LISTE des communes
  est un fait public, et la reprendre pour construire une collection n'a
  rien a voir avec s'appeler comme elle.

  Ce script se sert donc du nom pour INTERROGER Wikidata — il faut bien le
  nommer pour le trouver — et c'est tout. Le nom de la collection dans le
  jeu reste a choisir, et ce ne sera pas celui-la.

COMMENT L'ASSOCIATION EST TROUVEE
  Par son libelle, pas par un identifiant que j'aurais retenu de memoire et
  qui pourrait etre faux. Si Wikidata n'a pas d'entite portant exactement ce
  libelle, le script le dit au lieu de renvoyer une liste vide sans
  explication.

USAGE
    cd _sql
    python3 villages-1-inventaire.py

  Aucune dependance : bibliotheque standard seulement.

CE QUI SORT
    villages-inventaire.csv   code_insee, commune, departement, wikidata
"""

import csv, json, sys, time
import urllib.parse, urllib.request

UA = "TerraFront/1.0 (https://terrafront.fr) python-urllib"
WDQS = "https://query.wikidata.org/sparql"
NOM = u"Les Plus Beaux Villages de France"

# On resout l'association par son libelle francais, puis on prend ses
# membres. P463 = « membre de », P374 = code INSEE.
REQUETE = u"""
SELECT ?item ?itemLabel ?insee WHERE {
  ?asso rdfs:label "%s"@fr .
  ?item wdt:P463 ?asso .
  ?item wdt:P374 ?insee .
  SERVICE wikibase:label { bd:serviceParam wikibase:language "fr,en". }
}
ORDER BY ?insee
""" % NOM


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
            print("      ! %s — nouvel essai dans %ds" % (e, 4 * n), file=sys.stderr)
            time.sleep(4 * n)


def main():
    print(u"Interrogation de Wikidata : les membres de « %s »...\n" % NOM)
    url = WDQS + "?" + urllib.parse.urlencode({"query": REQUETE, "format": "json"})
    data = http_json(url)
    lignes = []
    vus = set()
    for b in data["results"]["bindings"]:
        insee = b["insee"]["value"].strip()
        if insee in vus:
            continue
        vus.add(insee)
        lignes.append({
            "code_insee": insee,
            "commune": b.get("itemLabel", {}).get("value", ""),
            "departement": insee[:3] if insee.startswith("97") else insee[:2],
            "wikidata": b["item"]["value"].rsplit("/", 1)[-1],
        })

    if not lignes:
        print(u"Aucun resultat. Deux explications possibles, et elles ne se")
        print(u"corrigent pas pareil :")
        print(u"  — aucune entite Wikidata ne porte exactement ce libelle en")
        print(u"    francais, et il faudrait la chercher autrement ;")
        print(u"  — les communes membres n'ont pas la propriete « membre de ».")
        print(u"Dis-le moi, je ne devinerai pas.")
        return

    lignes.sort(key=lambda l: l["code_insee"])
    with open("villages-inventaire.csv", "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=["code_insee", "commune",
                                           "departement", "wikidata"])
        w.writeheader()
        w.writerows(lignes)

    deps = {}
    for l in lignes:
        deps[l["departement"]] = deps.get(l["departement"], 0) + 1
    tete = sorted(deps.items(), key=lambda x: -x[1])[:8]

    print(u"%d communes trouvees, dans %d departements.\n" % (len(lignes), len(deps)))
    print(u"Les departements les mieux servis :")
    for d, n in tete:
        print(u"   %-4s %d" % (d, n))
    print(u"\nUn echantillon :")
    for l in lignes[:10]:
        print(u"   %-6s %s" % (l["code_insee"], l["commune"]))

    print(u"\nEcrit : villages-inventaire.csv")
    print(u"Rien n'a ete telecharge d'autre, rien n'a ete modifie en base.")


if __name__ == "__main__":
    main()
