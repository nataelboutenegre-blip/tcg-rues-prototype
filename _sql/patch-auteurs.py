# -*- coding: utf-8 -*-
u"""
patch-auteurs — monuments-2-images.py lit enfin les auteurs qu'il jetait.

CE QUI S'EST PASSE
  Neuf monuments sur 236 n'ont pas d'image, et ce sont de belles pieces :
  Cluny, Chenonceau, la villa Savoye, la cathedrale de Metz. Le script les
  a ecartees « faute d'auteur lisible ».

MA PREMIERE EXPLICATION ETAIT FAUSSE
  Je t'ai dit que Wikimedia ne donnait pas d'auteur pour ces fichiers. En
  regardant de pres, c'est mon script qui le jetait.

  Le champ Artist de Commons contient du HTML. Mon script retirait les
  balises et gardait le texte — ce qui marche quand le champ vaut
  « <a href="...">Jean Dupont</a> », et ne marche pas du tout quand il vaut
  « <a href="/wiki/User:Jean" title="User:Jean"></a> », c'est-a-dire un lien
  SANS texte, ou le nom n'existe que dans l'attribut title ou dans l'adresse.
  Retirer les balises ne laissait rien, et le script concluait a l'absence
  d'auteur.

CE QUE JE FAIS
  Avant de retirer les balises, on lit les liens : d'abord leur texte, et
  s'il est vide, l'attribut title, et sinon le nom d'utilisateur contenu
  dans l'adresse. Puis, si le champ Artist ne donne vraiment rien, on se
  rabat sur Attribution — le champ dans lequel Commons indique comment
  crediter le fichier, ce qui est exactement ce qu'on cherche.

  On ne descend PAS jusqu'au nom du contributeur qui a depose le fichier :
  le deposant n'est pas forcement l'auteur, et une attribution approximative
  est pire qu'une image manquante.

CE QUE CA NE CHANGE PAS
  Les 227 images deja posees ne sont pas retouchees : le journal de reprise
  les saute. Relancer le script ne traitera que ce qui manque.

A LANCER
    cd _sql
    python3 monuments-2-images.py
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

py = rempl(py,
u'''def metadonnees(fichiers):''',
u'''def nom_auteur(brut):
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

    s = re.sub(r"<a\\b([^>]*)>(.*?)</a>", du_lien, brut, flags=re.S | re.I)
    s = re.sub(r"<[^>]+>", " ", s)
    s = re.sub(r"&amp;", "&", s)
    s = re.sub(r"\\s+", " ", s).strip()
    return s


def metadonnees(fichiers):''',
u'la lecture des auteurs cachs dans les liens')

py = rempl(py,
u'''            "iiextmetadatafilter": "Artist|LicenseShortName",''',
u'''            "iiextmetadatafilter": "Artist|Attribution|LicenseShortName",''',
u'on demande aussi le champ Attribution')

py = rempl(py,
u'''            auteur = re.sub(r"<[^>]+>", "", lire("Artist"))
            infos[titre] = (re.sub(r"\\s+", " ", auteur).strip(), lire("LicenseShortName"))''',
u'''            # Artist d'abord ; a defaut Attribution, le champ dans lequel
            # Commons indique comment crediter. On ne descend pas jusqu'au
            # deposant du fichier : il n'est pas forcement l'auteur, et une
            # attribution approximative est pire qu'une image manquante.
            auteur = nom_auteur(lire("Artist")) or nom_auteur(lire("Attribution"))
            infos[titre] = (auteur, lire("LicenseShortName"))''',
u'le repli sur Attribution')

ecrire('monuments-2-images.py', py)
print(u'patch-auteurs applique.')
