-- ---------------------------------------------------------------------------
--  journal-etat.sql — lecture seule, ne modifie rien
--
--  Avant d'ajouter le filtre par type, la recherche et la pagination au
--  journal, il faut savoir ce qu'il y a deja : la definition exacte de
--  journal(), les colonnes et les index de la table qu'elle lit, et son
--  volume. Le tout en UN seul select, parce que l'editeur Supabase
--  n'affiche que le resultat du dernier.
-- ---------------------------------------------------------------------------
with f as (
  select 'A. definition de journal()' as quoi,
         pg_get_functiondef(p.oid) as detail
    from pg_proc p
    join pg_namespace n on n.oid = p.pronamespace
   where n.nspname = 'public'
     and p.proname = 'journal'
),
col as (
  select 'B. colonnes de ' || table_name as quoi,
         string_agg(column_name || ' : ' || data_type,
                    chr(10) order by ordinal_position) as detail
    from information_schema.columns
   where table_schema = 'public'
     and table_name in ('historique', 'journal_evenements', 'evenements')
   group by table_name
),
idx as (
  select 'C. index sur ' || tablename as quoi,
         string_agg(indexdef, chr(10) order by indexname) as detail
    from pg_indexes
   where schemaname = 'public'
     and tablename in ('historique', 'journal_evenements', 'evenements')
   group by tablename
),
vol as (
  -- estimation tiree des statistiques : aucun parcours de table
  select 'D. volume estime' as quoi,
         string_agg(c.relname || ' : ' || c.reltuples::bigint || ' lignes',
                    chr(10) order by c.relname) as detail
    from pg_class c
    join pg_namespace n on n.oid = c.relnamespace
   where n.nspname = 'public'
     and c.relkind = 'r'
     and c.relname in ('historique', 'journal_evenements', 'evenements',
                       'possessions', 'joueurs')
),
tab as (
  -- au cas ou la table du journal porte un autre nom que ceux essayes
  select 'E. toutes les tables publiques' as quoi,
         string_agg(tablename, ', ' order by tablename) as detail
    from pg_tables
   where schemaname = 'public'
)
select * from f
union all select * from col
union all select * from idx
union all select * from vol
union all select * from tab
order by 1;
