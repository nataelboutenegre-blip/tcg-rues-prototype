-- ===========================================================================
--  TerraFront — s2-105 : bâtiments, bombes et rébellions au classement du Front
--  (décidé par Nataël le 5/11 au soir et le 6/11 au matin : option B)
--
--  Une 4e part du score, « bâtiments » (orange dans le jeu) :
--    - chaque bâtiment TERMINÉ : Fonderie +50, Forteresse +80, Centre de
--      recherche +150, Banque +80 ; acquis même s'il est détruit ensuite,
--      mais jamais plus que le maximum de chaque type (2 Fonderies,
--      5 Forteresses, 1 Centre, 1 Banque : 730 au plus). Sans ce plafond,
--      reconstruire (ou se faire détruire un bâtiment par un échange de clan)
--      fabriquerait des points à volonté ;
--    - bombe lancée : +300 ;
--    - rébellion financée ou étouffée : +2 par lingot, 60 par jour au plus
--      (heure de Paris), financer et étouffer ensemble.
--  Comme les combats et les territoires, compté seulement quand
--  score_bonus_actif() (saison 2 et suivantes).
--
--  1. batiments_historique : chaque construction, gardée même après la
--     destruction du bâtiment (privée ; une construction annulée, ou détruite
--     avant d'être finie, ne compte pas). Rempli avec les bâtiments debout et
--     le journal (constructions de Fonderies et de Forteresses notées depuis
--     le 2/11) : ceux construits avant le 2/11 puis détruits sont inconnus.
--  2. score_batiments() : les points de chacun.
--  3. Le classement : colonne « batiments » dans classement_cache,
--     classement_calcul, classement_lignes et score_detail (recréées : leur
--     forme change) ; classement() et palmares_saison() l'ajoutent au score.
--  Réglages dans config_jeu 'score_s2' (bat_fonderie, bat_forteresse,
--  bat_centre, bat_banque, bombe, rebellion_lingot, rebellion_jour).
--  Prérequis : le lot du 6/11 (tables de la rébellion, s2-lot-7) et s2-104.
--  Rejouable. Contrôle attendu : t | t | t | 0 ou plus | t
-- ===========================================================================
do $$ begin
  if to_regclass('public.rebellions') is null or to_regclass('public.rebellions_etouffements') is null then
    raise exception 'Lance d''abord le lot du 6/11 (s2-lot-7-rebellion.sql)';
  end if;
  if to_regprocedure('public.lingots_max_fonderies(uuid)') is null then
    raise exception 'Lance d''abord s2-104-banque.sql';
  end if;
end $$;

begin;

-- 0. réglages ---------------------------------------------------------------
update public.config_jeu
   set valeur = (valeur::jsonb || '{"bat_fonderie": 50, "bat_forteresse": 80, "bat_centre": 150, "bat_banque": 80,
                                    "bombe": 300, "rebellion_lingot": 2, "rebellion_jour": 60}'::jsonb)::text
 where cle = 'score_s2' and not (valeur::jsonb ? 'bat_fonderie');

-- 1. l'historique des constructions ---------------------------------------------
create table if not exists public.batiments_historique(
  id           bigserial primary key,
  batiment_id  bigint unique,               -- null pour les lignes retrouvées dans le journal
  joueur_id    uuid not null,
  type         text not null,
  commune_code text,
  cree_le      timestamptz not null,
  pret_le      timestamptz not null,
  saison       text not null,
  origine      text not null default 'jeu'  -- jeu | debout_le_6_11 | journal
);
create index if not exists batiments_historique_joueur on public.batiments_historique(joueur_id, saison);
alter table public.batiments_historique enable row level security;
revoke all on public.batiments_historique from public, anon, authenticated;

create or replace function public.batiments_historique_noter()
 returns trigger language plpgsql security definer set search_path to 'public' as $f$
-- s2-105 : une construction lancée est notée ; annulée ou détruite avant d'être finie, elle est retirée
begin
  if tg_op = 'INSERT' then
    insert into batiments_historique(batiment_id, joueur_id, type, commune_code, cree_le, pret_le, saison)
    values (new.id, new.joueur_id, new.type, new.commune_code, new.cree_le, new.pret_le, saison_en_cours_id())
    on conflict (batiment_id) do nothing;
  elsif old.pret_le > now() then
    delete from batiments_historique where batiment_id = old.id;
  end if;
  return null;
exception when others then
  raise warning 'batiments_historique_noter : %', sqlerrm;
  return null;
end;
$f$;
drop trigger if exists trg_batiments_historique on public.batiments;
create trigger trg_batiments_historique after insert or delete on public.batiments
  for each row execute function public.batiments_historique_noter();

-- remplissage : les bâtiments debout…
insert into public.batiments_historique(batiment_id, joueur_id, type, commune_code, cree_le, pret_le, saison, origine)
select b.id, b.joueur_id, b.type, b.commune_code, b.cree_le, b.pret_le, saison_en_cours_id(), 'debout_le_6_11'
  from public.batiments b
on conflict (batiment_id) do nothing;
-- … et les constructions du journal (depuis le 2/11) dont le bâtiment n'est plus là
insert into public.batiments_historique(batiment_id, joueur_id, type, commune_code, cree_le, pret_le, saison, origine)
select null, j.acteur, j.type, j.commune_code, j.cree_le, j.cree_le + interval '6 hours', saison_en_cours_id(), 'journal'
  from public.journal j
 where j.type in ('fonderie', 'forteresse') and j.acteur is not null
   and j.cree_le >= (select debut from public.saisons where id = saison_en_cours_id())
   and not exists (select 1 from public.batiments b
                    where b.joueur_id = j.acteur and b.type = j.type and b.commune_code = j.commune_code
                      and abs(extract(epoch from b.cree_le - j.cree_le)) < 120)
   and not exists (select 1 from public.batiments_historique h
                    where h.origine = 'journal' and h.joueur_id = j.acteur and h.type = j.type
                      and h.commune_code = j.commune_code and h.cree_le = j.cree_le);

-- 2. les points --------------------------------------------------------------
create or replace function public.score_batiments()
 returns table(joueur_id uuid, points integer)
 language sql stable security definer set search_path to 'public' as $f$
  with s as (select sa.id, sa.debut from saisons sa where sa.etat <> 'terminee' order by sa.debut desc limit 1),
  bat as (
    select h.joueur_id,
           least(count(*) filter (where h.type = 'fonderie'),   batiment_reglage('fonderies_max'))  * coalesce(score_reglage('bat_fonderie'), 50)
         + least(count(*) filter (where h.type = 'forteresse'), batiment_reglage('forteresse_max')) * coalesce(score_reglage('bat_forteresse'), 80)
         + least(count(*) filter (where h.type = 'centre'), 1) * coalesce(score_reglage('bat_centre'), 150)
         + least(count(*) filter (where h.type = 'banque'), 1) * coalesce(score_reglage('bat_banque'), 80) as pts
      from batiments_historique h
     where h.saison = (select id from s) and h.pret_le <= now()
     group by h.joueur_id
  ),
  bo as (
    select b.lanceur as joueur_id, count(*) * coalesce(score_reglage('bombe'), 300) as pts
      from bombes b where b.le >= (select debut from s) group by b.lanceur
  ),
  lingots_jour as (
    select r.financeur as joueur_id, (r.debut at time zone 'Europe/Paris')::date as jour, r.mise as lingots
      from rebellions r where r.debut >= (select debut from s)
    union all
    select e.defenseur, (e.le at time zone 'Europe/Paris')::date, e.lingots
      from rebellions_etouffements e where e.le >= (select debut from s)
  ),
  re as (
    select x.joueur_id, sum(x.p) as pts
      from (select l.joueur_id, least(sum(l.lingots) * coalesce(score_reglage('rebellion_lingot'), 2),
                                      coalesce(score_reglage('rebellion_jour'), 60)) as p
              from lingots_jour l group by l.joueur_id, l.jour) x
     group by x.joueur_id
  ),
  ids as (select joueur_id from bat union select joueur_id from bo union select joueur_id from re)
  select i.joueur_id, (coalesce(bat.pts, 0) + coalesce(bo.pts, 0) + coalesce(re.pts, 0))::integer
    from ids i
    left join bat on bat.joueur_id = i.joueur_id
    left join bo  on bo.joueur_id  = i.joueur_id
    left join re  on re.joueur_id  = i.joueur_id
   where score_bonus_actif();
$f$;
revoke all on function public.score_batiments() from public, anon, authenticated;

-- 3. le classement -------------------------------------------------------------
alter table public.classement_cache add column if not exists batiments integer not null default 0;

drop function if exists public.score_detail(uuid[]);
drop function if exists public.classement_lignes();
drop function if exists public.classement_calcul();

create function public.classement_calcul()
 returns table(joueur_id uuid, cartes integer, combats integer, territoires integer, victoires integer,
               deps_domines integer, deps_controles integer, regions integer, communes integer, habitants bigint,
               legendaires integer, rares integer, batiments integer)
 language sql stable security definer set search_path to 'public' as $f$
  with tot as (
    select p.joueur_id,
           count(*)::integer                                      as communes,
           sum(coalesce(c.population, 0))::bigint                 as habitants,
           count(*) filter (where c.tier = 'legendaire')::integer as legendaires,
           count(*) filter (where c.tier = 'rare')::integer       as rares
      from possessions p join communes c on c.code = p.commune_code
     group by p.joueur_id
  ),
  f as (select * from front_scores()),
  b as (select * from score_batiments()),   -- s2-105
  ids as (select f.joueur_id from f union select b.joueur_id from b)
  select i.joueur_id, coalesce(f.cartes, 0), coalesce(f.combats, 0), coalesce(f.territoires, 0), coalesce(f.victoires, 0),
         coalesce(f.deps_domines, 0), coalesce(f.deps_controles, 0), coalesce(f.regions, 0),
         coalesce(t.communes, 0), coalesce(t.habitants, 0)::bigint,
         coalesce(t.legendaires, 0), coalesce(t.rares, 0), coalesce(b.points, 0)
    from ids i
    left join f   on f.joueur_id = i.joueur_id
    left join b   on b.joueur_id = i.joueur_id
    left join tot t on t.joueur_id = i.joueur_id;
$f$;

create function public.classement_lignes()
 returns table(joueur_id uuid, cartes integer, combats integer, territoires integer, victoires integer,
               deps_domines integer, deps_controles integer, regions integer, communes integer, habitants bigint,
               legendaires integer, rares integer, batiments integer)
 language plpgsql stable security definer set search_path to 'public' as $f$
begin
  -- depuis le jeu : la copie de la minute ; depuis l'éditeur SQL, ou si la
  -- copie a vieilli (tâche arrêtée) : le calcul direct
  if coalesce(current_setting('request.jwt.claims', true), '') <> '' and classement_cache_frais() then
    return query
      select k.joueur_id, k.cartes, k.combats, k.territoires, k.victoires, k.deps_domines,
             k.deps_controles, k.regions, k.communes, k.habitants, k.legendaires, k.rares, k.batiments
        from classement_cache k;
  else
    return query select * from classement_calcul();
  end if;
end;
$f$;

create function public.score_detail(p_joueurs uuid[])
 returns table(joueur_id uuid, cartes integer, combats integer, territoires integer, victoires integer,
               deps_domines integer, deps_controles integer, regions integer, batiments integer)
 language sql stable security definer set search_path to 'public' as $f$
  select l.joueur_id, l.cartes, l.combats, l.territoires, l.victoires,
         l.deps_domines, l.deps_controles, l.regions, l.batiments
    from classement_lignes() l   -- s2-100, s2-105
   where auth.uid() is not null and l.joueur_id = any(p_joueurs[1:60]);
$f$;

revoke all on function public.classement_calcul(), public.classement_lignes(), public.score_detail(uuid[]) from public, anon, authenticated;
grant execute on function public.classement_calcul(), public.classement_lignes() to service_role;
grant execute on function public.score_detail(uuid[]) to authenticated, service_role;

create or replace function public.classement_cache_maj()
 returns integer language plpgsql security definer set search_path to 'public' as $f$
declare
  n integer;
begin
  -- un seul calcul à la fois (tâche de la minute + appel à la main)
  if not pg_try_advisory_xact_lock(hashtext('classement_cache_maj')) then return -1; end if;
  delete from classement_cache;
  insert into classement_cache (joueur_id, cartes, combats, territoires, victoires, deps_domines,
                                deps_controles, regions, communes, habitants, legendaires, rares, batiments, maj_le)
  select l.joueur_id, l.cartes, l.combats, l.territoires, l.victoires, l.deps_domines,
         l.deps_controles, l.regions, l.communes, l.habitants, l.legendaires, l.rares, l.batiments, now()
    from classement_calcul() l;
  get diagnostics n = row_count;
  return n;
end;
$f$;

create or replace function public.classement(p_mode text default 'general'::text, p_limite integer default 20)
 returns table(rang integer, joueur_id uuid, pseudo text, score integer, communes integer, habitants bigint,
               legendaires integer, rares integer, est_moi boolean)
 language sql stable security definer set search_path to 'public' as $f$
  with mois as (
    -- ce mois-ci : communes acquises depuis le 1er du mois et encore possedees
    select h.joueur_id,
           sum(points_rarete(c.tier))::integer                    as score,
           count(*)::integer                                      as communes,
           sum(coalesce(c.population, 0))::bigint                 as habitants,
           count(*) filter (where c.tier = 'legendaire')::integer as legendaires,
           count(*) filter (where c.tier = 'rare')::integer       as rares
      from historique h
      join communes c on c.code = h.commune_code
      join possessions p on p.commune_code = h.commune_code and p.joueur_id = h.joueur_id
     where p_mode = 'mois'
       and h.released_at is null
       and h.acquired_at >= date_trunc('month', now())
     group by h.joueur_id
  ),
  tous as (
    -- la saison : cartes + combats + territoires + bâtiments (s2-100 : lus dans la copie de la minute ; s2-105)
    select l.joueur_id,
           l.cartes + case when score_bonus_actif() then l.combats + l.territoires + l.batiments else 0 end as score,
           l.communes, l.habitants, l.legendaires, l.rares
      from classement_lignes() l
     where p_mode <> 'mois'
    union all
    select m.joueur_id, m.score, m.communes, m.habitants, m.legendaires, m.rares
      from mois m
  ),
  classe as (
    select row_number() over (order by x.score desc, x.communes desc, x.habitants desc)::integer as rang,
           x.*, coalesce(j.pseudo, 'Joueur')::text as pseudo
    from tous x join joueurs j on j.id = x.joueur_id
    where x.score > 0 and not est_exclu_classement(j.pseudo)
  )
  -- les meilleurs, plus ma propre ligne meme si je suis loin derriere
  select c.rang, c.joueur_id, c.pseudo, c.score::integer, c.communes, c.habitants,
         c.legendaires, c.rares, (c.joueur_id = auth.uid()) as est_moi
  from classe c
  where c.rang <= greatest(p_limite, 3) or c.joueur_id = auth.uid()
  order by c.rang;
$f$;

create or replace function public.palmares_saison(p_exclus text[] default array[]::text[])
 returns table(joueur_id uuid, pseudo text, rang integer, communes integer, legendaires integer, rares integer,
               departements integer, score integer)
 language sql stable security definer set search_path to 'public' as $f$
  select t.joueur_id, t.pseudo,
         row_number() over (order by t.score desc, t.communes desc,
                                     t.habitants desc, t.pseudo)::integer,
         t.communes, t.legendaires, t.rares, t.departements, t.score
    from (
      select j.id as joueur_id,
             coalesce(j.pseudo, 'Joueur')::text as pseudo,
             (coalesce(pc.score, 0) + coalesce(bo.pts, 0))::integer as score,
             coalesce(pc.communes, 0) as communes,
             coalesce(pc.habitants, 0) as habitants,
             coalesce(pc.legendaires, 0) as legendaires,
             coalesce(pc.rares, 0) as rares,
             coalesce(pc.departements, 0) as departements
        from (
          select p.joueur_id,
                 sum(points_rarete(c.tier))::integer as score,
                 count(*)::integer as communes,
                 sum(coalesce(c.population, 0))::bigint as habitants,
                 count(*) filter (where c.tier = 'legendaire')::integer as legendaires,
                 count(*) filter (where c.tier = 'rare')::integer as rares,
                 count(distinct c.departement)::integer as departements
            from possessions p join communes c on c.code = p.commune_code
           group by p.joueur_id
        ) pc
        full join (select x.joueur_id, sum(x.pts) as pts from (
                     select f.joueur_id, f.combats + f.territoires as pts from front_scores() f where score_bonus_actif()
                     union all
                     select s.joueur_id, s.points from score_batiments() s) x   -- s2-105
                    group by x.joueur_id) bo
          on bo.joueur_id = pc.joueur_id
        join joueurs j on j.id = coalesce(pc.joueur_id, bo.joueur_id)
       -- Comparaison insensible a la casse et a la forme Unicode du « ë ».
       where not exists (select 1 from unnest(coalesce(p_exclus, ARRAY[]::text[])) x
                          where lower(normalize(x, NFC)) = lower(normalize(j.pseudo, NFC)))
    ) t
   where t.communes > 0 or t.score > 0;
$f$;

-- la copie de la minute, tout de suite avec la nouvelle colonne
select public.classement_cache_maj();

commit;

-- Contrôle : t | t | t | 0 ou plus | t
select to_regclass('public.batiments_historique') is not null                                         as historique,
       exists (select 1 from pg_trigger where tgname = 'trg_batiments_historique')                       as declencheur,
       has_function_privilege('authenticated', 'public.score_detail(uuid[])', 'execute')
       and not has_function_privilege('authenticated', 'public.score_batiments()', 'execute')            as droits,
       (select count(*) from public.score_batiments())                                                  as joueurs_avec_points,
       (select count(*) from public.classement_cache where batiments > 0) =
       (select count(*) from public.score_batiments() s where s.points > 0
          and exists (select 1 from public.classement_cache k where k.joueur_id = s.joueur_id))         as copie_ok;
