-- ===========================================================================
--  TerraFront — lecture du sondage « d'autres pays ? » (s2-80)
--  LECTURE SEULE, aucun pseudo. Une seule requête : un tableau.
--  Lignes « réponse » : nombre et pourcentage par réponse, et la part chez
--  les joueurs actifs (venus dans les 7 derniers jours) ;
--  lignes « pays » : le pays demandé en premier par ceux qui ont dit oui ;
--  lignes « carte » : réponses, cartes fermées sans répondre.
-- ===========================================================================
with r as (
  select s.*, (u.last_sign_in_at > now() - interval '7 days') as actif
    from public.sondage_pays s
    left join auth.users u on u.id = s.joueur_id
), rep as (
  select * from r where repondu_le is not null
), tot as (select count(*)::numeric as n, count(*) filter (where actif)::numeric as na from rep)
select 'réponse' as quoi,
       case choix when 'meme' then 'Oui, même carte' when 'apart' then 'Oui, mode à part'
                  when 'non' then 'Non, la France' else 'Ça m''est égal' end as detail,
       count(*) as nombre,
       round(100 * count(*) / nullif((select n from tot), 0), 1) as pourcent,
       round(100 * count(*) filter (where actif) / nullif((select na from tot), 0), 1) as pourcent_actifs
  from rep group by choix
union all
select 'pays', pays, count(*), round(100 * count(*)::numeric / nullif((select count(*) from rep where pays is not null), 0), 1), null
  from rep where pays is not null group by pays
union all
select 'carte', 'réponses', (select count(*) from rep), null, null
union all
select 'carte', 'fermées sans répondre', (select count(*) from r where repondu_le is null and fermetures > 0), null, null
order by 1 desc, 3 desc;
