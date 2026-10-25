-- ===========================================================================
--  TerraFront — les photos sur les cartes Terra (25 octobre 2026)
--  - terra_photos_moi() : la photo de chaque carte de ma collection
--    (lue par pages côté jeu, comme la collection) ;
--  - terra_photos(codes) : les photos de quelques cartes (vitrine d'un joueur).
--  Lecture seule sur des données publiques (communes). Rejouable.
--  Contrôle attendu : true | true.
-- ===========================================================================
create or replace function public.terra_photos_moi()
 returns table(code text, photo text, auteur text, licence text, source text)
 language sql stable security definer set search_path to 'public'
as $f$
  select c.code::text, c.photo, c.photo_auteur, c.photo_licence, c.photo_source
    from terra_collection t join communes c on c.code = t.commune_code
   where t.joueur_id = auth.uid() and t.exemplaires > 0 and c.photo is not null
$f$;

create or replace function public.terra_photos(p_codes text[])
 returns table(code text, photo text, auteur text, licence text, source text)
 language sql stable security definer set search_path to 'public'
as $f$
  select c.code::text, c.photo, c.photo_auteur, c.photo_licence, c.photo_source
    from communes c
   where c.code = any (p_codes[1:200]) and c.photo is not null
$f$;

revoke all on function public.terra_photos_moi()      from public, anon;
revoke all on function public.terra_photos(text[])    from public, anon;
grant execute on function public.terra_photos_moi()   to authenticated;
grant execute on function public.terra_photos(text[]) to authenticated;

select to_regprocedure('public.terra_photos_moi()') is not null    as moi_ok,
       to_regprocedure('public.terra_photos(text[])') is not null  as codes_ok;
