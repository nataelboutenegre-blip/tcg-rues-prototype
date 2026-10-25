# -*- coding: utf-8 -*-
u"""
Salons des clans sur le Discord de TerraFront (25 octobre 2026).

  python3 _discord/clans-discord.py               -> SIMULATION : affiche ce qui changerait, ne touche à rien
  python3 _discord/clans-discord.py --pour-de-vrai -> applique

Ce que fait le script, dans la catégorie « 🏰 Clans » :
  - le salon public « 🏰│recrutement-clans » (s'il manque) ;
  - pour chaque clan du jeu : un rôle « 🏰 [SIGLE] Nom » à la couleur du clan
    et un salon privé que seuls les membres du clan (et le bot) voient ;
  - donne le rôle aux membres du clan présents sur le Discord, et le RETIRE
    à ceux qui ont quitté le clan (sinon ils garderaient l'accès au salon).
  - le chef du clan reçoit « Gérer les permissions » sur SON salon : il peut y
    ajouter qui il veut (Modifier le salon › Permissions). Les personnes qu'il a
    ajoutées sont gardées quand le script repasse ; un ancien chef perd ce droit.
  - un clan dissous : son rôle est vidé (plus personne ne voit le salon) ;
    le salon reste, à supprimer à la main si tu veux.

La liste des clans vient de _discord/clans.json, à refaire avec
_discord/clans-discord.sql (dans Supabase) à chaque fois que les clans
changent. Ce fichier contient des pseudos : il n'est pas mis sur GitHub.

Un pseudo du jeu est reconnu comme dans donner-roles.py (majuscules, accents
et ponctuation ignorés ; _discord/correspondances.json pour les autres).
Le jeton du bot se lit dans ~/.terrafront-bot (hors du dépôt, qui est public).
Il faut « Server Members Intent » (déjà activé) et les droits « Gérer les
rôles » et « Gérer les salons » (le bot les a déjà pour habiller-discord.py).
"""
import json, os, subprocess, sys, time, unicodedata

ICI = os.path.dirname(os.path.abspath(__file__))
VRAI = '--pour-de-vrai' in sys.argv
API = 'https://discord.com/api/v10'
JETON_FICHIER = os.path.expanduser('~/.terrafront-bot')

CATEGORIE = u'🏰 Clans'
PUBLIC = u'🏰│recrutement-clans'
PUBLIC_SUJET = u"Tu cherches un clan ou des membres ? Présente-toi : sigle, nom du clan, ce que vous visez sur le Front. 6 membres au plus par clan."
PREFIXE_ROLE = u'🏰 ['
VOIR, ECRIRE, GERER_MSG, LIENS, FICHIERS, HISTORIQUE, REACTIONS = 0x400, 0x800, 0x2000, 0x4000, 0x8000, 0x10000, 0x40
DROITS_MEMBRE = VOIR | ECRIRE | LIENS | FICHIERS | HISTORIQUE | REACTIONS
DROITS_BOT = VOIR | ECRIRE | GERER_MSG | HISTORIQUE
GERER_PERMS = 0x10000000   # « Gérer les permissions » sur le salon : donné au chef du clan

def lire_jeton():
    if not os.path.exists(JETON_FICHIER):
        sys.exit(u"Jeton introuvable : crée le fichier %s avec le jeton du bot dedans (une seule ligne)." % JETON_FICHIER)
    j = open(JETON_FICHIER).read().strip()
    if len(j) < 50: sys.exit(u"Le fichier %s ne ressemble pas à un jeton de bot." % JETON_FICHIER)
    return j
JETON = lire_jeton()

def appel(methode, chemin, corps=None, fatal=True):
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
        time.sleep(0.35)
        return json.loads(texte) if texte.strip() else {}
    sys.exit(u'Discord limite trop les appels : réessaie dans une minute.')

def faire(texte, fn):
    print((u'  FAIT     ' if VRAI else u'  SIMULÉ   ') + texte)
    return fn() if VRAI else None

def cle(nom):
    s = unicodedata.normalize('NFD', (nom or '').lower())
    return ''.join(c for c in s if c.isalnum())

def nom_salon(clan):
    base = unicodedata.normalize('NFD', clan['nom'].lower())
    base = ''.join(c if c.isalnum() else '-' for c in base if not unicodedata.combining(c))
    base = '-'.join(x for x in base.split('-') if x)
    return u'🔒│%s-%s' % (clan['tag'].lower(), base)

# ------------------------------------------------------------------ les clans du jeu
fichier = os.path.join(ICI, 'clans.json')
if not os.path.exists(fichier):
    sys.exit(u"Fichier _discord/clans.json introuvable : lance _discord/clans-discord.sql dans Supabase et colle le résultat dedans.")
CLANS = json.load(open(fichier, encoding='utf-8'))
if isinstance(CLANS, dict): CLANS = CLANS.get('clans', [])
for c in CLANS:
    if not c.get('tag') or not c.get('nom'): sys.exit(u'clans.json : chaque clan doit avoir un « tag » et un « nom ».')
    c['membres'] = c.get('membres') or []

# ------------------------------------------------------------------ le serveur
moi = appel('GET', '/users/@me')
serveurs = appel('GET', '/users/@me/guilds')
if len(serveurs) != 1:
    sys.exit(u"Le bot est sur %d serveurs : il doit être seulement sur celui de TerraFront." % len(serveurs))
G = serveurs[0]['id']
EVERYONE = G
print(u'Serveur : %s · bot : %s · %s · %d clan(s) dans clans.json\n' % (serveurs[0]['name'], moi['username'],
      'POUR DE VRAI' if VRAI else 'SIMULATION (rien ne change)', len(CLANS)))

membres, apres = [], '0'
while True:
    page = appel('GET', '/guilds/%s/members?limit=1000&after=%s' % (G, apres), fatal=False)
    if page is None:
        sys.exit(u"Discord refuse la liste des membres : active « Server Members Intent » dans le portail développeur.")
    membres += [m for m in page if not m['user'].get('bot')]
    if len(page) < 1000: break
    apres = page[-1]['user']['id']
index = {}
for m in membres:
    u = m['user']
    for nom in (u.get('username'), u.get('global_name'), m.get('nick')):
        if nom: index.setdefault(cle(nom), set()).add(u['id'])
par_id = {m['user']['id']: m for m in membres}
corr_f = os.path.join(ICI, 'correspondances.json')
CORR = {cle(k): cle(v) for k, v in (json.load(open(corr_f, encoding='utf-8')).items() if os.path.exists(corr_f) else [])}
def trouver(pseudo):
    return list(index.get(CORR.get(cle(pseudo), cle(pseudo)), set()))

roles = appel('GET', '/guilds/%s/roles' % G)
salons = appel('GET', '/guilds/%s/channels' % G)

# ------------------------------------------------------------------ 1. catégorie et salon public
print(u'1. Catégorie et salon public')
cat = next((s for s in salons if s['type'] == 4 and s['name'] == CATEGORIE), None)
if cat: print(u'  déjà là  catégorie %s' % CATEGORIE)
else: cat = faire(u'catégorie %s' % CATEGORIE, lambda: appel('POST', '/guilds/%s/channels' % G, {'name': CATEGORIE, 'type': 4}))
CAT_ID = cat['id'] if cat else None
pub = next((s for s in salons if s['type'] == 0 and (s['name'] == PUBLIC or cle(s['name']).endswith('recrutementclans'))), None)
if pub: print(u'  déjà là  %s' % pub['name'])
else: faire(u'salon public %s' % PUBLIC, lambda: appel('POST', '/guilds/%s/channels' % G,
            {'name': PUBLIC, 'type': 0, 'topic': PUBLIC_SUJET, 'parent_id': CAT_ID}))

# ------------------------------------------------------------------ 2. chaque clan
print(u'\n2. Les clans')
introuvables = []
tags = set()
for clan in CLANS:
    tag = clan['tag']; tags.add(tag)
    nom_role = u'%s%s] %s' % (PREFIXE_ROLE, tag, clan['nom'])
    couleur = int(str(clan.get('couleur') or '#8E9AAF').lstrip('#'), 16)
    print(u'\n  [%s] %s · %d membre(s) dans le jeu' % (tag, clan['nom'], len(clan['membres'])))

    # le rôle
    role = next((r for r in roles if r['name'].startswith(u'%s%s]' % (PREFIXE_ROLE, tag))), None)
    if role:
        if role['name'] != nom_role or role.get('color') != couleur:
            faire(u'rôle renommé ou recoloré : %s' % nom_role, lambda: appel('PATCH', '/guilds/%s/roles/%s' % (G, role['id']),
                  {'name': nom_role, 'color': couleur}))
        else: print(u'  déjà là  rôle %s' % nom_role)
    else:
        role = faire(u'rôle %s (#%06X)' % (nom_role, couleur), lambda: appel('POST', '/guilds/%s/roles' % G,
                     {'name': nom_role, 'color': couleur, 'hoist': False, 'mentionable': True}))
    rid = role['id'] if role else None

    # le salon privé
    marque = u'[%s]' % tag
    sujet = u'Salon privé du clan %s %s : seuls ses membres le voient.' % (marque, clan['nom'])
    salon = next((s for s in salons if s['type'] == 0 and s.get('parent_id') == CAT_ID and marque in (s.get('topic') or '')), None)
    # le chef du clan peut gérer les permissions de SON salon : il y ajoute qui il veut
    ids_chef = trouver(clan['chef']) if clan.get('chef') else []
    chef_id = ids_chef[0] if len(ids_chef) == 1 else None
    if clan.get('chef') and not chef_id: print(u'  ?        chef %s : pas trouvé sur le Discord, il ne pourra pas inviter' % clan['chef'])
    voulues = {EVERYONE: {'id': EVERYONE, 'type': 0, 'allow': '0', 'deny': str(VOIR)},
               moi['id']: {'id': moi['id'], 'type': 1, 'allow': str(DROITS_BOT), 'deny': '0'}}
    if rid: voulues[rid] = {'id': rid, 'type': 0, 'allow': str(DROITS_MEMBRE), 'deny': '0'}
    if chef_id: voulues[chef_id] = {'id': chef_id, 'type': 1, 'allow': str(DROITS_MEMBRE | GERER_PERMS), 'deny': '0'}
    # on garde les personnes que le chef a ajoutées ; un ancien chef perd seulement le droit d'inviter
    finales = dict(voulues)
    for o in (salon.get('permission_overwrites', []) if salon else []):
        if o['id'] in voulues: continue
        o = {'id': o['id'], 'type': o['type'], 'allow': str(o['allow']), 'deny': str(o['deny'])}
        if o['type'] == 1 and int(o['allow']) & GERER_PERMS:
            o['allow'] = str(int(o['allow']) & ~GERER_PERMS)
        finales[o['id']] = o
    perms = list(finales.values())
    if salon:
        avant = {(o['id'], int(o['type']), int(o['allow']), int(o['deny'])) for o in salon.get('permission_overwrites', [])}
        apres = {(o['id'], int(o['type']), int(o['allow']), int(o['deny'])) for o in perms}
        if salon['name'] != nom_salon(clan) or salon.get('topic') != sujet or avant != apres:
            faire(u'salon mis à jour : %s%s' % (nom_salon(clan), u' (chef : %s)' % par_id[chef_id]['user']['username'] if chef_id else ''),
                  lambda: appel('PATCH', '/channels/%s' % salon['id'],
                  {'name': nom_salon(clan), 'topic': sujet, 'permission_overwrites': perms}))
        else: print(u'  déjà là  salon %s' % salon['name'])
    else:
        nouveau = faire(u'salon privé %s%s' % (nom_salon(clan), u' (chef : %s)' % par_id[chef_id]['user']['username'] if chef_id else ''),
                        lambda: appel('POST', '/guilds/%s/channels' % G,
              {'name': nom_salon(clan), 'type': 0, 'topic': sujet, 'parent_id': CAT_ID, 'permission_overwrites': perms}))
        if nouveau and nouveau.get('id'):
            appel('POST', '/channels/%s/messages' % nouveau['id'], {'allowed_mentions': {'parse': []}, 'content':
                u"🏰 **Salon privé du clan %s %s**\n"
                u"Seuls les membres du clan le voient. Le bot donne l'accès aux membres du jeu qui sont sur le Discord.\n\n"
                u"**Chef du clan** : tu peux inviter quelqu'un d'autre ici. Clic droit sur le salon (ou appui long sur téléphone) "
                u"› Modifier le salon › Permissions › Ajouter des membres ou des rôles › choisis la personne › autorise « Voir le salon ».\n"
                u"Un membre qui n'est pas encore sur le Discord doit d'abord rejoindre le serveur." % (marque, clan['nom'])}, fatal=False)

    # les membres
    voulus = set()
    for p in clan['membres']:
        ids = trouver(p)
        if len(ids) == 1: voulus.add(ids[0])
        elif not ids: introuvables.append(p); print(u'  ?        %s : pas trouvé sur le Discord' % p)
        else: print(u'  ?        %s : plusieurs membres possibles, mets-le dans correspondances.json' % p)
    actuels = {m['user']['id'] for m in membres if rid and rid in m.get('roles', [])}
    for uid in sorted(voulus - actuels, key=lambda x: par_id[x]['user']['username']):
        faire(u'rôle donné à %s' % par_id[uid]['user']['username'],
              lambda: appel('PUT', '/guilds/%s/members/%s/roles/%s' % (G, uid, rid), fatal=False) if rid else None)
    for uid in sorted(actuels - voulus, key=lambda x: par_id[x]['user']['username']):
        faire(u'rôle retiré à %s (n\'est plus dans le clan)' % par_id[uid]['user']['username'],
              lambda: appel('DELETE', '/guilds/%s/members/%s/roles/%s' % (G, uid, rid), fatal=False))
    for uid in voulus & actuels: print(u'  déjà là  %s' % par_id[uid]['user']['username'])

# ------------------------------------------------------------------ 3. clans dissous
anciens = [r for r in roles if r['name'].startswith(PREFIXE_ROLE) and r['name'][len(PREFIXE_ROLE):].split(']')[0] not in tags]
if anciens:
    print(u'\n3. Clans qui n\'existent plus dans le jeu')
    for r in anciens:
        porteurs = [m for m in membres if r['id'] in m.get('roles', [])]
        for m in porteurs:
            faire(u'%s : rôle retiré à %s' % (r['name'], m['user']['username']),
                  lambda: appel('DELETE', '/guilds/%s/members/%s/roles/%s' % (G, m['user']['id'], r['id']), fatal=False))
        print(u'  %s : plus personne ne voit son salon. Supprime le salon et le rôle à la main si tu veux.' % r['name'])

if introuvables:
    print(u'\n%d joueur(s) de clan pas trouvé(s) sur le Discord : %s' % (len(introuvables), ', '.join(sorted(set(introuvables)))))
    print(u"Soit ils ne sont pas sur le Discord, soit ils s'appellent autrement : ajoute-les dans _discord/correspondances.json.")
if not VRAI: print(u'\nSimulation terminée : rien n\'a changé. Si tout te va : python3 _discord/clans-discord.py --pour-de-vrai')
else: print(u'\nTerminé. Relance le script quand des joueurs rejoignent ou quittent un clan.')
