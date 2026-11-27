-- s3-88 (27/11/2026) : « Mes points » indisponible (Arkhannou).
-- score_prorata_region appelait est_zone_front et cdj_region sur chaque commune (37 643) : 1,3 s par appel,
-- appelée trois fois par région dans mon_score_detail -> plus de 8 s pour les gros joueurs, coupé par le serveur.
-- On compte d'abord par département (offset 0 empêche le planificateur de remonter le filtre). Résultat identique.
create or replace function public.score_prorata_region(p_region text)
 returns numeric language sql stable security definer set search_path to 'public'
as $f$
  select case when coalesce(score_reglage('region_prorata_communes'), 0) > 0
    then least(1, (select coalesce(sum(x.n), 0)
                     from (select c.departement, count(*) as n from communes c group by 1 offset 0) x   -- s3-88 : compter d'abord, filtrer ensuite
                    where est_zone_front(x.departement) and cdj_region(x.departement) = p_region)
                  / score_reglage('region_prorata_communes'))
    else 1 end;
$f$;
