-- ===========================================================================
--  s3-16 — des colonnes photo dans la réserve suisse
--  La réserve (suisse_communes_attente) n'est lue par aucun joueur : on peut y
--  poser les photos dès maintenant. photos-suisse.py (sur le Mac) les remplit,
--  s3-5 les recopie dans communes le jour J.
--  Contrôle attendu : 4 | 0
-- ===========================================================================
alter table public.suisse_communes_attente
  add column if not exists photo text,
  add column if not exists photo_auteur text,
  add column if not exists photo_licence text,
  add column if not exists photo_source text;
notify pgrst, 'reload schema';

select (select count(*) from information_schema.columns
         where table_name = 'suisse_communes_attente' and column_name like 'photo%') as colonnes,
       (select count(*) from public.suisse_communes_attente where photo is not null) as photos;
