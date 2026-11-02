-- ===========================================================================
--  LECTURE SEULE — à quel rythme le pot du Front se vide-t-il ? (2/11/2026)
--  « Tiré » = une commune sort du pot : elle arrive chez un joueur sans
--  qu'un autre joueur la perde au même moment (une conquête ou un échange
--  ne vide pas le pot). « Rendu » = une commune libérée (s2-67), qui revient
--  dans le pot.
--  Projection : communes libres ÷ (tirées − rendues) par jour, sur les
--  3 derniers jours complets, puis sur le rythme d'aujourd'hui.
--  Aucun pseudo. Ne modifie rien. Un seul tableau.
-- ===========================================================================
with s2 as (select timestamp '2026-10-25 10:00' at time zone 'Europe/Paris' as t),
auj as (select (now() at time zone 'Europe/Paris')::date as d),
tirees as (
  select (h.acquired_at at time zone 'Europe/Paris')::date as j, count(*)::numeric as n
    from historique h
   where h.acquired_at >= (select t from s2)
     and not exists (select 1 from historique h2
                      where h2.commune_code = h.commune_code and h2.joueur_id <> h.joueur_id
                        and h2.released_at between h.acquired_at - interval '30 seconds' and h.acquired_at + interval '30 seconds')
   group by 1
),
rendues as (
  select l.jour as j, count(*)::numeric as n from front_liberations l
   where l.le >= (select t from s2) group by 1
),
jours as (
  select d::date as j, coalesce(t.n, 0) as tirees, coalesce(r.n, 0) as rendues
    from generate_series((select d from auj) - 7, (select d from auj), interval '1 day') d
    left join tirees t on t.j = d::date
    left join rendues r on r.j = d::date
),
libres as (
  select count(*) filter (where true)                                 as tout,
         count(*) filter (where left(c.code, 2) not in ('97', '98'))  as metropole
    from communes c
   where not exists (select 1 from possessions p where p.commune_code = c.code)
),
r3 as (select avg(tirees - rendues) as net from jours where j between (select d from auj) - 3 and (select d from auj) - 1),
heures as (select greatest(1, extract(epoch from (now() - ((select d from auj)::timestamp at time zone 'Europe/Paris'))) / 3600.0) as h),
rauj as (select (tirees - rendues) * 24 / (select h from heures) as net from jours where j = (select d from auj))
select ligne, valeur from (
  select '1.' || (7 - ((select d from auj) - j)) || ' · ' || to_char(j, 'DD/MM') || case when j = (select d from auj) then ' (en cours)' else '' end as ligne,
         tirees::int || ' tirées · ' || rendues::int || ' rendues · net ' || (tirees - rendues)::int as valeur
    from jours
  union all select '2. communes libres maintenant', (select tout from libres) || ' (dont ' || (select metropole from libres) || ' en métropole)'
  union all select '3. rythme net, 3 derniers jours', round((select net from r3))::text || ' par jour'
  union all select '4. pot vide vers (rythme des 3 jours)',
         case when coalesce((select net from r3), 0) <= 0 then 'ne se vide pas à ce rythme'
              else to_char(now() + ((select tout from libres) / (select net from r3)) * interval '1 day', 'DD/MM')
                   || ' (dans ' || round((select tout from libres) / (select net from r3), 1) || ' jours)' end
  union all select '5. rythme net d''aujourd''hui (sur 24 h)', round(coalesce((select net from rauj), 0))::text || ' par jour'
  union all select '6. pot vide vers (rythme d''aujourd''hui)',
         case when coalesce((select net from rauj), 0) <= 0 then 'ne se vide pas à ce rythme'
              else to_char(now() + ((select tout from libres) / (select net from rauj)) * interval '1 day', 'DD/MM')
                   || ' (dans ' || round((select tout from libres) / (select net from rauj), 1) || ' jours)' end
) x
order by ligne;
