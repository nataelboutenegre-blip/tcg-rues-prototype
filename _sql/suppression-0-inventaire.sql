-- =====================================================================
--  TerraFront — suppression de compte, 0 : inventaire (LECTURE SEULE)
--
--  Ne modifie rien. Sert à savoir quelles tables contiennent des données
--  liées à un joueur, pour écrire la suppression de compte sans rien
--  oublier ni rien casser.
--
--  À lancer dans l'éditeur SQL de Supabase, puis exporter le résultat en
--  CSV (bouton « Export » sous le résultat) et me l'envoyer.
-- =====================================================================

with
-- 1. les liens déclarés vers un joueur (clés étrangères)
liens as (
  select 'lien'::text as quoi,
         cl.relname::text as table_,
         string_agg(a.attname, ', ' order by a.attnum)::text as colonne,
         (case c.confdeltype when 'c' then 'cascade' when 'n' then 'set null' when 'r' then 'restrict'
                             when 'a' then 'no action' when 'd' then 'set default' end
          || ' → ' || ns2.nspname || '.' || cl2.relname)::text as detail
    from pg_constraint c
    join pg_class cl  on cl.oid  = c.conrelid
    join pg_namespace ns on ns.oid = cl.relnamespace
    join pg_class cl2 on cl2.oid = c.confrelid
    join pg_namespace ns2 on ns2.oid = cl2.relnamespace
    join pg_attribute a on a.attrelid = c.conrelid and a.attnum = any(c.conkey)
   where c.contype = 'f' and ns.nspname = 'public'
     and ((ns2.nspname = 'public' and cl2.relname = 'joueurs') or (ns2.nspname = 'auth' and cl2.relname = 'users'))
   group by cl.relname, c.confdeltype, ns2.nspname, cl2.relname, c.conname
),
-- 2. toutes les colonnes qui peuvent contenir un identifiant de joueur,
--    même sans lien déclaré (type uuid)
uuids as (
  select 'colonne uuid', c.table_name::text, c.column_name::text,
         case when c.is_nullable = 'YES' then 'peut être vide' else 'obligatoire' end
    from information_schema.columns c
    join information_schema.tables t on t.table_schema = c.table_schema and t.table_name = c.table_name
   where c.table_schema = 'public' and t.table_type = 'BASE TABLE' and c.data_type = 'uuid'
),
-- 3. les colonnes de texte libre écrit par les joueurs (messages, pseudos…)
textes as (
  select 'colonne texte', c.table_name::text, c.column_name::text, c.data_type::text
    from information_schema.columns c
    join information_schema.tables t on t.table_schema = c.table_schema and t.table_name = c.table_name
   where c.table_schema = 'public' and t.table_type = 'BASE TABLE'
     and c.data_type in ('text', 'character varying')
     and c.column_name ~* '(message|texte|pseudo|nom|email|mail|commentaire|note|endpoint|cle|auth|p256)'
),
-- 4. les déclencheurs posés sur la table des joueurs
declencheurs as (
  select 'déclencheur', event_object_table::text, trigger_name::text, (action_timing || ' ' || event_manipulation)::text
    from information_schema.triggers
   where event_object_schema = 'public' and event_object_table in ('joueurs', 'possessions')
)
select * from liens
union all select * from uuids
union all select * from textes
union all select * from declencheurs
order by 1, 2, 3;
