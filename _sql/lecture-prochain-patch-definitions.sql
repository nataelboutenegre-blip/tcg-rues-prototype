-- ===========================================================================
--  LECTURE SEULE — prochain patch d'équilibrage : le code actuel en production
--  (4/11/2026). Voir le document du projet « prochain-patch-equilibrage ».
--
--  Pourquoi : plusieurs fonctions à modifier ont été créées ou retouchées
--  directement dans Supabase (bonus_proximite n'est même pas dans le dépôt).
--  On les lit telles qu'elles sont avant d'écrire le moindre changement.
--
--  Ce que ça renvoie, en un seul tableau :
--   1. le code des fonctions touchées par le lot (sièges, proximité, rounds,
--      garnisons, Forteresses, énergie, quêtes, mini-jeux, inactivité), découpé
--      en morceaux encodés (illisibles à l'œil, c'est normal : Claude les
--      recolle) ;
--   2. le nom des autres fonctions qui lisent les sièges, l'énergie, les
--      garnisons, jours_joues ou les quêtes (pour n'en oublier aucune) ;
--   3. les colonnes des tables concernées ;
--   4. les déclencheurs posés sur ces tables ;
--   5. les réglages du jeu liés au lot.
--  La colonne « lignes » donne le nombre total de lignes : si le tableau
--  copié en a moins, il a été coupé.
--
--  Aucun pseudo, aucune donnée de joueur. Ne modifie rien.
--  Pour l'envoyer : copier tout le résultat (il est long, c'est normal).
-- ===========================================================================
with noms(n) as (
  select unnest(array[
    -- sièges, proximité, rounds
    'attaquer', 'apercu_attaque', 'apercu_attaques', 'bonus_proximite', 'bonus_batiments',
    'communes_proches', 'chance_intensite', 'energie_intensite', 'delai_attaque',
    'defendre', 'sieges_contre_moi', 'sieges_communes', 'mes_sieges_effaces', 'front_round_noter',
    -- garnisons et Forteresses
    'garnison_poser', 'garnison_retirer', 'mes_garnisons', 'garnisons_visibles',
    'batiment_construire', 'batiment_reglage', 'mes_batiments', 'batiments_effet',
    -- énergie
    'front_energie', 'front_energie_lire', 'front_energie_gagner', 'front_energie_depenser',
    -- quêtes et mini-jeux
    'quetes', 'quetes_liste', 'quete_noter', 'radar_clore_si_fini', 'rafale_terminer',
    'pom_partie', 'pom_repondre', 'pom_d_repondre',
    -- inactivité
    'parrainage_jour', 'front_liberer', 'front_liberation_etat'
  ])
),
tables_lot as (
  select c.oid, c.relname
    from pg_class c
   where c.relnamespace = 'public'::regnamespace
     and c.relname in ('sieges', 'front_rounds', 'front_garnisons', 'jours_joues', 'batiments',
                       'sieges_effaces', 'possessions')
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
                          and t.tgrelid in (select oid from tables_lot where relname in ('sieges', 'front_rounds', 'front_garnisons'))))
),
tout(section, nom, partie, contenu) as (
  -- 1. le code, en morceaux de 6 000 caractères
  select '1. fonction', f.nom, g.i,
         substr(f.b, (g.i - 1) * 6000 + 1, 6000)
    from fonctions f
   cross join lateral generate_series(1, greatest(1, ceil(length(f.b) / 6000.0)::int)) as g(i)
  union all
  -- 2. les autres fonctions qui touchent au même sujet (nom seulement)
  select '2. autre fonction',
         p.proname || '(' || pg_get_function_identity_arguments(p.oid) || ')', 0,
         concat_ws(' ',
           case when p.prosrc ~ '\msieges\M'      then 'sieges' end,
           case when p.prosrc ~ 'front_energie'   then 'energie' end,
           case when p.prosrc ~ 'garnison'        then 'garnison' end,
           case when p.prosrc ~ 'jours_joues'     then 'jours_joues' end,
           case when p.prosrc ~ 'quete_noter'     then 'quetes' end,
           case when p.prosrc ~ 'bonus_proximite' then 'proximite' end)
    from pg_proc p
   where p.pronamespace = 'public'::regnamespace
     and p.prokind = 'f'
     and p.oid not in (select oid from fonctions)
     and (p.prosrc ~ '\msieges\M' or p.prosrc ~ 'front_energie' or p.prosrc ~ 'garnison'
          or p.prosrc ~ 'jours_joues' or p.prosrc ~ 'quete_noter' or p.prosrc ~ 'bonus_proximite')
  union all
  -- 3. les colonnes
  select '3. colonne', c.table_name || '.' || c.column_name, c.ordinal_position::int,
         c.data_type || coalesce(' = ' || c.column_default, '')
    from information_schema.columns c
   where c.table_schema = 'public'
     and (c.table_name in (select relname from tables_lot)
          or (c.table_name = 'joueurs' and c.column_name ~ 'energ'))
  union all
  -- 4. les déclencheurs
  select '4. déclencheur', t.tgname || ' sur ' || tl.relname, 0, pg_get_triggerdef(t.oid)
    from pg_trigger t
    join tables_lot tl on tl.oid = t.tgrelid
   where not t.tgisinternal
  union all
  -- 5. les réglages
  select '5. réglage', cj.cle, 0, cj.valeur::text
    from config_jeu cj
   where cj.cle ~* '(energ|batiment|garnis|quete|reserve|interface|saison|halving)'
)
select count(*) over () as lignes, section, nom, partie,
       replace(replace(contenu, '|', '¦'), E'\n', ' ⏎ ') as contenu
  from tout
 order by section, nom, partie;
