-- ===========================================================================
--  TerraFront — Qu'est-ce qu'on peut reconstituer, et depuis quand
--
--  POURQUOI
--    Deux statistiques demandées : le nombre total d'échanges réalisés, et
--    les points dépensés depuis le début, toutes sources confondues.
--
--    La première est probablement déjà là : la table des échanges garde ses
--    lignes. La seconde dépend de l'existence d'un endroit où chaque dépense
--    a laissé une trace. Le journal ne peut pas servir : il se purge à 30
--    jours, donc tout ce qui est plus ancien n'existe plus nulle part.
--
--    Plutôt que de deviner, ce fichier liste ce que la base contient
--    réellement : une ligne par table, avec ses colonnes et son nombre de
--    lignes. On saura en le lisant si « depuis le début » est tenable ou
--    s'il faudra écrire « depuis le 3 octobre ».
--
--  Lecture seule. Ne modifie rien, ne crée rien.
-- ===========================================================================

select t.relname                                   as table_,
       c.reltuples::bigint                         as lignes_estimees,
       string_agg(a.attname || ' ' ||
                  format_type(a.atttypid, a.atttypmod),
                  ', ' order by a.attnum)          as colonnes
  from pg_class t
  join pg_namespace n on n.oid = t.relnamespace
  join pg_class c on c.oid = t.oid
  join pg_attribute a on a.attrelid = t.oid and a.attnum > 0 and not a.attisdropped
 where n.nspname = 'public'
   and t.relkind = 'r'
 group by t.relname, c.reltuples
 order by t.relname;
