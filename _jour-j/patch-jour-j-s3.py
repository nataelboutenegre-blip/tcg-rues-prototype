# Saison 3, jour J — étape 5 : le jeu (à lancer APRÈS les étapes SQL 2 à 4)
#  - la Suisse s'allume dans le jeu et sur la carte en direct (SUISSE_OUVERTE) ;
#  - direct.js?v=5 -> v=6 (sinon les navigateurs gardent l'ancien fichier) ;
#  - patch415 : « © swisstopo » dans les mentions légales ;
#  - la cloche : l'entrée du 22/11.
# Ensuite : python3 maj-version.py, puis commit de app.js + index.html + version.json
# + direct/ + mentions-legales.html + data/nouveautes.json, puis push.
# L'habillage Topo, le sachet, la révélation et la vitrine s'allument seuls le 22/11
# à 10 h 01 (topo.js) : rien à faire ici.
import json, os, subprocess, sys
R = sys.argv[1] if len(sys.argv) > 1 else '.'
def rep(f, a, b, n=1):
    p = os.path.join(R, f); t = open(p, encoding='utf-8').read()
    if b in t and a not in t: print(f'{f} : déjà fait'); return
    assert t.count(a) == n, (f, a, t.count(a))
    open(p, 'w', encoding='utf-8').write(t.replace(a, b)); print(f'{f} : ok')

rep('app.js', 'const SUISSE_OUVERTE = false;', 'const SUISSE_OUVERTE = true;')
rep('direct/direct.js', 'const SUISSE_OUVERTE = false;', 'const SUISSE_OUVERTE = true;')
rep('direct/index.html', 'direct.js?v=5', 'direct.js?v=6')
rep('direct/tiktok.html', 'direct.js?v=5', 'direct.js?v=6')

if 'swisstopo' not in open(os.path.join(R, 'mentions-legales.html'), encoding='utf-8').read():
    subprocess.run([sys.executable, os.path.join(R, '_patchs', 'patch415.py'), R], check=True, cwd=R)
else:
    print('mentions-legales.html : déjà fait')

p = os.path.join(R, 'data', 'nouveautes.json')
d = json.load(open(p, encoding='utf-8'))
if not any(x.get('date') == '2026-11-22' for x in d):
    d.insert(0, {'date': '2026-11-22', 'nouveautes': [
        "⚔️ La saison 3 est lancée ! Le Front repart de zéro, tes 5 communes ★ sont toujours à toi, et tes TP aussi.",
        "🏰 Le siège remplace les dés : pose un siège (2 ⚡), envoie des vagues d'énergie et remplis la jauge de la commune avant que son propriétaire la défende. Renforcer, garnison-bouclier, course entre assiégeants : tout est dans Règles › Le siège.",
        "🇨🇭 La Suisse rejoint la carte : 2 110 communes, 26 cantons qui comptent comme des départements, la région Suisse, et des cartes Aurore suisses.",
        "🧭 Zone de départ : avant ton premier paquet du Front, choisis une région ou la Suisse ; tes 3 premiers paquets y tombent.",
        "🃏 Paquet Terra suisse : au Tirage, choisis France ou Suisse, mêmes jetons et même prix.",
        "🎖️ Le pass de la saison 3 est ouvert (QG › Pass de saison) : 20 niveaux jusqu'au 13 décembre, des paquets, des lingots et des titres.",
        "🍺 Le Mess ouvre ses portes au QG : la Machine à chiffrer, le Recensement et le 421, avec des tickets gagnés en duel classé.",
        "🎨 Nouveau look : la carte, les paquets, l'ouverture des cartes et la boutique ont été refaits.",
        "🏆 Les récompenses de la saison 2 sont dans les profils : médailles du podium, titres, seigneuries, clan champion, et un paquet Terra offert à tous les pionniers du Front."],
        'correctifs': []})
    s = json.dumps(d, indent=2, ensure_ascii=False)
    assert json.loads(s) == d
    open(p, 'w', encoding='utf-8').write(s + '\n'); print('cloche du 22/11 : ok')
else:
    print('cloche du 22/11 : déjà là')
print('Ensuite : python3 maj-version.py, vérifier VERSION_JEU = version.json, commit, push.')
