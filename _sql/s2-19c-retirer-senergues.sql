-- s2-19c — retire Sénergues de la collection « Plus beaux villages ». Rejouable.
-- s2-19b l'avait prise comme commune la plus proche de Conques, mais
-- Sénergues n'est pas Conques : le village de Conques n'existe pas dans le
-- jeu. La collection compte donc 184 villages.
-- Contrôle attendu : 434 | 184 | 0

begin;
delete from public.collection_communes where collection_id = 'villages' and code = '12268';
commit;

select (select count(*) from public.collection_communes)                                   as total_434,
       (select count(*) from public.collection_communes where collection_id = 'villages')  as villages_184,
       (select count(*) from public.collection_communes where code = '12268')              as senergues_0;
