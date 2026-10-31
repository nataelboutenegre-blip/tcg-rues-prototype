-- ===========================================================================
--  TerraFront — repérer un tirage automatique (auto-clicker, script) sur le Front
--  Lecture seule, ne modifie rien.
--
--  Ce qu'on peut voir : chaque paquet Front laisse ses 5 communes dans
--  « historique », tirées une par une en quelques instants. On regroupe ces lignes en
--  paquets (cartes à moins de 20 s d'écart), puis on regarde le rythme de chaque joueur sur les 7 derniers jours.
--  (Les paquets Terra gratuits ne laissent aucune trace datée : pas d'analyse possible.)
--
--  Repères : un paquet Front se recharge toutes les 20 min, réserve de 3.
--  Un humain dort, mange, travaille : il a des pauses de plusieurs heures et
--  des écarts irréguliers. Un script ouvre au plus vite, jour et nuit, à
--  intervalles presque identiques (autour de 20 min).
--
--  Colonnes à lire :
--    paquets_par_jour  : 72 recharges par jour au plus, plus les paquets achetés ou offerts
--    heures_actives    : sur 24, les heures de la journée où il a ouvert au moins un paquet
--    paquets_2h_6h     : paquets ouverts entre 2 h et 6 h du matin
--    pause_max_moy_h   : la plus longue pause de chaque jour, en moyenne (un humain : souvent 6 h et plus)
--    rythme_20min      : écarts de 18 à 25 min entre deux paquets (le rythme exact de la recharge)
--    regularite_s      : écart type de ces écarts, en secondes (un script : très faible)
--    alerte            : un résumé ; ce n'est pas une preuve, juste où regarder
-- ===========================================================================

with lignes as (
  select h.joueur_id, h.acquired_at
    from public.historique h
   where h.acquired_at > now() - interval '7 days'
),
marques as (                       -- une carte à plus de 20 s de la précédente ouvre un nouveau groupe
  select joueur_id, acquired_at,
         case when acquired_at - lag(acquired_at) over (partition by joueur_id order by acquired_at) <= interval '20 seconds'
              then 0 else 1 end as nouveau
    from lignes
),
groupes as (
  select joueur_id, acquired_at, sum(nouveau) over (partition by joueur_id order by acquired_at) as g
    from marques
),
paquets as (                       -- au moins 3 cartes tirées à la suite = un paquet (5 cartes, tirées une par une)
  select joueur_id, min(acquired_at) as le
    from groupes
   group by joueur_id, g
  having count(*) >= 3
),
ecarts as (
  select joueur_id, le,
         extract(epoch from le - lag(le) over (partition by joueur_id order by le)) as ecart_s
    from paquets
),
par_jour as (                      -- la plus longue pause qui se termine ce jour-là (la nuit compte)
  select joueur_id, (le at time zone 'Europe/Paris')::date as jour, count(*) as n,
         max(ecart_s) as pause_max_s
    from ecarts
   group by joueur_id, (le at time zone 'Europe/Paris')::date
),
synthese as (
  select e.joueur_id,
         count(*)                                                                         as paquets_7j,
         count(distinct extract(hour from e.le at time zone 'Europe/Paris'))              as heures_actives,
         count(*) filter (where extract(hour from e.le at time zone 'Europe/Paris') between 2 and 5) as paquets_2h_6h,
         count(*) filter (where e.ecart_s between 1080 and 1500)                          as rythme_20min,
         round(stddev_samp(e.ecart_s) filter (where e.ecart_s between 1080 and 1500))     as regularite_s
    from ecarts e
   group by e.joueur_id
)
select j.pseudo,
       s.paquets_7j,
       round(s.paquets_7j / greatest(1, (select count(*) from par_jour pj where pj.joueur_id = s.joueur_id))::numeric, 1) as paquets_par_jour,
       (select max(n) from par_jour pj where pj.joueur_id = s.joueur_id)                as max_un_jour,
       s.heures_actives,
       s.paquets_2h_6h,
       (select round(avg(pause_max_s) / 3600.0, 1) from par_jour pj where pj.joueur_id = s.joueur_id) as pause_max_moy_h,
       s.rythme_20min,
       s.regularite_s,
       concat_ws(' · ',
         case when s.heures_actives >= 20 then 'actif presque 24 h sur 24' end,
         case when s.paquets_2h_6h >= 10 then 'beaucoup de paquets la nuit' end,
         case when (select count(*) from par_jour pj where pj.joueur_id = s.joueur_id) >= 3
               and (select avg(pause_max_s) from par_jour pj where pj.joueur_id = s.joueur_id) < 4 * 3600 then 'jamais de longue pause' end,
         case when s.rythme_20min >= 30 and s.regularite_s < 45 then 'rythme de 20 min très régulier' end
       ) as alerte
  from synthese s
  join public.joueurs j on j.id = s.joueur_id
 order by (s.heures_actives >= 20)::int + (s.paquets_2h_6h >= 10)::int
          + (s.rythme_20min >= 30 and coalesce(s.regularite_s, 9999) < 45)::int desc,
          s.paquets_7j desc
 limit 40;
