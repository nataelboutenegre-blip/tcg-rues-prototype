-- ===========================================================================
--  TerraFront — s2-101 : « Invite un ami », un objectif dans les quêtes
--  (idée de Nataël, aperçu validé le 5/11 ; jeu : patch350).
--
--  Constat : le parrainage existe depuis le 23/10 (lien dans le profil), et
--  aucun parrainage en 13 jours pour ~110 nouveaux comptes : personne ne le
--  voit. patch350 met le lien dans les quêtes et au Tirage ; ce fichier
--  ajoute les récompenses.
--
--  1. Réglage config_jeu 'parrainage' :
--       paliers       {"1": 1, "3": 2, "5": 3} : amis actifs dans la saison → paquets Terra
--       accueil       1 : paquet Terra de plus pour l'invité, à son 3e jour
--       parrain_age_h 0 : âge minimum du compte qui invite (avant : 3 jours en dur)
--  2. parrainage_recompenses : ce qui a été récupéré (un palier par saison,
--     l'accueil une fois).
--  3. parrainage_objectif() : ce qu'affiche la carte (lien, paliers, amis en
--     route, « X t'a invité »).
--  4. parrainage_recuperer('palier_1' | 'palier_3' | 'palier_5' | 'accueil') :
--     vérifie, note, donne les paquets Terra.
--  5. declarer_parrain et mon_parrainage : l'âge minimum du parrain vient du
--     réglage (0 : on invite dès son premier jour).
--  « Ami actif » ne change pas : 3 jours différents et au moins une carte
--  (parrainage_jour). Les +10 ⚡ par ami (5 par saison) ne changent pas.
--
--  Indépendant du lot du 8/11 : s2-lot-5 remplace « least(60, » dans
--  declarer_parrain, et ce texte reste intact ici (testé dans les deux ordres).
--  Rejouable.
--  Contrôle attendu : true | true | true | true
-- ===========================================================================
begin;

create or replace function pg_temp.remp(d text, avant text, apres text, nb int, quoi text)
 returns text language plpgsql as $f$
begin
  if (length(d) - length(replace(d, avant, ''))) / length(avant) <> nb then
    raise exception '% : texte attendu % fois, trouvé % fois — rien n''a changé : %',
      quoi, nb, (length(d) - length(replace(d, avant, ''))) / length(avant), avant;
  end if;
  return replace(d, avant, apres);
end;
$f$;

-- 1. le réglage ------------------------------------------------------------------
insert into public.config_jeu(cle, valeur)
values ('parrainage', '{"paliers": {"1": 1, "3": 2, "5": 3}, "accueil": 1, "parrain_age_h": 0}')
on conflict (cle) do nothing;

create or replace function public.parrainage_reglage()
 returns jsonb language sql stable security definer set search_path = public
as $f$
  select '{"paliers": {"1": 1, "3": 2, "5": 3}, "accueil": 1, "parrain_age_h": 0}'::jsonb
         || coalesce((select c.valeur::jsonb from config_jeu c where c.cle = 'parrainage'), '{}'::jsonb);
$f$;
revoke all on function public.parrainage_reglage() from public, anon, authenticated;

-- 2. ce qui a été récupéré ------------------------------------------------------------
create table if not exists public.parrainage_recompenses (
  joueur_id uuid not null references public.joueurs(id) on delete cascade,
  quoi      text not null,                  -- 'accueil', 'palier_1', 'palier_3', 'palier_5'
  saison    text not null,                  -- la saison du palier ; 'toujours' pour l'accueil
  paquets   integer not null,
  le        timestamptz not null default now(),
  primary key (joueur_id, quoi, saison)
);
alter table public.parrainage_recompenses enable row level security;
revoke all on public.parrainage_recompenses from public, anon, authenticated;

-- 3. la carte du jeu ----------------------------------------------------------------
create or replace function public.parrainage_objectif()
 returns jsonb language plpgsql stable security definer set search_path = public
as $f$
declare
  v_uid    uuid := auth.uid();
  v_saison text := parrainage_saison();
  r        jsonb := parrainage_reglage();
  moi      joueurs%rowtype;
  pa       parrainages%rowtype;
  v_actifs integer;
  v_jours  integer := 0;
begin
  if v_uid is null then raise exception 'Non connecte'; end if;
  select * into moi from joueurs where id = v_uid;
  if not found then raise exception 'Joueur inconnu'; end if;
  select count(*) into v_actifs from parrainages p
   where p.parrain_id = v_uid and p.valide_le is not null and p.saison_valide = v_saison;
  select * into pa from parrainages p where p.filleul_id = v_uid;
  if pa.filleul_id is not null then
    select count(*) into v_jours from jours_joues d where d.joueur_id = v_uid;
  end if;

  return jsonb_build_object(
    'pseudo',       moi.pseudo,
    'peut_inviter', coalesce(moi.created_at <= now() - make_interval(hours => coalesce((r->>'parrain_age_h')::integer, 0)), false),
    'actifs',       v_actifs,
    'energie_ami',  10,
    'paliers', (
      select coalesce(jsonb_agg(jsonb_build_object(
               'n', e.k::integer, 'paquets', e.v::integer,
               'titre', case when e.k::integer = 5 then 'Le Parrain' end,
               'reclame', exists (select 1 from parrainage_recompenses x
                                   where x.joueur_id = v_uid and x.quoi = 'palier_' || e.k and x.saison = v_saison))
             order by e.k::integer), '[]'::jsonb)
        from jsonb_each_text(r->'paliers') as e(k, v)),
    -- les amis pas encore actifs, arrivés depuis moins de 30 jours
    'en_route', (
      select coalesce(jsonb_agg(jsonb_build_object(
               'pseudo', j.pseudo,
               'jours', least(3, (select count(*) from jours_joues d where d.joueur_id = f.filleul_id)))
             order by f.cree_le desc), '[]'::jsonb)
        from (select p.filleul_id, p.cree_le from parrainages p
               where p.parrain_id = v_uid and p.valide_le is null and p.cree_le > now() - interval '30 days'
               order by p.cree_le desc limit 5) f
        join joueurs j on j.id = f.filleul_id),
    -- l'invité : sa carte, jusqu'à ce qu'il ait récupéré son paquet (30 jours au plus s'il n'est pas validé)
    'invite_par', case
       when pa.filleul_id is null then null
       when exists (select 1 from parrainage_recompenses x where x.joueur_id = v_uid and x.quoi = 'accueil') then null
       when pa.valide_le is null and pa.cree_le < now() - interval '30 days' then null
       else jsonb_build_object(
         'pseudo',  (select j.pseudo from joueurs j where j.id = pa.parrain_id),
         'jours',   least(3, v_jours),
         'paquets', coalesce((r->>'accueil')::integer, 1),
         'pret',    pa.valide_le is not null,
         'reclame', false)
     end);
end;
$f$;
revoke all on function public.parrainage_objectif() from public, anon;
grant execute on function public.parrainage_objectif() to authenticated, service_role;

-- 4. récupérer ----------------------------------------------------------------------
create or replace function public.parrainage_recuperer(p_quoi text)
 returns jsonb language plpgsql security definer set search_path = public
as $f$
declare
  v_uid     uuid := auth.uid();
  v_saison  text := parrainage_saison();
  r         jsonb := parrainage_reglage();
  moi       joueurs%rowtype;
  v_n       integer;
  v_paquets integer;
  v_actifs  integer;
  v_cle     text;
  v         numeric;
begin
  if v_uid is null then raise exception 'Non connecte'; end if;
  select * into moi from joueurs where id = v_uid for update;
  if not found then raise exception 'Joueur inconnu'; end if;

  if p_quoi = 'accueil' then
    -- validé par parrainage_jour : 3 jours différents et au moins une carte
    if not exists (select 1 from parrainages p where p.filleul_id = v_uid and p.valide_le is not null) then
      raise exception 'Joue 3 jours différents (et tire au moins une carte) pour récupérer ce paquet';
    end if;
    v_paquets := greatest(0, coalesce((r->>'accueil')::integer, 1));
    v_cle := 'toujours';
  elsif p_quoi ~ '^palier_[0-9]{1,2}$' then
    v_n := substring(p_quoi from 8)::integer;
    v_paquets := (r->'paliers'->>v_n::text)::integer;
    if v_paquets is null then raise exception 'Palier inconnu'; end if;
    select count(*) into v_actifs from parrainages p
     where p.parrain_id = v_uid and p.valide_le is not null and p.saison_valide = v_saison;
    if v_actifs < v_n then
      raise exception 'Il te faut % amis actifs cette saison (tu en as %)', v_n, v_actifs;
    end if;
    v_cle := v_saison;
  else
    raise exception 'Récompense inconnue';
  end if;

  insert into parrainage_recompenses(joueur_id, quoi, saison, paquets)
  values (v_uid, p_quoi, v_cle, v_paquets)
  on conflict do nothing;
  if not found then raise exception 'Récompense déjà récupérée'; end if;

  if v_paquets > 0 then
    v := terra_jetons_lire(moi.terra_jetons, moi.terra_jetons_maj);
    update joueurs set terra_jetons = v + v_paquets, terra_jetons_maj = now() where id = v_uid;
  end if;

  return jsonb_build_object('paquets', v_paquets, 'message',
    v_paquets || ' paquet' || case when v_paquets > 1 then 's' else '' end || ' Terra : '
    || case when v_paquets > 1 then 'ils t''attendent' else 'il t''attend' end || ' au Tirage.');
end;
$f$;
revoke all on function public.parrainage_recuperer(text) from public, anon;
grant execute on function public.parrainage_recuperer(text) to authenticated, service_role;

-- 5. on invite dès son premier jour (réglage parrain_age_h) ------------------------------
do $$
declare d text;
begin
  d := pg_get_functiondef('public.declarer_parrain(text)'::regprocedure);
  if position('s2-101' in d) > 0 then raise notice 'declarer_parrain : déjà à jour';
  else
    d := pg_temp.remp(d,
      '  if p.created_at is null or p.created_at > now() - interval ''3 days'' then',
      '  -- s2-101 : âge minimum du parrain dans le réglage (0 : dès son premier jour)
  if p.created_at is null
     or p.created_at > now() - make_interval(hours => coalesce((parrainage_reglage()->>''parrain_age_h'')::integer, 0)) then',
      1, 'declarer_parrain');
    execute d;
  end if;

  d := pg_get_functiondef('public.mon_parrainage()'::regprocedure);
  if position('s2-101' in d) > 0 then raise notice 'mon_parrainage : déjà à jour';
  else
    d := pg_temp.remp(d,
      '''peut_parrainer'', (select created_at <= now() - interval ''3 days'' from joueurs where id = v_uid),',
      '''peut_parrainer'', (select created_at <= now() - make_interval(hours => coalesce((parrainage_reglage()->>''parrain_age_h'')::integer, 0))
                         from joueurs where id = v_uid),   -- s2-101',
      1, 'mon_parrainage');
    execute d;
  end if;
end $$;

commit;

-- Contrôle : true | true | true | true
select (select count(*) from public.config_jeu where cle = 'parrainage') = 1
       and (public.parrainage_reglage()->'paliers'->>'1')::integer = 1                                  as reglage,
       position('s2-101' in pg_get_functiondef('public.declarer_parrain(text)'::regprocedure)) > 0
       and position('s2-101' in pg_get_functiondef('public.mon_parrainage()'::regprocedure)) > 0        as des_le_premier_jour,
       has_function_privilege('authenticated', 'public.parrainage_objectif()', 'execute')
       and has_function_privilege('authenticated', 'public.parrainage_recuperer(text)', 'execute')
       and has_function_privilege('authenticated', 'public.declarer_parrain(text)', 'execute')          as droits,
       not has_function_privilege('anon', 'public.parrainage_recuperer(text)', 'execute')
       and not has_function_privilege('authenticated', 'public.parrainage_reglage()', 'execute')        as prive;
