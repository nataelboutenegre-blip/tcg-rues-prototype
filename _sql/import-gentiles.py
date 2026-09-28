#!/usr/bin/env python3
# ---------------------------------------------------------------------------
#  TerraFront — recuperation brute du champ "Gentile" des infobox Wikipedia FR
#
#  Ne nettoie rien, ne decide rien : ecrit la valeur telle qu'elle est dans
#  l'article, avec ses <ref>, ses <br> et ses modeles. Le nettoyage se fait
#  ensuite, sur le CSV, sans retelecharger.
#
#  Cinquante articles par requete, au lieu d'un : ~790 requetes au lieu de
#  39 517, et plus de HTTP 429. Le flux est compresse a la source.
#
#  Reprenable : le CSV de sortie fait foi. Si ca coupe, relancer continue.
#
#  Entree  : communes-wikipedia.csv      (produit par sonde-gentiles.py)
#  Sortie  : gentiles-bruts.csv          (insee, titre, brut)
#
#  Usage :  python3 import-gentiles.py
# ---------------------------------------------------------------------------
import csv
import gzip
import io
import json
import os
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request

UA = 'TerraFront/1.0 (terrafront.fr) import-gentiles'
API = 'https://fr.wikipedia.org/w/api.php'
ENTREE = 'communes-wikipedia.csv'
SORTIE = 'gentiles-bruts.csv'
LOT = 50

RE_CHAMP = re.compile(r'\n\s*\|\s*gentil[ée]?\s*=', re.I)


def poster(params):
    """Un appel a l'API, compresse, avec reprise sur 429 et 503."""
    corps = urllib.parse.urlencode(params).encode('utf-8')
    for essai in range(6):
        try:
            req = urllib.request.Request(API, data=corps, headers={
                'User-Agent': UA,
                'Accept-Encoding': 'gzip',
                'Content-Type': 'application/x-www-form-urlencoded',
            })
            with urllib.request.urlopen(req, timeout=180) as r:
                donnees = r.read()
                if r.headers.get('Content-Encoding') == 'gzip':
                    donnees = gzip.GzipFile(fileobj=io.BytesIO(donnees)).read()
                return json.loads(donnees.decode('utf-8')), len(donnees)
        except urllib.error.HTTPError as e:
            if e.code in (429, 503) and essai < 5:
                pause = 5 * (essai + 1)
                print('    %d — pause de %ds' % (e.code, pause), flush=True)
                time.sleep(pause)
                continue
            raise
        except Exception:
            if essai == 5:
                raise
            time.sleep(3 * (essai + 1))
    raise RuntimeError('abandon')


def valeur_du_champ(texte):
    """Le contenu brut du parametre gentile, en respectant les modeles.

    Une expression reguliere ne suffit pas : la valeur peut contenir des
    {{modeles}} et des [[liens]] qui contiennent eux-memes des barres
    verticales. On avance caractere par caractere en comptant la profondeur,
    et on s'arrete au premier separateur de parametre reellement au niveau
    zero.
    """
    m = RE_CHAMP.search(texte)
    if not m:
        return ''
    i, n = m.end(), len(texte)
    modele = lien = 0
    out = []
    while i < n:
        deux = texte[i:i + 2]
        if deux == '{{':
            modele += 1
            out.append(deux); i += 2; continue
        if deux == '}}':
            if modele == 0:
                break
            modele -= 1
            out.append(deux); i += 2; continue
        if deux == '[[':
            lien += 1
            out.append(deux); i += 2; continue
        if deux == ']]':
            if lien:
                lien -= 1
            out.append(deux); i += 2; continue
        c = texte[i]
        if modele == 0 and lien == 0:
            if c == '|':
                break
            if c == '\n':
                j = i + 1
                while j < n and texte[j] in ' \t':
                    j += 1
                if j >= n or texte[j] == '|' or texte[j:j + 2] == '}}':
                    break
        out.append(c); i += 1
    return ' '.join(''.join(out).split())


def deja_fait():
    if not os.path.exists(SORTIE):
        return set()
    with open(SORTIE, encoding='utf-8') as f:
        return set(r['insee'] for r in csv.DictReader(f))


def main():
    if not os.path.exists(ENTREE):
        print('%s manquant — lance d\'abord sonde-gentiles.py' % ENTREE)
        return 1

    with open(ENTREE, encoding='utf-8') as f:
        toutes = [r for r in csv.DictReader(f) if '|' not in r['titre']]
    fait = deja_fait()
    restantes = [r for r in toutes if r['insee'] not in fait]

    print('%d communes au total, %d deja faites, %d a faire'
          % (len(toutes), len(fait), len(restantes)))
    if not restantes:
        print('rien a faire.')
        return 0
    print('environ %d requetes. Tu peux interrompre et relancer a tout moment.\n'
          % ((len(restantes) + LOT - 1) // LOT), flush=True)

    neuf = not os.path.exists(SORTIE)
    octets = trouves = traites = 0
    debut = time.time()

    with open(SORTIE, 'a', encoding='utf-8', newline='') as sortie:
        w = csv.DictWriter(sortie, fieldnames=['insee', 'titre', 'brut'])
        if neuf:
            w.writeheader()

        for depart in range(0, len(restantes), LOT):
            lot = restantes[depart:depart + LOT]
            attendu = dict((r['titre'], r['insee']) for r in lot)

            try:
                d, taille = poster({
                    'action': 'query', 'format': 'json', 'formatversion': '2',
                    'prop': 'revisions', 'rvprop': 'content', 'rvslots': 'main',
                    'redirects': '1', 'maxlag': '5',
                    'titles': '|'.join(r['titre'] for r in lot),
                })
            except Exception as e:
                print('\nARRET sur %s : %s' % (lot[0]['titre'], e))
                print('Relance le script : il reprendra ici.')
                break
            octets += taille

            q = d.get('query', {})
            # Wikipedia renormalise et suit les redirections : il faut savoir
            # a quel titre demande correspond chaque page rendue.
            vers_demande = {}
            for chaine in ('normalized', 'redirects'):
                for e in q.get(chaine, []):
                    vers_demande[e['to']] = vers_demande.get(e['from'], e['from'])

            for page in q.get('pages', []):
                titre = page.get('title', '')
                demande = titre
                for _ in range(4):
                    if demande in attendu:
                        break
                    if demande in vers_demande:
                        demande = vers_demande[demande]
                    else:
                        break
                insee = attendu.get(demande)
                if not insee:
                    continue
                texte = ''
                try:
                    texte = page['revisions'][0]['slots']['main']['content']
                except (KeyError, IndexError):
                    pass
                v = valeur_du_champ(texte) if texte else ''
                if v:
                    trouves += 1
                w.writerow({'insee': insee, 'titre': demande, 'brut': v})
                traites += 1
            sortie.flush()

            ecoule = max(time.time() - debut, 1)
            print('  %6d/%d   %5d avec valeur   %5.0f Mo   %4.0f/s'
                  % (traites, len(restantes), trouves, octets / 1e6,
                     traites / ecoule), flush=True)
            time.sleep(.2)

    print('\n' + '=' * 60)
    print('  ecrit dans %s' % SORTIE)
    print('  %d communes traitees cette fois, %d avec une valeur' % (traites, trouves))
    print('  %.0f Mo telecharges' % (octets / 1e6))
    print('=' * 60)
    return 0


if __name__ == '__main__':
    sys.exit(main())
