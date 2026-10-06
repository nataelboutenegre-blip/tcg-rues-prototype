# -*- coding: utf-8 -*-
u"""
Fabrique les trois pages d'information de TerraFront (patch75) :
mentions-legales.html, confidentialite.html, cgu.html.
Même en-tête et même pied pour les trois. À relancer après une
modification du texte ci-dessous, puis maj-version.py.
"""
import io, os

ICI = os.path.dirname(os.path.abspath(__file__))
BASE = os.path.dirname(ICI) if os.path.basename(ICI) == '_patchs' else ICI
MAJ = u'6 octobre 2026'
CONTACT = u'<a href="mailto:contact@terrafront.fr">contact@terrafront.fr</a>'

PAGES = [
    ('mentions-legales.html', u'Mentions légales'),
    ('confidentialite.html', u'Confidentialité'),
    ('cgu.html', u"Conditions d'utilisation"),
]

def page(fichier, titre, description, corps):
    nav = u''.join(
        u'<a href="%s"%s>%s</a>' % (f, u' aria-current="page"' if f == fichier else u'', t)
        for f, t in PAGES)
    return u'''<!doctype html>
<html lang="fr">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>%(titre)s — TerraFront</title>
<meta name="description" content="%(description)s">
<meta name="theme-color" content="#0F1F38">
<link rel="icon" type="image/png" href="favicon.png">
<link rel="stylesheet" href="fonts/polices.css">
<link rel="stylesheet" href="pages.css">
</head>
<body>
<header class="pg-tete"><div class="pg-tete-int">
  <a class="pg-marque" href="./">Terra<span>Front</span></a>
  <nav class="pg-nav" aria-label="Informations">%(nav)s</nav>
</div></header>
<main>
<h1>%(titre)s</h1>
<p class="pg-maj">Dernière mise à jour : %(maj)s</p>
%(corps)s
<a class="pg-retour" href="./">Retour au jeu</a>
</main>
<footer class="pg-pied"><div class="pg-pied-int">
  <span>TerraFront — un jeu indépendant, fait en France.</span>
  %(nav)s
</div></footer>
</body>
</html>
''' % dict(titre=titre, description=description, nav=nav, maj=MAJ, corps=corps)

# ---------------------------------------------------------------------
MENTIONS = u'''
<h2>Éditeur du site</h2>
<div class="pg-bloc">
  <p><b>Nataël Boutenegre</b>, particulier</p>
  <p>Contact : %(contact)s</p>
  <p>Directeur de la publication : Nataël Boutenegre</p>
</div>

<h2>Hébergement</h2>
<h3>Le site</h3>
<div class="pg-bloc">
  <p><b>GitHub, Inc.</b> (service GitHub Pages)</p>
  <p>88 Colin P. Kelly Jr. Street, San Francisco, CA 94107, États-Unis</p>
  <p><a href="https://github.com" rel="noopener">github.com</a></p>
</div>
<h3>Les comptes et les données du jeu</h3>
<div class="pg-bloc">
  <p><b>Supabase Pte. Ltd.</b></p>
  <p>65 Chulia Street #38-02/03, OCBC Centre, Singapour 049513</p>
  <p>Les données sont stockées sur des serveurs situés dans l'Union européenne.</p>
  <p><a href="https://supabase.com" rel="noopener">supabase.com</a></p>
</div>
<h3>Le nom de domaine</h3>
<div class="pg-bloc">
  <p><b>OVH SAS</b>, 2 rue Kellermann, 59100 Roubaix, France</p>
</div>

<h2>Propriété intellectuelle</h2>
<p>Le jeu TerraFront, son code, ses règles, ses textes et ses visuels (cartes, logo, illustrations) sont la propriété de leur auteur. Toute reproduction sans autorisation est interdite.</p>
<p>Les informations sur les communes (noms, codes, populations, contours) proviennent de données publiques ouvertes de l'INSEE et de l'IGN, réutilisées selon leurs licences. Les noms des habitants proviennent de Wikipédia.</p>
<p>Les photos de monuments proviennent de Wikimedia Commons : leur auteur et leur licence sont indiqués sous chaque photo.</p>
<p>Les polices Big Shoulders Display et Instrument Sans sont distribuées sous licence SIL Open Font License 1.1.</p>

<h2>Signaler un problème</h2>
<p>Pour signaler un contenu (un pseudo, un message), un bug ou une atteinte à tes droits, écris à %(contact)s.</p>
''' % dict(contact=CONTACT)

# ---------------------------------------------------------------------
CONFIDENTIALITE = u'''
<p class="pg-intro">TerraFront ne collecte que ce qu'il faut pour faire tourner le jeu. <b>Pas de publicité, pas de revente de données, pas de traceurs publicitaires.</b></p>

<h2>Qui est responsable de tes données</h2>
<p>Nataël Boutenegre, éditeur du jeu. Pour toute question : %(contact)s.</p>

<h2>Ce que le jeu enregistre</h2>
<div class="pg-defile"><table class="pg-tableau">
  <thead><tr><th>Données</th><th>Pourquoi</th></tr></thead>
  <tbody>
    <tr><td><b>Adresse e-mail et mot de passe</b> (le mot de passe est enregistré sous une forme brouillée que personne ne peut relire)</td><td>Créer ton compte, te connecter, réinitialiser ton mot de passe</td></tr>
    <tr><td><b>Pseudo et avatar</b></td><td>Te désigner auprès des autres joueurs : ils sont <b>visibles par tous</b> (carte, classement, journal, combats)</td></tr>
    <tr><td><b>Ta partie</b> : communes, points, paquets, combats, échanges, amis, succès, Commune du jour, Radar</td><td>Faire fonctionner le jeu</td></tr>
    <tr><td><b>Messages joints aux échanges</b></td><td>Les transmettre au joueur concerné</td></tr>
    <tr><td><b>Abonnement aux notifications</b>, si tu les actives</td><td>T'envoyer des alertes. Tu peux les couper dans le jeu ou dans ton navigateur</td></tr>
    <tr><td><b>Adresse IP et journaux techniques</b>, gardés par les hébergeurs</td><td>Sécurité du service et lutte contre les abus</td></tr>
  </tbody>
</table></div>
<p>Ton navigateur garde aussi, sur ton appareil, ta session de connexion et tes réglages (son, animations…). Ce sont des éléments nécessaires au fonctionnement du jeu : ils ne demandent pas ton accord et ne servent à aucun suivi.</p>

<h2>Sur quelle base</h2>
<ul>
  <li><b>L'exécution du service</b> que tu demandes en créant un compte (les conditions d'utilisation) : compte, partie, messages.</li>
  <li><b>L'intérêt légitime</b> de protéger le jeu contre la triche et les abus : journaux techniques.</li>
  <li><b>Ton accord</b> pour les notifications, que tu peux retirer à tout moment.</li>
</ul>

<h2>Qui y a accès</h2>
<p>Seul l'éditeur, et les prestataires techniques qui font tourner le jeu, chacun pour sa tâche :</p>
<ul>
  <li><b>Supabase</b> : base de données et comptes, serveurs dans l'Union européenne ;</li>
  <li><b>GitHub</b> (États-Unis) : hébergement des pages du site ;</li>
  <li><b>Resend</b> (États-Unis) : envoi des e-mails de compte (confirmation, mot de passe oublié) ;</li>
  <li><b>jsDelivr</b> et <b>cdnjs</b> : distribution de deux bibliothèques de code, qui voient passer ton adresse IP.</li>
</ul>
<p>Les transferts vers les États-Unis sont encadrés par les garanties prévues par le RGPD (cadre de protection des données UE–États-Unis ou clauses contractuelles types de la Commission européenne). Tes données ne sont <b>ni vendues ni louées</b>.</p>

<h2>Combien de temps</h2>
<ul>
  <li>Ton compte et ta partie : tant que tu as un compte. Un compte resté sans connexion pendant 3 ans peut être supprimé, après un e-mail de prévenance.</li>
  <li>Les journaux techniques : la courte durée fixée par les hébergeurs.</li>
  <li>Après la suppression de ton compte, seules restent des traces anonymes : le journal du jeu affiche « un joueur », les classements de saison « Joueur supprimé ».</li>
</ul>

<h2>Supprimer ton compte</h2>
<p>Depuis l'onglet <b>Profil</b> du jeu, bouton « Supprimer mon compte », ou en écrivant à %(contact)s depuis l'adresse de ton compte. La suppression est définitive : tes communes retournent dans les paquets ; ton e-mail, ton pseudo, tes amis, tes échanges et leurs messages sont effacés.</p>

<h2>Tes droits</h2>
<p>Tu peux demander à accéder à tes données, les corriger, les effacer, en recevoir une copie, limiter ou refuser leur utilisation. Écris à %(contact)s : réponse sous un mois au plus.</p>
<p>Si tu estimes que tes droits ne sont pas respectés, tu peux saisir la CNIL : <a href="https://www.cnil.fr/fr/plaintes" rel="noopener">cnil.fr/fr/plaintes</a>.</p>

<h2>Mineurs</h2>
<p>Le jeu est ouvert à partir de 15 ans. Avant 15 ans, il faut l'accord d'un parent.</p>
''' % dict(contact=CONTACT)

# ---------------------------------------------------------------------
CGU = u'''
<p class="pg-intro">En créant un compte, tu acceptes ces règles. Elles sont faites pour que le jeu reste juste et agréable pour tout le monde.</p>

<h2>1. Le jeu</h2>
<p>TerraFront est un jeu gratuit, dans le navigateur, où les communes de France sont des cartes à collectionner : une commune n'appartient qu'à un seul joueur à la fois. Il est édité par Nataël Boutenegre (voir les <a href="mentions-legales.html">mentions légales</a>).</p>

<h2>2. Ton compte</h2>
<ul>
  <li>Le jeu est ouvert <b>à partir de 15 ans</b>, ou plus jeune avec l'accord d'un parent.</li>
  <li><b>Un seul compte par personne.</b> Les comptes multiples sont interdits.</li>
  <li>Tu es responsable de ton compte et de ton mot de passe. Ne les partage pas.</li>
  <li>Ton pseudo est visible par tous : pas d'insulte, de propos haineux ou sexuels, de nom d'une autre personne ou de marque. L'éditeur peut modifier un pseudo qui ne respecte pas ces règles.</li>
</ul>

<h2>3. Jouer franc-jeu</h2>
<p>Sont interdits :</p>
<ul>
  <li>la triche, les programmes ou scripts qui jouent à ta place, l'exploitation volontaire d'un bug (signale-le plutôt) ;</li>
  <li>les comptes multiples ou partagés pour s'avantager ;</li>
  <li>le harcèlement, les insultes ou les menaces envers d'autres joueurs, notamment dans les messages d'échange ;</li>
  <li>la vente ou l'achat de comptes, de cartes ou de points contre de l'argent réel ou tout autre bien hors du jeu.</li>
</ul>

<h2>4. Points, cartes et objets du jeu</h2>
<p>Les points, cartes, communes, paquets et autres objets du jeu sont des éléments virtuels : <b>ils n'ont aucune valeur en argent</b>, ne peuvent pas être convertis en argent et ne t'appartiennent pas en dehors du jeu. Ils peuvent être modifiés, rééquilibrés ou remis à zéro, notamment à la fin d'une saison, selon les règles annoncées dans le jeu.</p>

<h2>5. Ce que les joueurs écrivent</h2>
<p>Tu es responsable de ce que tu écris (pseudo, messages d'échange). Pour signaler un contenu choquant ou illégal, écris à <a href="mailto:contact@terrafront.fr">contact@terrafront.fr</a> en indiquant le pseudo concerné et ce qui pose problème. Les signalements sont examinés au plus vite ; un contenu manifestement illégal est retiré.</p>

<h2>6. Sanctions</h2>
<p>Si ces règles ne sont pas respectées, l'éditeur peut, selon la gravité : avertir, retirer un contenu, annuler des gains obtenus en trichant, suspendre ou supprimer un compte. Tu peux contester une décision en écrivant à <a href="mailto:contact@terrafront.fr">contact@terrafront.fr</a>.</p>

<h2>7. Un jeu qui évolue</h2>
<p>TerraFront est développé par une seule personne et change souvent : règles, équilibrage, saisons, fonctions. Le jeu est fourni tel quel, sans garantie qu'il soit toujours disponible ou sans erreur. Il peut être interrompu pour maintenance ou, à terme, arrêté ; dans ce cas, les joueurs seront prévenus à l'avance dans le jeu et sur le Discord.</p>

<h2>8. Supprimer ton compte</h2>
<p>Tu peux supprimer ton compte à tout moment, depuis l'onglet Profil ou en écrivant à <a href="mailto:contact@terrafront.fr">contact@terrafront.fr</a>. Ce qu'il advient de tes données est détaillé dans la <a href="confidentialite.html">politique de confidentialité</a>.</p>

<h2>9. Données personnelles</h2>
<p>Voir la <a href="confidentialite.html">politique de confidentialité</a>.</p>

<h2>10. Changements de ces conditions</h2>
<p>Ces conditions peuvent évoluer avec le jeu. Les changements importants sont annoncés dans le jeu ou sur le Discord ; continuer à jouer vaut acceptation de la nouvelle version.</p>

<h2>11. Droit applicable</h2>
<p>Ces conditions sont soumises au droit français. En cas de désaccord, écris d'abord à <a href="mailto:contact@terrafront.fr">contact@terrafront.fr</a> : on cherchera une solution à l'amiable.</p>
'''

def ecrire(nom, texte):
    with io.open(os.path.join(BASE, nom), 'w', encoding='utf-8') as f:
        f.write(texte)

ecrire('mentions-legales.html', page('mentions-legales.html', u'Mentions légales',
       u"Mentions légales de TerraFront : éditeur, hébergeurs, propriété intellectuelle.", MENTIONS))
ecrire('confidentialite.html', page('confidentialite.html', u'Confidentialité',
       u"Ce que TerraFront enregistre, pourquoi, combien de temps, et tes droits.", CONFIDENTIALITE))
ecrire('cgu.html', page('cgu.html', u"Conditions d'utilisation",
       u"Les règles d'utilisation de TerraFront.", CGU))
print(u'pages légales : OK')
