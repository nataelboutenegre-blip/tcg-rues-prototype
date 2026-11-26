-- s3-86 (26/11) : retirer une garnison rend 100 % de son énergie (avant : 75 %), toujours dans la limite du plafond.
do $do$
declare d text; d2 text;
begin
  d := pg_get_functiondef('public.garnison_retirer(text)'::regprocedure);
  d2 := replace(d, $a$v_rendue := (v_e * 3) / 4;   -- s2-79 : 75 %$a$, $b$v_rendue := v_e;   -- s3-86 : 100 % (avant : 75 %)$b$);
  if d2 = d then raise exception 's3-86 : inchangé'; end if;
  execute d2;
end $do$;
