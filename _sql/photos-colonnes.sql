-- ===========================================================================
--  TerraFront — photos des communes, la place en base
--
--  A passer AVANT le script d'import, qui a besoin de ces colonnes et de
--  ce bucket pour ecrire.
--
--  L'ATTRIBUTION N'EST PAS OPTIONNELLE. Sur les 1 007 photos du premier
--  releve, 778 sont en CC BY-SA : citer l'auteur, la licence et sa source
--  est une obligation, pas une politesse. D'ou trois colonnes et non une.
-- ===========================================================================

alter table public.communes
  add column if not exists photo         text,   -- le nom du fichier dans le bucket
  add column if not exists photo_auteur  text,
  add column if not exists photo_licence text,
  add column if not exists photo_source  text;   -- la page Commons de l'image

-- Le bucket, public en lecture : les cartes s'affichent avant meme que le
-- joueur soit connecte, sur la page d'accueil.
insert into storage.buckets (id, name, public)
     values ('communes', 'communes', true)
on conflict (id) do update set public = true;


-- ---------------------------------------------------------------------------
--  Verification
-- ---------------------------------------------------------------------------
select 'A. colonnes' as controle,
       string_agg(column_name, ', ' order by column_name) as valeur
  from information_schema.columns
 where table_schema = 'public' and table_name = 'communes'
   and column_name like 'photo%'
union all
select 'B. bucket',
       coalesce((select id || ' (public : ' || public || ')'
                   from storage.buckets where id = 'communes'), 'ABSENT')
union all
select 'C. deja posees',
       (select count(*)::text from communes where photo is not null)
order by 1;
