# Boutique en euros — mise en place

Préparé le 19 octobre 2026. **Rien n'est en vente** : tous les articles sont
créés inactifs, et rien ne fonctionne sans les clés Stripe. Ce dossier ne
touche à aucune table ni fonction existante du jeu, et n'est pas publié par
GitHub Pages.

Testé : les fonctions SQL sur une base locale (paiement, rejeu, livraison
différée, plafond des mineurs, OG, remboursement, droits) ; les deux
fonctions Edge passent la vérification de types, et la vérification de
signature Stripe rejette un message modifié ou non signé.

## Comment ça marche

1. Le joueur choisit un objet, coche les cases, clique « Payer et recevoir l'objet ».
2. Le jeu appelle la fonction Edge `creer-paiement`, qui contrôle tout dans la
   base (`euros_preparer_commande`) puis crée la page de paiement Stripe avec
   le prix de la base.
3. Le joueur paie sur la page de Stripe (TerraFront ne voit jamais la carte).
4. Stripe prévient la fonction Edge `stripe-webhook`, qui vérifie la signature
   puis appelle `euros_confirmer_paiement` : objet livré tout de suite, ou dans
   14 jours si le joueur a gardé son droit de rétractation.
5. Un remboursement ou une contestation retire l'objet automatiquement.

## Mise en place (mode test d'abord)

1. **Base** : coller dans l'éditeur SQL de Supabase, dans l'ordre,
   `1-tables.sql`, `2-fonctions.sql`, puis (après avoir activé l'extension
   pg_cron) `3-livraisons-cron.sql`. Le contrôle final de `2-fonctions.sql`
   doit afficher `t | t`.
2. **Stripe** : rester en **mode test**. Récupérer la clé secrète de test
   (`sk_test_...`).
3. **Supabase > Edge Functions > Secrets** : ajouter `STRIPE_SECRET_KEY`
   et `SITE_URL` (`https://terrafront.fr`). La clé secrète ne va JAMAIS
   dans le code ni sur GitHub.
4. **Supabase > Edge Functions** : créer `creer-paiement` (vérification du
   JWT activée) et `stripe-webhook` (vérification du JWT **désactivée**),
   en collant le contenu des fichiers `fonctions/…/index.ts`.
5. **Stripe > Développeurs > Webhooks** : ajouter l'adresse
   `https://<projet>.supabase.co/functions/v1/stripe-webhook`, cocher les
   5 événements listés en tête de `stripe-webhook/index.ts`, puis copier le
   secret `whsec_...` dans le secret Supabase `STRIPE_WEBHOOK_SECRET`.
6. **Tester** avec les cartes de test Stripe (4242 4242 4242 4242, 3D Secure
   4000 0027 6000 3184, refusée 4000 0000 0000 0002).

## Ce qui reste à faire avant les vraies ventes

- [ ] L'écran de la boutique et de la garde-robe dans le jeu (aperçu d'abord).
- [ ] **Email de confirmation (Resend)** : le code est prêt dans
      `stripe-webhook` (objet, prix, date, choix sur la rétractation, CGV
      jointes). À faire : vérifier le domaine terrafront.fr dans Resend
      (enregistrements DNS à ajouter chez OVH), créer une clé « envoi
      seulement », puis ajouter les secrets `RESEND_API_KEY` et
      `EMAIL_EXPEDITEUR` (`TerraFront <boutique@terrafront.fr>`).
- [ ] Publier le PDF des CGV définitives (par exemple
      `https://terrafront.fr/cgv/cgv-2026-10-19-v3.pdf`) et mettre son
      adresse dans `euros_reglages` (`cgv_pdf_url`) : il est joint à chaque
      email (support durable). Changer de PDF à chaque nouvelle version.
- [ ] Le bandeau de financement (`euros_bandeau()` est prêt).
- [ ] L'avertissement avant suppression de compte (CGV art. 4).
- [ ] Le pass de saison : la progression n'existe pas encore ; ne pas
      activer d'article `pass` avant.
- [ ] Vérifier le taux de prélèvements dans `euros_reglages`
      (`taux_prelevements`, 0,229 par défaut : à confirmer sur le site de
      l'URSSAF).
- [ ] SIRET + médiateur dans les CGV, puis passage en clés `live`.

## Réglages utiles (table `euros_reglages`)

| Clé | Valeur | Rôle |
| --- | --- | --- |
| `cgv_version` | `2026-10-19-v3` | à changer à chaque nouvelle version des CGV : les commandes en cours avec l'ancienne sont refusées |
| `plafond_mineur_centimes` | 1500 | 15 € par mois civil avant 18 ans |
| `age_minimum` | 15 | âge minimum pour acheter |
| `objectif_mois_centimes` | 3000 | étape 1 du bandeau (frais du mois) |
| `objectif_app_centimes` | 12400 | étape 2 du bandeau (application mobile) |

Pour activer un article : `update euros_articles set actif = true where id = '…';`

## En cas de problème

- Une commande en `a_verifier` : le montant reçu ne correspond pas au prix
  (voir la colonne `note`). Rien n'est livré ; vérifier dans Stripe et
  rembourser si besoin.
- Remboursement partiel : non géré automatiquement, à traiter à la main.
- Contestation gagnée par toi : l'objet a été retiré ; le rendre à la main
  (`insert into euros_inventaire …`).
