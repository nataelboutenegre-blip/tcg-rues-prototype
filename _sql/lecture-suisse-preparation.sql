-- ===========================================================================
--  TerraFront — saison 3, la Suisse : ce que le serveur suppose sur les codes
--  et les départements. LECTURE SEULE : rien n'est modifié.
--
--  Les communes suisses auront un code « CH » + numéro fédéral (ex. CH6621,
--  CH261, CH1 : 3 à 6 caractères) et pour département le code du canton
--  (« GE », « VD », « ZH »…). Cette lecture dit, en une dizaine de lignes :
--    1. le type des colonnes de codes (un char(5) refuserait « CH6621 ») ;
--    2. les contraintes qui portent sur ces colonnes ;
--    3. les fonctions qui déduisent quelque chose du code ou du département,
--       regroupées par motif (« length(departement) = 2 » veut dire
--       « métropole » depuis l'outre-mer : un canton fait aussi 2 lettres) ;
--    4. les vues qui lisent le département.
-- ===========================================================================

with cols as (
  select c.table_name, c.column_name, c.data_type, c.character_maximum_length as lg
    from information_schema.columns c
    join information_schema.tables t
      on t.table_schema = c.table_schema and t.table_name = c.table_name and t.table_type = 'BASE TABLE'
   where c.table_schema = 'public'
     and (c.column_name in ('code', 'departement', 'dept', 'region', 'commune_code', 'code_commune', 'insee')
          or c.column_name like '%commune_code%' or c.column_name like '%departement%')
),
contraintes as (
  select conrelid::regclass::text as tbl, conname, pg_get_constraintdef(oid) as def
    from pg_constraint
   where connamespace = 'public'::regnamespace and contype in ('c', 'f')
     and (pg_get_constraintdef(oid) ~* 'departement|commune_code|\mcode\M')
),
src as (
  select p.proname, p.prosrc
    from pg_proc p
   where p.pronamespace = 'public'::regnamespace and p.prokind in ('f', 'p')
),
motifs(ordre, motif, rx) as (values
  (1, 'length(departement) = 2 / 3 (métropole / outre-mer)', 'length\s*\(\s*[a-z_.]*(departement|dept)\s*\)'),
  (2, 'departement ~ regex (^9[78], chiffres…)',               '(departement|dept)\s*!?~\*?\s*'''),
  (3, 'code ~ / like ''97%'' (zone lue dans le code)',          '(code|commune_code)\s*(!?~\*?|(not\s+)?i?like)\s*'''),
  (4, 'left/substr/substring du code',                          '(left|substr|substring)\s*\(\s*[a-z_.]*(code|commune_code)'),
  (5, 'departement converti en nombre',                         '(departement|dept)\s*::\s*(int|integer|numeric|bigint)|cast\s*\(\s*[a-z_.]*(departement|dept)'),
  (6, 'liste de départements écrite en dur',                    '''(0[1-9]|[1-9][0-9]|2A|2B)''\s*,\s*''(0[1-9]|[1-9][0-9]|2A|2B)'''),
  (7, 'régions (table, cas ou correspondance)',                 '\mregion'),
  (8, 'lit le département (tous usages)',                       'departement|\mdept\M')
)
select '1. colonne' as section, table_name || '.' || column_name as objet,
       data_type || coalesce('(' || lg || ')', '') as detail
  from cols
union all
select '2. contrainte', tbl || ' : ' || conname, left(def, 200)
  from contraintes
union all
select '3. fonctions : ' || m.ordre || '. ' || m.motif, count(*)::text || ' fonction(s)',
       left(string_agg(s.proname, ', ' order by s.proname), 1500)
  from motifs m join src s on s.prosrc ~* m.rx
 group by m.ordre, m.motif
union all
select '4. vue', c.relname, case c.relkind when 'm' then 'vue matérialisée' else 'vue' end
  from pg_class c
 where c.relnamespace = 'public'::regnamespace and c.relkind in ('v', 'm')
   and pg_get_viewdef(c.oid) ~* 'departement|\mdept\M'
order by 1, 2;
