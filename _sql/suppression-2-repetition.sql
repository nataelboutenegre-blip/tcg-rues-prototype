-- =====================================================================
--  TerraFront — suppression de compte, 2 : répétition à blanc
--
--  À lancer APRÈS suppression-1-compte.sql, et AVANT de pousser le jeu.
--  Remplace TON_PSEUDO par ton pseudo (garde les apostrophes).
--
--  Fait toute la suppression de ce compte puis l'annule : RIEN n'est
--  supprimé. Réponse attendue :
--    "repetition": "réussie, rien n'a été supprimé"
--  avec le nombre de communes, d'échanges et de liens d'amis qui
--  auraient été effacés. Si la réponse dit « ÉCHEC », envoie-la-moi et
--  ne pousse pas.
-- =====================================================================

select supprimer_compte_essai('TON_PSEUDO');
