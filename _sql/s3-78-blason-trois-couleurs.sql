-- s3-78 (ASMFCB) : blasons de clan à trois couleurs — 4 partitions « tiercé » et une couleur c3
-- (facultative : un ancien blason sans c3 reçoit gueules, sans effet sur son dessin).
do $do$
declare d text; avant text;
begin
  d := pg_get_functiondef('blason_propre(jsonb)'::regprocedure); avant := d;
  d := replace(d, $a$'chevron','croix','sautoir','echiquete','fusele','gironne'])$a$,
                  $b$'chevron','croix','sautoir','echiquete','fusele','gironne',
                                        'tierce_pal','tierce_fasce','tierce_bande','pairle'])$b$);
  d := replace(d, $a$and (b->>'c2') = any(e.emaux) and$a$,
                  $b$and (b->>'c2') = any(e.emaux) and coalesce(b->>'c3', 'gueules') = any(e.emaux) and$b$);
  d := replace(d, $a$'c2', b->>'c2',$a$, $b$'c2', b->>'c2', 'c3', coalesce(b->>'c3', 'gueules'),$b$);
  if (length(d) - length(replace(d, 'tierce_', ''))) / 7 <> 3 or position('''c3'', coalesce' in d) = 0
     or position('coalesce(b->>''c3'', ''gueules'') = any' in d) = 0 then
    raise exception 's3-78 : blason_propre mal modifiée';
  end if;
  execute d;
end $do$;
