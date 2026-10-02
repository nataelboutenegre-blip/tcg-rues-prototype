# -*- coding: utf-8 -*-
u"""
patch-auteurs3 — je demandais le texte de vingt pages d'un coup, ce qui n'existe pas.

CE QUE LE --MONTRER A REVELE
  Aucun auteur retrouve, pour aucun des six. Pas « des noms bizarres » :
  rien du tout. Quand une etape ne ramene strictement rien, ce n'est en
  general pas l'analyse qui echoue, c'est la demande.

  Et c'est le cas. L'interface de Wikimedia refuse de renvoyer le TEXTE de
  plusieurs pages dans une seule requete — c'est une limite documentee, pas
  un hasard. Je groupais par vingt, comme je le fais pour les metadonnees,
  ou le groupage est permis. L'interface renvoyait donc une erreur que mon
  script ignorait, et il concluait tranquillement a l'absence d'auteur.

CE QUE JE CHANGE
  Une page a la fois. Six requetes au lieu d'une, ce qui ne coute rien pour
  six fichiers.

ET SURTOUT, LE SCRIPT DIT MAINTENANT POURQUOI IL ECHOUE
  C'est la vraie lecon de la matinee. A chaque fois que je me suis trompe,
  c'est parce que le script disait « pas d'auteur » sans distinguer :
    — l'interface a renvoye une erreur
    — la page est revenue vide
    — la page est la mais ne contient pas de parametre auteur
  Ces trois cas demandent trois corrections differentes et le script les
  affichait pareil. Desormais --montrer imprime la raison exacte.

  Si apres ca il reste des fichiers sans auteur, on saura enfin pourquoi, et
  ce sera probablement la bonne raison : certaines pages anciennes n'ont
  reellement pas de champ auteur. Dans ce cas on s'arrete et ces six-la
  gardent leur icone. Six images sur 236, ca ne vaut pas une quatrieme
  tentative.

A LANCER
    cd _sql
    python3 monuments-2-images.py --montrer
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
#  Une page a la fois, et on retient la raison de chaque echec
# ---------------------------------------------------------------------------
DEBUT = py.index(u'def auteur_du_wikitexte(fichiers):')
FIN = py.index(u'def metadonnees(fichiers):')
ancien = py[DEBUT:FIN]

nouveau = u'''def auteur_du_wikitexte(fichiers):
    """({fichier: auteur}, {fichier: raison de l'echec}).

    L'auteur de ces fichiers n'est pas dans les metadonnees mais dans le
    texte de la page, dans le modele Information.

    UNE PAGE A LA FOIS : l'interface refuse de renvoyer le contenu de
    plusieurs pages dans une seule requete. Grouper, comme on le fait pour
    les metadonnees, ne ramenait rien du tout.
    """
    trouves, raisons = {}, {}
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
        m = re.search(r"\\|\\s*(?:author|artist|auteur|photographer)\\s*=\\s*(.*?)"
                      r"(?=\\n\\s*\\||\\n\\}\\}|\\Z)", texte, flags=re.S | re.I)
        if not m:
            raisons[f] = "page lue (%d caracteres), aucun parametre auteur" % len(texte)
            continue
        nom = nettoyer_wiki(m.group(1))
        if not nom:
            raisons[f] = "parametre auteur present mais vide apres nettoyage : %r" % m.group(1)[:80]
            continue
        trouves[f] = nom
        print("      %d/%d  %s -> %s" % (n, len(fichiers), f[:44], nom))
        time.sleep(0.3)
    return trouves, raisons


'''

py = py[:DEBUT] + nouveau + py[FIN:]

# ---------------------------------------------------------------------------
#  main : on recupere les raisons et on les affiche
# ---------------------------------------------------------------------------
py = rempl(py,
u'''        repechés = auteur_du_wikitexte(manquants)
        for f, nom in repechés.items():
            licence, libre = infos.get(f, ("", "", False))[1:3]
            infos[f] = (nom, licence, libre)
        print("   %d auteur(s) retrouve(s)." % len(repechés))''',
u'''        repeches, raisons_echec = auteur_du_wikitexte(manquants)
        for f, nom in repeches.items():
            licence, libre = infos.get(f, ("", "", False))[1:3]
            infos[f] = (nom, licence, libre)
        print("   %d auteur(s) retrouve(s) sur %d." % (len(repeches), len(manquants)))''',
u'le repechage renvoie aussi les raisons')

py = rempl(py,
u'''            else:
                etat = "AUCUN AUTEUR -> ecartee"''',
u'''            else:
                etat = "AUCUN AUTEUR -> ecartee"
                pourquoi = raisons_echec.get(l["image"])
                if pourquoi:
                    etat += "  (%s)" % pourquoi''',
u'la raison de l’echec dans --montrer')

py = rempl(py,
u'''    print("\\nAuteurs et licences...")''',
u'''    raisons_echec = {}
    print("\\nAuteurs et licences...")''',
u'raisons_echec existe meme sans repechage')

ecrire('monuments-2-images.py', py)
print(u'patch-auteurs3 applique.')
