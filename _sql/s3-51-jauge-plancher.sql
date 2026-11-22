-- s3-51 (22/11/2026) : la jauge d'un siège s'affiche arrondie vers le bas (64,8 / 65 s'affichait « 65 / 65 » :
-- Oshannir croyait sa commune prise). Affichage seulement : siege_vue et tableau_front. Les règles ne changent pas.
do $$
declare d text; n text;
begin
  d := pg_get_functiondef('public.siege_vue(bigint)'::regprocedure);
  n := replace(d, $a$'degats', round(s.degats)$a$, $a$'degats', floor(s.degats)$a$);
  if n = d then raise exception 's3-51 : siege_vue inchangée'; end if;
  execute n;
  d := pg_get_functiondef('public.tableau_front()'::regprocedure);
  n := replace(d, $a$round(e.degats)$a$, $a$floor(e.degats)$a$);
  if n = d then raise exception 's3-51 : tableau_front inchangée'; end if;
  execute n;
end $$;
