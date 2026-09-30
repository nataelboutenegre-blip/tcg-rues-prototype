#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
TerraFront — photos des communes, etape 2 sur 3 : l'import.

Telecharge les vignettes depuis Wikimedia Commons, les envoie dans
Supabase Storage, et renseigne les colonnes photo* de la table communes.

A LANCER APRES _sql/photos-colonnes.sql, qui cree les colonnes et le bucket.

LE PROBLEME QUE CE SCRIPT RESOUT AVANT TOUT
  Wikidata garde la fiche des anciennes communes ET celle des communes
  fusionnees, avec le MEME code INSEE et des photos differentes :

      16046  Blanzac               Blanzac 16 Entree village.jpg
      16046  Blanzac-Porcheresse   Blanzac4.JPG

  Environ 7 % des codes sont dans ce cas, soit pres de 2 400 cartes qui
  recevraient sinon la photo d'un autre lieu. La table communes fait
  autorite : on garde la candidate dont le nom correspond au tien. Celles
  qu'on ne sait pas trancher sont ECARTEES et listees, jamais devinees.

CLE SUPABASE
  Le script lit deux variables d'environnement. Tu les poses toi-meme,
  dans ton Terminal, et tu ne les envoies a personne :

      export SUPABASE_URL='https://xxxx.supabase.co'
      export SUPABASE_SERVICE_KEY='ey...'

LE CACHE N'EST PAS UN DETAIL
  Les images partent avec un cache-control de 30 jours. Sans lui, Supabase
  sert son defaut d'une heure et chaque session de jeu retelecharge toute
  la collection : 120 Go de trafic par mois pour 23 joueurs, contre 1,3 Go
  une seule fois. C'est le rapport entre viable et pas viable.

USAGE
    python3 photos-2-import.py --essai              # 20 communes, pour voir
    python3 photos-2-import.py --palier rare,legendaire
    python3 photos-2-import.py --palier tous        # les 34 739, compte des heures

  Reprenable : le script note ce qu'il a fait dans photos-faits.txt et
  repart de la si on le relance.
"""

import argparse, csv, json, os, re, sys, time, unicodedata
import urllib.parse, urllib.request, urllib.error

UA = "TerraFront/1.0 (https://terrafront.fr) python-urllib"
LARGEUR = 400                      # px : la vignette telle qu'elle sera servie

# COMBIEN DE TEMPS LE NAVIGATEUR GARDE UNE IMAGE.
#
#   C'est le poste de cout numero un, et il ne se rattrape pas apres coup :
#   sans cet en-tete, Supabase applique son defaut (une heure), et chaque
#   session de jeu retelecharge toute la collection. A 23 joueurs cela fait
#   120 Go de trafic par mois ; a un mois de cache, 1,3 Go une seule fois.
#
#   30 jours et pas un an : si une photo se revele fausse ou mal cadree, la
#   correction arrive chez les joueurs en un mois au pire. Et si tu veux
#   qu'elle arrive tout de suite, renomme le fichier (01053-2.jpg) et mets
#   a jour communes.photo : une adresse neuve n'est jamais en cache.
CACHE = "2592000"                  # 30 jours, en secondes
FAITS = "photos-faits.txt"
ECARTEES = "photos-ecartees.csv"


def cle_nom(s):
    """« Barbezieux-Saint-Hilaire » et « Barbezieux Saint Hilaire » pareil."""
    s = unicodedata.normalize("NFD", (s or "").lower())
    s = "".join(c for c in s if unicodedata.category(c) != "Mn")
    return re.sub(r"[^a-z0-9]", "", s)


def http(url, donnees=None, entetes=None, methode=None, essais=4, brut=False):
    for n in range(1, essais + 1):
        try:
            req = urllib.request.Request(url, data=donnees, method=methode)
            req.add_header("User-Agent", UA)
            for k, v in (entetes or {}).items():
                req.add_header(k, v)
            with urllib.request.urlopen(req, timeout=120) as r:
                donnees_recues = r.read()
                return donnees_recues if brut else json.loads(donnees_recues.decode("utf-8"))
        except urllib.error.HTTPError as e:
            if e.code in (404, 403) or n == essais:
                raise
            time.sleep(3 * n)
        except Exception:
            if n == essais:
                raise
            time.sleep(3 * n)


def communes_de_la_base(base, cle):
    """Toutes tes communes : code, nom, tier. Par pages de 1000."""
    tout, debut = {}, 0
    while True:
        url = ("%s/rest/v1/communes?select=code,nom,tier&order=code"
               "&offset=%d&limit=1000" % (base, debut))
        lot = http(url, entetes={"apikey": cle, "Authorization": "Bearer " + cle})
        for c in lot:
            tout[c["code"]] = (c.get("nom") or "", c.get("tier") or "")
        if len(lot) < 1000:
            return tout
        debut += 1000
        print("   %d communes lues..." % len(tout))


def choisir(candidates, nom_en_base):
    """Parmi plusieurs lignes d'inventaire pour un meme code, laquelle ?"""
    if len(candidates) == 1:
        return candidates[0], None
    cible = cle_nom(nom_en_base)
    exactes = [c for c in candidates if cle_nom(c["nom"]) == cible]
    if len(exactes) == 1:
        return exactes[0], None
    # pas de correspondance nette : on n'invente pas
    return None, "%d candidates, aucune ne correspond a « %s »" % (len(candidates), nom_en_base)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--essai", action="store_true", help="20 communes, puis on s'arrete")
    ap.add_argument("--palier", default="rare,legendaire",
                    help="rare,legendaire | peucommun | tous")
    ap.add_argument("--inventaire", default="photos-inventaire.csv")
    args = ap.parse_args()

    base = (os.environ.get("SUPABASE_URL") or "").rstrip("/")
    cle = os.environ.get("SUPABASE_SERVICE_KEY") or ""
    if not base or not cle:
        sys.exit("Il manque SUPABASE_URL ou SUPABASE_SERVICE_KEY dans l'environnement.\n"
                 "Voir l'en-tete de ce fichier.")

    print("Lecture de %s..." % args.inventaire)
    par_code = {}
    with open(args.inventaire, encoding="utf-8") as fh:
        for r in csv.DictReader(fh):
            if r.get("fichier") and r.get("auteur"):      # sans auteur, on n'a pas le droit
                par_code.setdefault(r["code_insee"], []).append(r)
    print("   %d codes INSEE, %d lignes."
          % (len(par_code), sum(len(v) for v in par_code.values())))

    print("Lecture de ta table communes...")
    communes = communes_de_la_base(base, cle)
    print("   %d communes en base." % len(communes))

    paliers = None if args.palier == "tous" else set(args.palier.split(","))
    faits = set()
    if os.path.exists(FAITS):
        faits = set(open(FAITS, encoding="utf-8").read().split())
        print("   %d deja faites, on les saute." % len(faits))

    a_faire, ecartees = [], []
    for code, (nom, tier) in sorted(communes.items()):
        if code in faits or (paliers and tier not in paliers):
            continue
        cands = par_code.get(code)
        if not cands:
            continue
        choisie, souci = choisir(cands, nom)
        if choisie:
            a_faire.append((code, nom, choisie))
        else:
            ecartees.append((code, nom, souci, " | ".join(c["fichier"] for c in cands)))

    if ecartees:
        with open(ECARTEES, "w", newline="", encoding="utf-8") as fh:
            w = csv.writer(fh)
            w.writerow(["code_insee", "nom_en_base", "raison", "candidates"])
            w.writerows(ecartees)
        print("   %d ecartees (ambigues) -> %s" % (len(ecartees), ECARTEES))

    if args.essai:
        a_faire = a_faire[:20]
    print("\n%d commune(s) a traiter.\n" % len(a_faire))
    if not a_faire:
        return

    ok = rates = 0
    with open(FAITS, "a", encoding="utf-8") as journal:
        for i, (code, nom, r) in enumerate(a_faire, 1):
            fichier = r["fichier"]
            src = ("https://commons.wikimedia.org/wiki/Special:FilePath/"
                   + urllib.parse.quote(fichier.replace(" ", "_"))
                   + "?width=%d" % LARGEUR)
            try:
                image = http(src, brut=True)
                if len(image) < 800:
                    raise ValueError("vignette vide (%d octets)" % len(image))

                dest = "%s/storage/v1/object/communes/%s.jpg" % (base, code)
                http(dest, donnees=image, methode="POST", brut=True, entetes={
                    "apikey": cle, "Authorization": "Bearer " + cle,
                    "Content-Type": "image/jpeg", "x-upsert": "true",
                    "cache-control": "max-age=" + CACHE})

                page = ("https://commons.wikimedia.org/wiki/File:"
                        + urllib.parse.quote(fichier.replace(" ", "_")))
                maj = json.dumps({
                    "photo": code + ".jpg",
                    "photo_auteur": r.get("auteur") or None,
                    "photo_licence": r.get("licence") or None,
                    "photo_source": page,
                }).encode("utf-8")
                http("%s/rest/v1/communes?code=eq.%s" % (base, code),
                     donnees=maj, methode="PATCH", brut=True, entetes={
                         "apikey": cle, "Authorization": "Bearer " + cle,
                         "Content-Type": "application/json", "Prefer": "return=minimal"})

                journal.write(code + "\n"); journal.flush()
                ok += 1
                if i % 25 == 0 or args.essai:
                    print("%5d/%d  %-28s %6.1f Ko" % (i, len(a_faire), nom[:28], len(image) / 1024))
            except Exception as e:
                rates += 1
                print("%5d/%d  %-28s ECHEC : %s" % (i, len(a_faire), nom[:28], e))
            time.sleep(0.25)          # on reste poli avec Commons

    print("\n%d posees, %d en echec." % (ok, rates))
    print("Relancer la meme commande reprend ou ca s'est arrete.")


if __name__ == "__main__":
    main()
