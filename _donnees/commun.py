# -*- coding: utf-8 -*-
"""
TerraFront — outils partagés par les scripts de téléchargement des pays
(Luxembourg, Espagne). Repris du script belge. Aucune dépendance.
"""

import csv, json, os, re, sys, time, urllib.parse, urllib.request

UA = "TerraFront/1.0 (https://terrafront.fr; contact via Discord) python-urllib"
WDQS = os.environ.get("TF_WDQS", "https://query.wikidata.org/sparql")
COMMONS = os.environ.get("TF_COMMONS", "https://commons.wikimedia.org/w/api.php")


def requete(url, donnees=None, accepte="application/json"):
    req = urllib.request.Request(url, data=donnees)
    req.add_header("User-Agent", UA)
    req.add_header("Accept", accepte)
    return req


def http(url, donnees=None, accepte="application/json", essais=4, delai=180):
    for tentative in range(1, essais + 1):
        try:
            with urllib.request.urlopen(requete(url, donnees, accepte), timeout=delai) as r:
                return r.read()
        except Exception as e:
            if tentative == essais:
                raise
            attente = 4 * tentative
            print("      ! %s — nouvel essai dans %ds" % (e, attente), file=sys.stderr)
            time.sleep(attente)


def http_json(url, donnees=None, accepte="application/json"):
    return json.loads(http(url, donnees, accepte).decode("utf-8"))


def telecharger(url, chemin):
    """Téléchargement par morceaux. Saute un fichier déjà complet."""
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


def nom_fichier(url):
    return urllib.parse.unquote(url.split("?")[0].rsplit("/", 1)[-1]) or "fichier"


def sparql(req):
    corps = urllib.parse.urlencode({"query": req, "format": "json"}).encode("utf-8")
    data = http_json(WDQS, donnees=corps)
    v = lambda b, k: (b.get(k) or {}).get("value", "")
    return [{k: v(b, k) for k in data["head"]["vars"]} for b in data["results"]["bindings"]]


def ecrire_csv(dossier, nom, entetes, lignes):
    with open(os.path.join(dossier, nom), "w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh)
        w.writerow(entetes)
        w.writerows(lignes)


def point(coord):
    m = re.match(r"Point\(([-\d.]+) ([-\d.]+)\)", coord or "")
    return (m.group(2), m.group(1)) if m else ("", "")


def article(url):
    return urllib.parse.unquote(url.rsplit("/", 1)[-1]).replace("_", " ") if url else ""


def metadonnees(fichiers):
    """{nom_fichier: (auteur, licence, licence_url)} pour des photos Commons, par paquets de 50."""
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
        if n % 10 == 0 or n == len(paquets):
            print("   auteurs et licences %d/%d" % (n, len(paquets)))
        time.sleep(0.4)
    return infos


def ogc_collections(base):
    """Les collections d'une API OGC Features : [(id, titre)]."""
    data = http_json(base.rstrip("/") + "/collections?f=json")
    return [(c.get("id", ""), c.get("title", "") or "") for c in data.get("collections", [])]


def ogc_tout(base, collection, chemin, filtre="", par_page=1000, max_pages=200):
    """Toutes les entités d'une collection OGC Features, page par page, dans un GeoJSON.
    Relançable : les pages déjà reçues sont gardées dans <chemin>.pages/."""
    dossier = chemin + ".pages"
    os.makedirs(dossier, exist_ok=True)
    url = "%s/collections/%s/items?f=json&limit=%d%s" % (base.rstrip("/"), collection, par_page, filtre)
    n, total = 0, 0
    while url and n < max_pages:
        n += 1
        page = os.path.join(dossier, "%04d.json" % n)
        if os.path.exists(page):
            with open(page, encoding="utf-8") as fh:
                data = json.load(fh)
        else:
            data = json.loads(http(url, accepte="application/geo+json, application/json", delai=300).decode("utf-8"))
            with open(page + ".partiel", "w", encoding="utf-8") as fh:
                json.dump(data, fh)
            os.replace(page + ".partiel", page)
        total += len(data.get("features", []))
        if n % 5 == 0:
            print("   page %d : %d entités" % (n, total))
        url = next((l["href"] for l in data.get("links", []) if l.get("rel") == "next"), None)
        if not data.get("features"):
            break
    entites = []
    for f in sorted(os.listdir(dossier)):
        with open(os.path.join(dossier, f), encoding="utf-8") as fh:
            entites.extend(json.load(fh).get("features", []))
    with open(chemin, "w", encoding="utf-8") as fh:
        json.dump({"type": "FeatureCollection", "features": entites}, fh)
    print("   %d entités → %s (%.1f Mo)" % (len(entites), os.path.basename(chemin), os.path.getsize(chemin) / 1e6))
    return len(entites)


def wikidata_pays(dossier, prefixe, filtre, langues, code_var="code"):
    """Communes d'un pays depuis Wikidata : liste (noms, position, article), population, photos.
    filtre : motif SPARQL qui lie ?c (la commune) et ?code (son code officiel)."""
    noms = "\n".join('  OPTIONAL { ?c rdfs:label ?n_%s FILTER(LANG(?n_%s) = "%s") }' % (l, l, l) for l in langues)
    req = """SELECT ?code ?c %s ?coord ?article WHERE {
%s
%s
  OPTIONAL { ?c wdt:P625 ?coord }
  OPTIONAL { ?article schema:about ?c ; schema:isPartOf <https://fr.wikipedia.org/> }
}""" % (" ".join("?n_" + l for l in langues), filtre, noms)
    lignes = []
    for b in sparql(req):
        lat, lon = point(b["coord"])
        lignes.append([b["code"], b["c"].rsplit("/", 1)[-1]] + [b["n_" + l] for l in langues] + [lat, lon, article(b["article"])])
    lignes.sort(key=lambda l: (l[0], l[1]))
    ecrire_csv(dossier, "wikidata-communes.csv", ["code", "wikidata"] + ["nom_" + l for l in langues] + ["lat", "lon", "article_fr"], lignes)
    nb = len({l[0] for l in lignes})
    print("   %d communes (%d lignes)" % (nb, len(lignes)))
    time.sleep(1)

    pops = sparql("""SELECT ?code ?pop ?date WHERE {
%s
  ?c p:P1082 ?st . ?st ps:P1082 ?pop .
  OPTIONAL { ?st pq:P585 ?date }
  ?st wikibase:rank ?rang FILTER(?rang != wikibase:DeprecatedRank)
}""" % filtre)
    ecrire_csv(dossier, "wikidata-population.csv", ["code", "population", "date"],
               sorted([p["code"], p["pop"], p["date"][:10]] for p in pops))
    print("   %d chiffres de population" % len(pops))
    time.sleep(1)

    images = sparql("""SELECT ?code (SAMPLE(?img) AS ?image) WHERE {
%s
  ?c wdt:P18 ?img
} GROUP BY ?code""" % filtre)
    photos = [(b["code"], urllib.parse.unquote(b["image"].rsplit("/", 1)[-1])) for b in images if b["image"]]
    print("   %d communes avec une photo" % len(photos))
    print("   Commons : auteurs et licences des photos")
    infos = metadonnees(sorted({f for _, f in photos}))
    nom = {l[0]: next((x for x in l[2:2 + len(langues)] if x), "") for l in lignes}
    ecrire_csv(dossier, "photos-inventaire.csv", ["code", "nom", "fichier", "auteur", "licence", "licence_url"],
               sorted([prefixe + o, nom.get(o, ""), f] + list(infos.get(f, ("", "", ""))) for o, f in photos))
    return {"communes": nb, "populations": len(pops), "photos": len(photos),
            "photos_sans_auteur": sum(1 for _, f in photos if not infos.get(f, ("",))[0])}


def fin(dossier, resume, manque, pays):
    with open(os.path.join(dossier, "resume.json"), "w", encoding="utf-8") as fh:
        json.dump(resume, fh, ensure_ascii=False, indent=1)
    print("\nFini. Dans _donnees/%s/brut/ :" % pays)
    for f in sorted(os.listdir(dossier)):
        p = os.path.join(dossier, f)
        if os.path.isfile(p) and not f.endswith(".partiel"):
            print("   %-55s %8.1f Mo" % (f, os.path.getsize(p) / 1e6))
    if manque:
        print("\nÀ TÉLÉCHARGER À LA MAIN (le script n'a pas trouvé) :")
        for quoi, page in manque:
            print("   - %s\n     sur %s\n     → pose le fichier dans _donnees/%s/brut/ puis relance le script" % (quoi, page, pays))
    print("Rien n'a été modifié dans la base ni dans le jeu.")
