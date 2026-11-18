-- s3-30 : bonus de territoire selon la population (idée d'Oshannir, décidé par Nataël le 18/11/2026, 22 h 08)
--   Le bonus d'un département (et d'une région) est multiplié par un coefficient selon sa population :
--   racine(population / médiane des départements de métropole), borné entre 0,6 et 1,6.
--   Médiane ≈ 543 000 habitants : Lozère × 0,6 ; département moyen × 1 ; Nord, Paris, Bouches-du-Rhône × 1,6.
--   Région : même calcul contre la médiane des 13 régions de métropole. Cantons suisses et « Suisse » : même règle.
--   La légendaire rapporte 45 au lieu de 60 au classement du Front (Terra ne change pas : points_rarete intact).
--   Seuils inchangés (pourcentage de communes). Interrupteur : score_s2.pop_actif (0 ici ; 1 le 22 après la clôture).

begin;

create or replace function pg_temp.retoucher(p_sig text, p_marque text, p_ancien text, p_nouveau text)
returns void language plpgsql as $f$
declare d text; n integer;
begin
  d := pg_get_functiondef(p_sig::regprocedure);
  if position(p_marque in d) > 0 then return; end if;
  n := (length(d) - length(replace(d, p_ancien, ''))) / length(p_ancien);
  if n <> 1 then raise exception 's3-30 : % a changé (« % » trouvé % fois)', p_sig, left(p_ancien, 70), n; end if;
  if position(p_marque in p_nouveau) = 0 then raise exception 's3-30 : marque % absente du nouveau texte', p_marque; end if;
  execute replace(d, p_ancien, p_nouveau);
end $f$;

update public.config_jeu
   set valeur = ((valeur::jsonb) || jsonb_build_object(
         'pop_actif', coalesce((valeur::jsonb)->'pop_actif', '0'::jsonb),
         'pop_coef_min', 0.6, 'pop_coef_max', 1.6, 'points_legendaire', 45))::text
 where cle = 'score_s2';

-- les populations (France + cantons suisses, y compris ceux pas encore chargés), calculées une fois
create table if not exists public.score_pop (departement text primary key, pop numeric not null, region text, coef numeric not null);
create table if not exists public.score_pop_region (region text primary key, pop numeric not null, coef numeric not null);
alter table public.score_pop enable row level security;
alter table public.score_pop_region enable row level security;
revoke all on public.score_pop, public.score_pop_region from anon, authenticated;

create or replace function public.score_pop_calculer()
returns integer language plpgsql security definer set search_path to 'public' as $$
declare v_min numeric := coalesce(score_reglage('pop_coef_min'), 0.6); v_max numeric := coalesce(score_reglage('pop_coef_max'), 1.6);
  v_med numeric; v_rmed numeric; n integer;
begin
  delete from score_pop; delete from score_pop_region;
  insert into score_pop (departement, pop, region, coef)
  select t.departement, sum(t.population), cdj_region(t.departement), 1
    from (select c.code, c.departement, coalesce(c.population, 0) population from communes c
           where est_metropole(c.departement) or est_canton(c.departement)
          union
          select a.code, a.departement, coalesce(a.population, 0) from suisse_communes_attente a
           where est_canton(a.departement) and not exists (select 1 from communes c where c.code = a.code)) t
   group by t.departement;
  select percentile_cont(0.5) within group (order by pop) into v_med from score_pop where est_metropole(departement);
  update score_pop set coef = round(least(v_max, greatest(v_min, sqrt(pop / v_med))), 3);
  insert into score_pop_region (region, pop, coef) select region, sum(pop), 1 from score_pop where region is not null group by region;
  select percentile_cont(0.5) within group (order by p.pop) into v_rmed
    from score_pop_region p where exists (select 1 from score_pop s where s.region = p.region and est_metropole(s.departement));
  update score_pop_region set coef = round(least(v_max, greatest(v_min, sqrt(pop / v_rmed))), 3);
  select count(*) into n from score_pop;
  return n;
end;
$$;
revoke all on function public.score_pop_calculer() from public, anon, authenticated;
select public.score_pop_calculer();

create or replace function public.score_coef_dep(p_dep text)
returns numeric language sql stable security definer set search_path to 'public' as $$
  select case when coalesce(score_reglage('pop_actif'), 0) >= 1
              then coalesce((select s.coef from score_pop s where s.departement = p_dep), 1) else 1 end;
$$;
create or replace function public.score_coef_region(p_region text)
returns numeric language sql stable security definer set search_path to 'public' as $$
  select case when coalesce(score_reglage('pop_actif'), 0) >= 1
              then coalesce((select s.coef from score_pop_region s where s.region = p_region), 1) else 1 end;
$$;
-- les points d'une carte au classement du Front (Terra garde points_rarete)
create or replace function public.points_front(p_tier text)
returns integer language sql stable security definer set search_path to 'public' as $$
  select case when p_tier = 'legendaire' and coalesce(score_reglage('pop_actif'), 0) >= 1
              then coalesce(score_reglage('points_legendaire'), 60)::integer else points_rarete(p_tier)::integer end;
$$;
revoke all on function public.score_coef_dep(text), public.score_coef_region(text), public.points_front(text) from public, anon;

-- le classement
select pg_temp.retoucher('public.front_territoires()', 's3-30a',
  $a$    select d.*, round(score_reglage('palier_' || d.palier)$a$,
  $b$    select d.*, round(score_coef_dep(d.departement) /* s3-30a */ * score_reglage('palier_' || d.palier)$b$);
select pg_temp.retoucher('public.front_territoires()', 's3-30b',
  $a$    select r.joueur_id, count(*)::integer as n$a$,
  $b$    select r.joueur_id, count(*)::integer as n, sum(score_coef_region(r.region)) as c   -- s3-30b$b$);
select pg_temp.retoucher('public.front_territoires()', 's3-30c',
  $a$(sum(d.pts) + coalesce(max(ro.n), 0) * score_reglage('region'))::integer$a$,
  $b$(sum(d.pts) + round(coalesce(max(ro.c), 0) * score_reglage('region')))::integer   -- s3-30c$b$);
select pg_temp.retoucher('public.front_scores()', 's3-30d',
  $a$    select p.joueur_id, sum(points_rarete(c.tier))::integer as pts$a$,
  $b$    select p.joueur_id, sum(points_front(c.tier))::integer as pts   -- s3-30d$b$);

-- le détail « Mon score »
select pg_temp.retoucher('public.mon_score_detail()', 's3-30e',
  $a$points_rarete(c.tier)::integer pu$a$,
  $b$points_front(c.tier)::integer /* s3-30e */ pu$b$);
select pg_temp.retoucher('public.mon_score_detail()', 's3-30f',
  $a$    select d.*, round(score_reglage('palier_' || d.palier)$a$,
  $b$    select d.*, round(score_coef_dep(d.departement) /* s3-30f */ * score_reglage('palier_' || d.palier)$b$);
select pg_temp.retoucher('public.mon_score_detail()', 's3-30g',
  $a$'seul', d.seul, 'pts', d.pts)$a$,
  $b$'seul', d.seul, 'pts', d.pts, 'coef', score_coef_dep(d.departement) /* s3-30g */)$b$);
select pg_temp.retoucher('public.mon_score_detail()', 's3-30h',
  $a$'pts', case when g.gagnee then score_reglage('region')::integer else 0 end)$a$,
  $b$'pts', case when g.gagnee then round(score_coef_region(g.region) * score_reglage('region'))::integer else 0 end,
                                                       'coef', score_coef_region(g.region) /* s3-30h */)$b$);
select pg_temp.retoucher('public.mon_score_detail()', 's3-30i',
  $a$+ coalesce((select count(*) from regs g where g.gagnee), 0)::integer * score_reglage('region')::integer,$a$,
  $b$+ coalesce((select round(sum(score_coef_region(g.region) * score_reglage('region'))) from regs g where g.gagnee), 0)::integer,   -- s3-30i$b$);

-- le profil (score des communes du Front)
select pg_temp.retoucher('public.profil_joueur(uuid)', 's3-30j',
  $a$coalesce(sum(points_rarete(c.tier)), 0)::integer       as score,$a$,
  $b$coalesce(sum(points_front(c.tier)), 0)::integer /* s3-30j */ as score,$b$);

commit;

-- Contrôle : 10 retouches · interrupteur 0 · coefficients
select (select count(*) from unnest(array[
          position('s3-30a' in pg_get_functiondef('public.front_territoires()'::regprocedure)),
          position('s3-30b' in pg_get_functiondef('public.front_territoires()'::regprocedure)),
          position('s3-30c' in pg_get_functiondef('public.front_territoires()'::regprocedure)),
          position('s3-30d' in pg_get_functiondef('public.front_scores()'::regprocedure)),
          position('s3-30e' in pg_get_functiondef('public.mon_score_detail()'::regprocedure)),
          position('s3-30f' in pg_get_functiondef('public.mon_score_detail()'::regprocedure)),
          position('s3-30g' in pg_get_functiondef('public.mon_score_detail()'::regprocedure)),
          position('s3-30h' in pg_get_functiondef('public.mon_score_detail()'::regprocedure)),
          position('s3-30i' in pg_get_functiondef('public.mon_score_detail()'::regprocedure)),
          position('s3-30j' in pg_get_functiondef('public.profil_joueur(uuid)'::regprocedure))]) x where x > 0) as retouches,
       score_reglage('pop_actif') as pop_actif,
       (select string_agg(departement || ' ' || coef, ', ' order by departement) from score_pop where departement in ('48', '16', '59', '75', 'ZH', 'GE')) as exemples,
       (select string_agg(region || ' ' || coef, ', ' order by coef) from score_pop_region) as regions;

-- Le 22, après la clôture (étape 4 ter du déroulé) :
-- update public.config_jeu set valeur = ((valeur::jsonb) || '{"pop_actif": 1}'::jsonb)::text where cle = 'score_s2';
