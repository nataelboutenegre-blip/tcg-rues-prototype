-- ===========================================================================
--  LECTURE SEULE — Front : combien de communes sont tenues par des joueurs
--  absents (saison 2, depuis le 25/10 10 h).
--  « Dernier passage » = le dernier jour où le joueur a ouvert le jeu
--  (jours_joues), ou sa dernière connexion si c'est plus récent.
--  Tranches : 0-2 jours, 3-4 jours, 5-6 jours, 7 jours et plus, et
--  « pas revenu depuis le début de la saison 2 ».
--  Dernière ligne : les communes encore libres, pour comparer.
--  Un seul tableau (l'éditeur Supabase n'affiche que le dernier résultat).
-- ===========================================================================
with debut as (select date '2026-10-25' as d),
auj as (select (now() at time zone 'Europe/Paris')::date as d),
vu as (
  select j.id,
         greatest((select max(jj.jour) from jours_joues jj where jj.joueur_id = j.id),
                  (select (u.last_sign_in_at at time zone 'Europe/Paris')::date from auth.users u where u.id = j.id)) as dernier
    from joueurs j
),
proprio as (
  select p.joueur_id, count(*) as communes,
         count(*) filter (where c.tier in ('rare', 'epique', 'legendaire')) as rares_et_plus
    from possessions p join communes c on c.code = p.commune_code
   where p.joueur_id is not null
   group by 1
),
t as (
  select case when v.dernier is null or v.dernier < (select d from debut) then '5. pas revenu en saison 2'
              when (select d from auj) - v.dernier >= 7 then '4. absent depuis 7 jours et plus'
              when (select d from auj) - v.dernier >= 5 then '3. absent depuis 5-6 jours'
              when (select d from auj) - v.dernier >= 3 then '2. absent depuis 3-4 jours'
              else '1. actif (0-2 jours)' end as tranche,
         p.communes, p.rares_et_plus
    from proprio p left join vu v on v.id = p.joueur_id
)
select tranche,
       count(*)                                                        as joueurs,
       sum(communes)                                                   as communes,
       round(100.0 * sum(communes) / sum(sum(communes)) over (), 1)    as pct_des_possedees,
       sum(rares_et_plus)                                              as dont_rares_et_plus
  from t group by tranche
union all
select '6. communes libres (pour comparer)', null,
       (select count(*) from communes c left join possessions p on p.commune_code = c.code
         where p.commune_code is null or p.joueur_id is null),
       null, null
order by 1;
