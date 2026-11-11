-- s2-137 (11/11/2026) : « Mes points », le détail de MON score du Front (idée d'Oshannir)
-- Une seule fonction, en lecture, pour le joueur connecté uniquement (auth.uid()) : mêmes calculs que
-- front_scores(), front_territoires() et score_batiments(), ligne par ligne. Rien d'autre ne change.
-- Le classement lit une copie faite chaque minute : un écart d'une minute au plus est possible.

create or replace function public.mon_score_detail()
returns jsonb
language plpgsql
stable
security definer
set search_path to 'public'
as $$
declare
  v_uid uuid := auth.uid();
  v_actif boolean := score_bonus_actif();
  v_s record;
  v_cartes jsonb; v_cartes_pts integer;
  v_vict integer; v_combats_pts integer;
  v_deps jsonb; v_regions jsonb; v_terr_pts integer; v_sans integer;
  v_bat jsonb; v_bat_pts integer;
  v_bombes jsonb; v_bombes_pts integer;
  v_reb_lingots integer; v_reb_pts integer;
begin
  if v_uid is null then raise exception 'Non connecte'; end if;
  select sa.id, sa.debut into v_s from saisons sa where sa.etat <> 'terminee' order by sa.debut desc limit 1;

  -- 1. cartes
  select coalesce(jsonb_agg(jsonb_build_object('tier', x.tier, 'n', x.n, 'pu', x.pu, 'pts', x.n * x.pu)
                            order by array_position(array['legendaire','epique','rare','peucommun','commun'], x.tier::text)), '[]'::jsonb),
         coalesce(sum(x.n * x.pu), 0)::integer
    into v_cartes, v_cartes_pts
    from (select c.tier, count(*)::integer n, points_rarete(c.tier)::integer pu
            from possessions p join communes c on c.code = p.commune_code
           where p.joueur_id = v_uid group by c.tier) x;

  -- 2. combats
  select count(*)::integer into v_vict
    from front_victoires v where v.joueur_id = v_uid and v.compte and v.saison = v_s.id;
  v_combats_pts := case when v_actif then (v_vict * score_reglage('victoire'))::integer else 0 end;

  -- 3. territoires (front_territoires, pour mes départements)
  with mesdeps as (
    select distinct c.departement from possessions p join communes c on c.code = p.commune_code
     where p.joueur_id = v_uid and length(c.departement) = 2
  ), tailles as (
    select c.departement, count(*)::numeric n from communes c where c.departement in (select departement from mesdeps) group by 1
  ), parts as (
    select c.departement, p.joueur_id, count(*)::numeric n
      from possessions p join communes c on c.code = p.commune_code
     where c.departement in (select departement from mesdeps) group by 1, 2
  ), tetes as (
    select pa.departement, max(pa.n) maxi, count(*) filter (where true) nb from parts pa group by 1
  ), deps as (
    select pa.departement, pa.n, ta.n taille,
           (pa.n = t.maxi and (select count(*) from parts p2 where p2.departement = pa.departement and p2.n = t.maxi) = 1) seul,
           pa.n / ta.n part
      from parts pa join tailles ta on ta.departement = pa.departement join tetes t on t.departement = pa.departement
     where pa.joueur_id = v_uid
  ), deps_p as (
    select d.*,
           case when d.part >= 1 then 100 when d.part >= 0.75 then 75 when d.part >= 0.50 then 50
                when d.seul and d.part >= 0.25 then 25 when d.seul and d.part >= 0.10 then 10
                when d.seul and d.part >= 0.05 and d.n >= score_reglage('palier_5_min_communes') then 5 end palier
      from deps d
  ), deps_ok as (
    select d.*, round(score_reglage('palier_' || d.palier)
                      * case when coalesce(score_reglage('prorata_communes'), 20) > 0
                             then least(1, d.taille / coalesce(score_reglage('prorata_communes'), 20)) else 1 end)::integer pts,
           cdj_region(d.departement) region
      from deps_p d where d.palier is not null
  ), reg_tailles as (
    select cdj_region(t.departement) region, count(*) n
      from (select distinct c.departement from communes c where length(c.departement) = 2) t group by 1
  ), regs as (
    select r.region, r.n, rt.n total, (r.n * 2 > rt.n) gagnee
      from (select d.region, count(*) n from deps_ok d where d.palier >= 10 group by 1) r
      join reg_tailles rt on rt.region = r.region
  )
  select coalesce((select jsonb_agg(jsonb_build_object('dep', d.departement, 'n', d.n::integer, 'taille', d.taille::integer,
                                                       'part', round(d.part * 100, 1), 'palier', d.palier, 'seul', d.seul, 'pts', d.pts)
                                    order by d.pts desc, d.part desc) from deps_ok d), '[]'::jsonb),
         coalesce((select jsonb_agg(jsonb_build_object('region', g.region, 'n', g.n, 'total', g.total, 'gagnee', g.gagnee,
                                                       'pts', case when g.gagnee then score_reglage('region')::integer else 0 end)
                                    order by g.gagnee desc, g.n desc) from regs g), '[]'::jsonb),
         coalesce((select sum(d.pts) from deps_ok d), 0)::integer
           + coalesce((select count(*) from regs g where g.gagnee), 0)::integer * score_reglage('region')::integer,
         (select count(*) from deps_p d where d.palier is null)::integer
    into v_deps, v_regions, v_terr_pts, v_sans;
  if not v_actif then v_terr_pts := 0; end if;

  -- 4. bâtiments, bombes, rébellions (score_batiments)
  with h as (
    select h.type, count(*)::integer n from batiments_historique h
     where h.joueur_id = v_uid and h.saison = v_s.id and h.pret_le <= now() group by 1
  ), x as (
    select t.type, t.ordre, coalesce(h.n, 0) n, t.maxi, t.pu
      from (values ('fonderie', 1, batiment_reglage('fonderies_max')::integer, coalesce(score_reglage('bat_fonderie'), 50)::integer),
                   ('forteresse', 2, batiment_reglage('forteresse_max')::integer, coalesce(score_reglage('bat_forteresse'), 80)::integer),
                   ('centre', 3, 1, coalesce(score_reglage('bat_centre'), 150)::integer),
                   ('banque', 4, 1, coalesce(score_reglage('bat_banque'), 80)::integer),
                   ('radar', 5, 1, coalesce(score_reglage('bat_radar'), 80)::integer)) t(type, ordre, maxi, pu)
      left join h on h.type = t.type
  )
  select coalesce(jsonb_agg(jsonb_build_object('type', x.type, 'n', x.n, 'comptes', least(x.n, x.maxi), 'maxi', x.maxi,
                                               'pu', x.pu, 'pts', least(x.n, x.maxi) * x.pu) order by x.ordre) filter (where x.n > 0), '[]'::jsonb),
         coalesce(sum(least(x.n, x.maxi) * x.pu), 0)::integer
    into v_bat, v_bat_pts from x;

  select coalesce(jsonb_agg(jsonb_build_object('niveau', b.niveau, 'le', b.le, 'nom', c.nom, 'pts', b.pts) order by b.le), '[]'::jsonb),
         coalesce(sum(b.pts), 0)::integer
    into v_bombes, v_bombes_pts
    from (select b.*, (case when b.le < to_timestamp(coalesce(score_reglage('bombe_bareme_depuis'), 0))
                            then greatest(coalesce(score_reglage('bombe'), 300), coalesce(score_reglage('bombe_' || b.niveau), score_reglage('bombe'), 300))
                            else coalesce(score_reglage('bombe_' || b.niveau), score_reglage('bombe'), 300) end)::integer pts
            from bombes b where b.lanceur = v_uid and b.le >= v_s.debut) b
    left join communes c on c.code = b.cible_code;

  with lj as (
    select (r.debut at time zone 'Europe/Paris')::date jour, r.mise lingots from rebellions r
     where r.financeur = v_uid and r.debut >= v_s.debut
    union all
    select (e.le at time zone 'Europe/Paris')::date, e.lingots from rebellions_etouffements e
     where e.defenseur = v_uid and e.le >= v_s.debut
  )
  select coalesce(sum(j.l), 0)::integer, coalesce(sum(j.p), 0)::integer into v_reb_lingots, v_reb_pts
    from (select sum(lj.lingots) l, least(sum(lj.lingots) * coalesce(score_reglage('rebellion_lingot'), 2),
                                           coalesce(score_reglage('rebellion_jour'), 60)) p
            from lj group by lj.jour) j;

  if not v_actif then v_bat_pts := 0; v_bombes_pts := 0; v_reb_pts := 0; end if;

  return jsonb_build_object(
    'actif', v_actif,
    'total', v_cartes_pts + v_combats_pts + v_terr_pts + v_bat_pts + v_bombes_pts + v_reb_pts,
    'cartes', jsonb_build_object('pts', v_cartes_pts, 'lignes', v_cartes),
    'combats', jsonb_build_object('pts', v_combats_pts, 'victoires', v_vict, 'pu', score_reglage('victoire')::integer),
    'territoires', jsonb_build_object('pts', v_terr_pts, 'deps', v_deps, 'regions', v_regions, 'sans', v_sans,
                                      'region_pts', score_reglage('region')::integer),
    'batiments', jsonb_build_object('pts', v_bat_pts + v_bombes_pts + v_reb_pts, 'lignes', v_bat,
                                    'bombes', v_bombes, 'bombes_pts', v_bombes_pts,
                                    'rebellions_lingots', v_reb_lingots, 'rebellions_pts', v_reb_pts));
end;
$$;

revoke all on function public.mon_score_detail() from public, anon;
grant execute on function public.mon_score_detail() to authenticated;
notify pgrst, 'reload schema';

-- contrôle : la fonction existe, fermée à anon
select has_function_privilege('authenticated', 'public.mon_score_detail()', 'execute') as joueurs_ok,
       not has_function_privilege('anon', 'public.mon_score_detail()', 'execute') as anon_ferme;
