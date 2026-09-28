-- ---------------------------------------------------------------------------
--  journal-etat-2.sql — lecture seule, ne modifie rien
--
--  La table du journal s'appelle « journal », comme la fonction. Cette
--  requete lit ce qu'il me manque pour ecrire la migration : les colonnes,
--  les index (pour savoir si le tri et le curseur vont couter cher), les
--  valeurs reelles de la colonne type, le volume, et si unaccent est bien
--  installe pour la recherche.
-- ---------------------------------------------------------------------------
with col as (
  select 'A. colonnes de journal' as quoi,
         string_agg(column_name || ' : ' || data_type
                    || case when is_nullable = 'YES' then '' else ' (non nul)' end,
                    chr(10) order by ordinal_position) as detail
    from information_schema.columns
   where table_schema = 'public' and table_name = 'journal'
),
idx as (
  select 'B. index sur journal' as quoi,
         string_agg(indexdef, chr(10) order by indexname) as detail
    from pg_indexes
   where schemaname = 'public' and tablename = 'journal'
),
typ as (
  select 'C. valeurs de type' as quoi,
         string_agg(t.type || ' : ' || t.n, chr(10) order by t.n desc) as detail
    from (select coalesce(type::text, '(null)') as type, count(*) as n
            from journal group by 1) t
),
vol as (
  select 'D. volume' as quoi,
         count(*) || ' lignes, de ' || min(cree_le)::date
                  || ' a ' || max(cree_le)::date as detail
    from journal
),
ext as (
  select 'E. extensions utiles' as quoi,
         coalesce(string_agg(extname, ', ' order by extname), 'aucune') as detail
    from pg_extension
   where extname in ('unaccent', 'pg_trgm')
),
rls as (
  select 'F. RLS et politiques sur journal' as quoi,
         (select case when c.relrowsecurity then 'RLS activee' else 'RLS desactivee' end
            from pg_class c join pg_namespace n on n.oid = c.relnamespace
           where n.nspname = 'public' and c.relname = 'journal')
         || coalesce(chr(10) || (select string_agg(policyname || ' (' || cmd || ')', chr(10))
                                   from pg_policies
                                  where schemaname = 'public' and tablename = 'journal'), '')
         as detail
)
select * from col
union all select * from idx
union all select * from typ
union all select * from vol
union all select * from ext
union all select * from rls
order by 1;
