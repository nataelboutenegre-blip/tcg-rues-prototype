-- ===========================================================================
--  TerraFront — collection Vins de France : les crus communaux du Muscadet
--  (25 octobre 2026, remarque de Maroli sur Discord)
--  Les crus communaux du Muscadet Sèvre-et-Maine portent le nom de
--  communes : Clisson, Gorges, Le Pallet, Vallet, Château-Thébaud,
--  La Haie-Fouassière, et Mouzillon (cru « Mouzillon-Tillières »).
--  Les joueurs qui ont déjà reçu la récompense de la collection la gardent.
--  Rejouable. Contrôle attendu : 7 | le nouveau total de la collection (78).
-- ===========================================================================
begin;

insert into public.collection_communes (collection_id, code)
select 'vins', v.code from (values
  ('44043'), ('44064'), ('44117'), ('44212'), ('44037'), ('44070'), ('44108')
) as v(code)
 where exists (select 1 from public.communes c where c.code = v.code)
on conflict do nothing;

commit;

select (select count(*) from public.collection_communes
         where collection_id = 'vins' and code in ('44043','44064','44117','44212','44037','44070','44108')) as muscadet_7,
       (select count(*) from public.collection_communes where collection_id = 'vins')                     as vins_total;
