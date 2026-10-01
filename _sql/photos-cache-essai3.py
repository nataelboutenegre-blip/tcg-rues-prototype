#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
TerraFront — Le meme essai, mais en lisant la SOURCE et pas le cache.

CE QUI CLOCHAIT DANS L'ESSAI 2
  Je relisais toujours la meme adresse. Cloudflare garde une reponse par
  adresse : je lisais peut-etre sa copie au lieu de ce que Supabase stocke.
  L'essai 1 ne pouvait pas avoir ce defaut, ses trois noms etaient neufs — et
  c'est justement lui qui disait que l'en-tete marche.

CE QUI CHANGE ICI
  — chaque lecture ajoute un parametre unique a l'adresse, ce qui oblige a
    aller chercher a la source
  — on affiche cf-cache-status et age, pour voir d'ou vient la reponse
  — on teste aussi une commune REELLE du jeu, en lecture seule, pour savoir
    si son no-cache vient de la source ou du cache

USAGE
    python3 photos-cache-essai3.py
"""

import os, sys, time, uuid, urllib.request, urllib.error

CACHE = "2592000"
UA = "TerraFront/1.0 (https://terrafront.fr) python-urllib"
NOM = "_essai3-" + uuid.uuid4().hex[:8] + ".jpg"


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

    def lire(nom):
        """Adresse unique a chaque fois : Cloudflare ne peut pas repondre de memoire."""
        time.sleep(1)
        url = "%s/storage/v1/object/public/communes/%s?x=%s" % (base, nom, uuid.uuid4().hex[:10])
        ent, _ = appel(url, lire_entetes=True)
        if not isinstance(ent, dict):
            return "(lecture impossible)"
        cc = ent.get("Cache-Control") or ent.get("cache-control") or "(aucun)"
        cf = ent.get("Cf-Cache-Status") or ent.get("cf-cache-status") or "?"
        return "%-26s  [cloudflare : %s]" % (cc, cf)

    def envoyer(nom, avec_entete):
        e = dict(auth, **{"Content-Type": "image/jpeg", "x-upsert": "true"})
        if avec_entete:
            e["cache-control"] = "max-age=" + CACHE
        return appel(base + "/storage/v1/object/communes/" + nom,
                     donnees=image, methode="POST", entetes=e)[0]

    print("Fichier d'essai : %s\n" % NOM)
    print("1. neuf, SANS en-tete       : %s -> %s" % (envoyer(NOM, False), lire(NOM)))
    print("2. REECRITURE avec en-tete  : %s -> %s" % (envoyer(NOM, True), lire(NOM)))
    reecrire = "max-age=" + CACHE in lire(NOM)

    appel(base + "/storage/v1/object/communes/" + NOM, methode="DELETE", entetes=auth)
    print("3. supprime puis renvoye    : %s -> %s" % (envoyer(NOM, True), lire(NOM)))
    supprimer = "max-age=" + CACHE in lire(NOM)

    print("\n4. une commune REELLE du jeu, en lecture seule :")
    print("   01053 (envoyee deux fois) : %s" % lire("01053.jpg"))
    print("   62574 (envoyee une fois)  : %s" % lire("62574.jpg"))

    appel(base + "/storage/v1/object/communes/" + NOM, methode="DELETE", entetes=auth)
    print("\nVERDICT")
    if reecrire:
        print("  Reecrire suffit : relancer l'import avec le bon script regle tout.")
    elif supprimer:
        print("  Reecrire ne suffit pas, mais supprimer puis renvoyer fonctionne.")
    else:
        print("  Ni l'un ni l'autre sur un objet existant. A creuser autrement.")


if __name__ == "__main__":
    main()
