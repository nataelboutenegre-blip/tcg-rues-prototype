-- TerraFront — diagnostic (lecture seule) : pourquoi un joueur a des points
-- « territoires ». Changer le pseudo sur la ligne marquée. Une seule requête.
-- Colonnes : département, ses communes, celles du joueur, sa part, la part du
-- 2e joueur du département, le statut retenu, puis les seuils en vigueur.
with j as (select id from joueurs where pseudo = 'Master__Of__Kitten'),   -- <== pseudo
tailles as (select departement, count(*)::numeric n from communes group by departement),
parts as (
  select c.departement, p.joueur_id, count(*)::numeric n
    from possessions p join communes c on c.code = p.commune_code
   group by c.departement, p.joueur_id)
select pa.departement, ta.n::int as communes_dep, pa.n::int as a_lui,
       round(100 * pa.n / ta.n, 1) as part_pct,
       (select max(p2.n)::int from parts p2 where p2.departement = pa.departement and p2.joueur_id <> pa.joueur_id) as deuxieme,
       case when pa.n / ta.n >= score_reglage('seuil_controle') then 'contrôlé'
            when pa.n / ta.n >= score_reglage('seuil_domine')
             and pa.n > coalesce((select max(p2.n) from parts p2 where p2.departement = pa.departement and p2.joueur_id <> pa.joueur_id), 0)
            then 'dominé' else '—' end as statut,
       score_reglage('seuil_domine') as seuil_domine, score_reglage('seuil_controle') as seuil_controle,
       score_reglage('dep_domine') as pts_domine, score_reglage('dep_controle') as pts_controle
  from parts pa join tailles ta on ta.departement = pa.departement
 where pa.joueur_id = (select id from j)
 order by (pa.n / ta.n) desc
 limit 15;
