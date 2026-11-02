-- ===========================================================================
--  LECTURE SEULE — combien de communes du Front sont tenues par des absents ?
--  (2/11/2026, pour la « roue d'arrivée » des nouveaux joueurs)
--  « Absent depuis N jours » = n'a pas ouvert le jeu (jours_joues) ni ne
--  s'est connecté depuis N jours.
--  Pour chaque seuil : joueurs, communes, et leur répartition par rareté.
--  Aucun pseudo. Ne modifie rien. Un seul tableau.
-- ===========================================================================
with auj as (select (now() at time zone 'Europe/Paris')::date as d),
j as (
  select jo.id,
         greatest((select max(jj.jour) from jours_joues jj where jj.joueur_id = jo.id),
                  (select (u.last_sign_in_at at time zone 'Europe/Paris')::date from auth.users u where u.id = jo.id)) as dernier
    from joueurs jo
   where exists (select 1 from possessions p where p.joueur_id = jo.id)
),
p as (
  select x.joueur_id, c.tier, c.departement
    from possessions x join communes c on c.code = x.commune_code
),
seuils as (select unnest(array[3, 7, 14]) as n),
calc as (
  select s.n,
         count(distinct j.id)                                         as joueurs,
         count(p.*)                                                   as communes,
         count(p.*) filter (where p.tier = 'commun')                  as commun,
         count(p.*) filter (where p.tier = 'peucommun')               as peucommun,
         count(p.*) filter (where p.tier = 'rare')                    as rare,
         count(p.*) filter (where p.tier in ('epique', 'legendaire')) as epique_legendaire,
         count(distinct p.departement)                                as departements
    from seuils s
    join j on j.dernier is null or j.dernier <= (select d from auj) - s.n
    join p on p.joueur_id = j.id
   group by s.n
)
select ligne, valeur from (
  select '0. communes au Front (tous joueurs)' as ligne,
         (select count(*) from possessions)::text || ' communes, ' || (select count(*) from j)::text || ' joueurs' as valeur
  union all
  select '1. absents depuis ' || lpad(n::text, 2, '0') || ' jours',
         joueurs || ' joueurs · ' || communes || ' communes (' || commun || ' communes, ' || peucommun || ' peu communes, '
         || rare || ' rares, ' || epique_legendaire || ' épiques ou légendaires) · ' || departements || ' départements'
    from calc
) x
order by ligne;
