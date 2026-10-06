-- =====================================================================
--  TerraFront — Radar : duel en différé, classé à l'Elo
--
--  Cinq communes à placer sur la carte, 15 secondes chacune. Score = total
--  des distances (1 000 km si le temps est écoulé). Le plus petit total
--  gagne.
--
--  LE DUEL EN DIFFÉRÉ
--  - « Lancer » cherche une partie déjà terminée par un autre joueur, d'Elo
--    proche, que personne n'a encore affrontée : on rejoue ses cinq
--    communes, et le duel se règle à la dernière manche (Elo des deux).
--  - S'il n'y en a pas, on joue cinq communes neuves : la partie attend le
--    prochain adversaire, et le résultat arrive quand il a joué.
--  - Une partie ne sert qu'à un seul duel.
--
--  CONTRE LA TRICHE
--  - Le nom d'une commune n'est donné qu'à l'ouverture de sa manche ; le
--    chrono est celui du serveur (15 s + 2 s de marge pour le réseau).
--  - Quitter en pleine manche ne l'arrête pas : à la reprise, une manche
--    dépassée compte 1 000 km.
--  - 5 duels lancés par jour (heure de Paris).
--
--  Aucun gain : ni points, ni paquets, ni cartes. Seulement l'Elo.
--  Rejouable.
-- =====================================================================

create table if not exists public.radar_joueurs(
  joueur_id  uuid primary key,
  elo        integer not null default 1000,
  parties    integer not null default 0,
  victoires  integer not null default 0,
  maj        timestamptz not null default now()
);

create table if not exists public.radar_parties(
  id             bigserial primary key,
  joueur_id      uuid not null,
  communes       text[] not null,          -- les 5 codes, dans l'ordre
  source_id      bigint references public.radar_parties(id),  -- la partie affrontée (null : partie neuve)
  manche         smallint not null default 0,                  -- manche en cours, 0 à 4 ; 5 = terminée
  manche_debut   timestamptz,                                  -- ouverture de la manche en cours
  coups          jsonb not null default '[]'::jsonb,           -- [{lon,lat,km}] ; lon/lat null si temps écoulé
  total_km       integer,
  fini           boolean not null default false,
  utilisee       boolean not null default false,               -- déjà affrontée (partie neuve seulement)
  elo_avant      integer,
  elo_apres      integer,
  resultat       text,                                          -- victoire / defaite / egalite (pour ce joueur)
  vu             boolean not null default true,                -- résultat déjà vu par ce joueur
  jour           date not null default (now() at time zone 'Europe/Paris')::date,
  cree_le        timestamptz not null default now(),
  fin_le         timestamptz
);
create index if not exists radar_parties_joueur on public.radar_parties(joueur_id, jour);
create index if not exists radar_parties_dispo  on public.radar_parties(fini, utilisee) where source_id is null;

alter table public.radar_joueurs enable row level security;
alter table public.radar_parties enable row level security;
revoke all on public.radar_joueurs, public.radar_parties from public, anon, authenticated;
revoke all on sequence public.radar_parties_id_seq from public, anon, authenticated;

-- ---------------------------------------------------------------------
-- Réglages
-- ---------------------------------------------------------------------
create or replace function public.radar_reglage(p text)
returns integer language sql immutable
set search_path to 'public'
as $$
  select case p
    when 'manches'    then 5
    when 'secondes'   then 15
    when 'marge'      then 2
    when 'penalite'   then 1000
    when 'par_jour'   then null   -- null : pas de limite (6 octobre)
    when 'k'          then 24
    when 'population' then 15000
  end;
$$;

create or replace function public.radar_rang(p_elo integer)
returns text language sql immutable
set search_path to 'public'
as $$
  select case when p_elo >= 1200 then 'Navigateur'
              when p_elo >= 1100 then 'Vigie'
              when p_elo >= 1000 then 'Guetteur'
              when p_elo >= 900  then 'Randonneur'
              else 'Promeneur' end;
$$;

-- ---------------------------------------------------------------------
-- Interne : clore les manches dépassées d'une partie (temps écoulé)
-- ---------------------------------------------------------------------
create or replace function public.radar_rattraper(p_id bigint)
returns void
language plpgsql security definer
set search_path to 'public'
as $$
declare
  p radar_parties;
  v_limite interval := make_interval(secs => radar_reglage('secondes') + radar_reglage('marge'));
begin
  select * into p from radar_parties where id = p_id for update;
  -- une manche ouverte et dépassée compte la pénalité, la suivante n'est
  -- pas ouverte toute seule : le joueur la verra s'ouvrir à son retour
  if not p.fini and p.manche_debut is not null and now() > p.manche_debut + v_limite then
    update radar_parties
       set coups = coups || jsonb_build_object('lon', null, 'lat', null, 'km', radar_reglage('penalite')),
           manche = manche + 1,
           manche_debut = null
     where id = p_id;
    perform radar_clore_si_fini(p_id);
  end if;
end;
$$;

-- ---------------------------------------------------------------------
-- Interne : fin de partie, et règlement du duel s'il y a un adversaire
-- ---------------------------------------------------------------------
create or replace function public.radar_clore_si_fini(p_id bigint)
returns void
language plpgsql security definer
set search_path to 'public'
as $$
declare
  p radar_parties;
  s radar_parties;
  v_total int;
  ea int; eb int;
  v_att numeric;
  v_score numeric;
  v_k int := radar_reglage('k');
  va int; vb int;
begin
  select * into p from radar_parties where id = p_id for update;
  if p.fini or p.manche < radar_reglage('manches') then return; end if;

  select coalesce(sum((c->>'km')::int), 0) into v_total from jsonb_array_elements(p.coups) c;
  update radar_parties set fini = true, total_km = v_total, fin_le = now() where id = p_id;

  if p.source_id is null then return; end if;   -- partie neuve : elle attend un adversaire

  -- le duel se règle maintenant
  select * into s from radar_parties where id = p.source_id for update;
  insert into radar_joueurs(joueur_id) values (p.joueur_id), (s.joueur_id) on conflict do nothing;
  select elo into ea from radar_joueurs where joueur_id = p.joueur_id for update;
  select elo into eb from radar_joueurs where joueur_id = s.joueur_id for update;

  v_score := case when v_total < s.total_km then 1 when v_total > s.total_km then 0 else 0.5 end;
  v_att := 1 / (1 + power(10, (eb - ea) / 400.0));
  va := ea + round(v_k * (v_score - v_att));
  vb := eb + round(v_k * ((1 - v_score) - (1 - v_att)));

  update radar_joueurs set elo = va, parties = parties + 1,
         victoires = victoires + (v_score = 1)::int, maj = now() where joueur_id = p.joueur_id;
  update radar_joueurs set elo = vb, parties = parties + 1,
         victoires = victoires + (v_score = 0)::int, maj = now() where joueur_id = s.joueur_id;

  update radar_parties set elo_avant = ea, elo_apres = va, vu = true,
         resultat = case v_score when 1 then 'victoire' when 0 then 'defaite' else 'egalite' end
   where id = p.id;
  update radar_parties set elo_avant = eb, elo_apres = vb, vu = false,
         resultat = case v_score when 0 then 'victoire' when 1 then 'defaite' else 'egalite' end
   where id = s.id;
end;
$$;

-- ---------------------------------------------------------------------
-- Interne : ce que le joueur a le droit de voir d'une partie
-- ---------------------------------------------------------------------
create or replace function public.radar_vue(p_id bigint)
returns jsonb
language plpgsql security definer
set search_path to 'public'
as $$
declare
  p radar_parties;
  s radar_parties;
  v_manches jsonb := '[]'::jsonb;
  i int;
  c communes;
  v_adv jsonb := null;
begin
  select * into p from radar_parties where id = p_id;
  if p.source_id is not null then select * into s from radar_parties where id = p.source_id; end if;

  -- les manches jouées : la commune, le coup du joueur, celui de l'adversaire
  for i in 1 .. jsonb_array_length(p.coups) loop
    select * into c from communes where code = p.communes[i];
    v_manches := v_manches || jsonb_build_object(
      'nom', c.nom, 'dept', c.departement, 'lat', c.latitude, 'lon', c.longitude,
      'moi', p.coups->(i - 1),
      'lui', case when s.id is not null then s.coups->(i - 1) end);
  end loop;

  if s.id is not null then
    v_adv := jsonb_build_object(
      'pseudo', (select coalesce(pseudo, 'Joueur') from joueurs where id = s.joueur_id),
      'elo', (select elo from radar_joueurs where joueur_id = s.joueur_id),
      'joue_le', s.fin_le,
      'total_km', case when p.fini then s.total_km end);
  end if;

  return jsonb_build_object(
    'id', p.id,
    'manche', p.manche,
    'manches', radar_reglage('manches'),
    'secondes', radar_reglage('secondes'),
    -- la manche ouverte : seulement son nom, et le temps qui reste
    'en_cours', case when not p.fini and p.manche_debut is not null then jsonb_build_object(
        'nom', (select nom from communes where code = p.communes[p.manche + 1]),
        'reste_ms', greatest(0, round(extract(epoch from (p.manche_debut
                      + make_interval(secs => radar_reglage('secondes')) - now())) * 1000)))
      end,
    'jouees', v_manches,
    'fini', p.fini,
    'total_km', p.total_km,
    'adversaire', v_adv,
    'en_attente', p.fini and p.source_id is null and p.resultat is null,
    'resultat', p.resultat,
    'elo_avant', p.elo_avant,
    'elo_apres', p.elo_apres);
end;
$$;

-- ---------------------------------------------------------------------
-- Ce que le jeu appelle
-- ---------------------------------------------------------------------

-- L'état du joueur pour l'écran QG : Elo, rang, duels restants, partie en
-- cours, derniers résultats, classement.
create or replace function public.radar_etat()
returns jsonb
language plpgsql security definer
set search_path to 'public'
as $$
declare
  v_uid uuid := auth.uid();
  v_jour date := (now() at time zone 'Europe/Paris')::date;
  v_elo int;
  v_parties int;
  v_premier uuid;
  v_en_cours bigint;
begin
  if v_uid is null then raise exception 'Connecte-toi pour jouer à Radar.'; end if;

  select elo, parties into v_elo, v_parties from radar_joueurs where joueur_id = v_uid;
  v_elo := coalesce(v_elo, 1000);

  -- le n°1 porte le titre Lapérouse (au moins 5 duels, au-dessus de 1 000)
  select joueur_id into v_premier from radar_joueurs
   where parties >= 5 and elo > 1000 order by elo desc, maj limit 1;

  select id into v_en_cours from radar_parties where joueur_id = v_uid and not fini order by id desc limit 1;
  if v_en_cours is not null then perform radar_rattraper(v_en_cours); end if;

  return jsonb_build_object(
    'elo', v_elo,
    'parties', coalesce(v_parties, 0),
    'rang', case when v_premier = v_uid then 'Lapérouse' else radar_rang(v_elo) end,
    -- null : pas de limite
    'restants', case when radar_reglage('par_jour') is null then null
                     else greatest(0, radar_reglage('par_jour')
                       - (select count(*) from radar_parties where joueur_id = v_uid and jour = v_jour)) end,
    'en_cours', (select id from radar_parties where joueur_id = v_uid and not fini order by id desc limit 1),
    'non_vus', (select count(*) from radar_parties where joueur_id = v_uid and not vu),
    'en_attente', (select count(*) from radar_parties
                    where joueur_id = v_uid and fini and source_id is null and resultat is null),
    'derniers', (select coalesce(jsonb_agg(x order by x.fin desc), '[]'::jsonb) from (
        -- mes duels réglés, que j'aie joué en premier ou en second
        select p.id, p.resultat, p.total_km, p.elo_avant, p.elo_apres, p.vu,
               coalesce(p2.fin_le, p.fin_le) as fin,
               (select coalesce(pseudo, 'Joueur') from joueurs where id = coalesce(p2.joueur_id, s.joueur_id)) as adversaire,
               coalesce(p2.total_km, s.total_km) as adversaire_km
          from radar_parties p
          left join radar_parties s  on s.id = p.source_id
          left join radar_parties p2 on p2.source_id = p.id and p2.fini
         where p.joueur_id = v_uid and p.resultat is not null
         order by coalesce(p2.fin_le, p.fin_le) desc limit 8) x),
    'classement', (select coalesce(jsonb_agg(x order by x.elo desc), '[]'::jsonb) from (
        select coalesce(j.pseudo, 'Joueur') as pseudo, r.elo, r.parties,
               case when r.joueur_id = v_premier then 'Lapérouse' else radar_rang(r.elo) end as rang,
               r.joueur_id = v_uid as moi
          from radar_joueurs r join joueurs j on j.id = r.joueur_id
         where r.parties > 0
         order by r.elo desc limit 20) x));
end;
$$;

-- Lancer un duel, ou reprendre celui qui est en cours.
create or replace function public.radar_lancer()
returns jsonb
language plpgsql security definer
set search_path to 'public'
as $$
declare
  v_uid uuid := auth.uid();
  v_jour date := (now() at time zone 'Europe/Paris')::date;
  v_id bigint;
  v_elo int;
  s radar_parties;
  v_codes text[];
begin
  if v_uid is null then raise exception 'Connecte-toi pour jouer à Radar.'; end if;
  perform pg_advisory_xact_lock(hashtextextended('radar' || v_uid::text, 7));

  -- une partie en cours : on la reprend
  select id into v_id from radar_parties where joueur_id = v_uid and not fini order by id desc limit 1;
  if v_id is not null then
    perform radar_rattraper(v_id);
    return radar_vue(v_id);
  end if;

  if (select count(*) from radar_parties where joueur_id = v_uid and jour = v_jour) >= radar_reglage('par_jour') then
    raise exception 'Plus de duel aujourd''hui. Reviens demain.';
  end if;

  insert into radar_joueurs(joueur_id) values (v_uid) on conflict do nothing;
  select elo into v_elo from radar_joueurs where joueur_id = v_uid;

  -- un adversaire : une partie terminée, pas encore affrontée, d'un autre
  -- joueur. De préférence quelqu'un que je n'ai pas affronté dans les
  -- dernières 24 h, puis le plus proche en Elo, puis la plus ancienne
  -- (personne n'attend trop). Ce n'est qu'une préférence : avec peu de
  -- joueurs, une exclusion laissait des parties sans adversaire (6 octobre).
  select p.* into s
    from radar_parties p
    left join radar_joueurs r on r.joueur_id = p.joueur_id
   where p.source_id is null and p.fini and not p.utilisee
     and p.joueur_id <> v_uid
   order by exists (select 1 from radar_parties m
                      join radar_parties ms on ms.id = m.source_id
                     where m.joueur_id = v_uid and ms.joueur_id = p.joueur_id
                       and m.cree_le > now() - interval '24 hours'),
            abs(coalesce(r.elo, 1000) - v_elo), p.fin_le
   limit 1
   for update of p skip locked;

  if s.id is not null then
    update radar_parties set utilisee = true where id = s.id;
    v_codes := s.communes;
  else
    select array_agg(code) into v_codes from (
      select c.code from communes c
       where c.population >= radar_reglage('population')
         and length(c.departement) = 2
         and c.latitude is not null
         and c.nom not ilike '%arrondissement%'
       order by random() limit radar_reglage('manches')) x;
  end if;

  insert into radar_parties(joueur_id, communes, source_id)
  values (v_uid, v_codes, s.id)
  returning id into v_id;
  return radar_vue(v_id);
end;
$$;

-- Ouvrir la manche suivante : c'est ici que le chrono démarre.
create or replace function public.radar_ouvrir(p_id bigint)
returns jsonb
language plpgsql security definer
set search_path to 'public'
as $$
declare
  v_uid uuid := auth.uid();
  p radar_parties;
begin
  if v_uid is null then raise exception 'Connecte-toi pour jouer à Radar.'; end if;
  perform radar_rattraper(p_id);
  select * into p from radar_parties where id = p_id and joueur_id = v_uid for update;
  if not found then raise exception 'Partie introuvable.'; end if;
  if not p.fini and p.manche_debut is null then
    update radar_parties set manche_debut = now() where id = p_id;
  end if;
  return radar_vue(p_id);
end;
$$;

-- Viser : le coup de la manche ouverte. lon/lat null = « je passe ».
create or replace function public.radar_viser(p_id bigint, p_lon numeric, p_lat numeric)
returns jsonb
language plpgsql security definer
set search_path to 'public'
as $$
declare
  v_uid uuid := auth.uid();
  p radar_parties;
  c communes;
  v_km int;
begin
  if v_uid is null then raise exception 'Connecte-toi pour jouer à Radar.'; end if;
  perform radar_rattraper(p_id);
  select * into p from radar_parties where id = p_id and joueur_id = v_uid for update;
  if not found then raise exception 'Partie introuvable.'; end if;
  if p.fini then return radar_vue(p_id); end if;
  if p.manche_debut is null then
    -- la manche n'est pas ouverte (ou vient d'être close par le chrono)
    return radar_vue(p_id);
  end if;

  select * into c from communes where code = p.communes[p.manche + 1];
  if p_lon is null or p_lat is null
     or p_lat not between 40 and 52 or p_lon not between -6 and 11 then
    v_km := radar_reglage('penalite');
    p_lon := null; p_lat := null;
  else
    v_km := least(radar_reglage('penalite'), round(cdj_km(p_lat, p_lon, c.latitude, c.longitude))::int);
  end if;

  update radar_parties
     set coups = coups || jsonb_build_object('lon', p_lon, 'lat', p_lat, 'km', v_km),
         manche = manche + 1,
         manche_debut = null
   where id = p_id;
  perform radar_clore_si_fini(p_id);
  return radar_vue(p_id);
end;
$$;

-- Marquer les résultats comme vus (pastille du QG).
create or replace function public.radar_vu()
returns void
language sql security definer
set search_path to 'public'
as $$
  update radar_parties set vu = true where joueur_id = auth.uid() and not vu;
$$;

-- ---------------------------------------------------------------------
-- Droits
-- ---------------------------------------------------------------------
revoke all on function public.radar_rattraper(bigint)       from public, anon, authenticated;
revoke all on function public.radar_clore_si_fini(bigint)   from public, anon, authenticated;
revoke all on function public.radar_vue(bigint)             from public, anon, authenticated;
revoke all on function public.radar_etat()                  from public, anon;
revoke all on function public.radar_lancer()                from public, anon;
revoke all on function public.radar_ouvrir(bigint)          from public, anon;
revoke all on function public.radar_viser(bigint, numeric, numeric) from public, anon;
revoke all on function public.radar_vu()                    from public, anon;
grant execute on function public.radar_etat()                  to authenticated;
grant execute on function public.radar_lancer()                to authenticated;
grant execute on function public.radar_ouvrir(bigint)          to authenticated;
grant execute on function public.radar_viser(bigint, numeric, numeric) to authenticated;
grant execute on function public.radar_vu()                    to authenticated;
