# -*- coding: utf-8 -*-
"""
TerraFront — Andorre (7 paroisses) et Monaco (1 commune), pour boucher les trous de la carte.

  cd ~/Code/tcg-rues-prototype && python3 _donnees/micro-etats/telecharger-andorre-monaco.py

Wikidata : nom, population (P1082, la plus récente), photo (P18), article fr, code ISO 3166-2 (P300),
contour (P3896, page « Data:…map » de Commons, issue d'OpenStreetMap : licence indiquée dans le fichier).
Écrit _donnees/micro-etats/brut/ : communes.json (tout) et un fichier de contour par territoire.
"""
import json, os, sys, time, urllib.parse

ICI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(ICI))
from commun import sparql, http, http_json, COMMONS   # noqa: E402

BRUT = os.path.join(ICI, "brut")
os.makedirs(BRUT, exist_ok=True)


def main():
    print("1/3 Wikidata : paroisses d'Andorre et Monaco…")
    lignes = sparql("""
      SELECT ?item ?iso ?nom ?pop ?date ?img ?forme ?article WHERE {
        { ?item wdt:P31 wd:Q24279 . } UNION { VALUES ?item { wd:Q235 } }
        OPTIONAL { ?item wdt:P300 ?iso }
        OPTIONAL { ?item rdfs:label ?nom FILTER(lang(?nom) = "fr") }
        OPTIONAL { ?item p:P1082 ?st . ?st ps:P1082 ?pop . OPTIONAL { ?st pq:P585 ?date } }
        OPTIONAL { ?item wdt:P18 ?img }
        OPTIONAL { ?item wdt:P3896 ?forme }
        OPTIONAL { ?article schema:about ?item ; schema:isPartOf <https://fr.wikipedia.org/> }
      }""")
    par = {}
    for l in lignes:
        q = l["item"].rsplit("/", 1)[-1]
        e = par.setdefault(q, {"wikidata": q, "iso": l["iso"], "nom": l["nom"], "pop": 0, "date": "", "img": l["img"],
                               "forme": l["forme"], "article": l["article"]})
        if l["pop"] and (l["date"] or "") >= e["date"]:
            e["pop"], e["date"] = int(float(l["pop"])), l["date"] or ""
        for k in ("iso", "img", "forme", "article"):
            e[k] = e[k] or l[k]
    print("   %d territoires : %s" % (len(par), ", ".join("%s (%s, %d hab.)" % (e["nom"], e["iso"], e["pop"]) for e in par.values())))

    print("2/3 Contours (Commons, pages Data:…map)…")
    for e in par.values():
        if not e["forme"]:
            print("   ! pas de contour sur Wikidata :", e["nom"]); continue
        # la valeur ressemble à http://commons.wikimedia.org/data/main/Data:Andorra/Canillo.map : le titre peut contenir des « / »
        f = urllib.parse.unquote(e["forme"])
        titre = f.split("/data/main/", 1)[1] if "/data/main/" in f else f.rsplit("/", 1)[-1]
        url = "https://commons.wikimedia.org/w/index.php?" + urllib.parse.urlencode({"title": titre, "action": "raw"})
        try:
            brut = http(url, essais=2)
        except Exception as err:
            print("   ! %s : contour introuvable (%s, %s)" % (e["nom"], titre, err)); continue
        d = json.loads(brut)
        e["contour_licence"] = d.get("license", "")
        e["contour_source"] = d.get("sources", "")
        nom = (e["iso"] or e["wikidata"]).replace("-", "_") + ".geojson"
        json.dump(d.get("data"), open(os.path.join(BRUT, nom), "w"))
        e["contour_fichier"] = nom
        print("   %s : %s (%s)" % (e["nom"], nom, e["contour_licence"]))
        time.sleep(0.5)

    # contours manquants : Nominatim (OpenStreetMap, ODbL), une requête par seconde au plus
    NOMS_OSM = {"AD-04": "La Massana", "AD-06": "Sant Julià de Lòria", "AD-07": "Andorra la Vella", "AD-08": "Escaldes-Engordany"}
    for e in par.values():
        if e.get("contour_fichier") and e["iso"] != "AD-08":   # Escaldes : le contour Commons est trop sommaire
            continue
        nom_osm = NOMS_OSM.get(e["iso"])
        if not nom_osm:
            continue
        url = "https://nominatim.openstreetmap.org/search?" + urllib.parse.urlencode(
            {"q": nom_osm, "countrycodes": "ad", "polygon_geojson": 1, "format": "geojson", "limit": 5})
        try:
            d = json.loads(http(url, essais=2))
        except Exception as err:
            print("   ! %s : Nominatim en échec (%s)" % (e["nom"], err)); time.sleep(1.5); continue
        polys = [f for f in d.get("features", []) if (f.get("geometry") or {}).get("type") in ("Polygon", "MultiPolygon")
                 and (f.get("properties") or {}).get("type") in ("administrative", "boundary") or
                 (f.get("properties") or {}).get("category") == "boundary"]
        polys = [f for f in polys if (f.get("geometry") or {}).get("type") in ("Polygon", "MultiPolygon")]
        if not polys:
            print("   ! %s : pas de polygone chez Nominatim" % e["nom"]); time.sleep(1.5); continue
        nom = e["iso"].replace("-", "_") + ".geojson"
        json.dump({"type": "FeatureCollection", "features": polys[:1]}, open(os.path.join(BRUT, nom), "w"))
        e.update({"contour_fichier": nom, "contour_licence": "ODbL-1.0", "contour_source": "OpenStreetMap (Nominatim)"})
        print("   %s : %s (OpenStreetMap, ODbL)" % (e["nom"], nom))
        time.sleep(1.5)

    print("3/3 Photos : auteurs et licences…")
    fichiers = [urllib.parse.unquote(e["img"].rsplit("/", 1)[-1]) for e in par.values() if e["img"]]
    if fichiers:
        corps = urllib.parse.urlencode({"action": "query", "format": "json", "prop": "imageinfo", "iiprop": "extmetadata",
                                        "iiextmetadatafilter": "Artist|LicenseShortName",
                                        "titles": "|".join("File:" + f for f in fichiers)}).encode("utf-8")
        data = http_json(COMMONS, donnees=corps)
        normal = {x["to"]: x["from"] for x in (data.get("query", {}).get("normalized") or [])}
        meta = {}
        for page in data.get("query", {}).get("pages", {}).values():
            t = normal.get(page.get("title", ""), page.get("title", ""))[len("File:"):]
            m = (page.get("imageinfo") or [{}])[0].get("extmetadata") or {}
            meta[t] = {"auteur": (m.get("Artist") or {}).get("value", ""), "licence": (m.get("LicenseShortName") or {}).get("value", "")}
        for e in par.values():
            if e["img"]:
                f = urllib.parse.unquote(e["img"].rsplit("/", 1)[-1])
                e["photo"] = f
                e.update({"photo_" + k: v for k, v in (meta.get(f) or {}).items()})
    json.dump(list(par.values()), open(os.path.join(BRUT, "communes.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print("\nFini : %d territoires, %d contours. Dis-le à Claude." % (len(par), sum(1 for e in par.values() if e.get("contour_fichier"))))


if __name__ == "__main__":
    main()
