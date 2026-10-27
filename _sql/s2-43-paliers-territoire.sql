-- ===========================================================================
--  s2-43 — Paliers de territoire (score Front), barème ×2
--
--  Par département (métropole), on ne garde que le palier le plus haut :
--     5 %  : +100   seul en tête ET au moins 5 communes
--    10 %  : +200   seul en tête
--    25 %  : +300   seul en tête
--    50 %  : +600
--    75 %  : +900
--   100 %  : +1400
--  Région : +1200 si plus de la moitié de ses départements sont à 10 % ou plus
--  (le palier 5 % ne compte pas pour les régions).
--
--  Le minimum de 5 communes ne touche que le palier 5 % : personne ne perd
--  un 10 % qu'il a aujourd'hui.
--  Les valeurs sont dans config_jeu 'score_s2' : on peut les rerégler sans
--  toucher à la fonction. Même signature de front_territoires (l'appli ne
--  change pas) : deps_domines = paliers 5 à 25 %, deps_controles = 50 % et plus.
--  Rejouable. Finit par un contrôle.
-- ===========================================================================

begin;

-- 1. Réglages (on fusionne, on ne remplace pas les autres clés) --------------
update public.config_jeu
   set valeur = (valeur::jsonb || '{
       "palier_5": 100, "palier_10": 200, "palier_25": 300,
       "palier_50": 600, "palier_75": 900, "palier_100": 1400,
       "palier_5_min_communes": 5,
       "dep_domine": 200, "dep_controle": 600, "region": 1200
     }'::jsonb)::text
 where cle = 'score_s2';

create or replace function public.score_reglage(p_cle text)
 returns numeric language sql stable security definer set search_path to 'public'
as $f$
  select coalesce(
    (select (c.valeur::jsonb ->> p_cle)::numeric from config_jeu c where c.cle = 'score_s2'),
    case p_cle when 'victoire' then 10 when 'dep_domine' then 200 when 'dep_controle' then 600
               when 'region' then 1200 when 'seuil_domine' then 0.10 when 'seuil_controle' then 0.50
               when 'victoires_par_jour' then 10 when 'par_adversaire_par_jour' then 2
               when 'palier_5' then 100 when 'palier_10' then 200 when 'palier_25' then 300
               when 'palier_50' then 600 when 'palier_75' then 900 when 'palier_100' then 1400
               when 'palier_5_min_communes' then 5 end);
$f$;

-- 2. Les territoires --------------------------------------------------------
create or replace function public.front_territoires()
 returns table(joueur_id uuid, deps_domines integer, deps_controles integer, regions integer, points integer)
 language sql stable security definer set search_path to 'public'
as $f$
  with tailles as (
    select c.departement, count(*)::numeric as n
      from communes c where length(c.departement) = 2 group by c.departement
  ), parts as (
    select c.departement, p.joueur_id, count(*)::numeric as n
      from possessions p join communes c on c.code = p.commune_code
     where length(c.departement) = 2
     group by c.departement, p.joueur_id
  ), tetes as (
    select pa.departement, max(pa.n) as maxi from parts pa group by pa.departement
  ), seuls as (   -- le premier du département, s'il est seul en tête
    select pa.departement, pa.joueur_id
      from parts pa join tetes t on t.departement = pa.departement and pa.n = t.maxi
     where (select count(*) from parts p2 where p2.departement = pa.departement and p2.n = t.maxi) = 1
  ), deps as (
    select pa.joueur_id, pa.departement,
           case when pa.n / ta.n >= 1    then 100
                when pa.n / ta.n >= 0.75 then 75
                when pa.n / ta.n >= 0.50 then 50
                when s.joueur_id is not null and pa.n / ta.n >= 0.25 then 25
                when s.joueur_id is not null and pa.n / ta.n >= 0.10 then 10
                when s.joueur_id is not null and pa.n / ta.n >= 0.05
                     and pa.n >= score_reglage('palier_5_min_communes') then 5
           end as palier
      from parts pa
      join tailles ta on ta.departement = pa.departement
      left join seuls s on s.departement = pa.departement and s.joueur_id = pa.joueur_id
  ), deps_ok as (
    select d.*, score_reglage('palier_' || d.palier) as pts
      from deps d where d.palier is not null
  ), reg_tailles as (
    select cdj_region(t.departement) as region, count(*) as n from tailles t group by 1
  ), regs_ok as (
    select r.joueur_id, count(*)::integer as n
      from (select d.joueur_id, cdj_region(d.departement) as region, count(*) as n
              from deps_ok d where d.palier >= 10 group by 1, 2) r
      join reg_tailles rt on rt.region = r.region
     where r.n * 2 > rt.n
     group by r.joueur_id
  )
  select d.joueur_id,
         count(*) filter (where d.palier < 50)::integer,
         count(*) filter (where d.palier >= 50)::integer,
         coalesce(max(ro.n), 0)::integer,
         (sum(d.pts) + coalesce(max(ro.n), 0) * score_reglage('region'))::integer
    from deps_ok d left join regs_ok ro on ro.joueur_id = d.joueur_id
   group by d.joueur_id;
$f$;
revoke all on function public.front_territoires() from public, anon, authenticated;

commit;

-- 3. Contrôle : 3 lignes attendues
select 'réglages' as quoi,
       (select valeur::jsonb ->> 'palier_100' from config_jeu where cle = 'score_s2') = '1400' as ok
union all
select 'métropole seule',
       pg_get_functiondef('public.front_territoires()'::regprocedure) ~ 'length\(c\.departement\) = 2'
union all
select 'joueurs avec un palier : ' || count(*), count(*) >= 0
  from front_territoires();
