# -*- coding: utf-8 -*-
u"""
Trie le forum des idées du Discord de TerraFront (23 novembre 2026).

1. LISTER (lecture seule, par défaut) :
     python3 _discord/trier-idees.py
   Écrit _discord/lectures/idees-fils-<date>.md (et .json) : chaque publication du forum avec son numéro,
   son titre, son auteur, ses étiquettes, son état (ouverte / archivée) et le début de son premier message.
   Claude lit ce fichier et te dit quels numéros sont déjà faits.

2. MARQUER « ✅ Fait » ET ARCHIVER :
     python3 _discord/trier-idees.py fait 123456789012345678 234567890123456789 ...
   Sans --go, le script montre seulement ce qu'il ferait. Avec --go, il le fait :
     python3 _discord/trier-idees.py fait 1234... 2345... --go
   - crée l'étiquette « Fait » (emoji ✅) dans le forum si elle n'existe pas ;
   - l'ajoute à chaque publication donnée (5 étiquettes au plus, la règle de Discord) ;
   - archive la publication (elle reste lisible, et revient si quelqu'un y répond).
   Option --message "texte" : poste d'abord ce message dans chaque publication (par exemple
   "✅ C'est en ligne, merci pour l'idée !"). Sans l'option, rien n'est posté.

Option pour les deux modes : --salon <morceau du nom> (par défaut : « idée »).
Le bot doit avoir la permission « Gérer les fils » (et « Gérer les salons » pour créer l'étiquette).
Le jeton du bot se lit dans ~/.terrafront-bot, comme pour lire-salon.py. Il ne sort pas du Mac.
Le dossier _discord/lectures est ignoré par git : rien ne part sur GitHub.
"""
import json, os, subprocess, sys, time, datetime, unicodedata

ICI = os.path.dirname(os.path.abspath(__file__))
API = 'https://discord.com/api/v10'
JETON_FICHIER = os.path.expanduser('~/.terrafront-bot')
ARGS = sys.argv[1:]

def option(nom, defaut=None):
    if nom in ARGS:
        i = ARGS.index(nom); v = ARGS[i + 1] if i + 1 < len(ARGS) else defaut
        del ARGS[i:i + 2]; return v
    return defaut
SALON = option('--salon', 'idee')
MESSAGE = option('--message')
GO = '--go' in ARGS
if GO: ARGS.remove('--go')
MODE = ARGS[0] if ARGS else 'liste'
IDS = [a for a in ARGS[1:] if a.isdigit()]

def lire_jeton():
    if not os.path.exists(JETON_FICHIER): sys.exit(u"Jeton introuvable : %s" % JETON_FICHIER)
    j = open(JETON_FICHIER).read().strip()
    if len(j) < 50: sys.exit(u"Le fichier %s ne ressemble pas à un jeton de bot." % JETON_FICHIER)
    return j
JETON = lire_jeton()

def appel(methode, chemin, corps=None, fatal=True):
    cmd = ['curl', '-sS', '-X', methode, API + chemin, '-H', 'Authorization: Bot ' + JETON,
           '-H', 'User-Agent: TerraFrontBot (terrafront.fr, 1)', '-w', '\n%{http_code}']
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
            return None
        time.sleep(0.35)
        return json.loads(texte) if texte.strip() else {}
    sys.exit(u'Discord limite trop les appels : réessaie dans une minute.')

def simple(s):
    s = unicodedata.normalize('NFD', (s or '').lower())
    return ''.join(c for c in s if c.isalnum())

G = appel('GET', '/users/@me/guilds')[0]['id']
salons = appel('GET', '/guilds/%s/channels' % G)
forums = [s for s in salons if s.get('type') == 15 and simple(SALON) in simple(s.get('name'))]
if not forums: sys.exit(u'Aucun forum ne contient « %s ». Forums : %s' % (SALON, ', '.join(s['name'] for s in salons if s.get('type') == 15) or 'aucun'))
F = forums[0]
TAGS = {t['id']: ((t.get('emoji_name') or '') + ' ' + t['name']).strip() for t in F.get('available_tags', [])}
print(u'Forum : #%s' % F['name'])

def tous_les_fils():
    fils = {t['id']: dict(t, _etat='ouverte') for t in (appel('GET', '/guilds/%s/threads/active' % G, fatal=False) or {}).get('threads', []) if t.get('parent_id') == F['id']}
    avant = None
    while True:
        lot = appel('GET', '/channels/%s/threads/archived/public?limit=100%s' % (F['id'], '&before=' + avant if avant else ''), fatal=False) or {}
        for t in lot.get('threads', []):
            if t['id'] not in fils: fils[t['id']] = dict(t, _etat='archivée')
        if not lot.get('has_more') or not lot.get('threads'): break
        avant = lot['threads'][-1]['thread_metadata']['archive_timestamp']
    return list(fils.values())

if MODE == 'liste':
    sortie = []
    for t in sorted(tous_les_fils(), key=lambda x: int(x['id'])):
        premier = appel('GET', '/channels/%s/messages/%s' % (t['id'], t['id']), fatal=False) or {}   # le premier message porte le numéro du fil
        sortie.append({'id': t['id'], 'titre': t.get('name'), 'etat': t['_etat'],
                       'etiquettes': [TAGS.get(x, x) for x in t.get('applied_tags', [])],
                       'auteur': ((premier.get('author') or {}).get('global_name') or (premier.get('author') or {}).get('username') or '?'),
                       'cree_le': datetime.datetime.fromtimestamp(((int(t['id']) >> 22) + 1420070400000) / 1000).strftime('%d/%m/%Y'),
                       'messages': t.get('message_count'), 'texte': (premier.get('content') or '')[:600],
                       'pieces': [a.get('url') for a in premier.get('attachments', [])]})
    os.makedirs(os.path.join(ICI, 'lectures'), exist_ok=True)
    base = os.path.join(ICI, 'lectures', 'idees-fils-%s' % datetime.date.today().isoformat())
    json.dump({'forum': F['name'], 'etiquettes': list(TAGS.values()), 'fils': sortie}, open(base + '.json', 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    with open(base + '.md', 'w', encoding='utf-8') as o:
        o.write(u'# Forum #%s · %d publications (lu le %s)\nÉtiquettes du forum : %s\n\n' % (F['name'], len(sortie), datetime.datetime.now().strftime('%d/%m/%Y %H:%M'), ', '.join(TAGS.values()) or 'aucune'))
        for s in sortie:
            o.write(u'## %s · %s\n- n° %s · %s · %s · %s messages%s\n- %s%s\n\n' % (s['titre'], s['auteur'], s['id'], s['cree_le'], s['etat'], s['messages'],
                    (' · ' + ', '.join(s['etiquettes'])) if s['etiquettes'] else '', s['texte'].replace('\n', ' '),
                    ''.join('\n- [pièce jointe] ' + u for u in s['pieces'])))
    ouvertes = sum(1 for s in sortie if s['etat'] == 'ouverte')
    print(u'%d publications (%d ouvertes, %d archivées) → %s.md' % (len(sortie), ouvertes, len(sortie) - ouvertes, base))

elif MODE == 'fait':
    if not IDS: sys.exit(u'Donne les numéros des publications : python3 _discord/trier-idees.py fait 1234... 5678...')
    fait = next((t for t in F.get('available_tags', []) if simple(t['name']) == 'fait'), None)
    if not fait:
        print(u'L\'étiquette « ✅ Fait » n\'existe pas encore : elle sera créée.')
        if GO:
            tags = [{k: t[k] for k in ('id', 'name', 'moderated', 'emoji_id', 'emoji_name') if k in t} for t in F.get('available_tags', [])]
            if len(tags) >= 20: sys.exit(u'Le forum a déjà 20 étiquettes (le maximum) : supprimes-en une ou crée « Fait » à la main.')
            maj = appel('PATCH', '/channels/%s' % F['id'], {'available_tags': tags + [{'name': 'Fait', 'emoji_name': '✅'}]})
            fait = next(t for t in maj.get('available_tags', []) if simple(t['name']) == 'fait')
    for i in IDS:
        t = appel('GET', '/channels/%s' % i, fatal=False)
        if not t or t.get('parent_id') != F['id']:
            print(u'  ✗ %s : pas une publication de #%s, ignorée' % (i, F['name'])); continue
        tags = list(t.get('applied_tags', []))
        deja = fait and fait['id'] in tags
        if fait and not deja:
            if len(tags) >= 5: tags = tags[:4]
            tags.append(fait['id'])
        archivee = (t.get('thread_metadata') or {}).get('archived')
        print(u'  %s « %s »%s%s' % ('→' if GO else '·', t.get('name'), '' if deja else ' + ✅ Fait', '' if archivee and deja else ' + archivée'))
        if not GO: continue
        if archivee: appel('PATCH', '/channels/%s' % i, {'archived': False})
        if MESSAGE: appel('POST', '/channels/%s/messages' % i, {'content': MESSAGE, 'allowed_mentions': {'parse': []}})
        appel('PATCH', '/channels/%s' % i, {'applied_tags': tags, 'archived': True})
    print(u'Fait.' if GO else u'Rien n\'a été changé. Ajoute --go à la fin pour le faire.')
else:
    sys.exit(u'Mode inconnu : « %s ». Utilise « liste » (par défaut) ou « fait ».' % MODE)
