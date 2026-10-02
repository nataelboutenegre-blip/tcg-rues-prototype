#!/usr/bin/env python3
# -*- coding: utf-8 -*-
u"""
TerraFront — Sonde : ce que Commons repond vraiment pour les images restantes.

POURQUOI CE SCRIPT EXISTE
  J'ai donne deux explications a ces images manquantes, et les deux etaient
  fausses. D'abord « Wikimedia ne donne pas d'auteur », ensuite « c'est mon
  script qui le jette ». La correction n'a rien change : les sept sont
  toujours ecartees.

  Je ne vais pas en inventer une troisieme. Ce script ne corrige rien : il
  affiche, mot pour mot, ce que Commons renvoie pour ces fichiers. On
  regardera, et ensuite seulement on saura quoi faire.

CE QU'IL FAIT
  Il lit dans ta base les monuments qui ont un nom de fichier mais pas de
  photo, demande a Commons TOUTES les metadonnees de ces fichiers — sans
  filtre, contrairement au script d'import — et imprime les champs qui
  parlent d'auteur, tels quels.

  Il n'ecrit nulle part : ni en base, ni dans le stockage, ni sur le disque.

CLE SUPABASE
  Les deux memes variables d'environnement que pour l'import :
      export SUPABASE_URL='https://xxxx.supabase.co'
      export SUPABASE_SERVICE_KEY='ey...'

USAGE
    cd _sql
    python3 monuments-auteurs-sonde.py
"""

import json, os, sys, time
import urllib.parse, urllib.request, urllib.error

UA = "TerraFront/1.0 (https://terrafront.fr) python-urllib"
INTERESSANTS = ("Artist", "Attribution", "Credit", "AttributionRequired",
                "LicenseShortName", "License", "UsageTerms", "Copyrighted")


def http(url, donnees=None, entetes=None, essais=3):
    for n in range(1, essais + 1):
        try:
            req = urllib.request.Request(url, data=donnees)
            req.add_header("User-Agent", UA)
            for k, v in (entetes or {}).items():
                req.add_header(k, v)
            with urllib.request.urlopen(req, timeout=90) as r:
                return json.loads(r.read().decode("utf-8"))
        except Exception as e:
            if n == essais:
                raise
            print("      ! %s — nouvel essai" % e, file=sys.stderr)
            time.sleep(3 * n)


def main():
    base = (os.environ.get("SUPABASE_URL") or "").rstrip("/")
    cle = os.environ.get("SUPABASE_SERVICE_KEY") or ""
    if not base or not cle:
        sys.exit("Il manque SUPABASE_URL ou SUPABASE_SERVICE_KEY dans l'environnement.")
    auth = {"apikey": cle, "Authorization": "Bearer " + cle}

    lignes = http("%s/rest/v1/monuments?select=nom,image&photo=is.null"
                  "&image=not.is.null&order=langues.desc" % base, entetes=auth)
    lignes = [l for l in lignes if (l.get("image") or "").strip()]
    if not lignes:
        print("Aucun monument sans photo mais avec un nom de fichier. Rien a sonder.")
        return
    print("%d fichier(s) a examiner.\n" % len(lignes))

    # pas de iiextmetadatafilter : on veut TOUT voir
    corps = urllib.parse.urlencode({
        "action": "query", "format": "json", "prop": "imageinfo",
        "iiprop": "extmetadata|user|url",
        "titles": "|".join("File:" + l["image"] for l in lignes)}).encode("utf-8")
    data = http("https://commons.wikimedia.org/w/api.php", donnees=corps)

    pages = (data.get("query", {}).get("pages", {}) or {})
    par_titre = {}
    for page in pages.values():
        par_titre[page.get("title", "")[len("File:"):]] = page

    for l in lignes:
        fichier = l["image"]
        page = par_titre.get(fichier)
        print("=" * 78)
        print("%s" % l["nom"])
        print("fichier : %s" % fichier)
        if page is None:
            print("  -> AUCUNE PAGE RENVOYEE PAR COMMONS (nom de fichier faux ?)")
            print()
            continue
        if "missing" in page:
            print("  -> COMMONS DIT QUE CE FICHIER N'EXISTE PAS")
            print()
            continue
        ii = (page.get("imageinfo") or [{}])[0]
        meta = ii.get("extmetadata") or {}
        print("  deposant (user) : %r" % ii.get("user"))
        print("  champs presents : %s" % ", ".join(sorted(meta.keys())) or "(aucun)")
        for champ in INTERESSANTS:
            if champ in meta:
                valeur = (meta[champ] or {}).get("value", "")
                print("  %-20s = %r" % (champ, valeur))
        print()

    print("=" * 78)
    print("Rien n'a ete modifie. Colle-moi cette sortie telle quelle.")


if __name__ == "__main__":
    main()
