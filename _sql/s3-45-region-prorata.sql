-- s3-45 : le bonus de région est réduit pour les petites régions, au prorata de leurs communes
-- (plein bonus à partir de 500 communes). Ok de Nataël le 22/11 à 12 h 48.
-- Pourquoi : le Luxembourg (100 communes, 12 cantons) donnait le bonus de région entier (1 200 × 0,6 = 720)
-- avec les 15 cartes de la zone de départ ; Maroli avait 1 195 points de territoire après 2 h de saison.
-- Effet : Luxembourg 720 → 144 · Corse 720 → 514 · les autres régions (565 communes et plus) inchangées.
-- Le bonus des cantons était déjà au prorata (s3-2). Va avec patch491 (textes du jeu).
-- Retour arrière : update config_jeu set valeur = ((valeur::jsonb) - 'region_prorata_communes')::text where cle = 'score_s2';

create or replace function public.score_prorata_region(p_region text) returns numeric
language sql stable security definer set search_path to 'public' as $$
  select case when coalesce(score_reglage('region_prorata_communes'), 0) > 0
    then least(1, (select coalesce(sum(x.n), 0) from (select c.departement, count(*) as n from communes c group by 1) x
                    where est_zone_front(x.departement) and cdj_region(x.departement) = p_region)
                  / score_reglage('region_prorata_communes'))
    else 1 end;
$$;
revoke all on function public.score_prorata_region(text) from public, anon;
grant execute on function public.score_prorata_region(text) to authenticated;

do $$
declare d text; n text;
begin
  d := pg_get_functiondef('public.front_territoires()'::regprocedure);
  n := replace(d, 'sum(score_coef_region(r.region)) as c   -- s3-30b', 'sum(score_coef_region(r.region) * score_prorata_region(r.region)) as c   -- s3-30b, s3-45');
  if n = d then raise exception 's3-45 : front_territoires a changé, rien n''est fait'; end if;
  execute n;
  d := pg_get_functiondef('public.mon_score_detail()'::regprocedure);
  n := replace(d, '''pts'', case when g.gagnee then round(score_coef_region(g.region) * score_reglage(''region''))::integer else 0 end,',
                  '''pts'', case when g.gagnee then round(score_coef_region(g.region) * score_prorata_region(g.region) * score_reglage(''region''))::integer else 0 end,
                                                       ''prorata'', score_prorata_region(g.region),   -- s3-45');
  n := replace(n, 'round(sum(score_coef_region(g.region) * score_reglage(''region'')))', 'round(sum(score_coef_region(g.region) * score_prorata_region(g.region) * score_reglage(''region'')))');
  if n = d or (length(n) - length(replace(n, 'score_prorata_region', ''))) / length('score_prorata_region') <> 3 then
    raise exception 's3-45 : mon_score_detail a changé, rien n''est fait';
  end if;
  execute n;
  update config_jeu set valeur = ((valeur::jsonb) || '{"region_prorata_communes": 500}'::jsonb)::text where cle = 'score_s2';
end $$;
select public.classement_cache_maj();

-- contrôle : 0.200 · 0.714 · 1 · 1
select round(score_prorata_region('Luxembourg'), 3) as luxembourg, round(score_prorata_region('Corse'), 3) as corse,
       score_prorata_region('Belgique') as belgique, score_prorata_region('Bretagne') as bretagne;
