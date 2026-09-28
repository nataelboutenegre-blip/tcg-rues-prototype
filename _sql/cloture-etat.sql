-- ---------------------------------------------------------------------------
--  cloture-etat.sql — lecture seule. Ce qu'il faut savoir avant d'ecrire
--  cloturer_saison().
--
--  J'ai deja en local la structure posee le 24 septembre : table saisons,
--  colonnes saison et gardee sur possessions, table classement_saisons,
--  fonctions saison_courante() et marquer_gardee(). Ce qui manque :
--
--   A. ce qui definit « libre ». draw_commune est la seule autorite sur ce
--      point : si elle regarde possessions, rendre une commune au pot veut
--      dire supprimer sa ligne ; si elle regarde autre chose, la cloture
--      doit toucher cette autre chose.
--   B. ce qu'il faut purger — sieges, annonces, echanges : leurs colonnes
--      disent s'ils portent une saison ou s'il faut les vider entierement.
--   C. les cles etrangeres qui pointent vers possessions : une suppression
--      en masse ne doit pas echouer sur une contrainte a mi-chemin.
--   D. l'etat actuel : volumes, et qui a deja marque des communes a garder.
-- ---------------------------------------------------------------------------
with f as (
  select 'A. ' || p.proname as quoi,
         pg_get_functiondef(p.oid) as detail
    from pg_proc p
    join pg_namespace n on n.oid = p.pronamespace
   where n.nspname = 'public'
     and p.proname in ('draw_commune', 'saison_courante')
),
col as (
  select 'B. colonnes de ' || table_name as quoi,
         string_agg(column_name || ' : ' || data_type,
                    chr(10) order by ordinal_position) as detail
    from information_schema.columns
   where table_schema = 'public'
     and table_name in ('possessions', 'sieges', 'annonces', 'echanges')
   group by table_name
),
fk as (
  -- ce qui pointe vers possessions : une suppression en masse peut y buter
  select 'C. cles etrangeres vers possessions' as quoi,
         coalesce(string_agg(
           tc.table_name || '.' || kcu.column_name
           || ' -> ' || ccu.table_name || '.' || ccu.column_name
           || '  (on delete ' || coalesce(rc.delete_rule, '?') || ')',
           chr(10) order by tc.table_name), '(aucune)') as detail
    from information_schema.table_constraints tc
    join information_schema.key_column_usage kcu
      on kcu.constraint_name = tc.constraint_name
     and kcu.table_schema = tc.table_schema
    join information_schema.constraint_column_usage ccu
      on ccu.constraint_name = tc.constraint_name
     and ccu.table_schema = tc.table_schema
    join information_schema.referential_constraints rc
      on rc.constraint_name = tc.constraint_name
     and rc.constraint_schema = tc.table_schema
   where tc.constraint_type = 'FOREIGN KEY'
     and tc.table_schema = 'public'
     and ccu.table_name = 'possessions'
),
vol as (
  select 'D. volumes' as quoi,
         'possessions ' || (select count(*) from possessions)
         || chr(10) || 'sieges ' || (select count(*) from sieges)
         || chr(10) || 'annonces ' || (select count(*) from annonces)
         || chr(10) || 'echanges ' || (select count(*) from echanges)
         || chr(10) || 'historique ' || (select count(*) from historique)
         || chr(10) || 'historique encore ouvert (released_at null) '
                    || (select count(*) from historique where released_at is null)
         || chr(10) || 'classement_saisons ' || (select count(*) from classement_saisons)
         as detail
),
gardees as (
  select 'E. communes deja marquees a garder' as quoi,
         coalesce(string_agg(l, chr(10) order by l), '(personne n''a encore marque)') as detail
    from (
      select coalesce(j.pseudo, '?') || ' : ' || count(*) as l
        from possessions p
        left join joueurs j on j.id = p.joueur_id
       where p.gardee
       group by coalesce(j.pseudo, '?')
    ) t
),
saison as (
  select 'F. saisons' as quoi,
         string_agg(id || ' — ' || nom || ' — ' || etat
                    || ' — debut ' || debut::date
                    || ' — seuil ' || seuil_communes
                    || ' — rebours ' || jours_rebours || ' j'
                    || ' — fin prevue ' || coalesce(fin_prevue::text, '(aucune)'),
                    chr(10) order by debut) as detail
    from saisons
)
select * from f
union all select * from col
union all select * from fk
union all select * from vol
union all select * from gardees
union all select * from saison
order by 1;
