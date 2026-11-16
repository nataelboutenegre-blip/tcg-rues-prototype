#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
TerraFront — saison 3 : les photos des communes suisses.

Même chose que _sql/photos-2-import.py pour la France, en plus court :
  1. lit brut/photos-inventaire-suisse.csv (écrit par telecharger-suisse.py :
     une ligne par photo Wikidata, avec auteur et licence Commons) ;
  2. télécharge la vignette (400 px) sur Wikimedia Commons ;
  3. l'envoie dans Supabase Storage (bucket « communes », CHxxxx.jpg,
     cache de 30 jours comme la France) ;
  4. renseigne photo, photo_auteur, photo_licence, photo_source dans la
     RÉSERVE suisse (suisse_communes_attente), pas dans communes.
     Aucun joueur ne voit rien : s3-5 recopie les photos le jour J.

AVANT : lancer _sql/s3-16-photos-suisse-colonnes.sql (Claude s'en charge).

POURQUOI SUR TON MAC
  Le conteneur de Claude n'a pas accès à commons.wikimedia.org. Ton Terminal, si.

CLÉ SUPABASE (tu la poses toi-même, tu ne l'envoies à personne)
    export SUPABASE_URL='https://yzcgroprydxhbwaufkdu.supabase.co'
    export SUPABASE_SERVICE_KEY='ey...'

USAGE (depuis le dossier du jeu)
    python3 _donnees/suisse/photos-suisse.py --essai    # 10 communes, pour voir
    python3 _donnees/suisse/photos-suisse.py            # toutes (~2 000, 15-25 min)

  Reprenable : ce qui est fait est noté dans brut/photos-suisse-faits.txt,
  relancer la même commande repart de là.
"""

import argparse, csv, json, os, sys, time
import urllib.parse, urllib.request, urllib.error

ICI = os.path.dirname(os.path.abspath(__file__))
BRUT = os.path.join(ICI, "brut")
INVENTAIRE = os.path.join(BRUT, "photos-inventaire-suisse.csv")
FAITS = os.path.join(BRUT, "photos-suisse-faits.txt")
RATES = os.path.join(BRUT, "photos-suisse-rates.csv")

UA = "TerraFront/1.0 (https://terrafront.fr) python-urllib"
LARGEUR = 400            # px, comme la France
CACHE = "2592000"        # 30 jours : sans ça, chaque session retélécharge tout


def http(url, donnees=None, entetes=None, methode=None, essais=4, brut=False):
    for n in range(1, essais + 1):
        try:
            req = urllib.request.Request(url, data=donnees, method=methode)
            req.add_header("User-Agent", UA)
            for k, v in (entetes or {}).items():
                req.add_header(k, v)
            with urllib.request.urlopen(req, timeout=120) as r:
                recu = r.read()
                return recu if brut else json.loads(recu.decode("utf-8"))
        except urllib.error.HTTPError as e:
            if e.code in (400, 401, 403, 404) or n == essais:
                raise
            time.sleep(3 * n)
        except Exception:
            if n == essais:
                raise
            time.sleep(3 * n)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--essai", action="store_true", help="10 communes, puis on s'arrête")
    args = ap.parse_args()

    base = (os.environ.get("SUPABASE_URL") or "").rstrip("/")
    cle = os.environ.get("SUPABASE_SERVICE_KEY") or ""
    if not base or not cle:
        sys.exit("Il manque SUPABASE_URL ou SUPABASE_SERVICE_KEY (voir l'en-tête du fichier).")
    if not os.path.exists(INVENTAIRE):
        sys.exit("Introuvable : %s\nLance d'abord : python3 _donnees/suisse/telecharger-suisse.py" % INVENTAIRE)
    auth = {"apikey": cle, "Authorization": "Bearer " + cle}

    # l'inventaire : une photo par commune, la première qui a un auteur
    # (sans auteur, on n'a pas le droit de l'afficher)
    choix = {}
    with open(INVENTAIRE, encoding="utf-8") as fh:
        for r in csv.DictReader(fh):
            if r.get("fichier") and r.get("auteur") and r["code"] not in choix:
                choix[r["code"]] = r
    print("Inventaire : %d communes avec une photo utilisable." % len(choix))

    # la réserve en base
    reserve = []
    try:
        while True:   # par pages de 1 000 (limite de Supabase)
            lot = http("%s/rest/v1/suisse_communes_attente?select=code,nom,photo&order=code&offset=%d&limit=1000"
                       % (base, len(reserve)), entetes=auth)
            reserve += lot
            if len(lot) < 1000:
                break
    except urllib.error.HTTPError as e:
        sys.exit("Lecture de la réserve refusée (%s). s3-16 est-il passé ? Clé service_role ?" % e.code)
    if reserve and "photo" not in reserve[0]:
        sys.exit("La réserve n'a pas de colonne photo : demande à Claude de lancer s3-16.")
    print("Réserve : %d communes, %d déjà avec photo." % (len(reserve), sum(1 for c in reserve if c.get("photo"))))

    faits = set(open(FAITS, encoding="utf-8").read().split()) if os.path.exists(FAITS) else set()
    a_faire = [(c["code"], c["nom"], choix[c["code"]]) for c in reserve
               if c["code"] in choix and c["code"] not in faits and not c.get("photo")]
    sans = len(reserve) - sum(1 for c in reserve if c["code"] in choix)
    print("%d sans photo sur Wikidata (elles resteront sans photo, comme en France)." % sans)
    if args.essai:
        a_faire = a_faire[:10]
    print("\n%d à traiter.\n" % len(a_faire))

    ok = 0
    rates = []
    with open(FAITS, "a", encoding="utf-8") as journal:
        for i, (code, nom, r) in enumerate(a_faire, 1):
            fichier = r["fichier"]
            src = ("https://commons.wikimedia.org/wiki/Special:FilePath/"
                   + urllib.parse.quote(fichier.replace(" ", "_")) + "?width=%d" % LARGEUR)
            try:
                image = http(src, brut=True)
                if len(image) < 800:
                    raise ValueError("vignette vide (%d octets)" % len(image))
                http("%s/storage/v1/object/communes/%s.jpg" % (base, code), donnees=image, methode="POST", brut=True,
                     entetes=dict(auth, **{"Content-Type": "image/jpeg", "x-upsert": "true",
                                           "cache-control": "max-age=" + CACHE}))
                maj = json.dumps({
                    "photo": code + ".jpg",
                    "photo_auteur": r.get("auteur") or None,
                    "photo_licence": r.get("licence") or None,
                    "photo_source": "https://commons.wikimedia.org/wiki/File:" + urllib.parse.quote(fichier.replace(" ", "_")),
                }).encode("utf-8")
                http("%s/rest/v1/suisse_communes_attente?code=eq.%s" % (base, code), donnees=maj, methode="PATCH", brut=True,
                     entetes=dict(auth, **{"Content-Type": "application/json", "Prefer": "return=minimal"}))
                journal.write(code + "\n"); journal.flush()
                ok += 1
                if i % 25 == 0 or args.essai:
                    print("%5d/%d  %-28s %6.1f Ko" % (i, len(a_faire), nom[:28], len(image) / 1024))
            except Exception as e:
                rates.append((code, nom, fichier, str(e)[:200]))
                print("%5d/%d  %-28s ÉCHEC : %s" % (i, len(a_faire), nom[:28], e))
            time.sleep(0.25)   # on reste poli avec Commons

    if rates:
        with open(RATES, "w", newline="", encoding="utf-8") as fh:
            w = csv.writer(fh)
            w.writerow(["code", "nom", "fichier", "erreur"])
            w.writerows(rates)
    print("\nFini : %d posées, %d en échec%s." % (ok, len(rates), " (liste : brut/photos-suisse-rates.csv)" if rates else ""))
    print("Relancer la même commande reprend là où ça s'est arrêté.")


if __name__ == "__main__":
    main()
