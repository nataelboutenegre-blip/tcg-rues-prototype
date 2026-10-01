#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
TerraFront — Trouver comment Supabase accepte vraiment un cache-control.

POURQUOI CE SCRIPT EXISTE
  J'ai envoye les 33 840 images avec un en-tete « cache-control: max-age=... ».
  Il est ignore : le serveur repond toujours « no-cache ». J'avais verifie que
  l'en-tete partait de mon script, pas qu'il arrivait. C'est l'erreur, et ce
  script existe pour ne pas la refaire.

CE QU'IL FAIT
  Il envoie la MEME image sous trois noms jetables, par trois methodes
  differentes, puis il relit chaque adresse publique et affiche ce que le
  serveur repond. Celle qui dit « max-age » est la bonne.

  A — corps binaire + en-tete cache-control        (la methode actuelle)
  B — formulaire multipart + champ cacheControl    (ce que fait la vraie
                                                    bibliotheque Supabase)
  C — les deux a la fois

  Les trois fichiers s'appellent _essai-a/b/c.jpg, ne sont references nulle
  part dans le jeu, et le script les supprime a la fin.

CLE SUPABASE
  Les deux memes variables d'environnement que pour l'import :
      export SUPABASE_URL='https://xxxx.supabase.co'
      export SUPABASE_SERVICE_KEY='ey...'

USAGE
    python3 photos-cache-essai.py
"""

import json, os, sys, time, urllib.request, urllib.error, uuid

CACHE = "2592000"
UA = "TerraFront/1.0 (https://terrafront.fr) python-urllib"


def appel(url, donnees=None, methode=None, entetes=None, lire_entetes=False):
    req = urllib.request.Request(url, data=donnees, method=methode)
    req.add_header("User-Agent", UA)
    for k, v in (entetes or {}).items():
        req.add_header(k, v)
    try:
        with urllib.request.urlopen(req, timeout=60) as r:
            return (dict(r.headers), r.read()) if lire_entetes else (r.status, r.read())
    except urllib.error.HTTPError as e:
        return (e.code, e.read()[:300])


def multipart(champs, fichier, nom_champ=""):
    """Construit un corps multipart/form-data a la main."""
    limite = "----terrafront" + uuid.uuid4().hex
    morceaux = []
    for k, v in champs.items():
        morceaux.append(("--%s\r\nContent-Disposition: form-data; name=\"%s\"\r\n\r\n%s\r\n"
                         % (limite, k, v)).encode("utf-8"))
    morceaux.append(("--%s\r\nContent-Disposition: form-data; name=\"%s\"; filename=\"image.jpg\"\r\n"
                     "Content-Type: image/jpeg\r\n\r\n" % (limite, nom_champ)).encode("utf-8"))
    morceaux.append(fichier)
    morceaux.append(("\r\n--%s--\r\n" % limite).encode("utf-8"))
    return b"".join(morceaux), "multipart/form-data; boundary=" + limite


def main():
    base = (os.environ.get("SUPABASE_URL") or "").rstrip("/")
    cle = os.environ.get("SUPABASE_SERVICE_KEY") or ""
    if not base or not cle:
        sys.exit("Il manque SUPABASE_URL ou SUPABASE_SERVICE_KEY dans l'environnement.")

    auth = {"apikey": cle, "Authorization": "Bearer " + cle}

    print("Recuperation d'une image existante pour servir de cobaye...")
    st, image = appel(base + "/storage/v1/object/public/communes/01053.jpg")
    if not isinstance(image, (bytes, bytearray)) or len(image) < 800:
        sys.exit("Impossible de relire 01053.jpg (%s)" % st)
    print("   %.1f Ko\n" % (len(image) / 1024.0))

    methodes = []

    # A — corps binaire + en-tete (la methode actuelle)
    methodes.append(("A  binaire + en-tete cache-control", "_essai-a.jpg",
                     image, dict(auth, **{"Content-Type": "image/jpeg", "x-upsert": "true",
                                          "cache-control": "max-age=" + CACHE})))

    # B — multipart + champ cacheControl
    corps, ctype = multipart({"cacheControl": CACHE}, image)
    methodes.append(("B  multipart + champ cacheControl", "_essai-b.jpg",
                     corps, dict(auth, **{"Content-Type": ctype, "x-upsert": "true"})))

    # C — les deux
    corps2, ctype2 = multipart({"cacheControl": CACHE}, image)
    methodes.append(("C  multipart + champ + en-tete", "_essai-c.jpg",
                     corps2, dict(auth, **{"Content-Type": ctype2, "x-upsert": "true",
                                           "cache-control": "max-age=" + CACHE})))

    for libelle, nom, corps, entetes in methodes:
        st, rep = appel(base + "/storage/v1/object/communes/" + nom,
                        donnees=corps, methode="POST", entetes=entetes)
        envoi = "envoi %s" % st
        time.sleep(1)
        ent, _ = appel(base + "/storage/v1/object/public/communes/" + nom, lire_entetes=True)
        cc = ent.get("Cache-Control") or ent.get("cache-control") or "(aucun)" \
             if isinstance(ent, dict) else "(lecture impossible)"
        verdict = "  <<< CELLE-CI" if "max-age=" + CACHE in str(cc) else ""
        print("%-38s %-12s -> %s%s" % (libelle, envoi, cc, verdict))

    print("\nMenage...")
    for nom in ("_essai-a.jpg", "_essai-b.jpg", "_essai-c.jpg"):
        appel(base + "/storage/v1/object/communes/" + nom, methode="DELETE", entetes=auth)
    print("Les trois fichiers d'essai sont supprimes.")


if __name__ == "__main__":
    main()
