-- ===========================================================================
--  TerraFront — boutique en euros : 8. suivre les commandes de test
--  Lecture seule. À relancer après chaque achat test : les 10 dernières
--  commandes, avec ce qui a été livré dans l'inventaire.
--  Attendu après un achat réussi : statut « livree » (livraison immédiate)
--  ou « payee » avec une date livrer_apres (livraison à 14 jours), et
--  « dans_inventaire » à true pour une commande livrée.
-- ===========================================================================

select c.cree_le, j.pseudo, c.nom_article, c.prix_centimes, c.livraison, c.statut,
       c.livrer_apres, c.retractation_le, c.remboursee_le,
       (i.article_id is not null) as dans_inventaire, c.note
  from public.euros_commandes c
  left join public.joueurs j on j.id = c.joueur_id
  left join public.euros_inventaire i on i.commande_id = c.id
 order by c.cree_le desc
 limit 10;
