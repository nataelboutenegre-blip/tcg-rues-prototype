-- ===========================================================================
--  LECTURE SEULE — prochain patch : calibrer les quêtes de performance
--  (idée de Stonirr : moins de 400 km au Radar, 5 communes en Rafale, 7/10 à
--  Plus ou moins). Avant de fixer les seuils, on regarde ce que font
--  vraiment les joueurs sur les 7 derniers jours.
--  Renvoie, en un seul tableau :
--   A. Radar : total de km des duels classés terminés (quartiles), et part
--      des parties sous 300 / 400 / 500 km ;
--   B. Plus ou moins : réponses justes sur 10 (répartition) ;
--   C. Rafale : les colonnes de rafale_parties (pour trouver le score), et
--      le code de rafale_clore (encodé) ;
--   D. le code de front_liberation_config (encodé) : réservoir d'énergie
--      de la libération, à suivre si le maximum passe à 90 ;
--   E. les déclencheurs posés sur joueurs.
--  Chiffres agrégés seulement : aucun pseudo, aucune donnée de joueur.
--  Ne modifie rien.
-- ===========================================================================
with radar as (
  select r.total_km
    from radar_parties r
   where r.fini and not r.amical and r.fin_le > now() - interval '7 days' and r.total_km is not null
),
pom as (
  select pp.justes from pom_parties pp
   where pp.fini and pp.jour > (now() at time zone 'Europe/Paris')::date - 7
),
tout(section, ligne, valeur) as (
  select 'A. Radar', 'parties classées terminées (7 j)', count(*)::text from radar
  union all
  select 'A. Radar', 'total km : 25 % / médiane / 75 %',
         coalesce(percentile_cont(0.25) within group (order by total_km)::int || ' / '
               || percentile_cont(0.5) within group (order by total_km)::int || ' / '
               || percentile_cont(0.75) within group (order by total_km)::int, '-') from radar
  union all
  select 'A. Radar', 'parties sous 300 / 400 / 500 km',
         count(*) filter (where total_km < 300) || ' / ' || count(*) filter (where total_km < 400)
         || ' / ' || count(*) filter (where total_km < 500) from radar
  union all
  select 'B. Plus ou moins', 'parties terminées (7 j)', count(*)::text from pom
  union all
  select 'B. Plus ou moins', 'justes = ' || j, count(p.justes)::text
    from generate_series(0, 10) j left join pom p on p.justes = j group by j
  union all
  select 'C. Rafale', 'colonne ' || c.column_name, c.data_type
    from information_schema.columns c where c.table_schema = 'public' and c.table_name = 'rafale_parties'
  union all
  select 'C. Rafale', 'code rafale_clore (encodé)',
         replace(encode(convert_to(pg_get_functiondef(p.oid), 'UTF8'), 'base64'), E'\n', '')
    from pg_proc p where p.pronamespace = 'public'::regnamespace and p.proname = 'rafale_clore'
  union all
  select 'D. Libération', 'code front_liberation_config (encodé)',
         replace(encode(convert_to(pg_get_functiondef(p.oid), 'UTF8'), 'base64'), E'\n', '')
    from pg_proc p where p.pronamespace = 'public'::regnamespace and p.proname = 'front_liberation_config'
  union all
  select 'E. Déclencheurs joueurs', t.tgname, pg_get_triggerdef(t.oid)
    from pg_trigger t where t.tgrelid = 'public.joueurs'::regclass and not t.tgisinternal
)
select count(*) over () as lignes, section, ligne, valeur from tout order by section, ligne;
