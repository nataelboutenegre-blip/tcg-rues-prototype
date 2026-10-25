# -*- coding: utf-8 -*-
u"""
Habille le serveur Discord de TerraFront (23 octobre 2026).

  python3 _discord/habiller-discord.py               -> SIMULATION : affiche ce qui serait fait, ne touche à rien
  python3 _discord/habiller-discord.py --pour-de-vrai -> applique

Le jeton du bot se lit dans ~/.terrafront-bot (hors du dépôt, qui est public).
Ne jamais mettre le jeton dans ce dossier ni dans un commit.

Ce que fait le script (sans jamais rien supprimer) :
  1. téléverse les emojis de _discord/emojis/ qui n'existent pas encore ;
  2. crée les rôles qui manquent, avec leurs couleurs, dans l'ordre ;
  3. crée les catégories, renomme les salons existants, crée ceux qui manquent,
     pose les sujets et la lecture seule ;
  4. poste et épingle les messages d'accueil, de règles et du guide (une seule
     fois : s'il les a déjà postés, il ne recommence pas ; si leur texte a
     changé dans messages.json, il modifie le message déjà posté).
Rejouable : un deuxième passage ne refait que ce qui manque.
"""
import base64, json, os, subprocess, sys, time

ICI = os.path.dirname(os.path.abspath(__file__))
VRAI = '--pour-de-vrai' in sys.argv
API = 'https://discord.com/api/v10'
JETON_FICHIER = os.path.expanduser('~/.terrafront-bot')

def lire_jeton():
    if not os.path.exists(JETON_FICHIER):
        sys.exit(u"Jeton introuvable : crée le fichier %s avec le jeton du bot dedans (une seule ligne)." % JETON_FICHIER)
    j = open(JETON_FICHIER).read().strip()
    if len(j) < 50: sys.exit(u"Le fichier %s ne ressemble pas à un jeton de bot." % JETON_FICHIER)
    return j
JETON = lire_jeton()

def appel(methode, chemin, corps=None, fatal=True):
    """Appel à l'API Discord par curl (les certificats du Mac, sans module à installer)."""
    for essai in range(6):
        cmd = ['curl', '-sS', '-X', methode, API + chemin,
               '-H', 'Authorization: Bot ' + JETON, '-H', 'User-Agent: TerraFrontBot (terrafront.fr, 1)',
               '-w', '\n%{http_code}']
        entree = None
        if corps is not None:
            cmd += ['-H', 'Content-Type: application/json', '--data-binary', '@-']
            entree = json.dumps(corps).encode('utf-8')
        elif methode in ('PUT', 'POST', 'PATCH'):
            cmd += ['-H', 'Content-Length: 0']
        r = subprocess.run(cmd, input=entree, capture_output=True)
        if r.returncode != 0:
            sys.exit(u'curl a échoué : ' + r.stderr.decode('utf-8', 'replace'))
        texte, _, code = r.stdout.decode('utf-8', 'replace').rpartition('\n')
        code = int(code or 0)
        if code == 429:
            attente = 2.0
            try: attente = float(json.loads(texte).get('retry_after', 2)) + 0.3
            except Exception: pass
            time.sleep(attente); continue
        if code >= 400:
            msg = u'Discord a refusé %s %s (%d) : %s' % (methode, chemin, code, texte[:400])
            if fatal: sys.exit(msg)
            print(u'  (ignoré) ' + msg)
            return None
        time.sleep(0.35)   # rester poli avec les limites de Discord
        return json.loads(texte) if texte.strip() else None
    sys.exit(u'Discord limite trop les appels : réessaie dans une minute.')

def dire(x): print(x)
def faire(texte, fn):
    dire(('  FAIT   ' if VRAI else '  SIMULÉ ') + texte)
    return fn() if VRAI else None

# ------------------------------------------------------------------ le serveur
moi = appel('GET', '/users/@me')
serveurs = appel('GET', '/users/@me/guilds')
if len(serveurs) != 1:
    sys.exit(u"Le bot est sur %d serveurs : il doit être seulement sur celui de TerraFront." % len(serveurs))
G = serveurs[0]['id']
dire(u'Serveur : %s · bot : %s · %s' % (serveurs[0]['name'], moi['username'], 'POUR DE VRAI' if VRAI else 'SIMULATION (rien ne change)'))

roles = appel('GET', '/guilds/%s/roles' % G)
salons = appel('GET', '/guilds/%s/channels' % G)
emojis = appel('GET', '/guilds/%s/emojis' % G)
EVERYONE = G   # le rôle @everyone a l'identifiant du serveur

# ------------------------------------------------------------------ 1. emojis
dire(u'\n1. Emojis')
noms_emojis = {e['name']: e['id'] for e in emojis}
dossier = os.path.join(ICI, 'emojis')
for f in sorted(os.listdir(dossier)):
    if not f.endswith('.png'): continue
    nom = f[:-4]
    if nom in noms_emojis: dire(u'  déjà là  :%s:' % nom); continue
    data = 'data:image/png;base64,' + base64.b64encode(open(os.path.join(dossier, f), 'rb').read()).decode()
    e = faire(u':%s:' % nom, lambda: appel('POST', '/guilds/%s/emojis' % G, {'name': nom, 'image': data}))
    if e: noms_emojis[nom] = e['id']

# ------------------------------------------------------------------ 2. rôles
dire(u'\n2. Rôles')
ROLES = [  # du plus haut au plus bas
    (u'👑 Fondateur', 0xF0B429, True), (u'🛡️ Modération', 0x2F7CF6, True),
    (u'🏆 Champion · Saison 1', 0xFFD36B, True), (u'🎖️ Distinction · Saison 1', 0xC29BFF, False),
    (u'🎩 Le Parrain', 0xE8C26A, False), (u'🏅 OG', 0x8FF3FF, False),
    (u'🃏 Terra', 0x22A06B, False), (u'⚔️ Front', 0xE5484D, False),
    (u'🔔 Nouveautés', 0xA9BCD4, False), (u'📍 Commune du jour', 0xA9BCD4, False),
]
par_nom = {r['name']: r for r in roles}
for nom, couleur, separe in ROLES:
    if nom in par_nom: dire(u'  déjà là  %s' % nom); continue
    r = faire(u'%s (#%06X)' % (nom, couleur), lambda: appel('POST', '/guilds/%s/roles' % G,
              {'name': nom, 'color': couleur, 'hoist': separe, 'mentionable': nom in (u'🔔 Nouveautés', u'📍 Commune du jour')}))
    if r: par_nom[nom] = r
if VRAI:
    # ordre : juste sous le rôle le plus haut du bot
    roles = appel('GET', '/guilds/%s/roles' % G)
    membre = appel('GET', '/guilds/%s/members/%s' % (G, moi['id']))
    pos_bot = max([r['position'] for r in roles if r['id'] in membre['roles']] or [1])
    nos = [par_nom[n]['id'] for n, _, _ in ROLES if n in par_nom]
    if pos_bot <= len(nos):
        dire(u"  ATTENTION : monte le rôle du bot tout en haut (Paramètres › Rôles), puis relance pour ranger les rôles.")
    else:
        appel('PATCH', '/guilds/%s/roles' % G, [{'id': rid, 'position': pos_bot - 1 - i} for i, rid in enumerate(nos)])
        dire(u'  rôles rangés dans l\'ordre')

# ------------------------------------------------------------------ 3. salons
dire(u'\n3. Catégories et salons')
LECTURE = 0x800        # envoyer des messages
VOIR_ECRIRE = 0x400 | 0x800 | 0x2000 | 0x10000   # voir, écrire, gérer les messages, lire l'historique
# (catégorie, [(cle de reconnaissance d'un salon existant ou None, nom, sujet, lecture seule, vocal)])
PLAN = [
 (u'👋 Bienvenue', [
   (None, u'👋│bienvenue', u'Bienvenue ! Lis les règles, choisis tes rôles et viens jouer sur terrafront.fr 🗺️', True, False),
   (None, u'📜│règles', u'Les règles du serveur et du jeu. À lire avant de poster.', True, False),
   (None, u'📖│guide-du-jeu', u'Terra, Front, raretés, énergie : tout le jeu en un message.', True, False)]),
 (u'📣 Infos', [
   (None, u'📣│annonces', u'Lancements de saison, événements, maintenances. Rien d\'autre.', True, False),
   (u'nouveautes', u'🆕│nouveautés', u'Ce qui a changé dans le jeu, un message par jour.', True, False),
   (None, u'🏆│palmarès', u'Podiums, distinctions et records de chaque saison.', True, False)]),
 (u'🗺️ Le jeu', [
   (u'discussion', u'💬│discussion', u'On parle de TerraFront, de nos communes et du reste 🇫🇷', False, False),
   (None, u'🃏│tirages', u'Tes plus beaux tirages en capture d\'écran. Une légendaire ? Une Aurore ? C\'est ici ✨', False, False),
   (None, u'⚔️│front', u'Sièges, conquêtes, alliances et rivalités du Front.', False, False),
   (u'echanges', u'🤝│échanges', u'Cherche, propose, échange tes doublons. Format : « Je cherche… / Je donne… »', False, False)]),
 (u'🎯 Mini-jeux', [
   (u'commune-du-jour', u'📍│commune-du-jour', u'Partage ton score. Pas de spoil : la réponse entre || barres || !', False, False),
   (u'radar', u'📡│radar-et-rafale', u'Défis, records et revanches au Radar et à la Rafale.', False, False)]),
 (u'🛠️ Aide', [
   (None, u'❓│questions', u'Une règle pas claire ? Demande ici, on répond vite.', False, False),
   (u'bugs', u'🐛│bugs', u'Décris le bug + une capture ou une vidéo. Téléphone ou ordinateur ?', False, False),
   (u'idees', u'💡│idées', u'Une idée pour le jeu ? Les meilleures finissent dans TerraFront 😉', False, False)]),
 (u'🔊 Vocal', [
   (u'general', u'🔊│QG', None, False, True)]),
]
import unicodedata
def cle(nom):
    s = unicodedata.normalize('NFD', nom.lower())
    s = ''.join(c for c in s if c.isalnum() or c == '-')
    return s.strip('-')
existants = [s for s in salons if s['type'] in (0, 2, 5)]
categories = {s['name']: s for s in salons if s['type'] == 4}
IDS = {}   # nom final -> id
ordre = []
pos_cat = 0
for nom_cat, liste in PLAN:
    cat = categories.get(nom_cat)
    if not cat:
        cat = faire(u'catégorie %s' % nom_cat, lambda: appel('POST', '/guilds/%s/channels' % G, {'name': nom_cat, 'type': 4}))
    else: dire(u'  déjà là  catégorie %s' % nom_cat)
    if cat: ordre.append({'id': cat['id'], 'position': pos_cat})
    pos_cat += 1
    for i, (reco, nom, sujet, lecture, vocal) in enumerate(liste):
        s = next((x for x in existants if x['name'] == nom), None)
        if not s and reco:
            s = next((x for x in existants if cle(x['name']).endswith(reco) or cle(x['name']) == reco), None)
        corps = {'name': nom, 'parent_id': cat['id'] if cat else None}
        if sujet is not None: corps['topic'] = sujet
        if s:
            change = s['name'] != nom or (sujet is not None and s.get('topic') != sujet) or s.get('parent_id') != (cat['id'] if cat else None)
            if change: faire(u'%s → %s' % (s['name'], nom), lambda: appel('PATCH', '/channels/%s' % s['id'], corps))
            else: dire(u'  déjà là  %s' % nom)
        else:
            corps['type'] = 2 if vocal else 0
            s = faire(u'nouveau salon %s' % nom, lambda: appel('POST', '/guilds/%s/channels' % G, corps))
        if s:
            IDS[nom] = s['id']
            ordre.append({'id': s['id'], 'position': i})
            if lecture:
                ow = next((o for o in s.get('permission_overwrites', []) if o['id'] == EVERYONE), None)
                deny = int(ow['deny']) if ow else 0
                allow = int(ow['allow']) if ow else 0
                if not deny & LECTURE:
                    faire(u'   lecture seule sur %s' % nom, lambda: appel('PUT', '/channels/%s/permissions/%s' % (s['id'], EVERYONE),
                          {'type': 0, 'allow': str(allow & ~LECTURE), 'deny': str(deny | LECTURE)}))
                # le bot garde le droit d'écrire et d'épingler (seulement s'il manque)
                if not any(o['id'] == moi['id'] for o in s.get('permission_overwrites', [])): faire(u'   le bot peut écrire dans %s' % nom, lambda: appel('PUT', '/channels/%s/permissions/%s' % (s['id'], moi['id']),
                      {'type': 1, 'allow': str(VOIR_ECRIRE), 'deny': '0'}))
if VRAI and ordre:
    appel('PATCH', '/guilds/%s/channels' % G, ordre, fatal=False)
    dire(u'  ordre des salons envoyé (si un « ignoré » s\'affiche au-dessus, range-les à la main : rien de grave)')
vieilles = [c['name'] for c in salons if c['type'] == 4 and c['name'] not in [p[0] for p in PLAN]]
if vieilles: dire(u'  (les anciennes catégories %s resteront vides : supprime-les à la main si tu veux)' % ', '.join(vieilles))

# ------------------------------------------------------------------ 4. messages
dire(u'\n4. Messages')
MESSAGES = json.load(open(os.path.join(ICI, 'messages.json'), encoding='utf-8'))
def preparer(texte):
    for nom, eid in noms_emojis.items():
        texte = texte.replace(':%s:' % nom, '<:%s:%s>' % (nom, eid))
    for nom, cid in IDS.items():
        texte = texte.replace(nom, '<#%s>' % cid)
    return texte
for m in MESSAGES:
    cid = IDS.get(m['salon'])
    if not cid:
        dire(u'  SIMULÉ  « %s » dans %s (le salon sera créé avant)' % (m['titre'], m['salon'])); continue
    deja = appel('GET', '/channels/%s/messages?limit=50' % cid) if cid else []
    ancien = next((x for x in (deja or []) if x['author']['id'] == moi['id'] and m['repere'] in x.get('content', '')), None)
    if ancien:
        # 25 octobre : le texte a changé dans messages.json -> on modifie le message déjà posté
        nouveau = preparer(m['texte'])
        if ancien.get('content') != nouveau:
            if len(nouveau) > 2000: sys.exit(u'Message « %s » trop long (%d caractères)' % (m['titre'], len(nouveau)))
            faire(u'mettre à jour « %s » (texte modifié)' % m['titre'], lambda: appel('PATCH', '/channels/%s/messages/%s' % (cid, ancien['id']),
                  {'content': nouveau, 'allowed_mentions': {'parse': []}}))
        if not ancien.get('pinned'):
            ok = faire(u'épingler « %s » (déjà posté)' % m['titre'], lambda: appel('PUT', '/channels/%s/pins/%s' % (cid, ancien['id']), fatal=False) is not None or True)
        else:
            dire(u'  déjà posté et épinglé  « %s »' % m['titre'])
        continue
    contenu = preparer(m['texte'])
    if len(contenu) > 2000: sys.exit(u'Message « %s » trop long (%d caractères)' % (m['titre'], len(contenu)))
    def poster(cid=cid, contenu=contenu):
        msg = appel('POST', '/channels/%s/messages' % cid, {'content': contenu, 'allowed_mentions': {'parse': []}})
        appel('PUT', '/channels/%s/pins/%s' % (cid, msg['id']), fatal=False)
        return msg
    faire(u'« %s » dans %s, épinglé' % (m['titre'], m['salon']), poster)

dire(u'\nTerminé.' if VRAI else u'\nSimulation terminée : rien n\'a changé. Si tout te va : python3 _discord/habiller-discord.py --pour-de-vrai')
