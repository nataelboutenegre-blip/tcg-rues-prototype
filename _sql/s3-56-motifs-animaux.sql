-- s3-56 (23/11/2026) : 16 animaux héraldiques gratuits dans les motifs (patch505, demande d'ASMFCB).
-- Dessins game-icons.net, CC BY 3.0 (crédit dans l'éditeur et les mentions légales).
-- Retour arrière : delete from motif_formes where id in ('lion','aigle','griffon','dragon','sanglier','ours','loup','cerf','dauphin','coq','cygne','corbeau','licorne','salamandre','abeille','pegase');
--   (un motif qui utilise déjà un animal serait alors refusé à sa prochaine modification, pas effacé)
insert into public.motif_formes(id, pack) values
  ('lion', null), ('aigle', null), ('griffon', null), ('dragon', null), ('sanglier', null), ('ours', null), ('loup', null), ('cerf', null), ('dauphin', null), ('coq', null), ('cygne', null), ('corbeau', null), ('licorne', null), ('salamandre', null), ('abeille', null), ('pegase', null)
on conflict (id) do update set pack = excluded.pack;
select count(*) filter (where pack is null) gratuites, count(*) toutes from motif_formes;
