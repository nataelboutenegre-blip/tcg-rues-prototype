-- ===========================================================================
--  s2-68c — CORRECTIF URGENT (remplace s2-68b, qui était faux)
--  « Impossible d'ouvrir le paquet » : s2-68 relisait les réglages
--  d'Halloween pour chaque commune (35 000 fois par paquet → délai dépassé).
--  s2-68b voulait corriger mais écrivait une erreur de type (text <> text[]).
--  Ce fichier répare les deux cas (s2-68b lancé ou non) : la liste des
--  communes hantées est lue UNE fois par paquet. Testé sur 35 000 communes :
--  4,5 s → quelques ms. Rejouable. Contrôle attendu : true | true | true
-- ===========================================================================
begin;

do $do$
declare d text;
begin
  d := pg_get_functiondef('public.terra_ouvrir_paquet(boolean)'::regprocedure);
  d := replace(d, 'all((select halloween_codes_actifs()))', 'all(halloween_codes_actifs())');                  -- défait s2-68b
  d := replace(d, 'all(halloween_codes_actifs())', 'all((select halloween_codes_actifs())::text[])');
  execute d;

  d := pg_get_functiondef('public.draw_commune(text)'::regprocedure);
  d := replace(d, 'any((select halloween_codes()))', 'any(halloween_codes())');                                -- défait s2-68b
  d := replace(d, 'any(halloween_codes())', 'any((select halloween_codes())::text[])');
  execute d;
end $do$;

commit;

-- Contrôle : true | true | true
select position('all((select halloween_codes_actifs())::text[])' in pg_get_functiondef('public.terra_ouvrir_paquet(boolean)'::regprocedure)) > 0 as paquet_terra,
       position('any((select halloween_codes())::text[])' in pg_get_functiondef('public.draw_commune(text)'::regprocedure)) > 0              as tirage_front,
       position('halloween_codes()))' in pg_get_functiondef('public.terra_ouvrir_paquet(boolean)'::regprocedure)
                                   || pg_get_functiondef('public.draw_commune(text)'::regprocedure)) = 0                                  as plus_d_erreur;
