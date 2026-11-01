# Les clans sur le Discord, tout seuls (2 novembre 2026)

Avant : lancer `clans-discord.sql` dans Supabase, coller le résultat dans
`clans.json`, lancer `clans-discord.py` sur le Mac. Maintenant : une fonction
Supabase fait le même travail **toutes les 10 minutes**, sans le Mac.

Ce que fait le bot à chaque passage (comme `clans-discord.py`) : catégorie
« 🏰 Clans » et salon « 🏰│recrutement-clans » ; pour chaque clan, un rôle
« 🏰 [SIGLE] Nom » à sa couleur et un salon privé (message d'accueil à la
création) ; le rôle donné aux membres du clan présents sur le Discord, retiré à
ceux qui sont partis ; le chef peut inviter dans son salon, un ancien chef plus ;
un clan dissous : son rôle est vidé, le salon reste.

Fichiers :
- `fonction-discord-clans/index.ts` : la fonction Edge `discord-clans`.
- `clans-auto.sql` : tables, secret, lancement, pg_cron (départ en **simulation**).
- `clans-auto-tester.sql`, `clans-auto-journal.sql`, `clans-auto-activer.sql`,
  `clans-auto-arreter.sql` : piloter.
- `correspondances-import.sql` (sur le Mac seulement, **pas sur GitHub**) :
  reprend `correspondances.json` dans la table `discord_correspondances`.

## Mise en place (une fois)

1. **Supabase > Database > Extensions** : activer **pg_net** (pg_cron l'est déjà).
2. **Éditeur SQL** : lancer `clans-auto.sql`.
   Contrôle : `simulation | true | true | true | true`.
3. Lancer `correspondances-import.sql` (les pseudos qui diffèrent entre le jeu
   et le Discord).
4. **Edge Functions > Secrets** : ajouter `DISCORD_BOT_TOKEN` = le jeton du bot
   (le même que `~/.terrafront-bot`). Pour le copier sans l'afficher, dans le
   Terminal : `pbcopy < ~/.terrafront-bot`, puis coller dans Supabase.
   Le jeton ne va jamais dans le code ni sur GitHub.
5. **Edge Functions > Deploy a new function > Via Editor** : nom
   **`discord-clans`**, coller tout `fonction-discord-clans/index.ts`, déployer.
   Puis dans les réglages de la fonction : **Verify JWT désactivé**
   (l'appel est protégé par un secret tiré au hasard dans la base).
6. **Tester** : lancer `clans-auto-tester.sql`, attendre 30 secondes, lancer
   `clans-auto-journal.sql`. La 1re ligne doit être `ok = true` en mode
   `simulation`, avec la liste de ce que le bot ferait (`SIMULÉ …`).
   Normalement : presque rien, puisque `clans-discord.py` est déjà passé ;
   les nouveaux clans apparaissent (« rôle … », « salon privé … »).
7. **Si la liste te va** : lancer `clans-auto-activer.sql`. Le bot agit tout
   de suite, puis toutes les 10 minutes.

## Au quotidien

- **Rien à faire.** Un passage sans changement n'écrit rien dans le journal.
- `clans-auto-journal.sql` : ce qui a été fait, les joueurs pas reconnus sur le
  Discord (`introuvables`), les refus de Discord.
- Un joueur pas reconnu (pseudo Discord différent) : l'ajouter dans
  `discord_correspondances` (pseudo du jeu, nom d'utilisateur Discord).
- Arrêter : `clans-auto-arreter.sql`. Le journal garde 14 jours.
- `clans-discord.py` reste utilisable à la main, mais ne pas faire tourner les
  deux en même temps.

## Si ça bloque

- Journal `ok = false` « Secret DISCORD_BOT_TOKEN manquant » : étape 4.
- Rien dans le journal après un test : la fonction n'est pas déployée sous ce
  nom exact, ou Verify JWT est resté activé (étape 5). Les réponses de pg_net :
  `select status_code, content from net._http_response order by id desc limit 3;`
- « Gérer les permissions » refusé pour un chef : le donner à la main une fois
  (clic droit sur le salon › Modifier › Permissions) ; le bot ne réessaie plus
  ensuite.
