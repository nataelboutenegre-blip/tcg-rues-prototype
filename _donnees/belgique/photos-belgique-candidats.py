#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
TerraFront — Belgique : des photos candidates pour les communes qui n'en ont pas (Gand, communes fusionnées en 2025…).

CE QUE FAIT CE SCRIPT (aucune clé, rien n'est écrit en base)
  Pour chaque commune sans photo de jeu/communes-belgique.csv :
  1. Wikidata : sa catégorie Commons (P373) et les anciennes communes qu'elle remplace (P1365),
     avec leur photo (P18) et leur catégorie ;
  2. Commons : les fichiers de ces catégories, avec auteur, licence et taille ;
  3. écrit brut/photos-candidates-belgique.csv (jusqu'à 8 candidates par commune, les plus sûres d'abord).
  Claude lit ce fichier et choisit ; le choix part dans prep/photos-choisies-belgique.csv, que
  photos-belgique.py pose ensuite comme les autres.

USAGE (depuis le dossier du jeu, sur ton Mac)
    git pull && python3 _donnees/belgique/photos-belgique-candidats.py
"""
import csv, json, os, re, sys, time, urllib.parse, urllib.request

UA = "TerraFront/1.0 (https://terrafront.fr; contact via Discord) python-urllib"
WD = "https://www.wikidata.org/w/api.php"
COMMONS = "https://commons.wikimedia.org/w/api.php"
ICI = os.path.dirname(os.path.abspath(__file__))
BRUT = os.path.join(ICI, "brut")
TABLE = os.path.join(ICI, "jeu", "communes-belgique.csv")
SORTIE = os.path.join(BRUT, "photos-candidates-belgique.csv")
LICENCES_OK = re.compile(r"^(CC BY|CC0|Public domain|PD)", re.I)


def get(url, params):
    q = url + "?" + urllib.parse.urlencode(dict(params, format="json"))
    for n in range(1, 5):
        try:
            req = urllib.request.Request(q, headers={"User-Agent": UA})
            with urllib.request.urlopen(req, timeout=120) as r:
                return json.loads(r.read().decode("utf-8"))
        except Exception as e:
            if n == 4:
                raise
            time.sleep(3 * n)


def entites(ids):
    out = {}
    for i in range(0, len(ids), 40):
        d = get(WD, {"action": "wbgetentities", "ids": "|".join(ids[i:i + 40]), "props": "claims|labels", "languages": "fr|nl"})
        out.update(d.get("entities", {}))
        time.sleep(0.3)
    return out


def valeurs(ent, prop):
    r = []
    for c in (ent.get("claims", {}).get(prop) or []):
        v = ((c.get("mainsnak") or {}).get("datavalue") or {}).get("value")
        if isinstance(v, dict) and "id" in v: r.append(v["id"])
        elif isinstance(v, str): r.append(v)
    return r


def infos_fichiers(titres):
    """{fichier: (auteur, licence, largeur, hauteur)}"""
    out = {}
    for i in range(0, len(titres), 40):
        d = get(COMMONS, {"action": "query", "prop": "imageinfo", "iiprop": "extmetadata|size",
                          "iiextmetadatafilter": "Artist|LicenseShortName", "titles": "|".join("File:" + t for t in titres[i:i + 40])})
        for p in (d.get("query", {}).get("pages", {}) or {}).values():
            ii = (p.get("imageinfo") or [{}])[0]
            m = ii.get("extmetadata") or {}
            lire = lambda k: re.sub(r"\s+", " ", re.sub(r"<[^>]+>", "", (m.get(k) or {}).get("value", "") or "")).strip()
            out[p.get("title", "")[5:]] = (lire("Artist"), lire("LicenseShortName"), ii.get("width", 0), ii.get("height", 0))
        time.sleep(0.3)
    return out


def fichiers_categorie(cat, n=40):
    d = get(COMMONS, {"action": "query", "list": "categorymembers", "cmtitle": "Category:" + cat, "cmtype": "file", "cmlimit": n})
    return [m["title"][5:] for m in d.get("query", {}).get("categorymembers", []) if re.search(r"\.(jpe?g|png)$", m["title"], re.I)]


def main():
    os.makedirs(BRUT, exist_ok=True)
    sans = [r for r in csv.DictReader(open(TABLE, encoding="utf-8")) if not r["photo"]]
    print("%d communes sans photo." % len(sans))
    ents = entites([r["wikidata"] for r in sans if r["wikidata"]])
    lignes = []
    for r in sorted(sans, key=lambda r: int(r["rang"])):
        e = ents.get(r["wikidata"], {})
        cands = []   # (fichier, origine)
        anciens = valeurs(e, "P1365")
        ea = entites(anciens) if anciens else {}
        for a in anciens:
            for f in valeurs(ea.get(a, {}), "P18"): cands.append((f, "photo de l'ancienne commune " + ((ea[a].get("labels", {}).get("fr") or ea[a].get("labels", {}).get("nl") or {}).get("value", a))))
        cats = valeurs(e, "P373") + [c for a in anciens for c in valeurs(ea.get(a, {}), "P373")]
        for c in cats[:4]:
            try:
                for f in fichiers_categorie(c): cands.append((f, "catégorie " + c))
            except Exception as ex:
                print("   ! %s : %s" % (c, ex))
        vus, uniques = set(), []
        for f, o in cands:
            if f not in vus: vus.add(f); uniques.append((f, o))
        info = infos_fichiers([f for f, _ in uniques]) if uniques else {}
        bons = []
        for f, o in uniques:
            aut, lic, w, h = info.get(f, ("", "", 0, 0))
            if not aut or not LICENCES_OK.search(lic or "") or w < 800 or h > w * 1.1: continue   # auteur, licence libre, assez grande, plutôt en largeur
            bons.append((0 if o.startswith("photo") else 1, -w, f, aut, lic, w, h, o))
        bons.sort()
        for b in bons[:8]:
            lignes.append([r["code"], r["nom"], r["tier"], b[2], b[3], b[4], b[5], b[6], b[7]])
        print("   %-30s %-10s %d candidate(s)" % (r["nom"][:30], r["tier"], min(8, len(bons))))
        time.sleep(0.5)
    with open(SORTIE, "w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh)
        w.writerow(["code", "nom", "tier", "fichier", "auteur", "licence", "largeur", "hauteur", "origine"])
        w.writerows(lignes)
    print("\nFini : %s (%d lignes). Rien n'a été écrit en base." % (SORTIE, len(lignes)))


if __name__ == "__main__":
    main()
