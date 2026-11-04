# TerraFront — dossier d'équilibrage du Front (saison 2, 4/11/2026)

Ce dossier rassemble les règles et les chiffres du Front, pour réfléchir à l'équilibrage avec une IA ou entre joueurs. Il va avec le tableau de la lecture `lecture-equilibrage-partage.sql` : colle ce tableau à la fin de ce fichier (section « Chiffres du jour »).

Le tableau ne contient que des chiffres agrégés : aucun pseudo, aucune commune, aucun emplacement de bâtiment.

## Comment s'en servir
- Propose des changements **chiffrés** (« la Forteresse passe de −15 % à −10 % »), avec l'effet attendu et ce qu'il pourrait casser.
- Pense à **trois profils** : le gros joueur très présent, le joueur qui passe une fois par jour, le nouveau qui arrive en cours de saison.
- Les décisions restent à Nataël.

## Principes du jeu (à respecter dans les propositions)
- **Une seule nouvelle décision à la fois** pour le joueur : on ajoute peu, et progressivement.
- **Rien de proportionnel au nombre de communes** (production, nombre de bâtiments) : sinon les gros joueurs grossissent encore plus vite.
- **Terra ne donne aucune force au Front**, et rien de ce qui aide à gagner ne s'achète.
- **Jouable sur téléphone, en quelques minutes**. Rester simple et épuré.

## La carte et les paquets
- Environ **35 000 communes de France**, une seule propriétaire par commune. La carte repart à chaque saison.
- **Raretés selon la population** :

| Rareté | Population | Communes |
|---|---|---|
| Légendaire | 30 000 et plus | 302 |
| Épique | 8 000 à 29 999 | 1 015 |
| Rare | 2 300 à 7 999 | 3 406 |
| Peu commune | 450 à 2 299 | 12 841 |
| Commune | moins de 450 | 17 183 |

- Les **129 communes d'outre-mer** forment un set à part, avec leurs propres raretés.
- **Paquets du Front** : gratuits uniquement, rien ne s'achète. Un paquet toutes les **20 min**, **3 en réserve**, **5 communes** par paquet, toutes raretés. Une commune de la liste Aurore sort en Aurore une fois sur trois. Les chances exactes par rareté ne sont pas dans ce dossier.
- **Réserve d'accueil** : quand il reste **3 000 communes libres ou moins** dans le pot, un compte de plus de **7 jours** ne peut plus ouvrir de paquet du Front (le paquet est gardé). Les nouveaux tirent normalement.

## Combat
- **Énergie** : **50 au maximum**, **1 toutes les 10 min**.
  - Quêtes du Front : +5 chacune, **35 par jour au plus**.
  - Chaque légendaire tenue depuis 24 h : **+2 par jour** (10 au plus), à récolter à la main.
  - Ces deux sources peuvent faire dépasser le maximum, jusqu'à 60.
- **Engagement** (choisi avant chaque assaut) : **prudent 1 énergie / 35 %**, **normal 2 / 50 %**, **offensif 3 / 65 %**. Le coût ne dépend pas de la rareté de la cible.
- **Proximité** : le jeu compte tes communes à moins de **20 km** de la cible et ajoute un bonus (valeurs exactes dans le tableau, ligne RÉGLAGES). Sans aucune commune proche, c'est une attaque à distance, avec un malus.
- **Bâtiments et bombe** : Forteresse **−15 %** pour les attaquants sur sa commune, **+5 %** aux attaques de son propriétaire à moins de 20 km (une seule compte). Bombe **+15 %** pour tous dans sa zone pendant 24 h.
- **Bornes** : les chances restent entre **10 et 90 %**.
- **Conquête** : **3 rounds gagnés**, pas forcément d'affilée ; une défaite ne fait rien perdre.
- **Délai entre deux assauts sur la même commune** : commune 2 min, peu commune 5 min, rare 10 min, épique 1 h, légendaire 3 h. On peut attaquer plusieurs communes en parallèle.
- **Protection** : une commune prise est protégée **3 h**.
- **Course à la commune** : quand un joueur prend une commune, les sièges des autres attaquants sur elle sont effacés.

## Défense
- **Défense à la main** : quand un attaquant gagne un round, le défenseur peut tenter une défense pour **1 énergie**, **deux fois par attaque**. Réussie, l'attaquant perd une victoire.
  - Une défense utilisée **revient 24 h après la dernière défense** (deux au plus).
  - Si la série de l'attaquant retombe à zéro, le défenseur les récupère toutes.
- **Garnison** : sur **3 communes au plus**, jusqu'à **10 énergie** par commune.
  - Quand un attaquant gagne un round, la garnison tente seule une défense : **1 chance sur 2**, **1 énergie** par tentative. Réussie, la victoire ne compte pas.
  - Retirer une garnison rend les trois quarts de son énergie.
  - Une défense réussie à la main sur une commune en garnison y remet 3 énergie.
  - L'attaquant voit qu'il y a une garnison, pas combien elle contient.

## Bâtiments et lingots
- **Lingots** : ils ne servent qu'aux bâtiments, ne s'échangent pas et repartent à zéro chaque saison.
- **Fonderie** : la 1re est gratuite, **10 lingots par jour**, réserve de **30**. La **2e coûte 30 lingots** : 10 de plus par jour, réserve de **45**.
- **Combats** : **+2** lingots par commune conquise, **+1** par défense réussie, **10 par jour au plus**.
- **Forteresse** : **20 lingots**, **3 au plus** (effets dans « Combat »).
- **Construction** : **6 h** pour tout bâtiment, annulable pendant ce temps (lingots rendus, sauf pendant un assaut sur la commune).
- **Perte** : un bâtiment disparaît si sa commune est prise. Prendre une Fonderie pille la **moitié** des lingots de son propriétaire (le **quart** s'il en a deux).
- **Centre de recherche** : **40 lingots**, il faut **2 Fonderies**, un seul par joueur. Il est **secret** sur la carte.
- **Bombe** :
  - **Préparation** : **45 lingots**, annoncée à tous avec le département, sans le nom.
  - **Rayon** : **10 km** à 24 h, **15 km** à 48 h, **20 km** à 72 h.
  - **Visibilité** : à partir de **48 h** de préparation, le centre apparaît sur la carte ; s'il est pris, la bombe est perdue.
  - **Cible** : une commune à moins de **50 km** des communes du lanceur.
  - **Effet** : détruit garnisons et Forteresses de **tout le monde** dans la zone, puis **+15 %** aux attaques de tous dans la zone pendant 24 h. Aucune commune n'est prise.
  - **Limite** : pas de bombe à moins de 20 km d'une zone encore active.

## Score du Front (classement)
- **Chaque commune tenue** : 1 (commune) · 3 (peu commune) · 12 (rare) · 25 (épique) · 60 (légendaire).
- **Victoire** (conquête, défense, garnison qui repousse) : **+10**, 10 par jour au plus, 2 par jour contre un même joueur. Elle compte une seule fois par commune et par type.
- **Département** (seul le meilleur palier compte, métropole seulement) :
  - 5 % (seul en tête, au moins 5 communes) **+100** ;
  - 10 % (seul en tête) **+200** ;
  - 25 % (seul en tête) **+300** ;
  - 50 % **+600** ; 75 % **+900** ; 100 % **+1 400**.
- **Région** : **+1 200** si plus de la moitié de ses départements sont à 10 % ou plus.
- **TerraPoints gagnés au Front** :
  - conquête +5 / +10 / +25 / +50 / +100 selon la rareté ; défense réussie +10 ;
  - **250 TP par jour au plus** ;
  - reprendre une commune perdue depuis moins de 24 h ne rapporte rien, et reprendre plusieurs fois la même commune au même joueur rapporte de moins en moins.

## Clans
- **8 joueurs au plus**, pas d'attaque entre membres.
- **Échanges de clan** :
  - une commune contre une de même rareté, entre membres depuis 48 h ;
  - **3 par jour avec chaque coéquipier**, et 3 propositions en attente par coéquipier ;
  - pas une commune prise il y a moins de 24 h, en garnison, ou échangée il y a moins de 48 h.
- **Classement des clans** : moyenne des membres actifs (jeu ouvert dans les 7 jours), 3 membres au moins pour être classé.

## Saison
- **4 semaines**. Chacun garde **5 communes** pour la saison suivante (une seule légendaire).
- À la fin, le classement est figé et les autres communes retournent au pot.
- Ta collection Terra reçoit tes 5 communes gardées et toutes tes communes d'un département tenu à plus de 45 %.
- **Outre-mer** : toutes tes communes d'un même territoire comptent comme voisines, même loin. Pas de bonus de département ni de région.

## Ce que le tableau ne mesure pas
L'énergie dépensée, les garnisons, le nombre réel de défenses à la main (le score ne les compte qu'une fois par commune), les chances par rareté des paquets.

## Questions ouvertes (à garder ou retirer avant d'envoyer)
- Une légendaire coûte la même énergie qu'une commune : faut-il un supplément ?
- Le pot se vide vite : la réserve d'accueil suffit-elle pour les nouveaux ?
- Les joueurs absents perdent-ils leurs communes trop vite, ou pas assez ?
- Les bâtiments (Forteresse, bombe) changent-ils assez les combats ?

## Chiffres du jour
(colle ici le tableau de `lecture-equilibrage-partage.sql`, avec sa date)
