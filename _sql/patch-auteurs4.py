# -*- coding: utf-8 -*-
u"""
patch-auteurs4 — {{self}} est une declaration d'auteur, pas une absence d'auteur.

CE QUE LE DIAGNOSTIC A ETABLI
  Les pages sont bien lues — 323 a 731 caracteres — et elles ne contiennent
  reellement aucun parametre auteur. Ce sont de vieux depots de 2005-2008 :
  une ligne de description, un modele de licence, rien d'autre. Cette fois
  ce n'est pas une supposition, c'est le script qui l'a mesure.

POURQUOI CA CHANGE LA REPONSE
  Ces pages portent le modele {{self|cc-by-sa-3.0}}. Ce modele n'est pas une
  decoration : il veut dire « moi, le deposant, je suis l'auteur de cette
  image et je la publie sous cette licence ». C'est une declaration formelle
  faite par le deposant lui-meme.

  Mon refus precedent — « le deposant n'est pas forcement l'auteur » — reste
  vrai en general, et devient faux exactement pour ces fichiers-la. Pour une
  page marquee {{self}}, crediter le deposant est la bonne reponse, c'est
  meme ce que Commons demande.

CE QUE JE FAIS
  Quand la page n'a pas de parametre auteur MAIS porte {{self}}, on retient
  le deposant. Les pages sans parametre auteur et sans {{self}} restent
  ecartees : la, on ne sait vraiment pas.

  Le script dit lequel des deux cas s'applique, fichier par fichier, dans
  --montrer. C'est verifiable avant d'ecrire quoi que ce soit.

CE QUI NE CHANGE PAS AILLEURS
  Rien. La fonction qui va chercher les auteurs est la seule touchee ; les
  230 images posees ne sont pas relues.

ENGAGEMENT
  C'est le dernier essai sur ce sujet. Si le --montrer ne sort pas six noms
  credibles, les six gardent leur icone et on n'y revient plus.
"""
import io, os

BASE = os.path.dirname(os.path.abspath(__file__))

def lire(n):
    with io.open(os.path.join(BASE, n), encoding='utf-8') as f:
        return f.read()

def ecrire(n, s):
    with io.open(os.path.join(BASE, n), 'w', encoding='utf-8') as f:
        f.write(s)


py = lire('monuments-2-images.py')

DEBUT = py.index(u'def auteur_du_wikitexte(fichiers):')
FIN = py.index(u'def metadonnees(fichiers):')

nouveau = u'''def deposants(fichiers):
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
        m = re.search(r"\\|\\s*(?:author|artist|auteur|photographer)\\s*=\\s*(.*?)"
                      r"(?=\\n\\s*\\||\\n\\}\\}|\\Z)", texte, flags=re.S | re.I)
        if m:
            nom = nettoyer_wiki(m.group(1))
            origine = "champ auteur de la page"

        if not nom and re.search(r"\\{\\{\\s*self\\b", texte, flags=re.I):
            # {{self}} : le deposant declare etre l'auteur. C'est une
            # declaration, pas une supposition de notre part.
            nom = qui_a_depose.get(f, "")
            origine = "deposant, declare auteur par {{self}}"

        if not nom:
            if re.search(r"\\{\\{\\s*self\\b", texte, flags=re.I):
                raisons[f] = "page avec {{self}} mais deposant inconnu"
            else:
                raisons[f] = ("page lue (%d caracteres), ni champ auteur ni {{self}}"
                              % len(texte))
            continue

        trouves[f] = nom
        print("      %d/%d  %-40s -> %s  [%s]" % (n, len(fichiers), f[:40], nom, origine))
        time.sleep(0.3)
    return trouves, raisons


'''

py = py[:DEBUT] + nouveau + py[FIN:]
ecrire('monuments-2-images.py', py)
print(u'patch-auteurs4 applique.')
