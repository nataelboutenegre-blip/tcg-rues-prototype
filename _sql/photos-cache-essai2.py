#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
TerraFront — Reecrire une image met-il a jour son reglage de cache ?

LA QUESTION
  Les 33 840 images sont en ligne avec « no-cache », parce que le script qui a
  tourne cette nuit etait l'ancien. Les reecrire par-dessus avec le bon en-tete
  suffit-il, ou Supabase garde-t-il le reglage de la premiere fois ?

  Si reecrire suffit : une relance de l'import et c'est fini.
  Sinon : il faut supprimer avant de renvoyer, ce qui est une autre operation.

CE QU'IL FAIT
  1. envoie une image SANS en-tete  -> elle doit arriver en no-cache
  2. la reecrit AVEC l'en-tete      -> on regarde si ca a change
  3. la supprime, la renvoie avec   -> verification que la suppression marche
  4. menage

  Un seul fichier jetable, _essai-maj.jpg, reference nulle part.

USAGE
    python3 photos-cache-essai2.py
"""

import os, sys, time, urllib.request, urllib.error

CACHE = "2592000"
UA = "TerraFront/1.0 (https://terrafront.fr) python-urllib"
NOM = "_essai-maj.jpg"


def appel(url, donnees=None, methode=None, entetes=None, lire_entetes=False):
    req = urllib.request.Request(url, data=donnees, method=methode)
    req.add_header("User-Agent", UA)
    for k, v in (entetes or {}).items():
        req.add_header(k, v)
    try:
        with urllib.request.urlopen(req, timeout=60) as r:
            return (dict(r.headers), r.read()) if lire_entetes else (r.status, r.read())
    except urllib.error.HTTPError as e:
        return (e.code, e.read()[:200])


def main():
    base = (os.environ.get("SUPABASE_URL") or "").rstrip("/")
    cle = os.environ.get("SUPABASE_SERVICE_KEY") or ""
    if not base or not cle:
        sys.exit("Il manque SUPABASE_URL ou SUPABASE_SERVICE_KEY dans l'environnement.")
    auth = {"apikey": cle, "Authorization": "Bearer " + cle}

    st, image = appel(base + "/storage/v1/object/public/communes/01053.jpg")
    if not isinstance(image, (bytes, bytearray)) or len(image) < 800:
        sys.exit("Impossible de relire 01053.jpg (%s)" % st)

    def envoyer(avec_entete):
        e = dict(auth, **{"Content-Type": "image/jpeg", "x-upsert": "true"})
        if avec_entete:
            e["cache-control"] = "max-age=" + CACHE
        return appel(base + "/storage/v1/object/communes/" + NOM,
                     donnees=image, methode="POST", entetes=e)[0]

    def relire():
        time.sleep(1)
        ent, _ = appel(base + "/storage/v1/object/public/communes/" + NOM, lire_entetes=True)
        if not isinstance(ent, dict):
            return "(lecture impossible)"
        return ent.get("Cache-Control") or ent.get("cache-control") or "(aucun)"

    appel(base + "/storage/v1/object/communes/" + NOM, methode="DELETE", entetes=auth)

    print("1. envoi SANS en-tete      : %s -> %s" % (envoyer(False), relire()))
    print("2. REECRITURE avec en-tete : %s -> %s" % (envoyer(True), relire()))
    reecrire_suffit = "max-age=" + CACHE in relire()

    appel(base + "/storage/v1/object/communes/" + NOM, methode="DELETE", entetes=auth)
    print("3. suppression puis renvoi : %s -> %s" % (envoyer(True), relire()))

    appel(base + "/storage/v1/object/communes/" + NOM, methode="DELETE", entetes=auth)
    print("\nVERDICT : %s" % ("reecrire suffit, une relance de l'import regle tout."
                              if reecrire_suffit else
                              "reecrire NE SUFFIT PAS, il faudra supprimer avant de renvoyer."))


if __name__ == "__main__":
    main()
