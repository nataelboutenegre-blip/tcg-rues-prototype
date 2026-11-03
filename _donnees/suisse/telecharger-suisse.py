#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
TerraFront — saison 3, la Suisse : téléchargement des données brutes.

CE QUE FAIT CE SCRIPT
  1. swisstopo : télécharge swissBOUNDARIES3D (limites des communes, des
     cantons et du pays, avec la population et la surface de chaque commune).
     Conditions : « Open use. Must provide the source. » Usage commercial
     autorisé, à condition d'afficher « © swisstopo » dans le jeu.
  2. Wikidata : la liste des communes suisses (numéro OFS, noms en français,
     allemand et italien, position, article Wikipédia), leur population et
     leur photo. Données Wikidata : CC0.
  3. Wikimedia Commons : l'auteur et la licence de chaque photo, comme pour
     la France (l'attribution est obligatoire pour les photos en CC BY-SA).

  Il N'ÉCRIT RIEN dans la base et ne touche pas au jeu. Tout part dans
  _donnees/suisse/brut/ (ignoré par git : le fichier swisstopo est gros).

POURQUOI IL TOURNE CHEZ TOI
  Mon espace de travail et le pont vers ton Mac ne peuvent pas joindre
  swisstopo, Wikidata ni Commons. Ton Terminal, si.

USAGE (depuis le dossier du jeu)
    python3 _donnees/suisse/telecharger-suisse.py           # tout (1, 2, 3)
    python3 _donnees/suisse/telecharger-suisse.py --lacs    # seulement les lacs

  --lacs : swissTLMRegio (swisstopo), pour la forme des lacs. Les communes de
  swissBOUNDARIES3D englobent leur part de lac (Lausanne descend jusqu'au
  milieu du Léman) : il faut les lacs pour les découper. Conditions :
  usage commercial autorisé, source à citer (« © swisstopo »).
  Aucune dépendance à installer. Relançable : un fichier déjà téléchargé
  en entier n'est pas retéléchargé.
"""

import csv, json, os, re, sys, time, urllib.parse, urllib.request

UA = "TerraFront/1.0 (https://terrafront.fr; contact via Discord) python-urllib"
STAC_RACINE = os.environ.get("TF_STAC", "https://data.geo.admin.ch/api/stac/v0.9")
STAC = STAC_RACINE + "/collections/ch.swisstopo.swissboundaries3d/items"
WDQS = os.environ.get("TF_WDQS", "https://query.wikidata.org/sparql")
COMMONS = os.environ.get("TF_COMMONS", "https://commons.wikimedia.org/w/api.php")
ICI = os.path.dirname(os.path.abspath(__file__))
BRUT = os.path.join(ICI, "brut")


def requete(url, donnees=None, accepte="application/json"):
    req = urllib.request.Request(url, data=donnees)
    req.add_header("User-Agent", UA)
    req.add_header("Accept", accepte)
    return req


def http_json(url, donnees=None, essais=4):
    """Un GET ou POST JSON, avec reprise sur erreur passagère."""
    for tentative in range(1, essais + 1):
        try:
            with urllib.request.urlopen(requete(url, donnees), timeout=180) as r:
                return json.loads(r.read().decode("utf-8"))
        except Exception as e:
            if tentative == essais:
                raise
            attente = 4 * tentative
            print("      ! %s — nouvel essai dans %ds" % (e, attente), file=sys.stderr)
            time.sleep(attente)


# ---------------------------------------------------------------------------
# 1. swisstopo
# ---------------------------------------------------------------------------
def derniere_edition(collection_items=None, preferences=None):
    """Le jeu de données le plus récent et le fichier à prendre."""
    items, url = [], (collection_items or STAC) + "?limit=100"
    while url:
        page = http_json(url)
        items += page.get("features", [])
        url = next((l["href"] for l in page.get("links", []) if l.get("rel") == "next"), None)
    if not items:
        raise SystemExit("swisstopo : aucune édition trouvée.")
    items.sort(key=lambda it: ((it.get("properties") or {}).get("datetime") or "", it.get("id", "")))
    item = items[-1]
    assets = item.get("assets") or {}
    noms = list(assets)
    # par ordre de préférence : shapefile en coordonnées suisses (LV95),
    # n'importe quel shapefile, puis le GeoPackage
    for test in preferences or (lambda k: "2056" in k and k.endswith(".shp.zip"),
                 lambda k: k.endswith(".shp.zip"),
                 lambda k: "2056" in k and k.endswith(".gpkg.zip"),
                 lambda k: k.endswith(".gpkg.zip")):
        choix = [k for k in noms if test(k)]
        if choix:
            k = sorted(choix)[0]
            return item.get("id", "?"), k, assets[k]["href"]
    raise SystemExit("swisstopo : pas de fichier shapefile ni GeoPackage dans "
                     "l'édition %s. Fichiers proposés : %s" % (item.get("id"), ", ".join(noms)))


def telecharger(url, chemin):
    """Téléchargement par morceaux, avec l'avancement. Saute un fichier complet."""
    with urllib.request.urlopen(requete(url, accepte="*/*"), timeout=300) as r:
        total = int(r.headers.get("Content-Length") or 0)
        if total and os.path.exists(chemin) and os.path.getsize(chemin) == total:
            print("   déjà là (%.1f Mo), pas retéléchargé" % (total / 1e6))
            return total
        recu, dernier = 0, 0
        with open(chemin + ".partiel", "wb") as fh:
            while True:
                bloc = r.read(1 << 20)
                if not bloc:
                    break
                fh.write(bloc)
                recu += len(bloc)
                if recu - dernier > 10e6 or (total and recu == total):
                    dernier = recu
                    print("   %.0f / %s Mo" % (recu / 1e6, "%.0f" % (total / 1e6) if total else "?"))
    if total and recu != total:
        raise SystemExit("téléchargement incomplet (%d sur %d octets) : relance le script." % (recu, total))
    os.replace(chemin + ".partiel", chemin)
    return recu


# ---------------------------------------------------------------------------
# 2. Wikidata
# ---------------------------------------------------------------------------
# Q70208 = commune de Suisse ; P771 = numéro OFS ; P576 = date de dissolution
FILTRE = """
  ?c wdt:P771 ?ofs ;
     wdt:P31 wd:Q70208 .
  FILTER NOT EXISTS { ?c wdt:P576 ?fin }
"""

REQ_COMMUNES = """
SELECT ?ofs ?c ?fr ?de ?it ?coord ?article WHERE {
%s
  OPTIONAL { ?c rdfs:label ?fr FILTER(LANG(?fr) = "fr") }
  OPTIONAL { ?c rdfs:label ?de FILTER(LANG(?de) = "de") }
  OPTIONAL { ?c rdfs:label ?it FILTER(LANG(?it) = "it") }
  OPTIONAL { ?c wdt:P625 ?coord }
  OPTIONAL { ?article schema:about ?c ; schema:isPartOf <https://fr.wikipedia.org/> }
}
""" % FILTRE

REQ_POPULATION = """
SELECT ?ofs ?pop ?date WHERE {
%s
  ?c p:P1082 ?st .
  ?st ps:P1082 ?pop .
  OPTIONAL { ?st pq:P585 ?date }
  ?st wikibase:rank ?rang FILTER(?rang != wikibase:DeprecatedRank)
}
""" % FILTRE

REQ_IMAGES = """
SELECT ?ofs (SAMPLE(?img) AS ?image) WHERE {
%s
  ?c wdt:P18 ?img
}
GROUP BY ?ofs
""" % FILTRE


def sparql(req):
    corps = urllib.parse.urlencode({"query": req, "format": "json"}).encode("utf-8")
    data = http_json(WDQS, donnees=corps)
    v = lambda b, k: (b.get(k) or {}).get("value", "")
    return [{k: v(b, k) for k in data["head"]["vars"]} for b in data["results"]["bindings"]]


def ecrire_csv(nom, entetes, lignes):
    with open(os.path.join(BRUT, nom), "w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh)
        w.writerow(entetes)
        w.writerows(lignes)


def metadonnees(fichiers):
    """{nom_fichier: (auteur, licence, licence_url)} — par paquets de 50."""
    infos = {}
    paquets = [fichiers[i:i + 50] for i in range(0, len(fichiers), 50)]
    for n, paquet in enumerate(paquets, 1):
        corps = urllib.parse.urlencode({
            "action": "query", "format": "json", "prop": "imageinfo",
            "iiprop": "extmetadata", "iiextmetadatafilter": "Artist|LicenseShortName|LicenseUrl",
            "titles": "|".join("File:" + f for f in paquet),
        }).encode("utf-8")
        data = http_json(COMMONS, donnees=corps)
        # Commons renvoie le titre « normalisé » (espaces au lieu de _)
        normal = {x["to"]: x["from"] for x in (data.get("query", {}).get("normalized") or [])}
        for page in (data.get("query", {}).get("pages", {}) or {}).values():
            titre = normal.get(page.get("title", ""), page.get("title", ""))[len("File:"):]
            meta = ((page.get("imageinfo") or [{}])[0].get("extmetadata") or {})
            lire = lambda c: (meta.get(c) or {}).get("value", "") or ""
            auteur = re.sub(r"\s+", " ", re.sub(r"<[^>]+>", "", lire("Artist"))).strip()
            infos[titre] = (auteur, lire("LicenseShortName"), lire("LicenseUrl"))
        if n % 5 == 0 or n == len(paquets):
            print("   auteurs et licences %d/%d" % (n, len(paquets)))
        time.sleep(0.4)
    return infos


def lacs():
    """swissTLMRegio : on cherche la collection, puis le fichier le plus utile."""
    cols, url = [], STAC_RACINE + "/collections?limit=100"
    while url:
        page = http_json(url)
        cols += [c.get("id", "") for c in page.get("collections", [])]
        url = next((l["href"] for l in page.get("links", []) if l.get("rel") == "next"), None)
    trouvees = [c for c in cols if "swisstlmregio" in c.lower()]
    if not trouvees:
        raise SystemExit("swisstopo : pas de collection swissTLMRegio. Collections proches : "
                         + ", ".join(c for c in cols if "tlm" in c.lower() or "regio" in c.lower()))
    col = "ch.swisstopo.swisstlmregio" if "ch.swisstopo.swisstlmregio" in trouvees else sorted(trouvees)[0]
    print("   collection %s (trouvées : %s)" % (col, ", ".join(trouvees)))
    prefs = (lambda k: "hydro" in k.lower() and k.endswith(".shp.zip"),
             lambda k: "hydro" in k.lower() and k.endswith(".gpkg.zip"),
             lambda k: "2056" in k and k.endswith(".shp.zip"),
             lambda k: k.endswith(".shp.zip"),
             lambda k: "2056" in k and k.endswith(".gpkg.zip"),
             lambda k: k.endswith(".gpkg.zip"),
             lambda k: k.endswith(".zip"))
    edition, nom, url = derniere_edition(STAC_RACINE + "/collections/" + col + "/items", prefs)
    print("   édition %s : %s" % (edition, nom))
    taille = telecharger(url, os.path.join(BRUT, nom))
    with open(os.path.join(BRUT, "lacs.json"), "w", encoding="utf-8") as fh:
        json.dump({"collection": col, "edition": edition, "fichier": nom, "url": url, "octets": taille}, fh, indent=1)
    print("\nFini : %s (%.1f Mo) dans _donnees/suisse/brut/" % (nom, taille / 1e6))


def main():
    os.makedirs(BRUT, exist_ok=True)
    if "--lacs" in sys.argv:
        print("Lacs : swissTLMRegio")
        return lacs()
    resume = {}

    print("1/3  swisstopo (swissBOUNDARIES3D)")
    edition, nom, url = derniere_edition()
    print("   édition %s : %s" % (edition, nom))
    taille = telecharger(url, os.path.join(BRUT, nom))
    resume["swisstopo"] = {"edition": edition, "fichier": nom, "url": url, "octets": taille}

    print("\n2/3  Wikidata")
    communes = sparql(REQ_COMMUNES)
    lignes = []
    for b in communes:
        lat = lon = ""
        m = re.match(r"Point\(([-\d.]+) ([-\d.]+)\)", b["coord"])
        if m:
            lon, lat = m.group(1), m.group(2)
        article = urllib.parse.unquote(b["article"].rsplit("/", 1)[-1]).replace("_", " ") if b["article"] else ""
        lignes.append([b["ofs"], b["c"].rsplit("/", 1)[-1], b["fr"], b["de"], b["it"], lat, lon, article])
    lignes.sort(key=lambda l: (int(l[0]) if l[0].isdigit() else 99999, l[1]))
    ecrire_csv("wikidata-communes.csv", ["ofs", "wikidata", "nom_fr", "nom_de", "nom_it", "lat", "lon", "article_fr"], lignes)
    nb_ofs = len({l[0] for l in lignes})
    print("   %d communes (%d lignes)" % (nb_ofs, len(lignes)))
    time.sleep(1)

    pops = sparql(REQ_POPULATION)
    ecrire_csv("wikidata-population.csv", ["ofs", "population", "date"],
               sorted([p["ofs"], p["pop"], p["date"][:10]] for p in pops))
    print("   %d chiffres de population" % len(pops))
    time.sleep(1)

    images = sparql(REQ_IMAGES)
    photos = []
    for b in images:
        if b["image"]:
            photos.append((b["ofs"], urllib.parse.unquote(b["image"].rsplit("/", 1)[-1])))
    print("   %d communes avec une photo" % len(photos))

    print("\n3/3  Commons : auteurs et licences des photos")
    infos = metadonnees(sorted({f for _, f in photos}))
    noms_fr = {l[0]: l[2] for l in lignes}
    ecrire_csv("photos-inventaire-suisse.csv", ["code", "nom", "fichier", "auteur", "licence", "licence_url"],
               sorted(["CH" + o, noms_fr.get(o, ""), f] + list(infos.get(f, ("", "", ""))) for o, f in photos))
    sans_auteur = sum(1 for _, f in photos if not infos.get(f, ("",))[0])

    resume["wikidata"] = {"communes": nb_ofs, "populations": len(pops), "photos": len(photos),
                          "photos_sans_auteur": sans_auteur, "le": time.strftime("%Y-%m-%d %H:%M")}
    with open(os.path.join(BRUT, "resume.json"), "w", encoding="utf-8") as fh:
        json.dump(resume, fh, ensure_ascii=False, indent=1)

    print("\nFini. Dans _donnees/suisse/brut/ :")
    for f in sorted(os.listdir(BRUT)):
        if not f.endswith(".partiel"):
            print("   %-50s %8.1f Mo" % (f, os.path.getsize(os.path.join(BRUT, f)) / 1e6))
    print("Rien n'a été modifié dans la base ni dans le jeu.")


if __name__ == "__main__":
    main()
