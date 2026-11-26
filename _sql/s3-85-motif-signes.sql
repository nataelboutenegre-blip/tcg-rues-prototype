-- s3-85 (26/11, idée d'Arkhannou) : le motif accepte aussi - . / # _ + & ! ? ' parmi ses 3 caractères au plus.
-- Le filtre des combinaisons refusées ignore ces signes (« S.S » est refusé comme « SS »).
do $do$
declare d text; d2 text;
begin
  d := pg_get_functiondef('public.motif_net(jsonb, uuid)'::regprocedure);
  d2 := replace(d, $a$if l !~ '^[A-Z0-9]$' then$a$, $b$if l !~ '^[-A-Z0-9./#_+&!?'']$' then   /* s3-85 : quelques signes */$b$);
  if d2 = d then raise exception 's3-85 : regex inchangée'; end if; d := d2;
  d2 := replace(d, $a$if length(lettres) >= 2 and (select string_agg(x, '' order by x) from regexp_split_to_table(lettres, '') x)$a$,
                   $b$if length(regexp_replace(lettres, '[^A-Z0-9]', '', 'g')) >= 2 and (select string_agg(x, '' order by x) from regexp_split_to_table(regexp_replace(lettres, '[^A-Z0-9]', '', 'g'), '') x)$b$);
  if d2 = d then raise exception 's3-85 : filtre inchangé'; end if;
  execute d2;
end $do$;
