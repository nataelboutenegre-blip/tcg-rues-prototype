-- ===========================================================================
--  TerraFront — 3 sur 3 : qui compte les défenses ?
--
--  LECTURE SEULE. Ne modifie rien.
--  Tout coller, lancer, me coller le résultat.
--
--  CE QUE J'AI COMPRIS JUSQU'ICI
--    objectifs() lit la table objectifs_compteurs, colonnes defenses et
--    total_defenses. Mais defendre() ne touche jamais cette table : elle
--    débite le solde, met à jour sieges, et s'arrête là. Elle n'écrit pas
--    non plus la ligne de journal.
--
--    Donc quelqu'un d'autre fait les deux, et ce quelqu'un est forcément un
--    déclencheur sur sieges. C'est lui qui contient le bug de Boule2Pain :
--    il doit distinguer une défense d'une attaque en regardant si le nombre
--    de victoires monte ou descend, et quelque chose se perd quand deux
--    assaillants sont sur la même commune.
--
--  Cette requête sort tous les déclencheurs du schéma public avec le code
--  de la fonction qu'ils appellent.
-- ===========================================================================

select t.tgname                       as declencheur,
       c.relname                      as sur_la_table,
       pg_get_triggerdef(t.oid)       as definition,
       pg_get_functiondef(t.tgfoid)   as code_de_la_fonction
  from pg_trigger t
  join pg_class c     on c.oid = t.tgrelid
  join pg_namespace n on n.oid = c.relnamespace
 where n.nspname = 'public'
   and not t.tgisinternal
 order by c.relname, t.tgname;
