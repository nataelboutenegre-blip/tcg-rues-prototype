#!/usr/bin/env python3
# ---------------------------------------------------------------------------
#  TerraFront — sonde de couverture du gentile
#
#  Ne modifie rien, n'ecrit que deux fichiers a cote de lui. Objectif unique :
#  savoir si le champ "Gentile" de l'infobox de Wikipedia FR est assez bien
#  rempli pour valoir un import. On mesure avant d'investir.
#
#  Etape 1 : Wikidata donne la correspondance code INSEE -> titre d'article.
#            Mis en cache dans communes-wikipedia.csv (une seule fois).
#  Etape 2 : 60 communes tirees au hasard, on lit la premiere section de
#            chaque article et on cherche le champ dans l'infobox.
#
#  Usage :  python3 sonde-gentiles.py
# ---------------------------------------------------------------------------
import csv
import json
import os
import random
import re
import sys
import time
import urllib.parse
import urllib.request

UA = 'TerraFront/1.0 (terrafront.fr) sonde-gentiles'
CACHE = 'communes-wikipedia.csv'
ECHANTILLON = 60

# Le champ s'ecrit gentile, gentilé, Gentilé... et la valeur peut contenir
# des liens, des balises, une note. On prend brut, on nettoiera plus tard.
RE_GENTILE = re.compile(r'\|\s*[Gg]entil[ée]?\s*=\s*([^\n|}]*)')


def lire(url, essais=3):
    for n in range(essais):
        try:
            req = urllib.request.Request(url, headers={'User-Agent': UA})
            with urllib.request.urlopen(req, timeout=90) as r:
                return r.read().decode('utf-8')
        except Exception as e:
            if n == essais - 1:
                raise
            print('    reessai (%s)' % e, flush=True)
            time.sleep(2 + 2 * n)


# Les codes de departement, qui servent de prefixe pour decouper la requete.
# Wikidata coupe le flux au bout de 60 secondes : une requete sur les 34 739
# communes rend un JSON tronque. Une centaine de petites requetes passent.
PREFIXES = (['%02d' % i for i in range(1, 20)] + ['2A', '2B']
            + ['%02d' % i for i in range(21, 96)] + ['97'])


def un_prefixe(p):
    """Les communes dont le code INSEE commence par p."""
    requete = ('SELECT ?insee ?art WHERE { '
               '?c wdt:P374 ?insee . '
               '?art schema:about ?c ; schema:isPartOf <https://fr.wikipedia.org/> . '
               'FILTER(STRSTARTS(?insee, "%s")) }' % p)
    url = ('https://query.wikidata.org/sparql?format=json&query='
           + urllib.parse.quote(requete))
    brut = lire(url)
    donnees = json.loads(brut)['results']['bindings']
    out = []
    for b in donnees:
        insee = b['insee']['value'].strip()
        if len(insee) != 5:          # P374 sert aussi aux departements
            continue
        titre = urllib.parse.unquote(b['art']['value'].rsplit('/', 1)[-1])
        out.append({'insee': insee, 'titre': titre.replace('_', ' ')})
    return out


def correspondance():
    """code INSEE -> titre de l'article fr.wikipedia, via Wikidata.

    Ecrit au fur et a mesure : si ca coupe, relancer reprend ou ca s'est
    arrete. Le fichier fait foi, pas la memoire.
    """
    deja, faits = [], set()
    if os.path.exists(CACHE):
        with open(CACHE, encoding='utf-8') as f:
            deja = list(csv.DictReader(f))
        faits = set(r['insee'][:2] for r in deja)
        print('cache : %d communes deja recuperees' % len(deja))

    restants = [p for p in PREFIXES if p not in faits]
    if restants:
        print('interrogation de Wikidata, %d departements a faire...' % len(restants),
              flush=True)
        neuf = not deja
        with open(CACHE, 'a', encoding='utf-8', newline='') as f:
            w = csv.DictWriter(f, fieldnames=['insee', 'titre'])
            if neuf:
                w.writeheader()
            for p in restants:
                try:
                    lot = un_prefixe(p)
                except Exception as e:
                    print('  %-3s ECHEC (%s) — relance le script pour reprendre' % (p, e))
                    break
                w.writerows(lot)
                f.flush()
                deja.extend(lot)
                print('  %-3s %4d communes' % (p, len(lot)), flush=True)
                time.sleep(.4)

    print('correspondance : %d communes dans %s' % (len(deja), CACHE))
    return deja


def gentile_de(titre):
    """Renvoie la valeur brute du champ, ou None."""
    url = ('https://fr.wikipedia.org/w/api.php?action=parse&format=json'
           '&prop=wikitext&section=0&redirects=1&page='
           + urllib.parse.quote(titre))
    d = json.loads(lire(url))
    if 'error' in d:
        return None
    texte = d.get('parse', {}).get('wikitext', {}).get('*', '')
    m = RE_GENTILE.search(texte)
    if not m:
        return None
    v = m.group(1).strip()
    return v if v else None


def main():
    lignes = correspondance()
    if not lignes:
        print('aucune correspondance : la requete Wikidata a echoue.')
        return 1

    random.seed()
    echantillon = random.sample(lignes, min(ECHANTILLON, len(lignes)))

    trouves, vides = [], []
    print('\nsondage de %d communes tirees au hasard :\n' % len(echantillon), flush=True)
    for i, r in enumerate(echantillon, 1):
        try:
            v = gentile_de(r['titre'])
        except Exception as e:
            v = None
            print('  %2d. %-38s ERREUR %s' % (i, r['titre'][:38], e))
            time.sleep(.2)
            continue
        if v:
            trouves.append((r['insee'], r['titre'], v))
            print('  %2d. %-38s %s' % (i, r['titre'][:38], v[:60]))
        else:
            vides.append((r['insee'], r['titre']))
            print('  %2d. %-38s --' % (i, r['titre'][:38]))
        time.sleep(.15)

    n = len(echantillon)
    print('\n' + '=' * 62)
    print('  champ rempli : %d / %d  =  %.0f %%' % (len(trouves), n, 100 * len(trouves) / n))
    print('  extrapole sur 34 739 communes : environ %d gentiles'
          % round(34739 * len(trouves) / n))
    print('=' * 62)
    if vides:
        print('\nsans gentile : ' + ', '.join(t for _, t in vides[:12]))
    return 0


if __name__ == '__main__':
    sys.exit(main())
