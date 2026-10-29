-- ===========================================================================
--  Modération : supprimer un message du tchat de clan
--  Remplace 0 par l'id du message (dernière colonne de moderation-tchats-lire).
--  Le texte est effacé pour de bon ; dans le jeu, le message devient
--  « message supprimé », sans dire par qui.
-- ===========================================================================
update public.clan_messages
   set supprime = true, texte = '', supprime_par = null
 where id = 0
returning id, supprime;
