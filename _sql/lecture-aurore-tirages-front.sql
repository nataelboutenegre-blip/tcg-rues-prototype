-- ===========================================================================
--  TerraFront — LECTURE SEULE (27 octobre 2026)
--  À quelle fréquence une commune Aurore sort-elle d'un paquet Front ?
--  En Front, il n'y a pas de tirage Aurore à part : une commune de la liste
--  qui sort d'un paquet est Aurore. On compte les tirages du journal depuis
--  le lancement (25/10), en tout et par rareté, puis le stock libre actuel.
--  Ne modifie rien. Une ligne par rareté + une ligne TOTAL.
-- ===========================================================================
with t as (
  select j.commune_code, c.tier, (a.code is not null) as aurore
    from public.journal j
    join public.communes c on c.code = j.commune_code
    left join public.aurore_communes a on a.code = j.commune_code
   where j.type = 'tirage' and j.cree_le >= '2026-10-25'
),
libres as (
  select c.tier, count(*) as libres, count(*) filter (where a.code is not null) as libres_aurore
    from public.communes c
    left join public.possessions p on p.commune_code = c.code
    left join public.aurore_communes a on a.code = c.code
   where p.commune_code is null and length(c.departement) = 2
   group by c.tier
)
select t.tier                                                         as rarete,
       count(*)                                                       as cartes_tirees,
       count(*) filter (where t.aurore)                               as dont_aurore,
       round(100.0 * count(*) filter (where t.aurore) / count(*), 2)  as pct_aurore,
       max(l.libres)                                                  as libres_aujourdhui,
       max(l.libres_aurore)                                           as aurore_libres_aujourdhui
  from t left join libres l on l.tier = t.tier
 group by t.tier
union all
select 'TOTAL', count(*), count(*) filter (where aurore), round(100.0 * count(*) filter (where aurore) / nullif(count(*), 0), 2),
       (select sum(libres) from libres), (select sum(libres_aurore) from libres)
  from t
order by 2 desc;
