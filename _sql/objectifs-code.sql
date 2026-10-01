-- ===========================================================================
--  TerraFront — 1 sur 2 : le code des fonctions d'objectifs et de succès
--
--  LECTURE SEULE. Ne modifie rien.
--  Tout coller, lancer, me coller le résultat.
--
--  Il y a une seule requête dans ce fichier : rien à sélectionner.
-- ===========================================================================

select p.proname as fonction,
       pg_get_functiondef(p.oid) as source
  from pg_proc p
  join pg_namespace n on n.oid = p.pronamespace
 where n.nspname = 'public'
   and p.proname in ('objectifs', 'succes', 'reclamer_objectif',
                     'reclamer_departement', 'defendre')
 order by p.proname;
