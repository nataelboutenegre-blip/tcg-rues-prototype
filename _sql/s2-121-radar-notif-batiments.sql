-- s2-121 : les notifications « Ta Banque est repérée » et « Ton Centre est repéré »
-- ouvrent le volet Combat › Bâtiments (patch379) au lieu de Défendre.
-- Appliqué le 8 nov. 2026 (édition en place de radar_reperer).
do $a$
declare d text;
begin
  select pg_get_functiondef(p.oid) into d from pg_proc p join pg_namespace n on n.oid = p.pronamespace
   where n.nspname = 'public' and p.proname = 'radar_reperer';
  if (length(d) - length(replace(d, $q$'./?onglet=defense', 'radar')$q$, ''))) / length($q$'./?onglet=defense', 'radar')$q$) <> 2 then
    raise exception 'radar_reperer : 2 occurrences attendues';
  end if;
  d := replace(d, $q$'./?onglet=defense', 'radar')$q$, $q$'./?onglet=batiments', 'radar') /* s2-121 */$q$);
  execute d;
end $a$;
