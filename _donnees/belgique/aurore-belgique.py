#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
TerraFront — saison 3 : les candidates Aurore belges (décision de Nataël, 18/11 : « oui »).

Une Aurore est une photo pleine carte, donc EN HAUTEUR. Les photos Wikidata
sont presque toutes en largeur : ce script cherche sur Wikimedia Commons des
photos EN HAUTEUR de chaque ville, sous son nom officiel ET son nom français
(Gent / Gand, Brugge / Bruges…) :
  1. les photos marquées « représente <la ville> » (données structurées) ;
  2. les « Quality images » dont le titre contient le nom de la ville ;
  3. les grandes photos dont le titre contient le nom de la ville.
Il garde au plus 4 photos par ville (les meilleures d'abord), avec un auteur
et une licence, et télécharge une version de 600 px de large.

Villes cherchées : les 5 légendaires, les 16 épiques, les 56 rares et quelques
lieux connus s'ils sont rares ou plus (Dinant, Ypres, Ostende, Tournai…).

Il n'écrit rien en base et ne touche pas au jeu. Il dépose les images dans
_prochain-patch/aurore-belgique/ avec candidats.csv. Claude en fait une
page de tri.

USAGE (depuis le dossier du jeu, aucune clé nécessaire)
    python3 _donnees/belgique/aurore-belgique.py
  Environ 15 minutes. Rejouable : une image déjà là n'est pas retéléchargée.
"""

import csv, json, os, re, sys, time
import urllib.parse, urllib.request, urllib.error

ICI = os.path.dirname(os.path.abspath(__file__))
RACINE = os.path.dirname(os.path.dirname(ICI))
COMMUNES = os.path.join(ICI, "jeu", "communes-belgique.csv")
SORTIE = os.path.join(RACINE, "_prochain-patch", "aurore-belgique")
COMMONS = "https://commons.wikimedia.org/w/api.php"
UA = "TerraFront/1.0 (https://terrafront.fr) python-urllib"
LARGEUR = 600
PAR_VILLE = 4
PAR_RARE = 2
RAPPORT_MIN = 1.15        # hauteur / largeur
LARGEUR_MIN = 1000        # px de l'original
EPIQUES = 16
CONNUES = ["Dinant", "Durbuy", "Spa", "Bouillon", "Waterloo", "Malmedy", "Knokke-Heist", "Ieper", "Ottignies-Louvain-la-Neuve",
           "Huy", "Arlon", "Tournai", "Oostende", "Lier", "Diest", "Bastogne", "La Roche-en-Ardenne", "Han-sur-Lesse", "Rochefort", "Thuin"]


def http(url, donnees=None, brut=False, essais=4):
    for n in range(1, essais + 1):
        try:
            req = urllib.request.Request(url, data=donnees)
            req.add_header("User-Agent", UA)
            with urllib.request.urlopen(req, timeout=120) as r:
                recu = r.read()
                return recu if brut else json.loads(recu.decode("utf-8"))
        except urllib.error.HTTPError as e:
            if e.code in (400, 403, 404) or n == essais:
                raise
            time.sleep(3 * n)
        except Exception:
            if n == essais:
                raise
            time.sleep(3 * n)


def chercher(requete):
    """Fichiers trouvés par la recherche Commons, avec taille, vignette, auteur, licence."""
    corps = urllib.parse.urlencode({
        "action": "query", "format": "json", "generator": "search", "gsrnamespace": 6,
        "gsrsearch": requete, "gsrlimit": 50, "prop": "imageinfo",
        "iiprop": "size|url|extmetadata", "iiurlwidth": LARGEUR,
        "iiextmetadatafilter": "Artist|LicenseShortName|LicenseUrl",
    }).encode("utf-8")
    try:
        data = http(COMMONS, donnees=corps)
    except Exception as e:
        print("      recherche refusée (%s) : %s" % (e, requete))
        return []
    out = []
    for page in (data.get("query", {}).get("pages", {}) or {}).values():
        ii = (page.get("imageinfo") or [{}])[0]
        meta = ii.get("extmetadata") or {}
        lire = lambda k: (meta.get(k) or {}).get("value", "") or ""
        out.append({
            "fichier": page.get("title", "")[len("File:"):],
            "l": ii.get("width") or 0, "h": ii.get("height") or 0,
            "vignette": ii.get("thumburl") or "", "page": ii.get("descriptionurl") or "",
            "auteur": re.sub(r"\s+", " ", re.sub(r"<[^>]+>", "", lire("Artist"))).strip(),
            "licence": lire("LicenseShortName"), "licence_url": lire("LicenseUrl"),
        })
    return out


def bonne(x):
    lic = x["licence"].lower()
    return (x["l"] >= LARGEUR_MIN and x["h"] / max(x["l"], 1) >= RAPPORT_MIN and x["vignette"]
            and x["auteur"] and lic and "fair use" not in lic and "non-free" not in lic
            and re.search(r"\.(jpe?g|png|tiff?)$", x["fichier"], re.I))


def main():
    os.makedirs(SORTIE, exist_ok=True)
    toutes = list(csv.DictReader(open(COMMUNES, encoding="utf-8")))
    leg = [c for c in toutes if c["tier"] == "legendaire"]
    epi = sorted([c for c in toutes if c["tier"] == "epique"], key=lambda c: -int(c["population"] or 0))[:EPIQUES]
    connues = [c for c in toutes if c["nom_officiel"] in CONNUES or c["nom"] in CONNUES]
    villes, vues = [], set()
    rares = sorted([c for c in toutes if c["tier"] == "rare"], key=lambda c: -int(c["population"] or 0))
    for c in leg + epi + connues + rares:
        if c["code"] not in vues and c["tier"] in ("legendaire", "epique", "rare"):   # comme la Suisse : rares et au-dessus
            vues.add(c["code"]); villes.append(c)
    print("%d villes à chercher." % len(villes))

    lignes, deja, rates = [], set(), 0
    for n, c in enumerate(villes, 1):
        noms = [n for n in dict.fromkeys([c["nom_officiel"], c["nom_fr"], c["nom"]]) if n]
        sources = [("représente", "haswbstatement:P180=%s filetype:bitmap" % c["wikidata"]) if c.get("wikidata") else None]
        for nom_court in noms:
            sources += [("quality", 'intitle:"%s" incategory:Quality_images filetype:bitmap' % nom_court),
                        ("titre", 'intitle:"%s" filetype:bitmap fileh:>2000' % nom_court)]
        trouves = {}
        for rang, s in enumerate(x for x in sources if x):
            for x in chercher(s[1]):
                if bonne(x) and x["fichier"] not in deja and x["fichier"] not in trouves:
                    x["source"], x["rang"] = s[0], rang
                    trouves[x["fichier"]] = x
            time.sleep(0.4)
        choix = sorted(trouves.values(), key=lambda x: (x["rang"], -x["l"] * x["h"]))[:(PAR_RARE if c["tier"] not in ("legendaire", "epique") else PAR_VILLE)]
        print("%3d/%d  %-24s %d en hauteur, %d gardées" % (n, len(villes), c["nom"][:24], len(trouves), len(choix)))
        for k, x in enumerate(choix, 1):
            dest = os.path.join(SORTIE, "%s-%d.jpg" % (c["code"], k))
            try:
                if not (os.path.exists(dest) and os.path.getsize(dest) > 15000):
                    image = http(x["vignette"], brut=True)
                    if len(image) < 15000:
                        raise ValueError("image trop petite (%d octets)" % len(image))
                    open(dest, "wb").write(image)
                    time.sleep(0.25)
                deja.add(x["fichier"])
                lignes.append([c["code"], c["nom"], c["departement"], c["tier"], c["population"], k, x["source"],
                               x["fichier"], x["l"], x["h"], x["auteur"], x["licence"], x["licence_url"], x["page"]])
            except Exception as e:
                rates += 1
                print("      %s : ÉCHEC %s" % (x["fichier"][:50], e))

    with open(os.path.join(SORTIE, "candidats.csv"), "w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh)
        w.writerow(["code", "nom", "province", "tier", "population", "n", "source", "fichier", "largeur", "hauteur",
                    "auteur", "licence", "licence_url", "page"])
        w.writerows(lignes)
    print("\nFini : %d photos dans _prochain-patch/aurore-belgique/ (%d échecs)." % (len(lignes), rates))
    print("Dis à Claude que c'est prêt.")


if __name__ == "__main__":
    main()
