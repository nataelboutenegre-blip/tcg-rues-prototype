-- ===========================================================================
--  TerraFront — 2 sur 2 : les dernières défenses du journal
--
--  LECTURE SEULE. Ne modifie rien.
--  Tout coller, lancer, me coller le résultat.
--
--  Sert à trancher le bug signalé par Boule2Pain : quand une commune subit
--  deux attaques, une défense réussie n'est pas comptée. Soit le journal
--  n'écrit qu'une ligne par commune au lieu d'une par siège, soit les deux
--  lignes existent et c'est le comptage de l'objectif qui les confond.
--
--  Il y a une seule requête dans ce fichier : rien à sélectionner.
-- ===========================================================================

select *
  from journal
 where type = 'defense'
 order by cree_le desc
 limit 30;
