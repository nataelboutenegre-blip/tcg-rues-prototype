-- s2-19b — correctif des collections (à passer après s2-19). Rejouable.
--
-- 1. Paris, Lyon et Marseille sont découpées en arrondissements dans le jeu :
--    la préfecture compte pour l'arrondissement de l'hôtel de ville
--    (Paris 4e, Lyon 1er, Marseille 2e).
-- 2. Conques-en-Rouergue n'existe pas sous le code 12218 : on prend la
--    commune du jeu la plus proche du village de Conques (Aveyron).
--
-- Contrôle attendu : 435 | 96 | 185 | le nom de la commune retenue pour Conques

begin;

insert into public.collection_communes (collection_id, code)
select 'prefectures', v.code from (values ('75104'), ('69381'), ('13202')) as v(code)
 where exists (select 1 from public.communes c where c.code = v.code)
on conflict do nothing;

insert into public.collection_communes (collection_id, code)
select 'villages', c.code
  from public.communes c
 where c.departement = '12' and c.latitude is not null
 order by (c.latitude - 44.5990) ^ 2 + ((c.longitude - 2.3980) * 0.71) ^ 2
 limit 1
on conflict do nothing;

commit;

-- contrôle : 435 | 96 | 185 | commune retenue pour Conques
select (select count(*) from public.collection_communes)                                    as total_435,
       (select count(*) from public.collection_communes where collection_id = 'prefectures') as prefectures_96,
       (select count(*) from public.collection_communes where collection_id = 'villages')    as villages_185,
       (select c.code || ' ' || c.nom from public.communes c
         where c.departement = '12' and c.latitude is not null
         order by (c.latitude - 44.5990) ^ 2 + ((c.longitude - 2.3980) * 0.71) ^ 2 limit 1) as conques;
