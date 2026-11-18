#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
TerraFront — saison 3, la Belgique : téléchargement des données brutes.

CE QUE FAIT CE SCRIPT
  1. Statbel (office belge de statistique) : les secteurs statistiques 2025
     (contours, avec le code et les noms FR / NL / DE de chaque commune, sa
     province et son arrondissement) et la population par secteur au 1er janvier
     2025. Licence CC BY 4.0 : usage commercial autorisé, à condition d'afficher
     « Source : Statbel » dans le jeu. On regroupe ensuite les secteurs par
     commune (565 communes depuis les fusions de 2025).
  2. Wikidata : la liste des communes belges (code INS / NIS, noms en français,
     néerlandais et allemand, position, article Wikipédia), leur population et
     leur photo. Données Wikidata : CC0.
  3. Wikimedia Commons : l'auteur et la licence de chaque photo (attribution
     obligatoire pour les photos en CC BY-SA), comme pour la France et la Suisse.

  Il N'ÉCRIT RIEN dans la base et ne touche pas au jeu. Tout part dans
  _donnees/belgique/brut/ (ignoré par git : les fichiers Statbel sont gros).

POURQUOI IL TOURNE CHEZ TOI
  Mon espace de travail ne peut pas joindre Statbel, Wikidata ni Commons.
  Ton Terminal, si.

USAGE (depuis le dossier du jeu, sur ton Mac)
    git pull
    python3 _donnees/belgique/telecharger-belgique.py

  Aucune dépendance à installer. Relançable : un fichier déjà téléchargé en
  entier n'est pas retéléchargé. Si Statbel a changé ses pages et que le script
  ne trouve pas les fichiers, il te dit lesquels télécharger à la main et où
  les poser (dans _donnees/belgique/brut/), puis tu le relances.
"""

import csv, json, os, re, sys, time, urllib.parse, urllib.request

UA = "TerraFront/1.0 (https://terrafront.fr; contact via Discord) python-urllib"
WDQS = os.environ.get("TF_WDQS", "https://query.wikidata.org/sparql")
COMMONS = os.environ.get("TF_COMMONS", "https://commons.wikimedia.org/w/api.php")
ICI = os.path.dirname(os.path.abspath(__file__))
BRUT = os.path.join(ICI, "brut")

# Les pages Statbel où se trouvent les liens de téléchargement (plusieurs langues, au cas où)
PAGES_SECTEURS = [
    "https://statbel.fgov.be/en/open-data/statistical-sectors-2025",
    "https://statbel.fgov.be/fr/open-data/secteurs-statistiques-2025",
    "https://statbel.fgov.be/nl/open-data/statistische-sectoren-2025",
]
PAGES_POPULATION = [
    "https://statbel.fgov.be/en/open-data/population-statistical-sector-12",
    "https://statbel.fgov.be/fr/open-data/population-par-secteur-statistique-12",
    "https://statbel.fgov.be/nl/open-data/bevolking-statistische-sector-12",
]


def requete(url, donnees=None, accepte="application/json"):
    req = urllib.request.Request(url, data=donnees)
    req.add_header("User-Agent", UA)
    req.add_header("Accept", accepte)
    return req


def http(url, donnees=None, accepte="application/json", essais=4):
    for tentative in range(1, essais + 1):
        try:
            with urllib.request.urlopen(requete(url, donnees, accepte), timeout=180) as r:
                return r.read()
        except Exception as e:
            if tentative == essais:
                raise
            attente = 4 * tentative
            print("      ! %s — nouvel essai dans %ds" % (e, attente), file=sys.stderr)
            time.sleep(attente)


def http_json(url, donnees=None):
    return json.loads(http(url, donnees).decode("utf-8"))


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
# 1. Statbel
# ---------------------------------------------------------------------------
def liens(pages, motif):
    """Les liens de téléchargement trouvés sur la première page qui répond."""
    for page in pages:
        try:
            html = http(page, accepte="text/html").decode("utf-8", "replace")
        except Exception as e:
            print("   (page %s : %s)" % (page, e))
            continue
        trouves = []
        for href in re.findall(r'href="([^"]+)"', html):
            href = urllib.parse.urljoin(page, href.replace("&amp;", "&"))
            if re.search(motif, href, re.I) and href not in trouves:
                trouves.append(href)
        if trouves:
            print("   page : %s" % page)
            return page, trouves
    return None, []


def choisir(trouves, preferences):
    for pref in preferences:
        for href in trouves:
            if pref(href.lower()):
                return href
    return trouves[0] if trouves else None


def nom_fichier(url):
    return urllib.parse.unquote(url.split("?")[0].rsplit("/", 1)[-1]) or "fichier"


def statbel(resume):
    manque = []
    print("   les contours des secteurs statistiques 2025")
    page, trouves = liens(PAGES_SECTEURS, r"\.(zip|gpkg|geojson|json)(\?|$)")
    url = choisir(trouves, (lambda h: "gpkg" in h and "4326" in h,
                            lambda h: "geojson" in h and "4326" in h,
                            lambda h: "gpkg" in h and "3812" in h,
                            lambda h: "gpkg" in h and "31370" in h,
                            lambda h: "gpkg" in h,
                            lambda h: "geojson" in h,
                            lambda h: h.endswith(".zip")))
    if url:
        print("   fichier : %s" % nom_fichier(url))
        taille = telecharger(url, os.path.join(BRUT, nom_fichier(url)))
        resume["secteurs"] = {"page": page, "url": url, "fichier": nom_fichier(url), "octets": taille, "autres_liens": trouves}
    else:
        manque.append(("les secteurs statistiques 2025 (GeoPackage ou GeoJSON)", PAGES_SECTEURS[0]))

    print("\n   la population par secteur statistique (1er janvier 2025)")
    page, trouves = liens(PAGES_POPULATION, r"\.(zip|xlsx|csv|txt)(\?|$)")
    url = choisir(trouves, (lambda h: "2025" in h and h.endswith(".zip"),
                            lambda h: "2025" in h and h.endswith(".xlsx"),
                            lambda h: "2025" in h,
                            lambda h: h.endswith(".zip"),
                            lambda h: h.endswith(".xlsx")))
    if url:
        print("   fichier : %s" % nom_fichier(url))
        taille = telecharger(url, os.path.join(BRUT, nom_fichier(url)))
        resume["population"] = {"page": page, "url": url, "fichier": nom_fichier(url), "octets": taille, "autres_liens": trouves}
    else:
        manque.append(("la population par secteur statistique 2025 (zip ou xlsx)", PAGES_POPULATION[0]))
    return manque


# ---------------------------------------------------------------------------
# 2. Wikidata
# ---------------------------------------------------------------------------
# Q493522 = commune de Belgique ; P1567 = code INS (NIS) ; P576 = date de dissolution
FILTRE = """
  ?c wdt:P1567 ?nis ;
     wdt:P31/wdt:P279* wd:Q493522 .
  FILTER NOT EXISTS { ?c wdt:P576 ?fin }
"""

REQ_COMMUNES = """
SELECT ?nis ?c ?fr ?nl ?de ?coord ?article WHERE {
%s
  OPTIONAL { ?c rdfs:label ?fr FILTER(LANG(?fr) = "fr") }
  OPTIONAL { ?c rdfs:label ?nl FILTER(LANG(?nl) = "nl") }
  OPTIONAL { ?c rdfs:label ?de FILTER(LANG(?de) = "de") }
  OPTIONAL { ?c wdt:P625 ?coord }
  OPTIONAL { ?article schema:about ?c ; schema:isPartOf <https://fr.wikipedia.org/> }
}
""" % FILTRE

REQ_POPULATION = """
SELECT ?nis ?pop ?date WHERE {
%s
  ?c p:P1082 ?st .
  ?st ps:P1082 ?pop .
  OPTIONAL { ?st pq:P585 ?date }
  ?st wikibase:rank ?rang FILTER(?rang != wikibase:DeprecatedRank)
}
""" % FILTRE

REQ_IMAGES = """
SELECT ?nis (SAMPLE(?img) AS ?image) WHERE {
%s
  ?c wdt:P18 ?img
}
GROUP BY ?nis
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


def wikidata(resume):
    communes = sparql(REQ_COMMUNES)
    lignes = []
    for b in communes:
        lat = lon = ""
        m = re.match(r"Point\(([-\d.]+) ([-\d.]+)\)", b["coord"])
        if m:
            lon, lat = m.group(1), m.group(2)
        article = urllib.parse.unquote(b["article"].rsplit("/", 1)[-1]).replace("_", " ") if b["article"] else ""
        lignes.append([b["nis"], b["c"].rsplit("/", 1)[-1], b["fr"], b["nl"], b["de"], lat, lon, article])
    lignes.sort(key=lambda l: (l[0], l[1]))
    ecrire_csv("wikidata-communes.csv", ["nis", "wikidata", "nom_fr", "nom_nl", "nom_de", "lat", "lon", "article_fr"], lignes)
    nb = len({l[0] for l in lignes})
    print("   %d communes (%d lignes)" % (nb, len(lignes)))
    time.sleep(1)

    pops = sparql(REQ_POPULATION)
    ecrire_csv("wikidata-population.csv", ["nis", "population", "date"],
               sorted([p["nis"], p["pop"], p["date"][:10]] for p in pops))
    print("   %d chiffres de population" % len(pops))
    time.sleep(1)

    images = sparql(REQ_IMAGES)
    photos = [(b["nis"], urllib.parse.unquote(b["image"].rsplit("/", 1)[-1])) for b in images if b["image"]]
    print("   %d communes avec une photo" % len(photos))

    print("\n3/3  Commons : auteurs et licences des photos")
    infos = metadonnees(sorted({f for _, f in photos}))
    noms = {l[0]: (l[2] or l[3]) for l in lignes}
    ecrire_csv("photos-inventaire-belgique.csv", ["code", "nom", "fichier", "auteur", "licence", "licence_url"],
               sorted(["BE" + o, noms.get(o, ""), f] + list(infos.get(f, ("", "", ""))) for o, f in photos))
    resume["wikidata"] = {"communes": nb, "populations": len(pops), "photos": len(photos),
                          "photos_sans_auteur": sum(1 for _, f in photos if not infos.get(f, ("",))[0]),
                          "le": time.strftime("%Y-%m-%d %H:%M")}


def main():
    os.makedirs(BRUT, exist_ok=True)
    resume = {}
    print("1/3  Statbel")
    manque = statbel(resume)
    print("\n2/3  Wikidata")
    wikidata(resume)
    with open(os.path.join(BRUT, "resume.json"), "w", encoding="utf-8") as fh:
        json.dump(resume, fh, ensure_ascii=False, indent=1)

    print("\nFini. Dans _donnees/belgique/brut/ :")
    for f in sorted(os.listdir(BRUT)):
        if not f.endswith(".partiel"):
            print("   %-55s %8.1f Mo" % (f, os.path.getsize(os.path.join(BRUT, f)) / 1e6))
    if manque:
        print("\nÀ TÉLÉCHARGER À LA MAIN (le script n'a pas trouvé le lien) :")
        for quoi, page in manque:
            print("   - %s\n     sur %s\n     → pose le fichier dans _donnees/belgique/brut/ puis relance le script" % (quoi, page))
    print("Rien n'a été modifié dans la base ni dans le jeu.")


if __name__ == "__main__":
    main()
