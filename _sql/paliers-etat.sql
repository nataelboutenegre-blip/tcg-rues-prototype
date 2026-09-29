-- ===========================================================================
--  TerraFront — etat des paliers de rarete
--
--  LECTURE SEULE. Aucune ecriture, aucun appel a saison_courante().
--
--  But : savoir sur quoi reposent les paliers actuels et ce qu'un
--  reglage couterait, AVANT d'en proposer un.
-- ===========================================================================

-- ---------------------------------------------------------------------------
--  A. L'echelle actuelle, et sur quoi elle repose
--
--  Si les fourchettes de population ne se chevauchent pas, le palier est
--  decide par la population seule : on pourra le recalculer. Si elles se
--  chevauchent, autre chose intervient et il faudra le trouver.
-- ---------------------------------------------------------------------------
select 'A. echelle actuelle' as section,
       c.tier                                        as palier,
       count(*)                                      as communes,
       round(100.0 * count(*) / sum(count(*)) over (), 2) as pct,
       min(c.population)                             as pop_min,
       max(c.population)                             as pop_max,
       percentile_disc(0.5) within group (order by c.population) as pop_mediane
  from communes c
 group by c.tier
 order by count(*) desc;


-- ---------------------------------------------------------------------------
--  B. Les fourchettes se chevauchent-elles ?
-- ---------------------------------------------------------------------------
with bornes as (
  select tier, min(population) as bas, max(population) as haut
    from communes group by tier
)
select 'B. chevauchement' as section,
       a.tier || ' (' || a.bas || '-' || a.haut || ')'
         || ' recouvre ' || b.tier || ' (' || b.bas || '-' || b.haut || ')' as constat
  from bornes a join bornes b on a.tier < b.tier
 where a.haut >= b.bas and b.haut >= a.bas
union all
select 'B. chevauchement', 'aucun chevauchement : la population decide seule'
 where not exists (
   select 1 from bornes a join bornes b on a.tier < b.tier
    where a.haut >= b.bas and b.haut >= a.bas);


-- ---------------------------------------------------------------------------
--  C. Ce qu'un retirage deplacerait chez les joueurs
--
--  Combien de communes DETENUES par palier, et combien de joueurs
--  possedent au moins une legendaire aujourd'hui.
-- ---------------------------------------------------------------------------
select 'C. detenues par palier' as section,
       c.tier as palier,
       count(*) as detenues,
       count(*) filter (where p.gardee) as gardees
  from possessions p join communes c on c.code = p.commune_code
 group by c.tier
 order by count(*) desc;

select 'C. joueurs a legendaire' as section,
       count(distinct p.joueur_id)::text as valeur
  from possessions p join communes c on c.code = p.commune_code
 where c.tier = 'legendaire';


-- ---------------------------------------------------------------------------
--  D. La population aux rangs de coupure candidats
--
--  On classe les 34 739 communes de la plus peuplee a la moins peuplee.
--  Ces rangs sont ceux que donneraient plusieurs echelles regulieres.
--  Ca me dira si une coupure tombe sur un seuil de population presentable
--  (5 000 hab., 2 000 hab.) ou au milieu de nulle part.
-- ---------------------------------------------------------------------------
with classees as (
  select population,
         row_number() over (order by population desc, code) as rg
    from communes
)
select 'D. seuils' as section,
       t.rg as rang_de_coupure,
       c.population as population_a_ce_rang
  from (values (48), (100), (134), (200), (316),
               (805), (981), (1200), (1390), (1800),
               (4392), (4826), (6114), (7000)) as t(rg)
  join classees c on c.rg = t.rg
 order by t.rg;


-- ---------------------------------------------------------------------------
--  E. Combien de communes par tranche de population
--
--  Pour voir ou la matiere se trouve reellement : c'est ce qui limite les
--  echelles possibles.
-- ---------------------------------------------------------------------------
select 'E. tranches' as section,
       case
         when population >= 100000 then 'a. 100 000 et +'
         when population >=  50000 then 'b. 50 000 a 100 000'
         when population >=  20000 then 'c. 20 000 a 50 000'
         when population >=  10000 then 'd. 10 000 a 20 000'
         when population >=   5000 then 'e. 5 000 a 10 000'
         when population >=   2000 then 'f. 2 000 a 5 000'
         when population >=   1000 then 'g. 1 000 a 2 000'
         when population >=    500 then 'h. 500 a 1 000'
         when population >=    200 then 'i. 200 a 500'
         else                           'j. moins de 200'
       end as tranche,
       count(*) as communes,
       sum(count(*)) over (order by min(population) desc) as cumul
  from communes
 group by 2
 order by 2;
