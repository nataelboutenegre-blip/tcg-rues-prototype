-- ===========================================================================
--  LECTURE SEULE — prochain patch d'équilibrage, 2e partie (4/11/2026)
--  La 1re lecture a été coupée à 100 lignes par l'éditeur Supabase (141
--  annoncées) : il manque les déclencheurs, les réglages et quelques
--  colonnes. Celle-ci reprend ce qui manque, plus le code de fonctions
--  repérées par la 1re lecture (sièges, garnison, énergie, quêtes).
--  Moins de 100 lignes attendues ; la colonne « lignes » donne le total.
--  Aucun pseudo, aucune donnée de joueur. Ne modifie rien.
-- ===========================================================================
with noms(n) as (
  select unnest(array[
    'siege_course_effacer', 'reset_sieges_changement_proprietaire', 'siege_nettoyer_proprietaire',
    'siege_ignore_immunite', 'commune_assiegee', 'premiers_pas', 'defenses_rendre',
    'garnison_intervient', 'front_recolter', 'reclamer_quete', 'rafale_noter_quete',
    'clan_entrer', 'batiment_annuler', 'saison2_active', 'reserve_accueil_etat'
  ])
),
tables_lot as (
  select c.oid, c.relname
    from pg_class c
   where c.relnamespace = 'public'::regnamespace
     and c.relname in ('sieges', 'front_rounds', 'front_garnisons', 'jours_joues', 'sieges_effaces', 'possessions')
),
fonctions as (
  select p.oid,
         p.proname || '(' || pg_get_function_identity_arguments(p.oid) || ')' as nom,
         replace(encode(convert_to(pg_get_functiondef(p.oid), 'UTF8'), 'base64'), E'\n', '') as b
    from pg_proc p
   where p.pronamespace = 'public'::regnamespace
     and p.prokind = 'f'
     and (p.proname in (select n from noms)
          or p.oid in (select t.tgfoid from pg_trigger t
                        where not t.tgisinternal
                          and t.tgrelid in (select oid from tables_lot where relname in ('possessions', 'jours_joues'))))
     -- déjà lues dans la 1re partie
     and p.proname not in ('front_round_noter', 'notif_danger_siege', 'notif_premiere_attaque', 'suivi_combat')
),
tout(section, nom, partie, contenu) as (
  select '1. fonction', f.nom, g.i,
         substr(f.b, (g.i - 1) * 6000 + 1, 6000)
    from fonctions f
   cross join lateral generate_series(1, greatest(1, ceil(length(f.b) / 6000.0)::int)) as g(i)
  union all
  select '3. colonne', c.table_name || '.' || c.column_name, c.ordinal_position::int,
         c.data_type || coalesce(' = ' || c.column_default, '')
    from information_schema.columns c
   where c.table_schema = 'public'
     and c.table_name in ('sieges', 'sieges_effaces', 'possessions')
  union all
  select '4. déclencheur', t.tgname || ' sur ' || tl.relname, 0, pg_get_triggerdef(t.oid)
    from pg_trigger t
    join tables_lot tl on tl.oid = t.tgrelid
   where not t.tgisinternal
  union all
  select '5. réglage', cj.cle, 0, cj.valeur::text
    from config_jeu cj
   where cj.cle ~* '(energ|batiment|garnis|quete|reserve|interface|saison|halving)'
  union all
  -- 6. les tâches planifiées (pg_cron), seulement si l'extension est là
  select '6. tâches planifiées', 'cron.job', 0,
         case when exists (select 1 from pg_extension where extname = 'pg_cron')
              then query_to_xml('select jobname, schedule, command, active from cron.job order by jobname', false, false, '')::text
              else 'pg_cron absent' end
)
select count(*) over () as lignes, section, nom, partie,
       replace(replace(contenu, '|', '¦'), E'\n', ' ⏎ ') as contenu
  from tout
 order by section, nom, partie;
