# -*- coding: utf-8 -*-
u"""
Crée le salon vocal « 📺│carte-en-direct » sur le Discord de TerraFront (3 novembre 2026).

  python3 _discord/salon-carte-en-direct.py               -> SIMULATION : affiche ce qui serait fait, ne touche à rien
  python3 _discord/salon-carte-en-direct.py --pour-de-vrai -> applique

Le jeton du bot se lit dans ~/.terrafront-bot (hors du dépôt, qui est public), comme habiller-discord.py.

Ce que fait le script (sans jamais rien supprimer) :
  1. crée le salon vocal 📺│carte-en-direct dans la catégorie 🗺️ Le jeu
     (Discord range toujours les salons vocaux sous les salons écrits d'une catégorie) ;
  2. droits du salon : tout le monde peut le voir, y entrer et écrire dans son fil,
     mais pas parler ni partager son écran ; 👑 Fondateur et 🛡️ Modération peuvent tout
     (le propriétaire du serveur passe de toute façon au-dessus de ces droits) ;
     si Discord refuse un droit au bot, le script le dit et continue (à régler à la main) ;
  3. poste et épingle dans ⚔️│front un message qui renvoie vers le salon et vers
     terrafront.fr/direct/ (une seule fois ; s'il est déjà posté, le texte est remis à jour).
Rejouable : un deuxième passage ne refait que ce qui manque.
"""
import json, os, subprocess, sys, time

VRAI = '--pour-de-vrai' in sys.argv
API = 'https://discord.com/api/v10'
JETON_FICHIER = os.path.expanduser('~/.terrafront-bot')

NOM_SALON = u'📺│carte-en-direct'
NOM_CATEGORIE = u'🗺️ Le jeu'
NOM_FRONT = u'⚔️│front'
ROLES_LIBRES = [u'👑 Fondateur', u'🛡️ Modération']
REPERE = u'La carte du Front en direct'

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
        time.sleep(0.35)
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
EVERYONE = G
dire(u'Serveur : %s · bot : %s · %s' % (serveurs[0]['name'], moi['username'], 'POUR DE VRAI' if VRAI else 'SIMULATION (rien ne change)'))
roles = appel('GET', '/guilds/%s/roles' % G)
salons = appel('GET', '/guilds/%s/channels' % G)

# droits Discord
VOIR, CONNECTER, PARLER, VIDEO, ECRIRE, HISTORIQUE = 1 << 10, 1 << 20, 1 << 21, 1 << 9, 1 << 11, 1 << 16
TOUT = VOIR | CONNECTER | PARLER | VIDEO | ECRIRE | HISTORIQUE

# ------------------------------------------------------------------ 1. le salon vocal
dire(u'\n1. Le salon vocal')
cat = next((s for s in salons if s['type'] == 4 and s['name'] == NOM_CATEGORIE), None)
if not cat: sys.exit(u'Catégorie « %s » introuvable : lance d\'abord habiller-discord.py.' % NOM_CATEGORIE)
par_nom = {r['name']: r for r in roles}
droits = [{'id': EVERYONE, 'type': 0, 'allow': str(VOIR | CONNECTER | ECRIRE | HISTORIQUE), 'deny': str(PARLER | VIDEO), 'quoi': u'tout le monde : regarder et écrire, ni parler ni partager'},
          {'id': moi['id'], 'type': 1, 'allow': str(VOIR | CONNECTER | ECRIRE | HISTORIQUE), 'deny': '0', 'quoi': u'le bot'}]
for nom in ROLES_LIBRES:
    r = par_nom.get(nom)
    if r: droits.append({'id': r['id'], 'type': 0, 'allow': str(TOUT), 'deny': '0', 'quoi': nom + u' : tout'})
    else: dire(u'  (rôle %s introuvable : il n\'aura pas de droit particulier)' % nom)
salon = next((s for s in salons if s['type'] == 2 and s['name'] == NOM_SALON), None)
if salon:
    dire(u'  déjà là  %s' % NOM_SALON)
    existants = {o['id']: o for o in salon.get('permission_overwrites', [])}
    for d in droits:
        e = existants.get(d['id'])
        if not e or int(e['allow']) != int(d['allow']) or int(e['deny']) != int(d['deny']):
            faire(u'droits (%s)' % d['quoi'], lambda d=d: appel('PUT', '/channels/%s/permissions/%s' % (salon['id'], d['id']),
                  {'type': d['type'], 'allow': d['allow'], 'deny': d['deny']}, fatal=False))
    if salon.get('parent_id') != cat['id']:
        faire(u'ranger dans %s' % NOM_CATEGORIE, lambda: appel('PATCH', '/channels/%s' % salon['id'], {'parent_id': cat['id']}))
else:
    # le salon d'abord, puis chaque droit à part : si Discord en refuse un, le reste passe quand même
    salon = faire(u'nouveau salon vocal %s dans %s' % (NOM_SALON, NOM_CATEGORIE), lambda: appel('POST', '/guilds/%s/channels' % G,
                  {'name': NOM_SALON, 'type': 2, 'parent_id': cat['id']}))
    for d in droits:
        faire(u'droits (%s)' % d['quoi'], lambda d=d: appel('PUT', '/channels/%s/permissions/%s' % (salon['id'], d['id']),
              {'type': d['type'], 'allow': d['allow'], 'deny': d['deny']}, fatal=False) if salon else None)

# ------------------------------------------------------------------ 2. le message épinglé dans le Front
dire(u'\n2. Le message dans %s' % NOM_FRONT)
front = next((s for s in salons if s['type'] == 0 and s['name'] == NOM_FRONT), None)
if not front:
    dire(u'  salon %s introuvable : pas de message' % NOM_FRONT)
else:
    lien = '<#%s>' % salon['id'] if salon else NOM_SALON
    texte = (u'📺 **%s**\n\n'
             u'Quand Nataël est en direct, la carte du Front tourne dans %s : les conquêtes qui clignotent, le fil du Front et le classement des clans. '
             u'Rejoins le salon pour regarder (micro coupé).\n\n'
             u'Tu peux aussi l\'ouvrir à tout moment, sans te connecter : https://terrafront.fr/direct/\n'
             u'Molette pour zoomer, cliquer-glisser pour te déplacer, survole une commune pour voir à qui elle est.') % (REPERE, lien)
    deja = appel('GET', '/channels/%s/messages?limit=50' % front['id']) or []
    ancien = next((x for x in deja if x['author']['id'] == moi['id'] and REPERE in x.get('content', '')), None)
    if ancien:
        if ancien.get('content') != texte:
            faire(u'mettre à jour le message', lambda: appel('PATCH', '/channels/%s/messages/%s' % (front['id'], ancien['id']),
                  {'content': texte, 'allowed_mentions': {'parse': []}}))
        else: dire(u'  déjà posté')
        if not ancien.get('pinned'):
            faire(u'épingler le message', lambda: appel('PUT', '/channels/%s/pins/%s' % (front['id'], ancien['id']), fatal=False))
    else:
        def poster():
            m = appel('POST', '/channels/%s/messages' % front['id'], {'content': texte, 'allowed_mentions': {'parse': []}})
            appel('PUT', '/channels/%s/pins/%s' % (front['id'], m['id']), fatal=False)
            return m
        faire(u'« %s » dans %s, épinglé' % (REPERE, NOM_FRONT), poster)
        if not VRAI: dire(u'\n--- texte du message ---\n' + texte + u'\n------------------------')

dire(u'\nTerminé.' if VRAI else u'\nSimulation terminée : rien n\'a changé. Si tout te va : python3 _discord/salon-carte-en-direct.py --pour-de-vrai')
