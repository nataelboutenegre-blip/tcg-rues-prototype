#!/usr/bin/env python3
# ---------------------------------------------------------------------------
#  TerraFront — nettoyage des gentiles bruts de Wikipedia
#
#  Entree : gentiles-bruts.csv  (insee, titre, brut)
#  Sortie : gentiles-propres.csv (code, gentile)  et un rapport a l'ecran.
#
#  Principe : on ne devine jamais. Tout ce qui ne se reduit pas proprement a
#  un ou deux noms d'habitants est rejete et sort dans gentiles-rejets.csv,
#  pour qu'on puisse regarder ce qu'on perd au lieu de le supposer.
# ---------------------------------------------------------------------------
import csv
import io
import re
import sys
import unicodedata

ENTREE = 'gentiles-bruts.csv'
SORTIE = 'gentiles-propres.csv'
REJETS = 'gentiles-rejets.csv'

# --- balises et modeles ----------------------------------------------------
RE_REF = re.compile(r'<ref[^>]*/>|<ref[^>]*>.*?</ref>', re.S | re.I)
RE_COMM = re.compile(r'<!--.*?-->|<!--.*$', re.S)
RE_BR = re.compile(r'<br\s*/?>', re.I)
RE_BALISE = re.compile(r'</?[a-z][^>]*>', re.I)
RE_LIEN_INT = re.compile(r'\[\[(?:[^\]|]*\|)?([^\]|]*)\]\]')
RE_LIEN_EXT = re.compile(r'\[https?://\S+\s*([^\]]*)\]')
RE_NOBR = re.compile(r'\{\{\s*(?:nobr|no ?wrap|lang\|[^|}]*)\s*\|([^}]*)\}\}', re.I)
RE_MODELE = re.compile(r'\{\{[^{}]*\}\}')
RE_ITAL = re.compile(r"'{2,}")

# --- ce qui coupe la valeur ------------------------------------------------
RE_COUPE = re.compile(r'\b(anciennement|autrefois|jadis|parfois|aussi appel|'
                      r'surnom|localement|habitants? de)\b', re.I)

SEPARATEURS = re.compile(r'\s*(?:,|;|/|·|\s[-–—]\s|\bou\b|\bet\b)\s*')

# un nom d'habitant : lettres, traits d'union, apostrophes, espaces internes
LETTRE = "A-Za-zÀ-ÖØ-öø-ÿŒœÆæ"
RE_FORME = re.compile("^[A-ZÀ-ÖØ-ÞŒÆ][%s'’\\-]*(?: [a-zà-öø-ÿœæ][%s'’\\-]*)?$"
                      % (LETTRE, LETTRE))

# « Les Rancéens » : l'article n'est pas le nom des habitants.
RE_ARTICLE = re.compile(r"^(?:les|le|la|l['’]|des|du|de)\s+", re.I)
# des restes de syntaxe qu'aucun gentile ne peut etre
BLOCKLIST = {'les', 'le', 'la', 'des', 'du', 'de', 'et', 'ou', 'https', 'http',
             'saint', 'sainte', 'nc', 'aucun', 'idem', 'sans'}

PARENTHESE = re.compile(r'^([^()]+)\(([a-zà-ÿœæ]{1,4})\)([a-zà-ÿœæ]{0,3})$')


def sans_balises(v):
    v = RE_REF.sub(' ', v)
    v = RE_COMM.sub(' ', v)
    v = RE_BR.sub(', ', v)
    v = RE_NOBR.sub(r'\1', v)
    for _ in range(3):                      # modeles imbriques
        v2 = RE_MODELE.sub(' ', v)
        if v2 == v:
            break
        v = v2
    v = RE_LIEN_EXT.sub(r'\1', v)
    v = RE_LIEN_INT.sub(r'\1', v)
    v = RE_BALISE.sub(' ', v)
    v = RE_ITAL.sub('', v)
    v = v.replace('&nbsp;', ' ').replace(' ', ' ')
    return ' '.join(v.split())


def pluriel(mot):
    """Un gentile s'affiche au pluriel : « les Ypsiloniens »."""
    if not mot:
        return mot
    return mot if mot[-1] in 'sxzSXZ' else mot + 's'


def formes_de(v):
    """La liste des noms proposes, dans l'ordre, deja separes."""
    v = sans_balises(v)
    coupe = RE_COUPE.search(v)
    if coupe:
        v = v[:coupe.start()]
    v = v.strip(' .:·-–—')
    if not v:
        return []

    out = []
    for brut in SEPARATEURS.split(v):
        f = brut.strip(' .:·-–—')
        if not f:
            continue
        # Cappellois(es) -> Cappellois + Cappelloises
        f = RE_ARTICLE.sub('', f)
        f = re.sub(r'\((s)\)\s*$', r'\1', f.replace(' (', '('))
        m = PARENTHESE.match(f)
        if m:
            base, milieu, fin = m.group(1).strip(), m.group(2), m.group(3)
            out.append(base if fin == 's' and base[-1] in 'sxzSXZ'
                       else base + fin)            # Fossoyen + s
            out.append(base + milieu + fin)        # Fossoyen + ne + s
            continue
        # « Villeneuvociennes Villeneuvois » : deux noms colles par un espace.
        # Un vrai gentile en deux mots garde le second en minuscule
        # (« Capellains masmoleniens »), jamais en majuscule.
        for bout in re.split(r'\s+(?=[A-ZÀ-ÖØ-ÞŒÆ])', f):
            bout = RE_ARTICLE.sub('', bout).strip()
            if bout:
                out.append(bout)

    # majuscule initiale, sans toucher au reste
    nets = []
    for f in out:
        if not f:
            continue
        f = f[0].upper() + f[1:]
        if RE_FORME.match(f) and 4 <= len(f) <= 40 and f.lower() not in BLOCKLIST:
            nets.append(f)
    return nets


# Saint-Desiriens et Saint-Desideriens ont la meme racine sans etre masculin
# et feminin l'un de l'autre : ce sont deux noms concurrents. On n'accepte
# donc un feminin que s'il se forme depuis le masculin par une terminaison
# connue. Tout le reste est laisse de cote plutot que devine.
TERMINAISONS = ('e', 'ne', 'te', 'se', 'lle', 'esse')

def est_le_feminin(masc, fem):
    """fem est-il le feminin de masc ? Les deux sont au pluriel."""
    m = masc[:-1] if masc[-1] == 's' else masc
    f = fem[:-1] if fem[-1] == 's' else fem
    if any(f == m + t for t in TERMINAISONS):
        return True
    if m.endswith('f') and f == m[:-1] + 've':          # -fs -> -ves
        return True
    if m.endswith('er') and f == m[:-2] + 'ere':        # -ers -> -eres
        return True
    if m.endswith('er') and f == m[:-2] + '\u00e8re':
        return True
    return False


def gentile_de(brut):
    f = formes_de(brut)
    if not f:
        return None
    masc = pluriel(f[0])
    fem = None
    for autre in f[1:]:
        p = pluriel(autre)
        if p != masc and est_le_feminin(masc, p):
            fem = p
            break
    return masc + ' · ' + fem if fem else masc


def main():
    lignes = list(csv.DictReader(io.open(ENTREE, encoding='utf-8')))
    propres, rejets, vides, vus = [], [], 0, set()
    for r in lignes:
        brut = r['brut'].strip()
        if not brut or not sans_balises(brut).strip(' .:-'):
            vides += 1
            continue
        g = gentile_de(brut)
        if g:
            vus.add(r['insee'])
            propres.append({'code': r['insee'], 'titre': r['titre'], 'gentile': g})
        else:
            rejets.append({'code': r['insee'], 'titre': r['titre'], 'brut': brut})

    with io.open(SORTIE, 'w', encoding='utf-8', newline='') as f:
        w = csv.DictWriter(f, fieldnames=['code', 'titre', 'gentile'])
        w.writeheader()
        w.writerows(propres)
    with io.open(REJETS, 'w', encoding='utf-8', newline='') as f:
        w = csv.DictWriter(f, fieldnames=['code', 'titre', 'brut'])
        w.writeheader()
        w.writerows(rejets)

    n = len(lignes)
    print('communes lues          : %d' % n)
    print('sans champ gentile     : %d  (%.1f %%)' % (vides, 100 * vides / n))
    print('gentile retenu         : %d lignes, %d communes distinctes'
          % (len(propres), len(vus)))
    print('codes a plusieurs articles : %d' % (len(propres) - len(vus)))
    print('rejete (illisible)     : %d  (%.1f %%)' % (len(rejets), 100 * len(rejets) / n))
    print('\n-> %s et %s' % (SORTIE, REJETS))
    return 0


if __name__ == '__main__':
    sys.exit(main())
