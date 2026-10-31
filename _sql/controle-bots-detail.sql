-- ===========================================================================
--  TerraFront — le détail des journées les plus chargées (Front)
--  Lecture seule, ne modifie rien.
--
--  Pour les 5 joueurs qui ont ouvert le plus de paquets Front sur 7 jours :
--  leur journée la plus chargée, heure par heure, et d'où peuvent venir les
--  paquets au-delà des recharges.
--
--  Repères : une recharge toutes les 20 min = 72 paquets en 24 h, plus la
--  réserve de 3 du début de journée = 75 paquets gratuits au plus.
--  Au-delà : paquets achetés (200 TP, 5 par jour au plus) ou paquets offerts
--  (récompenses, cadeaux). Un paquet = au moins 3 cartes tirées à moins de
--  20 s d'écart (5 cartes, tirées une par une).
--
--  Colonnes :
--    jour / paquets        : la journée la plus chargée et son nombre de paquets
--    achetes_200tp         : paiements de 200 TP ce jour-là hors Terra (paquets Front achetés probables)
--    au_dela               : paquets - 75 - achetés : ce qui viendrait d'ailleurs (offerts, récompenses)
--    par_heure             : 24 nombres, de 0 h à 23 h (heure de Paris)
-- ===========================================================================

with lignes as (
  select h.joueur_id, h.acquired_at
    from public.historique h
   where h.acquired_at > now() - interval '7 days'
),
marques as (
  select joueur_id, acquired_at,
         case when acquired_at - lag(acquired_at) over (partition by joueur_id order by acquired_at) <= interval '20 seconds'
              then 0 else 1 end as nouveau
    from lignes
),
groupes as (
  select joueur_id, acquired_at, sum(nouveau) over (partition by joueur_id order by acquired_at) as g from marques
),
paquets as (
  select joueur_id, min(acquired_at) as le from groupes group by joueur_id, g having count(*) >= 3
),
top as (
  select joueur_id from paquets group by joueur_id order by count(*) desc limit 5
),
jours as (
  select p.joueur_id, (p.le at time zone 'Europe/Paris')::date as jour, count(*) as n
    from paquets p join top t using (joueur_id)
   group by p.joueur_id, (p.le at time zone 'Europe/Paris')::date
),
pire as (
  select distinct on (joueur_id) joueur_id, jour, n from jours order by joueur_id, n desc, jour desc
)
select j.pseudo,
       x.jour,
       x.n as paquets,
       (select count(*) from public.mouvements_points m
         where m.joueur_id = x.joueur_id and m.montant = -200
           and coalesce(m.motif, '') <> 'terra_paquet'
           and (m.cree_le at time zone 'Europe/Paris')::date = x.jour) as achetes_200tp,
       greatest(0, x.n - 75 - (select count(*) from public.mouvements_points m
         where m.joueur_id = x.joueur_id and m.montant = -200
           and coalesce(m.motif, '') <> 'terra_paquet'
           and (m.cree_le at time zone 'Europe/Paris')::date = x.jour)) as au_dela,
       (select string_agg(coalesce(c.n, 0)::text, ' ' order by h.h)
          from generate_series(0, 23) h(h)
          left join (select extract(hour from p.le at time zone 'Europe/Paris')::int as h, count(*) as n
                       from paquets p
                      where p.joueur_id = x.joueur_id and (p.le at time zone 'Europe/Paris')::date = x.jour
                      group by 1) c on c.h = h.h) as par_heure
  from pire x
  join public.joueurs j on j.id = x.joueur_id
 order by x.n desc;
