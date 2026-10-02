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


def nom_auteur(brut):
    """Le champ Artist de Commons est du HTML, et pas toujours bien forme.

    Retirer les balises suffit quand le champ vaut « <a ...>Jean Dupont</a> ».
    Ca ne donne rien quand il vaut « <a href="/wiki/User:Jean"
    title="User:Jean"></a> » : un lien sans texte, dont le nom n'existe que
    dans title ou dans l'adresse. On lit donc les liens avant de nettoyer.
    """
    if not brut:
        return ""

    def du_lien(m):
        attributs, texte = m.group(1), m.group(2)
        texte = re.sub(r"<[^>]+>", " ", texte).strip()
        if texte:
            return texte
        titre = re.search(r'title="([^"]*)"', attributs)
        if titre and titre.group(1).strip():
            t = titre.group(1).strip()
            # un lien vers un fichier ou une categorie n'est pas un auteur
            if t.lower().split(":", 1)[0] in ("file", "image", "category", "fichier"):
                return ""
            return t.split(":", 1)[1] if t.lower().startswith("user:") else t
        adresse = re.search(r'href="([^"]*)"', attributs)
        if adresse and "User:" in adresse.group(1):
            return urllib.parse.unquote(adresse.group(1).split("User:")[-1]).replace("_", " ")
        return ""

    s = re.sub(r"<a\b([^>]*)>(.*?)</a>", du_lien, brut, flags=re.S | re.I)
    s = re.sub(r"<[^>]+>", " ", s)
    s = re.sub(r"&amp;", "&", s)
    s = re.sub(r"\s+", " ", s).strip()
    return s


def nettoyer_wiki(v):
    """Un parametre de modele wiki vers un nom lisible."""
    if not v:
        return ""
    s = v.strip()
    s = re.sub(r"<!--.*?-->", " ", s, flags=re.S)
    # [[User:Foo|Bar]] -> Bar ; [[User:Foo]] -> Foo
    s = re.sub(r"\[\[[^\]|]*\|([^\]]*)\]\]", r"\1", s)
    s = re.sub(r"\[\[(?:[Uu]ser|[Uu]tilisateur):([^\]]*)\]\]", r"\1", s)
    s = re.sub(r"\[\[([^\]]*)\]\]", r"\1", s)
    # [http://x Bar] -> Bar
    s = re.sub(r"\[https?://\S+\s+([^\]]*)\]", r"\1", s)
    s = re.sub(r"\[https?://\S+\]", " ", s)
    # {{Creator:Foo}} / {{User:Foo/credit}} -> Foo
    s = re.sub(r"\{\{\s*(?:[Cc]reator|[Uu]ser)\s*:\s*([^|}/]+)[^}]*\}\}", r"\1", s)
    s = re.sub(r"\{\{[^}]*\}\}", " ", s)
    s = re.sub(r"<[^>]+>", " ", s)
    s = re.sub(r"'{2,}", "", s)
    s = re.sub(r"&amp;", "&", s)
    s = re.sub(r"\s+", " ", s).strip(" |\t")
    # un parametre vide ou un mot-cle qui ne nomme personne
    if s.lower() in ("", "unknown", "inconnu", "self", "own work", "travail personnel", "n/a", "-"):
        return ""
    return s


def deposants(fichiers):
    """{fichier: nom du deposant} — le groupage est permis pour imageinfo."""
    out = {}
    for i in range(0, len(fichiers), 50):
        corps = urllib.parse.urlencode({
            "action": "query", "format": "json", "prop": "imageinfo",
            "iiprop": "user",
            "titles": "|".join("File:" + f for f in fichiers[i:i + 50])}).encode("utf-8")
        try:
            data = http("https://commons.wikimedia.org/w/api.php", donnees=corps)
        except Exception:
            return out
        for page in ((data.get("query", {}) or {}).get("pages", {}) or {}).values():
            titre = page.get("title", "")[len("File:"):]
            ii = (page.get("imageinfo") or [{}])[0]
            if ii.get("user"):
                out[titre] = ii["user"]
        time.sleep(0.3)
    return out


def auteur_du_wikitexte(fichiers):
    """({fichier: auteur}, {fichier: raison de l'echec}).

    Deux sources, dans cet ordre :

      1. le parametre author du modele Information, dans le texte de la page ;
      2. a defaut, le deposant SI la page porte {{self}} — ce modele est la
         declaration par laquelle le deposant affirme etre l'auteur. Sans
         {{self}}, on ne retient rien : le deposant n'est pas forcement
         l'auteur.

    UNE PAGE A LA FOIS : l'interface refuse de renvoyer le contenu de
    plusieurs pages dans une seule requete.
    """
    trouves, raisons = {}, {}
    qui_a_depose = deposants(fichiers)

    for n, f in enumerate(fichiers, 1):
        corps = urllib.parse.urlencode({
            "action": "query", "format": "json", "prop": "revisions",
            "rvprop": "content", "rvslots": "main", "rvlimit": "1",
            "titles": "File:" + f}).encode("utf-8")
        try:
            data = http("https://commons.wikimedia.org/w/api.php", donnees=corps)
        except Exception as e:
            raisons[f] = "requete impossible : %s" % e
            continue
        if isinstance(data, dict) and data.get("error"):
            raisons[f] = "erreur de l'interface : %s" % str(
                data["error"].get("info", data["error"]))[:140]
            continue
        pages = (data.get("query", {}) or {}).get("pages", {}) or {}
        page = None
        for p in pages.values():
            page = p
        if page is None:
            raisons[f] = "aucune page renvoyee"
            continue
        if "missing" in page:
            raisons[f] = "fichier inexistant sur Commons"
            continue
        revs = page.get("revisions") or [{}]
        texte = (((revs[0].get("slots") or {}).get("main") or {}).get("*")
                 or revs[0].get("*") or "")
        if not texte:
            raisons[f] = "texte de la page non renvoye"
            continue

        nom, origine = "", ""
        m = re.search(r"\|\s*(?:author|artist|auteur|photographer)\s*=\s*(.*?)"
                      r"(?=\n\s*\||\n\}\}|\Z)", texte, flags=re.S | re.I)
        if m:
            nom = nettoyer_wiki(m.group(1))
            origine = "champ auteur de la page"

        if not nom and re.search(r"\{\{\s*self\b", texte, flags=re.I):
            # {{self}} : le deposant declare etre l'auteur. C'est une
            # declaration, pas une supposition de notre part.
            nom = qui_a_depose.get(f, "")
            origine = "deposant, declare auteur par {{self}}"

        if not nom:
            if re.search(r"\{\{\s*self\b", texte, flags=re.I):
                raisons[f] = "page avec {{self}} mais deposant inconnu"
            else:
                raisons[f] = ("page lue (%d caracteres), ni champ auteur ni {{self}}"
                              % len(texte))
            continue

        trouves[f] = nom
        print("      %d/%d  %-40s -> %s  [%s]" % (n, len(fichiers), f[:40], nom, origine))
        time.sleep(0.3)
    return trouves, raisons


def metadonnees(fichiers):
    """{nom: (auteur, licence)} — par paquets de 50."""
    infos = {}
    for i in range(0, len(fichiers), 50):
        paquet = fichiers[i:i + 50]
        corps = urllib.parse.urlencode({
            "action": "query", "format": "json", "prop": "imageinfo",
            "iiprop": "extmetadata",
            "iiextmetadatafilter": "Artist|Attribution|LicenseShortName|AttributionRequired",
            "titles": "|".join("File:" + f for f in paquet)}).encode("utf-8")
        data = http("https://commons.wikimedia.org/w/api.php", donnees=corps)
        for page in (data.get("query", {}).get("pages", {}) or {}).values():
            titre = page.get("title", "")[len("File:"):]
            meta = ((page.get("imageinfo") or [{}])[0].get("extmetadata") or {})
            lire = lambda c: (meta.get(c, {}) or {}).get("value", "") or ""
            # Artist d'abord ; a defaut Attribution, le champ dans lequel
            # Commons indique comment crediter. On ne descend pas jusqu'au
            # deposant du fichier : il n'est pas forcement l'auteur, et une
            # attribution approximative est pire qu'une image manquante.
            auteur = nom_auteur(lire("Artist")) or nom_auteur(lire("Attribution"))
            # le domaine public ne demande pas d'attribution : exiger un
            # auteur reviendrait a ecarter une image qu'on a le droit d'utiliser
            libre = (lire("AttributionRequired").strip().lower() == "false")
            infos[titre] = (auteur, lire("LicenseShortName"), libre)
        print("   metadonnees %d/%d" % (min(i + 50, len(fichiers)), len(fichiers)))
        time.sleep(0.4)
    return infos


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--essai", action="store_true", help="10 emblemes puis on s'arrete")
    ap.add_argument("--montrer", action="store_true",
                    help="affiche l'auteur retenu pour chaque fichier et n'ecrit rien")
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

    raisons_echec = {}
    print("\nAuteurs et licences...")
    infos = metadonnees(sorted({l["image"] for l in lignes}))

    # Ce que les metadonnees n'ont pas donne vit souvent dans le texte de la
    # page du fichier, que l'interface ne sait pas lire pour certains modeles.
    manquants = sorted({l["image"] for l in lignes
                        if not infos.get(l["image"], ("", "", False))[0]
                        and not infos.get(l["image"], ("", "", False))[2]})
    if manquants:
        print("   %d sans auteur dans les metadonnees, on lit la page du fichier..."
              % len(manquants))
        repeches, raisons_echec = auteur_du_wikitexte(manquants)
        for f, nom in repeches.items():
            licence, libre = infos.get(f, ("", "", False))[1:3]
            infos[f] = (nom, licence, libre)
        print("   %d auteur(s) retrouve(s) sur %d." % (len(repeches), len(manquants)))

    if args.montrer:
        print("\nCe que le script utiliserait (rien n'est ecrit) :\n")
        for l in lignes:
            auteur, licence, libre = infos.get(l["image"], ("", "", False))
            if auteur:
                etat = "auteur : %s" % auteur
            elif libre:
                etat = "domaine public, pas d'attribution requise"
            else:
                etat = "AUCUN AUTEUR -> ecartee"
                pourquoi = raisons_echec.get(l["image"])
                if pourquoi:
                    etat += "  (%s)" % pourquoi
            print("  %-46s %s" % (l["nom"][:46], etat))
            print("  %-46s   licence : %s" % ("", licence or "(aucune)"))
        print("\nRien n'a ete modifie. Relance sans --montrer si c'est juste.")
        return

    # Une image reste ecartee seulement si elle exige une attribution qu'on
    # ne sait pas donner. Le domaine public passe sans auteur.
    sans_auteur = [l for l in lignes
                   if not infos.get(l["image"], ("", "", False))[0]
                   and not infos.get(l["image"], ("", "", False))[2]]
    if sans_auteur:
        print("   %d sans auteur lisible, ecartes (l'attribution est obligatoire) :"
              % len(sans_auteur))
        for l in sans_auteur[:8]:
            print("      %s" % l["nom"])
        lignes = [l for l in lignes
                  if infos.get(l["image"], ("", "", False))[0]
                  or infos.get(l["image"], ("", "", False))[2]]

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
                auteur, licence = infos.get(fichier, ("", "", False))[:2]
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
