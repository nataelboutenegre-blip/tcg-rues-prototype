-- ===========================================================================
--  TerraFront — 4 sur 4 : les deux fonctions utilitaires, et la table
--
--  LECTURE SEULE. Ne modifie rien.
--  Tout coller, lancer, me coller le résultat.
--
--  POURQUOI
--    La correction consiste à faire écrire le journal et le compteur par
--    defendre() elle-même, puis à retirer la devinette des déclencheurs.
--    Pour ça il me faut la signature exacte de ajouter_compteur() et de
--    noter_journal(), et les colonnes de objectifs_compteurs — notamment
--    savoir si total_defenses est tenu par ajouter_compteur ou ailleurs.
--
--  Une seule requête : rien à sélectionner.
-- ===========================================================================

select 'fonction' as quoi,
       p.proname  as nom,
       pg_get_functiondef(p.oid) as detail
  from pg_proc p
  join pg_namespace n on n.oid = p.pronamespace
 where n.nspname = 'public'
   and p.proname in ('ajouter_compteur', 'noter_journal')

union all

select 'table',
       c.relname,
       string_agg(a.attname || ' ' || format_type(a.atttypid, a.atttypmod),
                  E'\n' order by a.attnum)
  from pg_class c
  join pg_namespace n on n.oid = c.relnamespace
  join pg_attribute a on a.attrelid = c.oid and a.attnum > 0 and not a.attisdropped
 where n.nspname = 'public'
   and c.relname in ('objectifs_compteurs', 'journal', 'sieges')
 group by c.relname

 order by 1, 2;
