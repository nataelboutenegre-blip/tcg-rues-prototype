-- ===========================================================================
--  LECTURE SEULE — les attaques visent-elles trop les légendaires ?
--  (3/11/2026, remarque d'Oshannir : « une légendaire coûte autant d'énergie
--  qu'une commune, des joueurs spamment les attaques de légendaires »)
--  À lancer quelques jours après s2-87 : le journal des rounds (front_rounds)
--  commence le jour où s2-87 est lancé. Les rounds annulés par une garnison
--  comptent comme perdus.
--   RARETÉ  : sur les 7 derniers jours, par rareté de la cible : rounds,
--             rounds par jour, attaquants différents, % gagnés, conquêtes.
--   JOUEURS : par joueur et par jour, combien de rounds sur des légendaires
--             (combien de joueurs-jours à 1-4, 5-9, 10-19, 20 ou plus).
--   PART    : la part des légendaires dans tous les rounds, et chez les
--             10 joueurs qui attaquent le plus.
--   SIÈGES  : les séries en cours aujourd'hui, par rareté.
--  Aucun pseudo. Ne modifie rien. Un seul tableau.
-- ===========================================================================
with r as (
  select x.*, (x.le at time zone 'Europe/Paris')::date as jour
    from public.front_rounds x
   where x.le > now() - interval '7 days'
),
jours as (select greatest(1, count(distinct jour)) as n from r),
ordre_tier(tier, o) as (values ('commun', 1), ('peucommun', 2), ('rare', 3), ('epique', 4), ('legendaire', 5)),
leg as (select attaquant_id, jour, count(*) as n from r where tier = 'legendaire' group by 1, 2),
gros as (select attaquant_id from r group by 1 order by count(*) desc limit 10)
select 1 as ordre, 'RARETÉ' as quoi, coalesce(r.tier, '?') as ligne,
       count(*) || ' rounds (' || round(count(*)::numeric / (select n from jours), 1) || ' par jour) · '
       || count(distinct r.attaquant_id) || ' attaquants · '
       || round(100.0 * count(*) filter (where r.gagne) / count(*)) || ' % gagnés · '
       || count(*) filter (where r.gagne and r.victoires >= 3) || ' conquêtes' as valeur,
       coalesce(max(o.o), 9) as tri
  from r left join ordre_tier o on o.tier = r.tier
 group by r.tier
union all
select 2, 'JOUEURS', 'légendaires par joueur et par jour',
       count(*) filter (where n between 1 and 4) || ' joueurs-jours à 1-4 rounds · '
       || count(*) filter (where n between 5 and 9) || ' à 5-9 · '
       || count(*) filter (where n between 10 and 19) || ' à 10-19 · '
       || count(*) filter (where n >= 20) || ' à 20 ou plus · maximum ' || coalesce(max(n), 0), 0
  from leg
union all
select 3, 'PART', 'tous les joueurs',
       coalesce(round(100.0 * count(*) filter (where tier = 'legendaire') / nullif(count(*), 0)), 0) || ' % des rounds visent une légendaire', 0
  from r
union all
select 3, 'PART', 'les 10 qui attaquent le plus',
       coalesce(round(100.0 * count(*) filter (where tier = 'legendaire') / nullif(count(*), 0)), 0) || ' % de leurs rounds visent une légendaire', 1
  from r where attaquant_id in (select attaquant_id from gros)
union all
select 4, 'SIÈGES', coalesce(c.tier, '?'),
       count(*) || ' séries en cours · ' || count(distinct s.attacker_id) || ' attaquants · '
       || count(*) filter (where s.victoires_consecutives >= 2) || ' à 2 victoires',
       coalesce(max(o.o), 9)
  from public.sieges s
  join public.communes c on c.code = s.commune_code
  left join ordre_tier o on o.tier = c.tier
 where coalesce(s.victoires_consecutives, 0) > 0
 group by c.tier
order by 1, 5, 3;
