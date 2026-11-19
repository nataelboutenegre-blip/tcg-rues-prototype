# Saison 3, jour J — étape 5 : le jeu (à lancer APRÈS les étapes SQL 2 à 4)
#  - la Suisse s'allume dans le jeu et sur la carte en direct (SUISSE_OUVERTE) ;
#  - direct.js?v=5 -> v=6 (sinon les navigateurs gardent l'ancien fichier) ;
#  - patch415 : « © swisstopo » dans les mentions légales ;
#  - la cloche : l'entrée du 22/11.
# Avant : _jour-j/s3-jj-4b-skins.sql (les cinq collections de la saison 3 en boutique, skin + dos ; dessins dans le jeu depuis patch454 et patch468).
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

# (ajout du 19/11) la Belgique ouvre aussi le 22 : BELGIQUE_OUVERTE, AURORE_V 2, direct.js?v+1, « Source : Statbel »
# (À lancer APRÈS _sql/s3-32-belgique-entree.sql, étape 3 bis.)
subprocess.run([sys.executable, os.path.join(R, '_jour-j', 'patch-ouverture-belgique.py'), R, '--sans-direct-v'], check=True, cwd=R)
# (ajout du 19/11, 11 h 32) le Luxembourg ouvre aussi le 22 : LUXEMBOURG_OUVERT, sources ACT et RNPP dans les mentions légales
# (À lancer APRÈS _sql/s3-35-luxembourg-entree.sql, étape 3 ter.)
subprocess.run([sys.executable, os.path.join(R, '_jour-j', 'patch-ouverture-luxembourg.py'), R, '--sans-direct-v'], check=True, cwd=R)

if 'swisstopo' not in open(os.path.join(R, 'mentions-legales.html'), encoding='utf-8').read():
    subprocess.run([sys.executable, os.path.join(R, '_patchs', 'patch415.py'), R], check=True, cwd=R)
else:
    print('mentions-legales.html : déjà fait')

p = os.path.join(R, 'data', 'nouveautes.json')
d = json.load(open(p, encoding='utf-8'))
if not any(x.get('date') == '2026-11-22' for x in d):
    d.insert(0, {'date': '2026-11-22', 'nouveautes': [
        "⚔️ La saison 3 est lancée ! Le Front repart de zéro, tes 5 communes ★ sont toujours à toi, et tes TP aussi.",
        "🧭 Les onglets changent de nom : Combat devient le QG (attaquer, défendre, bâtiments), et l'ancien QG des mini-jeux devient l'Arcade (Commune du jour, Radar, Rafale, le Mess et le pass). Les icônes ne bougent pas.",
        "🏰 Le siège remplace les dés : pose un siège (2 ⚡), envoie des vagues d'énergie et remplis la jauge de la commune avant que son propriétaire la défende. Renforcer, garnison-bouclier, course entre assiégeants : tout est dans Règles › Le siège.",
        "🇨🇭 La Suisse rejoint la carte : 2 110 communes, 26 cantons qui comptent comme des départements, la région Suisse, et des cartes Aurore suisses.",
        "🇧🇪 La Belgique aussi : 565 communes, 11 provinces qui comptent comme des départements (dont Bruxelles-Capitale), la région Belgique, et 51 cartes Aurore belges.",
        "🇱🇺 Et le Luxembourg : 100 communes, 12 cantons qui comptent comme des départements, la région Luxembourg. Une seule légendaire : Luxembourg-Ville.",
        "🧭 Zone de départ : avant ton premier paquet du Front, choisis une région, la Suisse, la Belgique ou le Luxembourg ; tes 3 premiers paquets y tombent.",
        "🃏 Paquets Terra suisse, belge et luxembourgeois : au Tirage, choisis France, Suisse, Belgique ou Luxembourg, mêmes jetons et même prix.",
        "🎡 La roue du Front reste ouverte toute la saison, en plus de tes paquets : elle a ses propres jetons (1 toutes les 20 min, 3 en réserve), jusqu'à 50 tours par jour, et la soirée de 21 h à 23 h.",
        "🎖️ Le pass de la saison 3 est ouvert (Arcade › Pass de saison) : 20 niveaux jusqu'au 13 décembre, des paquets, des lingots et des titres.",
        "🍺 Le Mess ouvre ses portes à l'Arcade : la Machine à chiffrer, le Recensement et le 421, avec des tickets gagnés en duel classé.",
        "🎨 Nouveau look : la carte, les paquets, l'ouverture des cartes et la boutique ont été refaits.",
        "🏰 Classement des clans : il additionne maintenant les points des 5 meilleurs membres actifs (idée d'Oshannir). Une recrue ne fait jamais baisser son clan.",
        "🃏 Nouvelles cartes : la photo prend toute la place, le nom est posé dessus, le département en plaque, et le cadre change de matière selon la rareté (métal, reflet irisé, or). Les cartes à skin, Aurore, brillantes et de l'atelier gardent leur look.",
        "📊 Classement du Front : les bonus de département et de région varient selon leur population (× 0,6 pour les moins peuplés, jusqu'à × 1,6 pour les plus peuplés) ; une légendaire vaut 45 points. Viser une zone dense devient une vraie stratégie.",
        "✨ Cinq nouvelles collections en boutique, le skin et son dos assorti : Topo, Givre, Kintsugi, Vitrail et Aquarelle. Et les onze skins existants ont été redessinés : ils jouent maintenant avec la photo de ta carte. Si tu en as déjà un, il change tout seul, sans rien payer.",
        "🏆 Les récompenses de la saison 2 sont dans les profils : médailles du podium, titres, seigneuries, clan champion, et un paquet Terra offert à tous les pionniers du Front."],
        'correctifs': []})
    s = json.dumps(d, indent=2, ensure_ascii=False)
    assert json.loads(s) == d
    open(p, 'w', encoding='utf-8').write(s + '\n'); print('cloche du 22/11 : ok')
else:
    print('cloche du 22/11 : déjà là')
print('Skins : _jour-j/s3-jj-4b-skins.sql a-t-il été lancé ? (5 collections S3 en boutique)')
print('Ensuite : python3 maj-version.py, vérifier VERSION_JEU = version.json, commit, push.')
