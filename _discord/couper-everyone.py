# -*- coding: utf-8 -*-
u"""
Enlève aux joueurs le droit de mentionner @everyone, @here et tous les rôles (24 novembre 2026, signalé par Maroli).

1. VOIR (lecture seule, par défaut) :
     python3 _discord/couper-everyone.py
   Liste les rôles et les salons qui donnent ce droit.

2. ENLEVER :
     python3 _discord/couper-everyone.py --go
   - retire le droit de chaque rôle qui l'a (dont @everyone), sauf les rôles administrateur, ceux des bots
     et ceux de l'équipe (Fondateur, Modération : liste GARDER) ;
   - retire l'autorisation dans les permissions propres des salons, si un salon la donnait.
   Le propriétaire du serveur et les administrateurs gardent le droit (Discord ne le leur retire jamais).

Le bot doit avoir « Gérer les rôles », et son rôle doit être placé au-dessus des rôles à modifier
(sinon Discord répond 403 et le script le dit, rôle par rôle).
Le jeton du bot se lit dans ~/.terrafront-bot. Il ne sort pas du Mac.
"""
import json, os, subprocess, sys, time

API = 'https://discord.com/api/v10'
JETON_FICHIER = os.path.expanduser('~/.terrafront-bot')
GO = '--go' in sys.argv[1:]
# rôles qui gardent le droit (morceau du nom, sans tenir compte des majuscules) : l'équipe
GARDER = ['fondateur', 'modération', 'moderation']
MENTION = 1 << 17      # MENTION_EVERYONE
ADMIN = 1 << 3         # ADMINISTRATOR

def lire_jeton():
    if not os.path.exists(JETON_FICHIER): sys.exit(u"Jeton introuvable : %s" % JETON_FICHIER)
    j = open(JETON_FICHIER).read().strip()
    if len(j) < 50: sys.exit(u"Le fichier %s ne ressemble pas à un jeton de bot." % JETON_FICHIER)
    return j
JETON = lire_jeton()

def appel(methode, chemin, corps=None, fatal=True):
    cmd = ['curl', '-sS', '-X', methode, API + chemin, '-H', 'Authorization: Bot ' + JETON,
           '-H', 'User-Agent: TerraFrontBot (terrafront.fr, 1)', '-H', 'X-Audit-Log-Reason: Plus de mention everyone pour les joueurs',
           '-w', '\n%{http_code}']
    if corps is not None: cmd += ['-H', 'Content-Type: application/json', '--data-binary', json.dumps(corps)]
    for essai in range(6):
        r = subprocess.run(cmd, capture_output=True)
        if r.returncode != 0: sys.exit(u'curl a échoué : ' + r.stderr.decode('utf-8', 'replace'))
        texte, _, code = r.stdout.decode('utf-8', 'replace').rpartition('\n')
        code = int(code or 0)
        if code == 429:
            try: time.sleep(float(json.loads(texte).get('retry_after', 2)) + 0.3)
            except Exception: time.sleep(2)
            continue
        if code >= 400:
            if fatal: sys.exit(u'Discord a refusé %s %s (%d) : %s' % (methode, chemin, code, texte[:300]))
            return (code, texte[:200])
        time.sleep(0.35)
        return json.loads(texte) if texte.strip() else {}
    sys.exit(u'Discord limite trop les appels : réessaie dans une minute.')

G = appel('GET', '/users/@me/guilds')[0]['id']
roles = appel('GET', '/guilds/%s/roles' % G)
salons = appel('GET', '/guilds/%s/channels' % G)
noms_roles = {r['id']: ('@everyone' if r['id'] == G else '@' + r['name']) for r in roles}

a_faire_roles, admins, gardes = [], [], []
for r in sorted(roles, key=lambda x: x['position']):
    p = int(r['permissions'])
    if not p & MENTION: continue
    if p & ADMIN: admins.append(noms_roles[r['id']]); continue
    if r.get('managed'): continue      # rôle d'un bot : Discord ne le laisse pas modifier
    if any(g in r['name'].lower() for g in GARDER): gardes.append(noms_roles[r['id']]); continue
    a_faire_roles.append((r, p))

a_faire_salons = []
for s in salons:
    for o in s.get('permission_overwrites', []):
        allow = int(o['allow'])
        if allow & MENTION:
            qui = noms_roles.get(o['id'], 'membre ' + o['id']) if o['type'] == 0 else 'membre ' + o['id']
            a_faire_salons.append((s, o, qui))

print(u'Rôles qui permettent de mentionner tout le monde : %s' % (', '.join(noms_roles[r['id']] for r, _ in a_faire_roles) or 'aucun'))
print(u'Salons qui le permettent en plus : %s' % (', '.join('#%s (%s)' % (s['name'], q) for s, o, q in a_faire_salons) or 'aucun'))
if admins: print(u'Rôles administrateur (gardent le droit) : %s' % ', '.join(admins))
if gardes: print(u'Rôles de l\'équipe (gardent le droit) : %s' % ', '.join(gardes))
if not GO:
    print(u'\nRien n\'a été changé. Relance avec --go pour enlever le droit.')
    sys.exit(0)

ok, refus = 0, []
for r, p in a_faire_roles:
    res = appel('PATCH', '/guilds/%s/roles/%s' % (G, r['id']), {'permissions': str(p & ~MENTION)}, fatal=False)
    if isinstance(res, tuple): refus.append(u'%s (%d)' % (noms_roles[r['id']], res[0]))
    else: ok += 1
for s, o, q in a_faire_salons:
    res = appel('PUT', '/channels/%s/permissions/%s' % (s['id'], o['id']),
                {'type': o['type'], 'allow': str(int(o['allow']) & ~MENTION), 'deny': o['deny']}, fatal=False)
    if isinstance(res, tuple): refus.append(u'#%s (%d)' % (s['name'], res[0]))
    else: ok += 1
print(u'\n%d réglage(s) modifié(s).' % ok)
if refus:
    print(u'Refusés : %s' % ', '.join(refus))
    print(u'→ Donne « Gérer les rôles » au bot et remonte son rôle au-dessus de ceux-là (Paramètres du serveur › Rôles, glisser), puis relance.')
else:
    print(u'Les joueurs ne peuvent plus mentionner @everyone ni @here.')
