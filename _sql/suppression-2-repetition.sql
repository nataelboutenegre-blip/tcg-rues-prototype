-- =====================================================================
--  TerraFront — suppression de compte, 2 : répétition à blanc
--
--  À lancer APRÈS suppression-1-compte.sql, et AVANT de pousser le jeu.
--  Rien à modifier : le fichier prend tout seul le joueur qui possède le
--  plus de communes (le cas le plus complet à tester).
--
--  Fait toute la suppression de ce compte puis l'annule : RIEN n'est
--  supprimé. Réponse attendue :
--    "repetition": "réussie, rien n'a été supprimé"
--  avec le nombre de communes, d'échanges et de liens d'amis qui
--  auraient été effacés. Si la réponse dit « ÉCHEC », envoie-la-moi et
--  ne pousse pas.
-- =====================================================================

select j.pseudo as joueur_teste,
       supprimer_compte_essai(j.pseudo) as resultat
  from joueurs j
 where j.id = (select joueur_id from possessions
                group by joueur_id order by count(*) desc limit 1);
