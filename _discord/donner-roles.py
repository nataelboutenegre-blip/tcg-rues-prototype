# -*- coding: utf-8 -*-
u"""
Donne les rôles de la saison 1 sur le Discord de TerraFront (25 octobre 2026).

  python3 _discord/donner-roles.py               -> SIMULATION : affiche qui recevrait quoi, ne touche à rien
  python3 _discord/donner-roles.py --pour-de-vrai -> donne les rôles

Les listes viennent de _discord/roles-saison-1.json (pseudos du jeu, tirés de
la base par _discord/roles-saison-1.sql).
Un pseudo du jeu est reconnu s'il correspond, sans tenir compte des majuscules,
des accents et de la ponctuation, au nom d'utilisateur, au nom affiché ou au
surnom sur le serveur d'un membre. Pour un joueur qui s'appelle autrement sur
Discord, ajoute-le dans _discord/correspondances.json :
  { "pseudo dans le jeu": "nom d'utilisateur Discord" }

Le jeton du bot se lit dans ~/.terrafront-bot (hors du dépôt, qui est public).
Le bot doit avoir « Server Members Intent » activé (portail développeur ›
Bot › Privileged Gateway Intents), sinon Discord refuse la liste des membres.
Ne retire jamais un rôle. Rejouable : ne redonne pas un rôle déjà là.
"""
import json, os, subprocess, sys, time, unicodedata

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

def cle(nom):
    s = unicodedata.normalize('NFD', (nom or '').lower())
    return ''.join(c for c in s if c.isalnum())

# ------------------------------------------------------------------ le serveur
moi = appel('GET', '/users/@me')
serveurs = appel('GET', '/users/@me/guilds')
if len(serveurs) != 1:
    sys.exit(u"Le bot est sur %d serveurs : il doit être seulement sur celui de TerraFront." % len(serveurs))
G = serveurs[0]['id']
print(u'Serveur : %s · bot : %s · %s' % (serveurs[0]['name'], moi['username'], 'POUR DE VRAI' if VRAI else 'SIMULATION (rien ne change)'))

LISTES = json.load(open(os.path.join(ICI, 'roles-saison-1.json'), encoding='utf-8'))
corr_f = os.path.join(ICI, 'correspondances.json')
CORR = {cle(k): cle(v) for k, v in (json.load(open(corr_f, encoding='utf-8')).items() if os.path.exists(corr_f) else [])}

roles = {r['name']: r for r in appel('GET', '/guilds/%s/roles' % G)}
manquants = [n for n in LISTES if n not in roles]
if manquants: sys.exit(u'Rôles introuvables sur le serveur : %s (lance d\'abord habiller-discord.py)' % ', '.join(manquants))

# tous les membres (par pages de 1000)
membres, apres = [], '0'
while True:
    page = appel('GET', '/guilds/%s/members?limit=1000&after=%s' % (G, apres), fatal=False)
    if page is None:
        sys.exit(u"Discord refuse la liste des membres : active « Server Members Intent » dans le portail "
                 u"développeur (Bot › Privileged Gateway Intents), puis relance.")
    membres += [m for m in page if not m['user'].get('bot')]
    if len(page) < 1000: break
    apres = page[-1]['user']['id']
print(u'%d membres sur le serveur\n' % len(membres))

index = {}
for m in membres:
    u = m['user']
    for nom in (u.get('username'), u.get('global_name'), m.get('nick')):
        if nom: index.setdefault(cle(nom), set()).add(u['id'])
par_id = {m['user']['id']: m for m in membres}

def trouver(pseudo):
    k = CORR.get(cle(pseudo), cle(pseudo))
    ids = index.get(k, set())
    return list(ids)

introuvables = set()
total = 0
for nom_role, pseudos in LISTES.items():
    rid = roles[nom_role]['id']
    print(nom_role)
    for p in pseudos:
        ids = trouver(p)
        if not ids:
            introuvables.add(p); print(u'  ?        %s : pas trouvé sur le serveur' % p); continue
        if len(ids) > 1:
            print(u'  ?        %s : plusieurs membres possibles, mets-le dans correspondances.json' % p); continue
        m = par_id[ids[0]]
        qui = u'%s (Discord : %s)' % (p, m['user'].get('username'))
        if rid in m.get('roles', []):
            print(u'  déjà là  %s' % qui); continue
        print((u'  FAIT     ' if VRAI else u'  SIMULÉ   ') + qui)
        total += 1
        if VRAI:
            appel('PUT', '/guilds/%s/members/%s/roles/%s' % (G, ids[0], rid), fatal=False)
    print('')

if introuvables:
    print(u'%d joueur(s) pas trouvé(s) : %s' % (len(introuvables), ', '.join(sorted(introuvables))))
    print(u"Soit ils ne sont pas sur le Discord, soit ils s'appellent autrement : ajoute-les dans _discord/correspondances.json.")
print(u'\n%d rôle(s) %s.' % (total, u'donnés' if VRAI else u'à donner'))
if not VRAI: print(u'Simulation terminée : rien n\'a changé. Si tout te va : python3 _discord/donner-roles.py --pour-de-vrai')
