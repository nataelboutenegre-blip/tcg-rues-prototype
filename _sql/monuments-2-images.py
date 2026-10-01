#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
TerraFront — Les emblemes, etape 2 : leurs images.

CE QUE FAIT CE SCRIPT
  Il telecharge l'image de chaque embleme depuis Wikimedia Commons, l'envoie
  dans Supabase Storage et renseigne monuments.photo.

  A LANCER APRES monuments.sql, qui cree la table.

CE QU'IL CHANGE PAR RAPPORT A L'IMPORT DES COMMUNES
  — 238 images au lieu de 33 840 : trois minutes, pas trois heures
  — l'en-tete de cache est pose des le depart, cette fois
  — largeur 600 px et non 400 : un embleme se regarde, une vignette de
    commune se survole
  — les fichiers s'appellent m-<code>.jpg pour ne pas ecraser la photo de
    la commune, qui vit dans le meme bucket

L'ATTRIBUTION
  Comme pour les communes, l'auteur et la licence sont recuperes en meme
  temps et stockes. Une image sans auteur lisible est ecartee : citer la
  source est une obligation, pas une politesse.

CLE SUPABASE
  Les deux memes variables d'environnement que pour les photos :
      export SUPABASE_URL='https://xxxx.supabase.co'
      export SUPABASE_SERVICE_KEY='ey...'

USAGE
    python3 monuments-2-images.py --essai     # 10 emblemes
    python3 monuments-2-images.py             # tous

  Reprenable : ce qui est fait est note dans monuments-faits.txt.
"""

import argparse, json, os, re, sys, time
import urllib.parse, urllib.request, urllib.error

UA = "TerraFront/1.0 (https://terrafront.fr) python-urllib"
LARGEUR = 600
CACHE = "2592000"          # 30 jours, pose des l'envoi — la lecon des communes
FAITS = "monuments-faits.txt"


def http(url, donnees=None, entetes=None, methode=None, essais=4, brut=False):
    for n in range(1, essais + 1):
        try:
            req = urllib.request.Request(url, data=donnees, method=methode)
            req.add_header("User-Agent", UA)
            for k, v in (entetes or {}).items():
                req.add_header(k, v)
            with urllib.request.urlopen(req, timeout=120) as r:
                d = r.read()
                return d if brut else json.loads(d.decode("utf-8"))
        except urllib.error.HTTPError as e:
            if e.code in (404, 403) or n == essais:
                raise
            time.sleep(3 * n)
        except Exception:
            if n == essais:
                raise
            time.sleep(3 * n)


def metadonnees(fichiers):
    """{nom: (auteur, licence)} — par paquets de 50."""
    infos = {}
    for i in range(0, len(fichiers), 50):
        paquet = fichiers[i:i + 50]
        corps = urllib.parse.urlencode({
            "action": "query", "format": "json", "prop": "imageinfo",
            "iiprop": "extmetadata",
            "iiextmetadatafilter": "Artist|LicenseShortName",
            "titles": "|".join("File:" + f for f in paquet)}).encode("utf-8")
        data = http("https://commons.wikimedia.org/w/api.php", donnees=corps)
        for page in (data.get("query", {}).get("pages", {}) or {}).values():
            titre = page.get("title", "")[len("File:"):]
            meta = ((page.get("imageinfo") or [{}])[0].get("extmetadata") or {})
            lire = lambda c: (meta.get(c, {}) or {}).get("value", "") or ""
            auteur = re.sub(r"<[^>]+>", "", lire("Artist"))
            infos[titre] = (re.sub(r"\s+", " ", auteur).strip(), lire("LicenseShortName"))
        print("   metadonnees %d/%d" % (min(i + 50, len(fichiers)), len(fichiers)))
        time.sleep(0.4)
    return infos


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--essai", action="store_true", help="10 emblemes puis on s'arrete")
    args = ap.parse_args()

    base = (os.environ.get("SUPABASE_URL") or "").rstrip("/")
    cle = os.environ.get("SUPABASE_SERVICE_KEY") or ""
    if not base or not cle:
        sys.exit("Il manque SUPABASE_URL ou SUPABASE_SERVICE_KEY dans l'environnement.")
    auth = {"apikey": cle, "Authorization": "Bearer " + cle}

    print("Lecture de la table monuments...")
    lignes = http("%s/rest/v1/monuments?select=commune_code,nom,image&order=langues.desc"
                  % base, entetes=auth)
    lignes = [l for l in lignes if l.get("image")]
    print("   %d emblemes avec une image." % len(lignes))

    faits = set()
    if os.path.exists(FAITS):
        faits = set(open(FAITS, encoding="utf-8").read().split())
        print("   %d deja faits, on les saute." % len(faits))
    lignes = [l for l in lignes if l["commune_code"] not in faits]
    if args.essai:
        lignes = lignes[:10]
    if not lignes:
        print("Rien a faire.")
        return

    print("\nAuteurs et licences...")
    infos = metadonnees(sorted({l["image"] for l in lignes}))
    sans_auteur = [l for l in lignes if not infos.get(l["image"], ("",))[0]]
    if sans_auteur:
        print("   %d sans auteur lisible, ecartes (l'attribution est obligatoire) :"
              % len(sans_auteur))
        for l in sans_auteur[:8]:
            print("      %s" % l["nom"])
        lignes = [l for l in lignes if infos.get(l["image"], ("",))[0]]

    print("\n%d a traiter.\n" % len(lignes))
    ok = rates = 0
    with open(FAITS, "a", encoding="utf-8") as journal:
        for i, l in enumerate(lignes, 1):
            code, fichier = l["commune_code"], l["image"]
            src = ("https://commons.wikimedia.org/wiki/Special:FilePath/"
                   + urllib.parse.quote(fichier.replace(" ", "_"))
                   + "?width=%d" % LARGEUR)
            try:
                image = http(src, brut=True)
                if len(image) < 800:
                    raise ValueError("vignette vide (%d octets)" % len(image))
                http("%s/storage/v1/object/communes/m-%s.jpg" % (base, code),
                     donnees=image, methode="POST", brut=True,
                     entetes=dict(auth, **{"Content-Type": "image/jpeg",
                                           "x-upsert": "true",
                                           "cache-control": "max-age=" + CACHE}))
                auteur, licence = infos.get(fichier, ("", ""))
                page = ("https://commons.wikimedia.org/wiki/File:"
                        + urllib.parse.quote(fichier.replace(" ", "_")))
                http("%s/rest/v1/monuments?commune_code=eq.%s" % (base, code),
                     donnees=json.dumps({"photo": "m-%s.jpg" % code,
                                         "photo_auteur": auteur or None,
                                         "photo_licence": licence or None,
                                         "photo_source": page}).encode("utf-8"),
                     methode="PATCH", brut=True,
                     entetes=dict(auth, **{"Content-Type": "application/json",
                                           "Prefer": "return=minimal"}))
                journal.write(code + "\n"); journal.flush()
                ok += 1
                print("%4d/%d  %-44s %6.1f Ko" % (i, len(lignes), l["nom"][:44], len(image)/1024))
            except Exception as e:
                rates += 1
                print("%4d/%d  %-44s ECHEC : %s" % (i, len(lignes), l["nom"][:44], e))
            time.sleep(0.25)

    print("\n%d posees, %d en echec." % (ok, rates))
    print("Verifie une adresse au hasard :")
    print("  curl -sI \"%s/storage/v1/object/public/communes/m-75107.jpg\" | grep -i cache"
          % base)


if __name__ == "__main__":
    main()
