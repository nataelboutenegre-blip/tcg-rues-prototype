# -*- coding: utf-8 -*-
u"""
Lit un salon du Discord de TerraFront et l'écrit dans un fichier, pour que Claude le lise (22 novembre 2026).
LECTURE SEULE : le script ne poste, ne modifie et ne supprime rien.

  python3 _discord/lire-salon.py                 -> le salon « bugs », 7 derniers jours
  python3 _discord/lire-salon.py bugs 14         -> 14 derniers jours
  python3 _discord/lire-salon.py idées 7         -> un autre salon (un morceau de son nom suffit)

Écrit _discord/lectures/<salon>-<date>.md (et .json), et les captures dans <salon>-<date>-pieces/. Ce dossier est ignoré par git : les messages des joueurs
ne partent jamais sur GitHub (le dépôt est public).

Le jeton du bot se lit dans ~/.terrafront-bot, comme pour habiller-discord.py. Il ne sort pas du Mac.

Si les messages sortent vides : sur https://discord.com/developers/applications > le bot > Bot >
« Privileged Gateway Intents », activer « MESSAGE CONTENT INTENT », enregistrer, relancer.
Prend aussi les fils (threads) du salon, et les publications si c'est un salon forum.
"""
import json, os, subprocess, sys, time, datetime, unicodedata

ICI = os.path.dirname(os.path.abspath(__file__))
API = 'https://discord.com/api/v10'
JETON_FICHIER = os.path.expanduser('~/.terrafront-bot')
CHERCHE = sys.argv[1] if len(sys.argv) > 1 else 'bugs'
JOURS = int(sys.argv[2]) if len(sys.argv) > 2 else 7
DEPUIS = datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(days=JOURS)

def lire_jeton():
    if not os.path.exists(JETON_FICHIER):
        sys.exit(u"Jeton introuvable : %s" % JETON_FICHIER)
    j = open(JETON_FICHIER).read().strip()
    if len(j) < 50: sys.exit(u"Le fichier %s ne ressemble pas à un jeton de bot." % JETON_FICHIER)
    return j
JETON = lire_jeton()

def appel(chemin, fatal=True):
    """GET seulement : ce script ne change rien sur le serveur."""
    for essai in range(6):
        r = subprocess.run(['curl', '-sS', API + chemin, '-H', 'Authorization: Bot ' + JETON,
                            '-H', 'User-Agent: TerraFrontBot (terrafront.fr, 1)', '-w', '\n%{http_code}'], capture_output=True)
        if r.returncode != 0: sys.exit(u'curl a échoué : ' + r.stderr.decode('utf-8', 'replace'))
        texte, _, code = r.stdout.decode('utf-8', 'replace').rpartition('\n')
        code = int(code or 0)
        if code == 429:
            try: time.sleep(float(json.loads(texte).get('retry_after', 2)) + 0.3)
            except Exception: time.sleep(2)
            continue
        if code >= 400:
            if fatal: sys.exit(u'Discord a refusé GET %s (%d) : %s' % (chemin, code, texte[:300]))
            return None
        time.sleep(0.3)
        return json.loads(texte) if texte.strip() else None
    sys.exit(u'Discord limite trop les appels : réessaie dans une minute.')

def simple(s):
    s = unicodedata.normalize('NFD', s.lower())
    return ''.join(c for c in s if c.isalnum())

def date_de(m): return datetime.datetime.fromisoformat(m['timestamp'].replace('Z', '+00:00'))

def messages_de(salon_id):
    """Tous les messages du salon depuis DEPUIS, du plus ancien au plus récent."""
    tout, avant = [], None
    while True:
        lot = appel('/channels/%s/messages?limit=100%s' % (salon_id, '&before=' + avant if avant else ''), fatal=False) or []
        if not lot: break
        tout += [m for m in lot if date_de(m) >= DEPUIS]
        if date_de(lot[-1]) < DEPUIS or len(lot) < 100: break
        avant = lot[-1]['id']
    return sorted(tout, key=date_de)

serveurs = appel('/users/@me/guilds')
G = serveurs[0]['id']
salons = appel('/guilds/%s/channels' % G)
voulu = simple(CHERCHE)
cands = [s for s in salons if s.get('type') in (0, 5, 15) and voulu in simple(s.get('name', ''))]
if not cands: sys.exit(u'Aucun salon ne contient « %s ». Salons : %s' % (CHERCHE, ', '.join(s['name'] for s in salons if s.get('type') in (0, 5, 15))))
salon = cands[0]
print(u'Salon : #%s · %d derniers jours' % (salon['name'], JOURS))

# les fils : actifs (tout le serveur, filtrés sur ce salon) et archivés publics
fils = [t for t in (appel('/guilds/%s/threads/active' % G, fatal=False) or {}).get('threads', []) if t.get('parent_id') == salon['id']]
arch = appel('/channels/%s/threads/archived/public?limit=100' % salon['id'], fatal=False) or {}
fils += [t for t in arch.get('threads', []) if t['id'] not in {f['id'] for f in fils}]

def propre(m):
    return {'id': m['id'], 'le': m['timestamp'], 'auteur': (m.get('author') or {}).get('global_name') or (m.get('author') or {}).get('username'),
            'texte': m.get('content', ''), 'pieces': [a.get('url') for a in m.get('attachments', [])],
            'reponse_a': (m.get('message_reference') or {}).get('message_id')}

sortie = {'salon': salon['name'], 'depuis': DEPUIS.isoformat(), 'messages': [], 'fils': []}
if salon.get('type') != 15:
    sortie['messages'] = [propre(m) for m in messages_de(salon['id'])]
for f in fils:
    ms = messages_de(f['id'])
    if ms: sortie['fils'].append({'titre': f.get('name'), 'messages': [propre(m) for m in ms]})

vides = sum(1 for m in sortie['messages'] + [x for f in sortie['fils'] for x in f['messages']] if not m['texte'] and not m['pieces'])
total = len(sortie['messages']) + sum(len(f['messages']) for f in sortie['fils'])

os.makedirs(os.path.join(ICI, 'lectures'), exist_ok=True)
base = os.path.join(ICI, 'lectures', '%s-%s' % (simple(CHERCHE), datetime.date.today().isoformat()))
# les captures d'écran, téléchargées à côté (les liens de Discord expirent)
dossier_pieces = base + '-pieces'
for m in sortie['messages'] + [x for f in sortie['fils'] for x in f['messages']]:
    locales = []
    for i, u in enumerate(m['pieces']):
        ext = os.path.splitext(u.split('?')[0])[1][:6] or '.bin'
        nom = '%s-%d%s' % (m['id'], i + 1, ext)
        os.makedirs(dossier_pieces, exist_ok=True)
        if subprocess.run(['curl', '-sS', '-o', os.path.join(dossier_pieces, nom), u], capture_output=True).returncode == 0:
            locales.append(os.path.basename(dossier_pieces) + '/' + nom)
    m['pieces_locales'] = locales
json.dump(sortie, open(base + '.json', 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
def ligne(m):
    h = date_de(m if 'timestamp' in m else {'timestamp': m['le']}).astimezone().strftime('%d/%m %H:%M')
    p = ''.join('\n    [pièce jointe] ' + u for u in (m.get('pieces_locales') or m['pieces']))
    return u'- %s · **%s** : %s%s' % (h, m['auteur'], m['texte'].replace('\n', '\n    '), p)
with open(base + '.md', 'w', encoding='utf-8') as o:
    o.write(u'# #%s · %d derniers jours (lu le %s)\n\n' % (salon['name'], JOURS, datetime.datetime.now().strftime('%d/%m/%Y %H:%M')))
    for m in sortie['messages']: o.write(ligne(m) + '\n')
    for f in sortie['fils']:
        o.write(u'\n## Fil : %s\n' % f['titre'])
        for m in f['messages']: o.write(ligne(m) + '\n')
print(u'%d messages (%d dans %d fils) → %s.md' % (total, total - len(sortie['messages']), len(sortie['fils']), base))
if total and vides > total / 2:
    print(u'⚠️  %d messages sans texte : active « MESSAGE CONTENT INTENT » pour le bot (voir en haut du script), puis relance.' % vides)
