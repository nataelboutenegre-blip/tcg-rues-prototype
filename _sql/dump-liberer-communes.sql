-- ===========================================================================
--  TerraFront — LECTURE SEULE (30 octobre 2026) — à exporter en CSV
--  Avant de coder « Libérer des communes » (idée de Maroli) : comment le
--  Front tire une commune dans un paquet, qui écrit dans possessions, ce
--  qu'est une commune « attaquée » (sieges), et l'énergie du Front.
--  Une seule table : fonction | arguments | definition.
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
   and (p.proname in ('draw_commune', 'tirer_carte', 'ouvrir_paquet', 'attaquer',
                      'front_energie_lire', 'front_energie_depenser', 'front_energie_gagner',
                      'mon_energie_front', 'front_statut', 'reclamer_quete')
     or p.proname ilike '%paquet%front%' or p.proname ilike '%front%paquet%'
     or p.proname ilike 'draw\_%' or p.proname ilike '%tirage%'
     or pg_get_functiondef(p.oid) ~* '(insert into (public\.)?possessions|delete from (public\.)?possessions|update (public\.)?possessions)'
     or pg_get_functiondef(p.oid) ~* '(insert into (public\.)?historique|update (public\.)?historique)')
union all
select '(déclencheurs)', '', coalesce(string_agg(c.relname || ' : ' || t.tgname || ' → ' || t.tgfoid::regproc::text, E'\n' order by c.relname, t.tgname), 'aucun')
  from pg_trigger t join pg_class c on c.oid = t.tgrelid
 where c.relname in ('possessions', 'historique', 'sieges') and not t.tgisinternal
union all
select '(table ' || table_name || ')', '', string_agg(column_name || ' ' || data_type || case when is_nullable = 'NO' then ' not null' else '' end, ', ' order by ordinal_position)
  from information_schema.columns
 where table_schema = 'public' and table_name in ('possessions', 'historique', 'sieges', 'joueurs')
 group by table_name
union all
select '(chiffres)', '',
       'possessions : ' || (select count(*) from public.possessions)
       || ' · dont sans joueur : ' || (select count(*) from public.possessions where joueur_id is null)
       || ' · sieges : ' || (select count(*) from public.sieges)
       || ' · communes : ' || (select count(*) from public.communes)
order by 1;
