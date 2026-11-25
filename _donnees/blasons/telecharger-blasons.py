# -*- coding: utf-8 -*-
"""
TerraFront — blasons des départements (France), cantons (Suisse), provinces (Belgique)
et cantons (Luxembourg), pour l'affichage d'un département complété à 100 % en Terra.

  cd ~/Code/tcg-rues-prototype && python3 _donnees/blasons/telecharger-blasons.py

1. Wikidata : l'image de blason (P94) de chaque territoire, retrouvé par son code ISO 3166-2 (P300).
2. Commons : auteur et licence de chaque fichier, puis une vignette PNG de 256 px.
Écrit :
  blasons/<code jeu>.png           les images servies par le jeu
  _donnees/blasons/blasons.json     code -> fichier Commons, auteur, licence (pour les crédits)
  _donnees/blasons/a-verifier.txt   ce qui manque, et les licences à regarder à la main
Rien n'est envoyé nulle part : tu me renvoies a-verifier.txt et blasons.json.
"""
import json, os, re, sys, time, urllib.parse

ICI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(ICI))
from commun import sparql, http_json, telecharger, COMMONS   # noqa: E402

RACINE = os.path.dirname(os.path.dirname(ICI))
SORTIE = os.path.join(RACINE, "blasons")
os.makedirs(SORTIE, exist_ok=True)

# codes du jeu -> code ISO 3166-2
FR = ["%02d" % i for i in range(1, 96) if i != 20] + ["2A", "2B", "971", "972", "973", "974", "976"]
CH = "AG AI AR BE BL BS FR GE GL GR JU LU NE NW OW SG SH SO SZ TG TI UR VD VS ZG ZH".split()
BE = "VAN VBR WBR VWV VOV WHT WLG VLI WLX WNA BRU".split()
LU = {"LCA": "CA", "LCL": "CL", "LDI": "DI", "LEC": "EC", "LES": "ES", "LGR": "GR", "LLU": "LU",
      "LME": "ME", "LRE": "RD", "LRM": "RM", "LVI": "VD", "LWI": "WI"}
ISO = {**{c: "FR-" + c for c in FR}, **{c: "CH-" + c for c in CH}, **{c: "BE-" + c for c in BE},
       **{c: "LU-" + v for c, v in LU.items()}}
JEU = {v: k for k, v in ISO.items()}
JEU["FR-75C"] = "75"   # Paris a changé de code ISO en 2023

# licences libres qu'on accepte (le reste part dans a-verifier.txt, sans image)
LIBRES = re.compile(r"^(public domain|pd|cc0|cc[ -]by([ -]sa)?|gfdl|attribution|copyrighted free use)", re.I)


def main():
    print("1/3 Wikidata : blasons (P94) par code ISO…")
    valeurs = " ".join('"%s"' % v for v in JEU)
    lignes = sparql("""
      SELECT ?iso ?item ?nom ?img WHERE {
        VALUES ?iso { %s }
        ?item wdt:P300 ?iso .
        OPTIONAL { ?item wdt:P94 ?img }
        OPTIONAL { ?item rdfs:label ?nom FILTER(lang(?nom) = "fr") }
      }""" % valeurs)
    par_code = {}
    for l in lignes:
        code = JEU.get(l["iso"])
        if not code or not l["img"]:
            par_code.setdefault(code, None)
            continue
        fichier = urllib.parse.unquote(l["img"].rsplit("/", 1)[-1]).replace("_", " ")
        # plusieurs blasons : on garde le premier en ordre alphabétique, pour que ce soit stable
        if not par_code.get(code) or fichier < par_code[code]["fichier"]:
            par_code[code] = {"fichier": fichier, "nom": l["nom"], "wikidata": l["item"].rsplit("/", 1)[-1]}
    print("   %d codes, %d avec un blason" % (len(ISO), sum(1 for v in par_code.values() if v)))

    print("2/3 Commons : auteurs, licences, vignettes…")
    fichiers = sorted({v["fichier"] for v in par_code.values() if v})
    infos = {}
    for i in range(0, len(fichiers), 40):
        paquet = fichiers[i:i + 40]
        corps = urllib.parse.urlencode({
            "action": "query", "format": "json", "prop": "imageinfo",
            "iiprop": "url|extmetadata", "iiurlwidth": "256",
            "iiextmetadatafilter": "Artist|LicenseShortName|LicenseUrl|AttributionRequired",
            "titles": "|".join("File:" + f for f in paquet)}).encode("utf-8")
        data = http_json(COMMONS, donnees=corps)
        normal = {x["to"]: x["from"] for x in (data.get("query", {}).get("normalized") or [])}
        for page in (data.get("query", {}).get("pages", {}) or {}).values():
            titre = normal.get(page.get("title", ""), page.get("title", ""))[len("File:"):]
            ii = (page.get("imageinfo") or [{}])[0]
            meta = ii.get("extmetadata") or {}
            lire = lambda c: (meta.get(c) or {}).get("value", "") or ""
            infos[titre] = {
                "auteur": re.sub(r"\s+", " ", re.sub(r"<[^>]+>", "", lire("Artist"))).strip(),
                "licence": lire("LicenseShortName"), "licence_url": lire("LicenseUrl"),
                "vignette": ii.get("thumburl", ""), "page": ii.get("descriptionurl", "")}
        time.sleep(0.5)

    print("3/3 Vignettes…")
    resultat, verifier = {}, []
    for code in ISO:
        v = par_code.get(code)
        if not v:
            verifier.append("%-4s %s : pas de blason sur Wikidata" % (code, ISO[code]))
            continue
        inf = infos.get(v["fichier"]) or {}
        if not inf.get("vignette"):
            verifier.append("%-4s %s : fichier introuvable sur Commons (%s)" % (code, ISO[code], v["fichier"]))
            continue
        if not LIBRES.match(inf["licence"] or ""):
            verifier.append("%-4s %s : licence « %s » à regarder (%s)" % (code, ISO[code], inf["licence"] or "?", inf["page"]))
            continue
        chemin = os.path.join(SORTIE, code + ".png")
        if not os.path.exists(chemin):
            telecharger(inf["vignette"], chemin)
            time.sleep(0.3)
        resultat[code] = {"nom": v["nom"], "fichier": v["fichier"], "auteur": inf["auteur"],
                          "licence": inf["licence"], "licence_url": inf["licence_url"], "page": inf["page"],
                          "wikidata": v["wikidata"]}

    json.dump(resultat, open(os.path.join(ICI, "blasons.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    open(os.path.join(ICI, "a-verifier.txt"), "w", encoding="utf-8").write("\n".join(verifier) + "\n")
    lic = {}
    for r in resultat.values():
        lic[r["licence"]] = lic.get(r["licence"], 0) + 1
    print("\nFini : %d blasons téléchargés sur %d, %d à vérifier." % (len(resultat), len(ISO), len(verifier)))
    print("Licences :", ", ".join("%s %d" % kv for kv in sorted(lic.items(), key=lambda kv: -kv[1])))
    print("Détail : _donnees/blasons/a-verifier.txt")


if __name__ == "__main__":
    main()
