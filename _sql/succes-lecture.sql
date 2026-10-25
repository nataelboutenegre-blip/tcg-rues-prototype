-- TerraFront — lecture seule : le code de succes() et de reclamer_objectif(),
-- pour voir pourquoi les succès de la saison 1 se réclament encore.
-- Copie le résultat (deux lignes) et envoie-le à Claude.
select p.proname as fonction, pg_get_functiondef(p.oid) as source
  from pg_proc p join pg_namespace n on n.oid = p.pronamespace
 where n.nspname = 'public' and p.proname in ('succes', 'reclamer_objectif')
 order by p.proname;
