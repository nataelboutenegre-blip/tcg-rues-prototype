-- ===========================================================================
--  s2-21-score.sql — le score du classement de la saison 2 (12 octobre 2026)
--
--  Score Front = cartes + combats + territoires
--   - cartes      : points de rareté des communes possédées (inchangé) ;
--   - combats     : X points par victoire de la saison (conquête, défense,
--                   garnison qui repousse une attaque). Une victoire compte
--                   une seule fois par commune et par type, 10 par jour au
--                   plus, et 2 par jour au plus contre le même adversaire
--                   (anti-complices). Acquises même si la commune est reperdue ;
--   - territoires : au moment présent. Département DOMINÉ (le plus de
--                   communes, seul, et au moins 10 % du département) ou
--                   CONTRÔLÉ (au moins 50 %) — les deux ne s'additionnent
--                   pas. Région dominée : plus de la moitié de ses
--                   départements dominés ou contrôlés.
--  Valeurs dans config_jeu, clé 'score_s2' : réglables sans toucher au code.
--
--  SANS EFFET SUR LA SAISON 1 : combats et territoires valent 0 tant que la
--  saison en cours est 'saison-1'. Le palmarès de la saison 1, calculé le
--  jour J, reste donc exactement celui d'aujourd'hui.
--  Effet immédiat : les comptes listés dans config_jeu 'exclus_classement'
--  (Nataël) disparaissent du classement en direct. Les victoires sont
--  enregistrées dès maintenant (pour vérifier que le compteur marche), mais
--  celles de la saison 1 ne comptent pas en saison 2.
--
--  Le compteur ne peut JAMAIS bloquer un combat : en cas d'erreur, il
--  n'enregistre rien et laisse le combat se faire.
--  Ne touche pas cloturer_saison. Rejouable. Finit par un contrôle.
-- ===========================================================================

begin;

-- 1. Réglages ---------------------------------------------------------------
insert into public.config_jeu (cle, valeur) values
  ('score_s2', '{"victoire": 10, "dep_domine": 100, "dep_controle": 300, "region": 600, "seuil_domine": 0.10, "seuil_controle": 0.50, "victoires_par_jour": 10, "par_adversaire_par_jour": 2}'),
  ('exclus_classement', '["Nataël"]')
on conflict (cle) do nothing;

create or replace function public.score_reglage(p_cle text)
 returns numeric language sql stable security definer set search_path to 'public'
as $f$
  select coalesce(
    (select (c.valeur::jsonb ->> p_cle)::numeric from config_jeu c where c.cle = 'score_s2'),
    case p_cle when 'victoire' then 10 when 'dep_domine' then 100 when 'dep_controle' then 300
               when 'region' then 600 when 'seuil_domine' then 0.10 when 'seuil_controle' then 0.50
               when 'victoires_par_jour' then 10 when 'par_adversaire_par_jour' then 2 end);
$f$;

-- comparaison insensible à la casse et à la forme Unicode du « ë »
create or replace function public.est_exclu_classement(p_pseudo text)
 returns boolean language sql stable security definer set search_path to 'public'
as $f$
  -- config_jeu.valeur est du texte : on le lit comme du JSON
  with l as (select (select c.valeur from config_jeu c where c.cle = 'exclus_classement')::jsonb as v)
  select exists (select 1 from l, jsonb_array_elements_text(case when jsonb_typeof(l.v) = 'array'
                                                               then l.v else '[]'::jsonb end) x
                  where lower(normalize(x, NFC)) = lower(normalize(coalesce(p_pseudo, ''), NFC)));
$f$;

-- les bonus (combats, territoires) ne valent qu'à partir de la saison 2
create or replace function public.score_bonus_actif()
 returns boolean language sql stable security definer set search_path to 'public'
as $f$
  select coalesce((select s.id <> 'saison-1' from saisons s where s.etat <> 'terminee'
                    order by s.debut desc limit 1), false);
$f$;

-- 2. Les victoires ----------------------------------------------------------
create table if not exists public.front_victoires(
  id            bigserial primary key,
  saison        text not null,
  joueur_id     uuid not null,
  adversaire    uuid,
  commune_code  text not null,
  type          text not null check (type in ('conquete', 'defense')),
  le            timestamptz not null default now(),
  compte        boolean not null,
  raison        text          -- pourquoi elle ne compte pas
);
create index if not exists front_victoires_jour on public.front_victoires(saison, joueur_id, le);
create unique index if not exists front_victoires_une_fois
  on public.front_victoires(saison, joueur_id, commune_code, type) where compte;
alter table public.front_victoires enable row level security;
revoke all on public.front_victoires from public, anon, authenticated;
revoke all on sequence public.front_victoires_id_seq from public, anon, authenticated;

create or replace function public.front_noter_victoire(p_joueur uuid, p_adversaire uuid, p_code text, p_type text)
 returns void language plpgsql security definer set search_path to 'public'
as $f$
declare
  v_saison text;
  v_jour   timestamptz;
  v_compte boolean := true;
  v_raison text;
begin
  if p_joueur is null or p_code is null or p_joueur = p_adversaire then return; end if;
  select s.id into v_saison from saisons s where s.etat <> 'terminee' order by s.debut desc limit 1;
  if v_saison is null then return; end if;

  -- un joueur à la fois : deux victoires simultanées ne passent pas toutes
  -- les deux sous le plafond
  perform pg_advisory_xact_lock(hashtext('front_victoires:' || p_joueur::text));
  v_jour := date_trunc('day', now() at time zone 'Europe/Paris') at time zone 'Europe/Paris';

  if exists (select 1 from front_victoires v where v.saison = v_saison and v.joueur_id = p_joueur
               and v.commune_code = p_code and v.type = p_type and v.compte) then
    v_compte := false; v_raison := 'deja_comptee';
  elsif p_adversaire is not null and (select count(*) from front_victoires v
          where v.saison = v_saison and v.joueur_id = p_joueur and v.adversaire = p_adversaire
            and v.compte and v.le >= v_jour) >= score_reglage('par_adversaire_par_jour') then
    v_compte := false; v_raison := 'plafond_adversaire';
  elsif (select count(*) from front_victoires v
          where v.saison = v_saison and v.joueur_id = p_joueur and v.compte and v.le >= v_jour)
        >= score_reglage('victoires_par_jour') then
    v_compte := false; v_raison := 'plafond_jour';
  end if;

  insert into front_victoires(saison, joueur_id, adversaire, commune_code, type, compte, raison)
  values (v_saison, p_joueur, p_adversaire, p_code, p_type, v_compte, v_raison);
exception when others then
  -- jamais bloquer un combat pour un compteur
  raise warning 'front_noter_victoire : %', sqlerrm;
end;
$f$;
revoke all on function public.front_noter_victoire(uuid, uuid, text, text) from public, anon, authenticated;

-- conquêtes et défenses passent toutes par le journal (noter_journal)
create or replace function public.front_victoire_journal()
 returns trigger language plpgsql security definer set search_path to 'public'
as $f$
begin
  perform front_noter_victoire(new.acteur, new.cible, new.commune_code, new.type);
  return null;
end;
$f$;
drop trigger if exists front_victoire_journal on public.journal;
create trigger front_victoire_journal after insert on public.journal
  for each row when (new.type in ('conquete', 'defense'))
  execute function public.front_victoire_journal();

-- une garnison qui repousse l'attaque : une défense pour son propriétaire
create or replace function public.front_victoire_garnison()
 returns trigger language plpgsql security definer set search_path to 'public'
as $f$
begin
  perform front_noter_victoire(new.defenseur, new.attaquant, new.commune_code, 'defense');
  return null;
end;
$f$;
drop trigger if exists front_victoire_garnison on public.front_garnison_journal;
create trigger front_victoire_garnison after insert on public.front_garnison_journal
  for each row when (new.reussie)
  execute function public.front_victoire_garnison();

-- 3. Les territoires (au moment présent) ------------------------------------
create or replace function public.front_territoires()
 returns table(joueur_id uuid, deps_domines integer, deps_controles integer, regions integer, points integer)
 language sql stable security definer set search_path to 'public'
as $f$
  with tailles as (
    select c.departement, count(*)::numeric as n from communes c group by c.departement
  ), parts as (
    select c.departement, p.joueur_id, count(*)::numeric as n
      from possessions p join communes c on c.code = p.commune_code
     group by c.departement, p.joueur_id
  ), tetes as (
    select pa.departement, max(pa.n) as maxi from parts pa group by pa.departement
  ), seuls as (   -- le premier du département, s'il est seul en tête
    select pa.departement, pa.joueur_id
      from parts pa join tetes t on t.departement = pa.departement and pa.n = t.maxi
     where (select count(*) from parts p2 where p2.departement = pa.departement and p2.n = t.maxi) = 1
  ), deps as (
    select pa.joueur_id, pa.departement,
           case when pa.n / ta.n >= score_reglage('seuil_controle') then 'controle'
                when s.joueur_id is not null and pa.n / ta.n >= score_reglage('seuil_domine') then 'domine'
           end as statut
      from parts pa
      join tailles ta on ta.departement = pa.departement
      left join seuls s on s.departement = pa.departement and s.joueur_id = pa.joueur_id
  ), deps_ok as (
    select * from deps where statut is not null
  ), reg_tailles as (
    select cdj_region(t.departement) as region, count(*) as n from tailles t group by 1
  ), regs_ok as (
    select r.joueur_id, count(*)::integer as n
      from (select d.joueur_id, cdj_region(d.departement) as region, count(*) as n
              from deps_ok d group by 1, 2) r
      join reg_tailles rt on rt.region = r.region
     where r.n * 2 > rt.n
     group by r.joueur_id
  )
  select d.joueur_id,
         count(*) filter (where d.statut = 'domine')::integer,
         count(*) filter (where d.statut = 'controle')::integer,
         coalesce(max(ro.n), 0)::integer,
         (count(*) filter (where d.statut = 'domine') * score_reglage('dep_domine')
          + count(*) filter (where d.statut = 'controle') * score_reglage('dep_controle')
          + coalesce(max(ro.n), 0) * score_reglage('region'))::integer
    from deps_ok d left join regs_ok ro on ro.joueur_id = d.joueur_id
   group by d.joueur_id;
$f$;
revoke all on function public.front_territoires() from public, anon, authenticated;

-- 4. Le score complet --------------------------------------------------------
create or replace function public.front_scores()
 returns table(joueur_id uuid, cartes integer, combats integer, territoires integer, victoires integer,
               deps_domines integer, deps_controles integer, regions integer)
 language sql stable security definer set search_path to 'public'
as $f$
  with s as (
    select sa.id from saisons sa where sa.etat <> 'terminee' order by sa.debut desc limit 1
  ), cartes as (
    select p.joueur_id, sum(points_rarete(c.tier))::integer as pts
      from possessions p join communes c on c.code = p.commune_code group by p.joueur_id
  ), vict as (
    select v.joueur_id, count(*)::integer as n
      from front_victoires v where v.compte and v.saison = (select id from s)
       and score_bonus_actif()
     group by v.joueur_id
  ), terr as (
    select * from front_territoires() where score_bonus_actif()
  ), ids as (
    select joueur_id from cartes union select joueur_id from vict union select joueur_id from terr
  )
  select i.joueur_id,
         coalesce(ca.pts, 0),
         (coalesce(v.n, 0) * score_reglage('victoire'))::integer,
         coalesce(t.points, 0),
         coalesce(v.n, 0),
         coalesce(t.deps_domines, 0), coalesce(t.deps_controles, 0), coalesce(t.regions, 0)
    from ids i
    left join cartes ca on ca.joueur_id = i.joueur_id
    left join vict v    on v.joueur_id = i.joueur_id
    left join terr t    on t.joueur_id = i.joueur_id;
$f$;
revoke all on function public.front_scores() from public, anon, authenticated;

-- le détail pour l'affichage (« cartes + combats + territoires »)
create or replace function public.score_detail(p_joueurs uuid[])
 returns table(joueur_id uuid, cartes integer, combats integer, territoires integer, victoires integer,
               deps_domines integer, deps_controles integer, regions integer)
 language sql stable security definer set search_path to 'public'
as $f$
  select f.* from front_scores() f
   where auth.uid() is not null and f.joueur_id = any(p_joueurs[1:60]);
$f$;
revoke all on function public.score_detail(uuid[]) from public, anon;
grant execute on function public.score_detail(uuid[]) to authenticated;

-- 5. Le classement en direct (même signature : l'appli ne change pas) --------
CREATE OR REPLACE FUNCTION public.classement(p_mode text DEFAULT 'general'::text, p_limite integer DEFAULT 20)
 RETURNS TABLE(rang integer, joueur_id uuid, pseudo text, score integer, communes integer, habitants bigint, legendaires integer, rares integer, est_moi boolean)
 LANGUAGE sql
 STABLE SECURITY DEFINER
 SET search_path TO 'public'
AS $function$
  with base as (
    select p.joueur_id, c.tier, c.population
    from possessions p join communes c on c.code = p.commune_code
    where p_mode <> 'mois'
    union all
    -- ce mois-ci : communes acquises depuis le 1er du mois et encore possedees
    select h.joueur_id, c.tier, c.population
    from historique h
    join communes c on c.code = h.commune_code
    join possessions p on p.commune_code = h.commune_code and p.joueur_id = h.joueur_id
    where p_mode = 'mois'
      and h.released_at is null
      and h.acquired_at >= date_trunc('month', now())
  ),
  totaux as (
    select b.joueur_id,
           sum(points_rarete(b.tier))::integer as cartes,
           count(*)::integer as communes,
           sum(coalesce(b.population, 0))::bigint as habitants,
           count(*) filter (where b.tier = 'legendaire')::integer as legendaires,
           count(*) filter (where b.tier = 'rare')::integer as rares
    from base b group by b.joueur_id
  ),
  -- saison 2 : combats + territoires (0 en saison 1 ; pas dans « ce mois-ci »)
  bonus as (
    select f.joueur_id, f.combats + f.territoires as pts
      from front_scores() f where p_mode <> 'mois' and score_bonus_actif()
  ),
  tous as (
    select coalesce(t.joueur_id, bo.joueur_id) as joueur_id,
           coalesce(t.cartes, 0) + coalesce(bo.pts, 0) as score,
           coalesce(t.communes, 0) as communes, coalesce(t.habitants, 0)::bigint as habitants,
           coalesce(t.legendaires, 0) as legendaires, coalesce(t.rares, 0) as rares
      from totaux t full join bonus bo on bo.joueur_id = t.joueur_id
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
$function$;

-- 6. Le palmarès de fin de saison (appelé par cloturer_saison) ---------------
--    Même signature. Saison 1 : identique à aujourd'hui (bonus à 0).
CREATE OR REPLACE FUNCTION public.palmares_saison(p_exclus text[] DEFAULT ARRAY[]::text[])
 RETURNS TABLE(joueur_id uuid, pseudo text, rang integer, communes integer, legendaires integer, rares integer, departements integer, score integer)
 LANGUAGE sql
 STABLE SECURITY DEFINER
 SET search_path TO 'public'
AS $function$
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
        full join (select f.joueur_id, f.combats + f.territoires as pts
                     from front_scores() f where score_bonus_actif()) bo
          on bo.joueur_id = pc.joueur_id
        join joueurs j on j.id = coalesce(pc.joueur_id, bo.joueur_id)
       -- Comparaison insensible a la casse et a la forme Unicode du « ë ».
       where not exists (select 1 from unnest(coalesce(p_exclus, ARRAY[]::text[])) x
                          where lower(normalize(x, NFC)) = lower(normalize(j.pseudo, NFC)))
    ) t
   where t.communes > 0 or t.score > 0;
$function$;

revoke all on function public.score_reglage(text), public.est_exclu_classement(text),
                       public.score_bonus_actif() from public, anon, authenticated;

commit;

-- Contrôle : true | true | true | false | (nombre) | Nataël absent : true
select to_regclass('public.front_victoires') is not null                                    as table_ok,
       (select count(*) = 2 from pg_trigger where tgname in ('front_victoire_journal', 'front_victoire_garnison')) as declencheurs_ok,
       has_function_privilege('authenticated', 'public.score_detail(uuid[])', 'execute')     as detail_ok,
       public.score_bonus_actif()                                                           as bonus_actif_doit_etre_false,
       (select count(*) from public.classement('general', 1000))                            as joueurs_classes,
       not exists (select 1 from public.classement('general', 100000) c
                    where public.est_exclu_classement(c.pseudo))                            as natael_absent;
