-- ===========================================================================
--  TerraFront — LECTURE SEULE (27 octobre 2026) — à exporter en CSV
--  Avant l'Aurore « 1 chance sur 3 » en Front : toutes les fonctions qui
--  écrivent dans possessions (tirage, conquête, échange, clôture…), pour
--  savoir où poser la marque Aurore et si elle suit la commune conquise.
--  Ne modifie rien. Les fonctions qui contiennent un secret ou un envoi
--  réseau sont listées mais leur texte est masqué.
-- ===========================================================================
select p.proname                                                   as fonction,
       pg_get_function_identity_arguments(p.oid)                   as arguments,
       case when pg_get_functiondef(p.oid) ~* '(secret|x-terrafront|net\.http|bearer|authorization|apikey)'
            then '[masqué : contient un secret ou un envoi réseau]'
            else pg_get_functiondef(p.oid) end                     as definition
  from pg_proc p join pg_namespace n on n.oid = p.pronamespace
 where n.nspname = 'public' and p.prokind = 'f'
   and pg_get_functiondef(p.oid) ~* '(insert\s+into\s+(public\.)?possessions|update\s+(public\.)?possessions|delete\s+from\s+(public\.)?possessions)'
union all
select '(table possessions)', '', string_agg(column_name || ' ' || data_type, ', ' order by ordinal_position)
  from information_schema.columns where table_schema = 'public' and table_name = 'possessions'
union all
select '(déclencheurs sur possessions)', '', coalesce(string_agg(tgname || ' → ' || tgfoid::regproc::text, ', '), 'aucun')
  from pg_trigger where tgrelid = 'public.possessions'::regclass and not tgisinternal
order by 1;
