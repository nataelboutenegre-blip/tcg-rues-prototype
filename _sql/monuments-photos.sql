-- ===========================================================================
--  TerraFront — L'attribution des images d'emblemes
--
--  A passer AVANT monuments-2-images.py, qui ecrit dans ces colonnes.
--
--  Meme raison que pour les photos de communes : les images de Commons sont
--  majoritairement en CC BY-SA. Citer l'auteur, la licence et la source est
--  une obligation legale, d'ou trois colonnes et non une.
--
--  La fonction du catalogue est reprise a l'identique, avec ces champs en
--  plus : l'ecran des emblemes doit pouvoir afficher le credit.
-- ===========================================================================

alter table public.monuments
  add column if not exists photo_auteur  text,
  add column if not exists photo_licence text,
  add column if not exists photo_source  text;


-- PostgreSQL refuse de changer les colonnes renvoyees par une fonction
-- existante : il faut la supprimer d'abord. Aucun risque, rien ne l'appelle
-- encore.
drop function if exists public.monuments_catalogue();

create function public.monuments_catalogue()
returns table(
  commune_code text, nom text, embleme text, departement text, tier text,
  langues integer, image text, photo text,
  photo_auteur text, photo_licence text, photo_source text,
  a_moi boolean, proprietaire text, libre boolean)
language sql
stable security definer
set search_path to 'public'
as $function$
  select m.commune_code,
         c.nom,
         m.nom,
         c.departement,
         c.tier,
         m.langues,
         m.image,
         m.photo,
         m.photo_auteur,
         m.photo_licence,
         m.photo_source,
         (p.joueur_id = auth.uid())            as a_moi,
         j.pseudo                              as proprietaire,
         (p.joueur_id is null)                 as libre
    from monuments m
    join communes c on c.code = m.commune_code
    left join possessions p on p.commune_code = m.commune_code
    left join joueurs j on j.id = p.joueur_id
   order by m.langues desc nulls last, c.nom;
$function$;

revoke all on function public.monuments_catalogue() from public;
grant execute on function public.monuments_catalogue() to anon, authenticated;


-- ---------------------------------------------------------------------------
--  Verification
-- ---------------------------------------------------------------------------
select 'A. colonnes d''attribution' as controle,
       string_agg(column_name, ', ' order by column_name) as valeur
  from information_schema.columns
 where table_schema = 'public' and table_name = 'monuments'
   and column_name like 'photo%'
union all
select 'B. images deja posees',
       (select count(*)::text from monuments where photo is not null)
union all
select 'C. le catalogue repond',
       (select count(*)::text || ' emblemes' from monuments_catalogue())
order by 1;
