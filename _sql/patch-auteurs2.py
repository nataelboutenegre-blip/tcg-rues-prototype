# -*- coding: utf-8 -*-
u"""
patch-auteurs2 — l'auteur est dans la page du fichier, pas dans les metadonnees.

CE QUE LA SONDE A MONTRE
  Pour les sept fichiers restants, Commons ne renvoie AUCUN champ d'auteur :
  ni Artist, ni Attribution, ni Credit. La liste des champs presents le dit
  noir sur blanc. Mes deux explications precedentes etaient donc fausses
  toutes les deux, et la seconde correction ne pouvait rien changer.

  Le seul nom de personne que l'interface donne est « deposant ». Or ces
  fichiers ont bien un auteur : il est ecrit dans la page du fichier, dans
  le modele Information, que l'interface des metadonnees n'a pas su lire.

DEUX CORRECTIONS, DE NATURE DIFFERENTE

  1. Le domaine public n'a pas besoin d'auteur.
     « Île d'Yeu.png » porte AttributionRequired = false et la mention
     « Public domain ». Exiger une attribution pour une image du domaine
     public n'a pas de sens : celle-la passe desormais sans auteur, avec sa
     licence. C'est certain, ca ne depend d'aucune supposition.

  2. On va chercher l'auteur dans la page du fichier.
     Si les metadonnees ne donnent rien, on lit le texte de la page et on en
     extrait le parametre « author » du modele Information. C'est la que vit
     la reponse pour ces six-la.

CE QUE JE N'AI PAS PU VERIFIER MOI-MEME
  Je n'ai pas acces a Wikimedia depuis mon conteneur. J'ai teste l'analyse
  du texte sur onze formes connues de ce parametre, mais pas sur les vraies
  pages. C'est pour ca que le script gagne un mode qui n'ecrit rien :

      python3 monuments-2-images.py --montrer

  Il affiche, pour chaque fichier restant, l'auteur qu'il utiliserait et
  d'ou il le tire. Tu regardes, et seulement si c'est juste tu relances sans
  l'option. Je ne veux pas poser une attribution fausse dans ta base parce
  que j'aurais devine une troisieme fois.

CE QUE JE REFUSE TOUJOURS
  Se rabattre sur le deposant. Il n'est pas forcement l'auteur, et une
  attribution approximative est pire qu'une image manquante.
"""
import io, os

BASE = os.path.dirname(os.path.abspath(__file__))

def lire(n):
    with io.open(os.path.join(BASE, n), encoding='utf-8') as f:
        return f.read()

def ecrire(n, s):
    with io.open(os.path.join(BASE, n), 'w', encoding='utf-8') as f:
        f.write(s)

def rempl(src, avant, apres, etiquette):
    n = src.count(avant)
    assert n == 1, u'%s : %d occurrences (attendu 1)' % (etiquette, n)
    return src.replace(avant, apres)


py = lire('monuments-2-images.py')

# ---------------------------------------------------------------------------
#  1. L'auteur lu dans le texte de la page du fichier
# ---------------------------------------------------------------------------
py = rempl(py,
u'''def metadonnees(fichiers):''',
u'''def nettoyer_wiki(v):
    """Un parametre de modele wiki vers un nom lisible."""
    if not v:
        return ""
    s = v.strip()
    s = re.sub(r"<!--.*?-->", " ", s, flags=re.S)
    # [[User:Foo|Bar]] -> Bar ; [[User:Foo]] -> Foo
    s = re.sub(r"\\[\\[[^\\]|]*\\|([^\\]]*)\\]\\]", r"\\1", s)
    s = re.sub(r"\\[\\[(?:[Uu]ser|[Uu]tilisateur):([^\\]]*)\\]\\]", r"\\1", s)
    s = re.sub(r"\\[\\[([^\\]]*)\\]\\]", r"\\1", s)
    # [http://x Bar] -> Bar
    s = re.sub(r"\\[https?://\\S+\\s+([^\\]]*)\\]", r"\\1", s)
    s = re.sub(r"\\[https?://\\S+\\]", " ", s)
    # {{Creator:Foo}} / {{User:Foo/credit}} -> Foo
    s = re.sub(r"\\{\\{\\s*(?:[Cc]reator|[Uu]ser)\\s*:\\s*([^|}/]+)[^}]*\\}\\}", r"\\1", s)
    s = re.sub(r"\\{\\{[^}]*\\}\\}", " ", s)
    s = re.sub(r"<[^>]+>", " ", s)
    s = re.sub(r"'{2,}", "", s)
    s = re.sub(r"&amp;", "&", s)
    s = re.sub(r"\\s+", " ", s).strip(" |\\t")
    # un parametre vide ou un mot-cle qui ne nomme personne
    if s.lower() in ("", "unknown", "inconnu", "self", "own work", "travail personnel", "n/a", "-"):
        return ""
    return s


def auteur_du_wikitexte(fichiers):
    """{nom de fichier: auteur} — lu dans le modele Information de la page.

    L'interface des metadonnees ne sait pas lire certains modeles anciens,
    alors que le texte de la page, lui, contient bien la reponse.
    """
    trouves = {}
    for i in range(0, len(fichiers), 20):
        paquet = fichiers[i:i + 20]
        corps = urllib.parse.urlencode({
            "action": "query", "format": "json", "prop": "revisions",
            "rvprop": "content", "rvslots": "main",
            "titles": "|".join("File:" + f for f in paquet)}).encode("utf-8")
        data = http("https://commons.wikimedia.org/w/api.php", donnees=corps)
        for page in (data.get("query", {}).get("pages", {}) or {}).values():
            titre = page.get("title", "")[len("File:"):]
            revs = page.get("revisions") or [{}]
            texte = (((revs[0].get("slots") or {}).get("main") or {}).get("*")
                     or revs[0].get("*") or "")
            m = re.search(r"\\|\\s*(?:author|artist|auteur)\\s*=\\s*(.*?)(?=\\n\\s*\\||\\n\\}\\}|\\Z)",
                          texte, flags=re.S | re.I)
            if m:
                nom = nettoyer_wiki(m.group(1))
                if nom:
                    trouves[titre] = nom
        time.sleep(0.4)
    return trouves


def metadonnees(fichiers):''',
u"la lecture de l'auteur dans le texte de la page")

# ---------------------------------------------------------------------------
#  2. metadonnees renvoie aussi s'il faut une attribution
# ---------------------------------------------------------------------------
py = rempl(py,
u'''            "iiextmetadatafilter": "Artist|Attribution|LicenseShortName",''',
u'''            "iiextmetadatafilter": "Artist|Attribution|LicenseShortName|AttributionRequired",''',
u'on demande aussi AttributionRequired')

py = rempl(py,
u'''            # Artist d'abord ; a defaut Attribution, le champ dans lequel
            # Commons indique comment crediter. On ne descend pas jusqu'au
            # deposant du fichier : il n'est pas forcement l'auteur, et une
            # attribution approximative est pire qu'une image manquante.
            auteur = nom_auteur(lire("Artist")) or nom_auteur(lire("Attribution"))
            infos[titre] = (auteur, lire("LicenseShortName"))''',
u'''            # Artist d'abord ; a defaut Attribution, le champ dans lequel
            # Commons indique comment crediter. On ne descend pas jusqu'au
            # deposant du fichier : il n'est pas forcement l'auteur, et une
            # attribution approximative est pire qu'une image manquante.
            auteur = nom_auteur(lire("Artist")) or nom_auteur(lire("Attribution"))
            # le domaine public ne demande pas d'attribution : exiger un
            # auteur reviendrait a ecarter une image qu'on a le droit d'utiliser
            libre = (lire("AttributionRequired").strip().lower() == "false")
            infos[titre] = (auteur, lire("LicenseShortName"), libre)''',
u"metadonnees dit aussi si l'attribution est obligatoire")

# ---------------------------------------------------------------------------
#  3. main : le repli, le mode --montrer, et la regle du domaine public
# ---------------------------------------------------------------------------
py = rempl(py,
u'''    ap.add_argument("--essai", action="store_true", help="10 emblemes puis on s'arrete")''',
u'''    ap.add_argument("--essai", action="store_true", help="10 emblemes puis on s'arrete")
    ap.add_argument("--montrer", action="store_true",
                    help="affiche l'auteur retenu pour chaque fichier et n'ecrit rien")''',
u'option --montrer')

py = rempl(py,
u'''    print("\\nAuteurs et licences...")
    infos = metadonnees(sorted({l["image"] for l in lignes}))
    sans_auteur = [l for l in lignes if not infos.get(l["image"], ("",))[0]]
    if sans_auteur:
        print("   %d sans auteur lisible, ecartes (l'attribution est obligatoire) :"
              % len(sans_auteur))
        for l in sans_auteur[:8]:
            print("      %s" % l["nom"])
        lignes = [l for l in lignes if infos.get(l["image"], ("",))[0]]''',
u'''    print("\\nAuteurs et licences...")
    infos = metadonnees(sorted({l["image"] for l in lignes}))

    # Ce que les metadonnees n'ont pas donne vit souvent dans le texte de la
    # page du fichier, que l'interface ne sait pas lire pour certains modeles.
    manquants = sorted({l["image"] for l in lignes
                        if not infos.get(l["image"], ("", "", False))[0]
                        and not infos.get(l["image"], ("", "", False))[2]})
    if manquants:
        print("   %d sans auteur dans les metadonnees, on lit la page du fichier..."
              % len(manquants))
        repechés = auteur_du_wikitexte(manquants)
        for f, nom in repechés.items():
            licence, libre = infos.get(f, ("", "", False))[1:3]
            infos[f] = (nom, licence, libre)
        print("   %d auteur(s) retrouve(s)." % len(repechés))

    if args.montrer:
        print("\\nCe que le script utiliserait (rien n'est ecrit) :\\n")
        for l in lignes:
            auteur, licence, libre = infos.get(l["image"], ("", "", False))
            if auteur:
                etat = "auteur : %s" % auteur
            elif libre:
                etat = "domaine public, pas d'attribution requise"
            else:
                etat = "AUCUN AUTEUR -> ecartee"
            print("  %-46s %s" % (l["nom"][:46], etat))
            print("  %-46s   licence : %s" % ("", licence or "(aucune)"))
        print("\\nRien n'a ete modifie. Relance sans --montrer si c'est juste.")
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
                  or infos.get(l["image"], ("", "", False))[2]]''',
u'le repli, le mode montrer et la regle du domaine public')

py = rempl(py,
u'''                auteur, licence = infos.get(fichier, ("", ""))''',
u'''                auteur, licence = infos.get(fichier, ("", "", False))[:2]''',
u'la pose lit le triplet')

ecrire('monuments-2-images.py', py)
print(u'patch-auteurs2 applique.')
