-- ===========================================================================
--  TerraFront — boutique en euros : 18. diagnostic d'une commande non reçue
--  Lecture seule, ne modifie rien. Les commandes des 3 derniers jours,
--  la plus récente en premier, avec ce qui est arrivé dans l'inventaire.
--  Lire la colonne « diagnostic ».
-- ===========================================================================

select c.cree_le at time zone 'Europe/Paris'                    as creee,
       j.pseudo,
       c.nom_article,
       round(c.prix_centimes / 100.0, 2)                        as prix_eur,
       c.livraison,
       c.statut,
       c.payee_le at time zone 'Europe/Paris'                   as payee,
       c.livrer_apres at time zone 'Europe/Paris'               as livrer_apres,
       c.livree_le at time zone 'Europe/Paris'                  as livree,
       (select count(*) from public.euros_inventaire i where i.commande_id = c.id) as objets_livres,
       (c.stripe_session is not null)                           as session_stripe,
       (c.stripe_paiement is not null)                          as paiement_stripe,
       c.case_immediate, c.case_renonciation,
       c.note,
       case
         when c.statut = 'livree' and exists (select 1 from public.euros_inventaire i where i.commande_id = c.id)
           then 'livrée : l''objet est dans son inventaire (Profil › Personnaliser)'
         when c.statut = 'livree' then 'livrée mais rien dans l''inventaire : à corriger'
         when c.statut = 'payee' and c.livraison = 'differee'
           then 'payée, livraison à 14 jours (cases de renonciation non cochées) : prévue le ' || to_char(c.livrer_apres at time zone 'Europe/Paris', 'DD/MM HH24:MI')
         when c.statut = 'payee' then 'payée en livraison immédiate mais pas livrée : à corriger'
         when c.statut = 'a_verifier' then 'payée mais montant inattendu : rien livré, voir la note'
         when c.statut = 'creee' and c.stripe_session is null then 'paiement jamais ouvert chez Stripe'
         when c.statut = 'creee' then 'paiement ouvert chez Stripe mais confirmation jamais reçue (webhook) : vérifier Stripe'
         when c.statut = 'annulee' then 'annulée : ' || coalesce(c.note, 'sans détail')
         else c.statut
       end as diagnostic
  from public.euros_commandes c
  left join public.joueurs j on j.id = c.joueur_id
 where c.cree_le > now() - interval '3 days'
 order by c.cree_le desc
 limit 30;
