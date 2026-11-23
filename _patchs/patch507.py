# patch507 : mise en règle des pages légales après l'audit du 23/11/2026 (claude/audit-juridique-2026-11-23.md).
# Demandé par Nataël le 23/11 à 1 h 53 : « corrige ceux que tu peux maintenant, on verra les monuments demain ».
#  - CGV v5 (2026-11-23-v5) : encadré des garanties légales (décret 2022-946, annexe à l'article D. 211-4 du Code de la
#    consommation, fourniture continue ; X = durée de la licence), compatibilité, phrase sur les promotions corrigée
#    (les promos du week-end existent : « sans offre qui pousse à acheter vite » n'était plus vrai).
#    Le texte de l'encadré a été écrit de mémoire et recoupé avec un extrait de Légifrance : À COMPARER MOT À MOT avec
#    https://www.legifrance.gouv.fr/codes/article_lc/LEGIARTI000045981322/ (Légifrance refuse la lecture automatique).
#  - Confidentialité : achats et Stripe, date de naissance, parrainage, Discord, notifications, motifs, pages publiques,
#    durées ; jsDelivr et cdnjs retirés (les bibliothèques sont servies par le site depuis /lib).
#  - CGU : pays, achats, modération, « tel quel » et « continuer à jouer vaut acceptation » réécrits.
#  - Mentions légales : licences des données (Licence Ouverte 2.0, CC BY-SA 4.0) ; lien « Conditions de vente » partout.
# PAS FAIT ICI (il faut Nataël) : numéro de téléphone dans les mentions légales, monuments récents, accord pour les e-mails.
# Après le push : _boutique-euros/19-cgv-v5.sql (cgv_version + cgv_pdf_url), le PDF doit être en ligne avant.
import os, sys, json
R = sys.argv[1] if len(sys.argv) > 1 else '.'
def rep(f, a, b, n=1):
    p = os.path.join(R, f); t = open(p, encoding='utf-8').read()
    if t.count(a) != n:
        if b in t: print(f'{f} : déjà fait ({a[:40]!r})'); return
        raise SystemExit(f'{f} : {t.count(a)} occurrence(s) pour {a[:80]!r}')
    open(p, 'w', encoding='utf-8').write(t.replace(a, b)); print(f'{f} : ok ({a[:40]!r})')

# ---------------------------------------------------------------- le lien « Conditions de vente » sur les trois autres pages
for f in ('mentions-legales.html', 'cgu.html', 'confidentialite.html'):
    p = os.path.join(R, f); t = open(p, encoding='utf-8').read()
    if 'href="cgv.html"' not in t:
        t = t.replace('Conditions d\'utilisation</a></nav>', 'Conditions d\'utilisation</a><a href="cgv.html">Conditions de vente</a></nav>')
        i = t.rindex('Conditions d\'utilisation</a>'); j = i + len('Conditions d\'utilisation</a>')
        t = t[:j] + '<a href="cgv.html">Conditions de vente</a>' + t[j:]
        open(p, 'w', encoding='utf-8').write(t); print(f'{f} : lien CGV ok')

# ---------------------------------------------------------------- CGV v5
C = 'cgv.html'
rep(C, 'Version du 26 octobre 2026 (2026-10-26-v4)', 'Version du 23 novembre 2026 (2026-11-23-v5)')
rep(C, '  <li>restent associés à ton compte d\'une saison à l\'autre, dans les conditions de durée de l\'article 4.</li>\n</ul>',
       '  <li>restent associés à ton compte d\'une saison à l\'autre, dans les conditions de durée de l\'article 4.</li>\n</ul>\n'
       '<p><b>Ce qu\'il faut pour s\'en servir.</b> Un compte TerraFront, une connexion internet et un navigateur récent, sur ordinateur ou sur téléphone. Il n\'y a rien à installer, et les objets ne fonctionnent pas en dehors du jeu.</p>')
rep(C, '  <li>le prix est affiché avant chaque achat, sans compte à rebours ni offre qui pousse à acheter vite.</li>',
       '  <li>le prix est affiché avant chaque achat, sans compte à rebours. Quand une promotion a lieu, sa date de fin est annoncée et le prix barré est le prix le plus bas pratiqué pendant les 30 jours qui la précèdent.</li>')
ENCADRE = '''<div class="pg-encadre" style="border:1px solid currentColor;border-radius:10px;padding:14px 16px;margin:18px 0">
<p><b>Garanties légales (encadré prévu par l'article D. 211-4 du Code de la consommation).</b></p>
<p>Le consommateur a droit à la mise en œuvre de la garantie légale de conformité en cas d'apparition d'un défaut de conformité durant toute la durée de la licence de l'objet (pour le pass de saison : durant la saison). Durant ce délai, le consommateur n'est tenu d'établir que l'existence du défaut de conformité et non la date d'apparition de celui-ci.</p>
<p>La garantie légale de conformité emporte obligation de fournir toutes les mises à jour nécessaires au maintien de la conformité du contenu numérique ou du service numérique durant toute la durée de la licence de l'objet (pour le pass de saison : durant la saison).</p>
<p>La garantie légale de conformité donne au consommateur droit à la mise en conformité du contenu numérique ou du service numérique sans retard injustifié suivant sa demande, sans frais et sans inconvénient majeur pour lui.</p>
<p>Le consommateur peut obtenir une réduction du prix en conservant le contenu numérique ou le service numérique, ou il peut mettre fin au contrat en se faisant rembourser intégralement contre renoncement au contenu numérique ou au service numérique, si :</p>
<p>1° Le professionnel refuse de mettre le contenu numérique ou le service numérique en conformité ;<br>
2° La mise en conformité du contenu numérique ou du service numérique est retardée de manière injustifiée ;<br>
3° La mise en conformité du contenu numérique ou du service numérique ne peut intervenir sans frais imposés au consommateur ;<br>
4° La mise en conformité du contenu numérique ou du service numérique occasionne un inconvénient majeur pour le consommateur ;<br>
5° La non-conformité du contenu numérique ou du service numérique persiste en dépit de la tentative de mise en conformité du professionnel restée infructueuse.</p>
<p>Le consommateur a également droit à une réduction du prix ou à la résolution du contrat lorsque le défaut de conformité est si grave qu'il justifie que la réduction du prix ou la résolution du contrat soit immédiate. Le consommateur n'est alors pas tenu de demander la mise en conformité du contenu numérique ou du service numérique au préalable.</p>
<p>Dans les cas où le défaut de conformité est mineur, le consommateur n'a droit à l'annulation du contrat que si le contrat ne prévoit pas le paiement d'un prix.</p>
<p>Toute période d'indisponibilité du contenu numérique ou du service numérique en vue de sa remise en conformité suspend la garantie qui restait à courir jusqu'à la fourniture du contenu numérique ou du service numérique de nouveau conforme.</p>
<p>Ces droits résultent de l'application des articles L. 224-25-1 à L. 224-25-31 du code de la consommation.</p>
<p>Le professionnel qui fait obstacle de mauvaise foi à la mise en œuvre de la garantie légale de conformité encourt une amende civile d'un montant maximal de 300 000 euros, qui peut être porté jusqu'à 10 % du chiffre d'affaires moyen annuel (article L. 242-18-1 du code de la consommation).</p>
<p>Le consommateur bénéficie également de la garantie légale des vices cachés en application des articles 1641 à 1649 du code civil, pendant une durée de deux ans à compter de la découverte du défaut. Cette garantie donne droit à une réduction de prix si le contenu numérique ou le service numérique est conservé, ou à un remboursement intégral contre renonciation au contenu numérique ou au service numérique.</p>
</div>
'''
p = os.path.join(R, C); t = open(p, encoding='utf-8').read()
if 'pg-encadre' not in t:
    i = t.index('<p><b>Garantie légale de conformité.</b>'); j = t.index('</p>', i) + len('</p>')
    t = t[:j] + '\n' + ENCADRE.rstrip('\n') + t[j:]
    open(p, 'w', encoding='utf-8').write(t); print('cgv.html : encadré ok')

# ---------------------------------------------------------------- confidentialité
K = 'confidentialite.html'
rep(K, 'Dernière mise à jour : 1er novembre 2026', 'Dernière mise à jour : 23 novembre 2026')
rep(K, '(carte, classement, journal, combats)</td></tr>',
       '(carte, classement, journal, combats), y compris sur des pages publiques du site : la carte en direct et le bilan de fin de saison</td></tr>')
rep(K, '<b>Ta partie</b> : communes, points, paquets, combats, échanges, amis, succès, Commune du jour, Radar</td>',
       '<b>Ta partie</b> : communes, points, paquets, combats, sièges, bâtiments, échanges, amis, clan, succès, mini-jeux, réponses aux sondages du jeu, réglages de notifications, date de ta dernière connexion</td>')
rep(K, '    <tr><td><b>Abonnement aux notifications</b>, si tu les actives</td><td>T\'envoyer des alertes. Tu peux les couper dans le jeu ou dans ton navigateur</td></tr>',
       '    <tr><td><b>Motif de territoire</b>, si tu en crées un, et les signalements de motifs</td><td>L\'afficher sur la carte, visible par tous ; les signalements servent à la modération</td></tr>\n'
       '    <tr><td><b>Parrainage</b> : qui a invité qui</td><td>Verser les récompenses de parrainage</td></tr>\n'
       '    <tr><td><b>Abonnement aux notifications</b>, si tu les actives</td><td>T\'envoyer des alertes, par le service de notifications de ton navigateur (Apple, Google ou Mozilla). Tu peux les couper dans le jeu ou dans ton navigateur</td></tr>\n'
       '    <tr><td><b>Achats en euros</b>, si tu en fais : objet, prix, date, version des conditions de vente acceptée, tes choix sur la rétractation, référence du paiement. <b>Le numéro de carte n\'est jamais reçu par TerraFront</b> : il est saisi chez Stripe</td><td>Te livrer l\'objet, te rembourser si besoin, tenir la comptabilité</td></tr>\n'
       '    <tr><td><b>Date de naissance</b>, demandée au premier achat</td><td>Appliquer le plafond d\'achats des moins de 18 ans. Elle ne sert à rien d\'autre</td></tr>\n'
       '    <tr><td><b>Ton nom sur le Discord de TerraFront</b>, si tu y es</td><td>Le rapprocher de ton pseudo du jeu pour te donner le rôle et le salon de ton clan</td></tr>')
rep(K, 'Ce sont des éléments nécessaires au fonctionnement du jeu : ils ne demandent pas ton accord et ne servent à aucun suivi.</p>',
       'Ce sont des éléments nécessaires au fonctionnement du jeu : ils ne demandent pas ton accord et ne servent à aucun suivi. Le jeu tient aussi des comptages quotidiens (nombre de joueurs actifs, de paquets, de conquêtes) : ce sont des totaux, sans nom.</p>')
rep(K, '  <li><b>L\'intérêt légitime</b> de protéger le jeu contre la triche et les abus : journaux techniques.</li>',
       '  <li><b>Le contrat de vente et les obligations légales</b> (comptabilité, droits des consommateurs) : les achats en euros.</li>\n'
       '  <li><b>L\'intérêt légitime</b> de protéger le jeu contre la triche et les abus : journaux techniques, modération.</li>\n'
       '  <li><b>L\'intérêt légitime</b> de protéger les plus jeunes : la date de naissance pour le plafond d\'achats.</li>\n'
       '  <li><b>L\'intérêt légitime</b> de faire vivre les clans sur le Discord : le rapprochement de ton pseudo et de ton nom Discord. Tu peux t\'y opposer en écrivant à contact@terrafront.fr.</li>')
rep(K, '  <li><b>jsDelivr</b> et <b>cdnjs</b> : distribution de deux bibliothèques de code, qui voient passer ton adresse IP.</li>',
       '  <li><b>Stripe</b> (Irlande et États-Unis) : paiement par carte, seulement si tu achètes ;</li>\n'
       '  <li><b>Discord</b> (États-Unis) : seulement si tu as rejoint le serveur Discord de TerraFront ;</li>\n'
       '  <li>le service de notifications de ton navigateur (<b>Apple</b>, <b>Google</b> ou <b>Mozilla</b>) : seulement si tu actives les notifications.</li>')
rep(K, '  <li>Les journaux techniques : la courte durée fixée par les hébergeurs.</li>',
       '  <li>Les achats en euros : 10 ans, la durée imposée pour les pièces comptables, même après la suppression du compte (ils ne sont alors plus rattachés à ton compte).</li>\n'
       '  <li>La date de naissance : tant que tu as un compte.</li>\n'
       '  <li>Les journaux techniques : la courte durée fixée par les hébergeurs.</li>')

# ---------------------------------------------------------------- CGU
U = 'cgu.html'
rep(U, 'Dernière mise à jour : 6 octobre 2026', 'Dernière mise à jour : 23 novembre 2026')
rep(U, 'où les communes de France sont des cartes à collectionner : une commune n\'appartient qu\'à un seul joueur à la fois.',
       'où les communes de France, de Suisse, de Belgique et du Luxembourg sont des cartes à collectionner : sur le Front, une commune n\'appartient qu\'à un seul joueur à la fois. Jouer est gratuit ; des objets d\'apparence et un pass de saison peuvent être achetés en euros, aux <a href="cgv.html">conditions générales de vente</a>.')
rep(U, 'Tu es responsable de ce que tu écris (pseudo, messages d\'échange).',
       'Tu es responsable de ce que tu écris et de ce que tu crées (pseudo, messages, motif de territoire). Dans le jeu, un bouton permet de signaler un message de la discussion ou un motif.')
rep(U, 'Tu peux contester une décision en écrivant à <a href="mailto:contact@terrafront.fr">contact@terrafront.fr</a>.</p>',
       'Avant une suppression de compte, tu reçois le motif par e-mail et tu as 15 jours pour contester. Pour toute autre sanction, tu peux en demander le motif et la contester en écrivant à <a href="mailto:contact@terrafront.fr">contact@terrafront.fr</a> : elle est alors réexaminée par l\'éditeur, qui te répond. Le sort des objets achetés en euros est fixé par les conditions générales de vente.</p>')
rep(U, 'Le jeu est fourni tel quel, sans garantie qu\'il soit toujours disponible ou sans erreur.',
       'L\'éditeur fait de son mieux pour que le jeu reste disponible et sans erreur, mais ne peut pas le promettre à chaque instant.')
rep(U, 'dans ce cas, les joueurs seront prévenus à l\'avance dans le jeu et sur le Discord.</p>',
       'dans ce cas, les joueurs seront prévenus à l\'avance dans le jeu et sur le Discord. Rien de ceci ne retire les droits que la loi te donne, notamment pour tes achats (voir les conditions générales de vente).</p>')
rep(U, 'Les changements importants sont annoncés dans le jeu ou sur le Discord ; continuer à jouer vaut acceptation de la nouvelle version.</p>',
       'Les changements importants sont annoncés dans le jeu (la cloche, « Nouveautés et correctifs ») ou sur le Discord au moins 7 jours avant de s\'appliquer, sauf urgence de sécurité ou obligation légale. Si tu n\'es pas d\'accord, tu peux supprimer ton compte à tout moment. Un changement de ces conditions ne modifie jamais un achat déjà fait.</p>')

# ---------------------------------------------------------------- mentions légales
M = 'mentions-legales.html'
rep(M, 'Dernière mise à jour : 20 octobre 2026', 'Dernière mise à jour : 23 novembre 2026')
rep(M, 'proviennent de données publiques ouvertes de l\'INSEE et de l\'IGN, réutilisées selon leurs licences. Les noms des habitants proviennent de Wikipédia.',
       'proviennent de données publiques ouvertes de l\'INSEE, de l\'IGN et d\'Etalab (geo.api.gouv.fr, « Contours administratifs »), réutilisées sous Licence Ouverte 2.0. Les noms des habitants proviennent de Wikipédia, sous licence CC BY-SA 4.0.')

# ---------------------------------------------------------------- les nouveautés (les CGU promettent d'annoncer les changements)
p = os.path.join(R, 'data', 'nouveautes.json'); d = json.load(open(p, encoding='utf-8'))
l = "📜 Pages légales mises à jour (conditions d'utilisation, conditions de vente v5, confidentialité, mentions légales) : garanties légales détaillées, données d'achat et Discord décrits, changements des règles annoncés 7 jours à l'avance. Rien ne change pour tes achats déjà faits."
e = d[0]
if l not in e['nouveautes']: e['nouveautes'].insert(0, l)
json.dump(d, open(p, 'w', encoding='utf-8'), ensure_ascii=False, indent=2); print('nouveautes.json : ok')
