# -*- coding: utf-8 -*-
u"""
TerraFront — cartes Aurore : télécharge les 233 photos et leurs crédits.

Ce script tourne dans TON Terminal (le jeu de Claude ne peut pas joindre
Wikimedia). Il ne demande aucune clé : les images vont dans le dépôt, à côté
du jeu, et partent en ligne avec le prochain push.

    cd ~/Code/tcg-rues-prototype
    python3 _sql/aurore-telecharger.py

Ce qu'il fait :
  - lit _sql/aurore-selection.csv (une photo par commune : la première quand
    une commune en a plusieurs) ;
  - demande à Commons, par paquets de 50, l'adresse d'une version de 600 px
    de large, l'auteur et la licence de chaque photo ;
  - enregistre les images dans aurore/<code INSEE>.jpg ;
  - écrit data/aurore.json : le crédit de chaque photo, que le jeu affiche
    sous la carte (obligatoire pour les licences CC BY et CC BY-SA).

  - VÉRIFIE chaque image (vraie image, au moins 400 px de côté) ;
  - écrit _sql/s2-18-aurore-liste.sql : la liste des communes Aurore côté
    serveur devient EXACTEMENT celle des images vérifiées. Le tirage ne peut
    donc jamais donner une Aurore sans photo.

Rejouable : une image déjà là et valide n'est pas retéléchargée. Une photo
sans auteur identifiable alors que sa licence en exige un est ÉCARTÉE et
listée à la fin, jamais devinée.

Après le push, pour vérifier que le site sert bien toutes les images :
    python3 _sql/aurore-telecharger.py --en-ligne
"""
import csv, io, json, os, re, subprocess, sys, time, urllib.error, urllib.parse, urllib.request

ICI = os.path.dirname(os.path.abspath(__file__))
RACINE = os.path.dirname(ICI)
DOSSIER = os.path.join(RACINE, 'aurore')
SORTIE = os.path.join(RACINE, 'data', 'aurore.json')
UA = 'TerraFront/1.0 (https://terrafront.fr; contact@terrafront.fr) python-urllib'
LARGEUR = 600
LISTE_SQL = os.path.join(ICI, 's2-18-aurore-liste.sql')
SITE = 'https://terrafront.fr/'
# Le champ Artist de Commons contient parfois une phrase entière (« This
# picture belongs to… », « No machine-readable author provided… »). Relu à la
# main le 11 octobre 2026 : le nom à afficher pour ces photos-là.
CORRECTIONS_AUTEURS = {
    '31582': 'Pinpin', '33122': 'MagnetiK', '34255': "Archives départementales de l'Hérault",
    '37018': 'Céréales Killer', '45191': 'Caesius', '47157': 'Dimitri2401', '57206': 'Aimelaime',
    '59268': 'Berthe Delannoy', '60471': 'Noyon', '64256': 'Patrick.charpiat',
    '67137': 'Ralph Hammann', '67372': 'Ralph Hammann', '67471': 'Ralph Hammann',
    '69202': 'Xavier Caré', '83130': 'Peter Potrowl', '87048': 'Sylvain Crouzillat (croucrou)',
}
MIN_COTE = 400        # en dessous, l'image serait floue sur la grande carte
MIN_OCTETS = 15000    # une « image » plus petite est une page d'erreur ou un pixel


def dimensions(octets):
    """(largeur, hauteur) d'un JPEG ou d'un PNG, None si ce n'en est pas un."""
    if octets[:8] == b'\x89PNG\r\n\x1a\n':
        return int.from_bytes(octets[16:20], 'big'), int.from_bytes(octets[20:24], 'big')
    if octets[:3] != b'\xff\xd8\xff':
        return None
    i = 2
    while i + 9 < len(octets):
        if octets[i] != 0xFF:
            i += 1
            continue
        m = octets[i + 1]
        if m in (0xC0, 0xC1, 0xC2, 0xC3, 0xC5, 0xC6, 0xC7, 0xC9, 0xCA, 0xCB, 0xCD, 0xCE, 0xCF):
            return int.from_bytes(octets[i + 7:i + 9], 'big'), int.from_bytes(octets[i + 5:i + 7], 'big')
        if m in (0xD8, 0x01) or 0xD0 <= m <= 0xD7:
            i += 2
            continue
        i += 2 + int.from_bytes(octets[i + 2:i + 4], 'big')
    return None


def reduire(chemin):
    """Commons ne sert plus que des tailles standard (960 px au lieu des 600
    demandés) : on ramène l'image à 600 px de large, JPEG qualité 80.
    Sans ça, 74 Mo d'images ; avec, environ 21 Mo."""
    try:
        from PIL import Image, ImageOps
    except ImportError:
        if sys.platform == 'darwin':   # sips est livré avec macOS
            subprocess.run(['sips', '--resampleWidth', str(LARGEUR), '-s', 'format', 'jpeg',
                            '-s', 'formatOptions', '80', chemin], capture_output=True)
        return
    im = ImageOps.exif_transpose(Image.open(chemin)).convert('RGB')
    if im.width > LARGEUR:
        im = im.resize((LARGEUR, round(im.height * LARGEUR / im.width)), Image.LANCZOS)
    im.save(chemin, 'JPEG', quality=80, optimize=True, progressive=True)


def probleme_image(octets):
    """None si l'image est bonne, sinon la raison."""
    if len(octets) < MIN_OCTETS:
        return 'fichier trop petit (%d octets)' % len(octets)
    d = dimensions(octets)
    if not d:
        return "ce n'est pas une image JPEG ou PNG"
    if min(d) < MIN_COTE:
        return 'trop petite (%d × %d px)' % d
    return None


def en_ligne():
    """Vérifie, après le push, que le site sert chaque image de data/aurore.json."""
    with io.open(SORTIE, encoding='utf-8') as f:
        codes = sorted(json.load(f)['cartes'])
    manquantes = []
    for n, code in enumerate(codes, 1):
        try:
            octets = http(SITE + 'aurore/%s.jpg?v=verif' % code, brut=True, essais=2)
            raison = probleme_image(octets)
        except Exception as e:
            raison = str(e)
        if raison:
            manquantes.append((code, raison))
        if n % 50 == 0:
            print('   %d / %d' % (n, len(codes)))
    if manquantes:
        print('%d image(s) NON servie(s) par le site :' % len(manquantes))
        for code, raison in manquantes:
            print('   %s — %s' % (code, raison))
    else:
        print('OK : les %d images Aurore sont en ligne et valides.' % len(codes))


def http(url, donnees=None, essais=4, brut=False):
    for n in range(1, essais + 1):
        try:
            req = urllib.request.Request(url, data=donnees, headers={'User-Agent': UA})
            with urllib.request.urlopen(req, timeout=60) as r:
                d = r.read()
                return d if brut else json.loads(d.decode('utf-8'))
        except urllib.error.HTTPError as e:
            if e.code in (403, 404) or n == essais:
                raise
            time.sleep(3 * n)
        except Exception:
            if n == essais:
                raise
            time.sleep(3 * n)


def nom_auteur(brut):
    """Le champ Artist de Commons est du HTML (même règle que monuments-2-images.py)."""
    if not brut:
        return ''

    def du_lien(m):
        attributs, texte = m.group(1), m.group(2)
        texte = re.sub(r'<[^>]+>', ' ', texte).strip()
        if texte:
            return texte
        titre = re.search(r'title="([^"]*)"', attributs)
        if titre and titre.group(1).strip():
            t = titre.group(1).strip()
            if t.lower().split(':', 1)[0] in ('file', 'image', 'category', 'fichier'):
                return ''
            return t.split(':', 1)[1] if t.lower().startswith('user:') else t
        adresse = re.search(r'href="([^"]*)"', attributs)
        if adresse and 'User:' in adresse.group(1):
            return urllib.parse.unquote(adresse.group(1).split('User:')[-1]).replace('_', ' ')
        return ''

    s = re.sub(r'<a\b([^>]*)>(.*?)</a>', du_lien, brut, flags=re.S | re.I)
    s = re.sub(r'<[^>]+>', ' ', s)
    s = s.replace('&amp;', '&').replace('&#39;', "'").replace('&quot;', '"')
    return re.sub(r'\s+', ' ', s).strip()


def main():
    with io.open(os.path.join(ICI, 'aurore-selection.csv'), encoding='utf-8') as f:
        lignes = list(csv.DictReader(f))
    choix = {}   # code -> fichier (la première photo de la commune)
    for r in lignes:
        choix.setdefault(r['code_insee'], r['fichier'])
    print('%d communes Aurore' % len(choix))
    os.makedirs(DOSSIER, exist_ok=True)

    # 1. adresses, auteurs, licences — par paquets de 50
    fichiers = sorted(set(choix.values()))
    infos = {}
    for i in range(0, len(fichiers), 50):
        paquet = fichiers[i:i + 50]
        corps = urllib.parse.urlencode({
            'action': 'query', 'format': 'json', 'prop': 'imageinfo',
            'iiprop': 'url|extmetadata', 'iiurlwidth': str(LARGEUR),
            'iiextmetadatafilter': 'Artist|Attribution|LicenseShortName|AttributionRequired',
            'titles': '|'.join('File:' + f for f in paquet)}).encode('utf-8')
        data = http('https://commons.wikimedia.org/w/api.php', donnees=corps)
        q = data.get('query', {}) or {}
        # Commons renvoie les titres « normalisés » (espaces, majuscule) : on
        # garde la correspondance pour retrouver le nom du CSV
        vers = {n['to']: n['from'] for n in q.get('normalized', []) or []}
        for page in (q.get('pages', {}) or {}).values():
            titre = vers.get(page.get('title', ''), page.get('title', ''))
            nom = titre[len('File:'):] if titre.startswith('File:') else titre
            ii = (page.get('imageinfo') or [{}])[0]
            meta = ii.get('extmetadata') or {}
            lire = lambda c: (meta.get(c, {}) or {}).get('value', '') or ''
            infos[nom] = {
                'url': ii.get('thumburl') or '',
                'page': ii.get('descriptionurl') or '',
                'auteur': nom_auteur(lire('Artist')) or nom_auteur(lire('Attribution')),
                'licence': re.sub(r'<[^>]+>', '', lire('LicenseShortName')).strip(),
                'libre': lire('AttributionRequired').strip().lower() == 'false',
            }
        print('   crédits %d / %d' % (min(i + 50, len(fichiers)), len(fichiers)))
        time.sleep(0.4)

    # 2. les images
    credits, ecartees = {}, []
    for n, (code, fichier) in enumerate(sorted(choix.items()), 1):
        inf = infos.get(fichier)
        if not inf or not inf['url']:
            ecartees.append((code, fichier, 'introuvable sur Commons'))
            continue
        if not inf['auteur'] and not inf['libre']:
            ecartees.append((code, fichier, "pas d'auteur identifiable (%s)" % (inf['licence'] or 'licence ?')))
            continue
        chemin = os.path.join(DOSSIER, code + '.jpg')
        if os.path.exists(chemin):
            with open(chemin, 'rb') as f:
                if probleme_image(f.read()):
                    os.remove(chemin)     # image abimee : on la retelecharge
        if not os.path.exists(chemin):
            try:
                octets = http(inf['url'], brut=True)
            except Exception as e:
                ecartees.append((code, fichier, 'téléchargement : %s' % e))
                continue
            raison = probleme_image(octets)
            if raison:
                ecartees.append((code, fichier, raison))
                continue
            # un PNG garde le nom .jpg : le navigateur lit le format, pas le nom
            with open(chemin, 'wb') as f:
                f.write(octets)
            reduire(chemin)
            time.sleep(0.25)
        credits[code] = {'a': CORRECTIONS_AUTEURS.get(code) or inf['auteur'] or 'Domaine public', 'l': inf['licence'], 's': inf['page']}
        if n % 25 == 0:
            print('   images %d / %d' % (n, len(choix)))

    # une image d'une commune qui n'est plus dans la liste ne doit pas trainer
    for x in os.listdir(DOSSIER):
        if x.endswith('.jpg') and x[:-4] not in credits:
            os.remove(os.path.join(DOSSIER, x))

    if len(credits) < 50:
        sys.exit('Seulement %d images valides : quelque chose ne va pas, rien n\'est écrit.' % len(credits))
    with io.open(SORTIE, 'w', encoding='utf-8') as f:
        json.dump({'v': 1, 'cartes': credits}, f, ensure_ascii=False, separators=(',', ':'), sort_keys=True)
    ecrire_liste_sql(sorted(credits))

    poids = sum(os.path.getsize(os.path.join(DOSSIER, x)) for x in os.listdir(DOSSIER))
    print('')
    print('%d images prêtes dans aurore/ (%.1f Mo), crédits dans data/aurore.json' % (len(credits), poids / 1e6))
    if ecartees:
        print('%d écartées :' % len(ecartees))
        for code, fichier, raison in ecartees:
            print('   %s  %s  — %s' % (code, fichier, raison))
    licences = {}
    for c in credits.values():
        licences[c['l']] = licences.get(c['l'], 0) + 1
    print('Licences : ' + ', '.join('%s ×%d' % kv for kv in sorted(licences.items(), key=lambda kv: -kv[1])))
    print('')
    print('Liste serveur écrite dans _sql/s2-18-aurore-liste.sql (%d communes).' % len(credits))


def ecrire_liste_sql(codes):
    valeurs = ',\n'.join('  ' + ', '.join("('%s')" % c for c in codes[i:i + 12]) for i in range(0, len(codes), 12))
    sql = '''-- s2-18 — Aurore : la liste du serveur = les communes dont la photo est vérifiée.
-- Écrit par _sql/aurore-telecharger.py, ne pas modifier à la main.
-- À passer APRÈS s2-17. Rejouable.
-- Contrôle attendu à la fin : %(n)d | %(n)d | 0

begin;
create temporary table aurore_photos (code text primary key) on commit drop;
insert into aurore_photos (code) values
%(valeurs)s;

-- une commune sans photo ne peut plus sortir en Aurore
delete from public.aurore_communes a where not exists (select 1 from aurore_photos p where p.code = a.code);
-- une commune avec photo qui manquait à la liste y entre
insert into public.aurore_communes (code)
select p.code from aurore_photos p where exists (select 1 from public.communes c where c.code = p.code)
on conflict (code) do nothing;

-- contrôle : %(n)d | %(n)d | 0
select (select count(*) from aurore_photos) as photos,
       (select count(*) from public.aurore_communes) as liste_serveur,
       (select count(*) from aurore_photos p where not exists (select 1 from public.aurore_communes a where a.code = p.code)) as photos_hors_liste;
commit;
''' % {'n': len(codes), 'valeurs': valeurs}
    with io.open(LISTE_SQL, 'w', encoding='utf-8') as f:
        f.write(sql)


if __name__ == '__main__':
    if '--en-ligne' in sys.argv:
        en_ligne()
    else:
        main()
