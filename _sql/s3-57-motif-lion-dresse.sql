-- s3-57 (23/11/2026) : le « Lion dressé » gratuit dans les motifs (patch506). Gravure de 1862, domaine public.
-- Retour arrière : delete from motif_formes where id = 'lionrampant';
insert into public.motif_formes(id, pack) values ('lionrampant', null) on conflict (id) do update set pack = excluded.pack;
select count(*) filter (where pack is null) gratuites, count(*) toutes from motif_formes;
