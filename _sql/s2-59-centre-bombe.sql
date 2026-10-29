-- ===========================================================================
--  s2-59 — Bâtiments, étape 2 : le Centre de recherche et la bombe
--  Décisions de Nataël du 28-29 octobre 2026 (aperçu « mallette v2 » validé :
--  « c'est parfait !! » ; dévoilement à 48 h : « pas mal ! ») ; plan :
--  claude/plan-strategie-front.md. À lancer APRÈS s2-58 (deux Fonderies).
--
--  CENTRE DE RECHERCHE : 40 lingots, il faut 2 Fonderies, prêt en 24 h, un
--    seul par joueur, sur une de ses communes du Front. SECRET : les autres ne
--    le voient pas sur la carte, sauf quand il est DÉVOILÉ :
--      - une bombe se prépare depuis 48 h ou plus (niveau 2 et au-delà) ;
--      - pendant 24 h après le lâcher d'une bombe.
--    Commune prise (ou échangée) : centre détruit, préparation en cours perdue.
--  PRÉPARER UNE BOMBE : 45 lingots, une à la fois. Au lancement, annonce
--    publique sans nom : « quelqu'un prépare une bombe dans le <département> ».
--    Rayon selon l'attente : 10 km à 24 h, 15 km à 48 h, 20 km à 72 h (max).
--  LÂCHER : sur une commune à moins de 50 km d'une de ses communes, et à plus
--    de 20 km du bord d'une zone encore active. Détruit les garnisons (énergie
--    perdue) et les forteresses de TOUS dans le rayon, celles du lanceur
--    comprises ; Fonderies, centres et communes épargnés. Pendant 24 h, +15 %
--    aux attaques de tous sur les communes de la zone. Le nom du lanceur est
--    donné à l'impact ; chaque joueur touché voit ce qu'il a perdu.
--  Réglages : config_jeu 'batiments' (clés centre_* et bombe_*), modifiables
--  sans code ; 'bombes_ouvertes' = interrupteur (1 ouvert, 0 fermé).
--
--  Fonctions pour le jeu (authenticated) :
--    bombe_preparer()          lance la préparation (45 lingots)
--    bombe_chercher(texte)     communes pour la mallette (portée comprise)
--    bombe_apercu(code)        ce que toucherait la bombe sur cette commune
--    bombe_lacher(code)        lâche la bombe
--    bombes_actives()          les zones bombardées en cours (carte)
--    bombes_alertes(jours)     annonces récentes (préparations, impacts)
--  Modifiées (mêmes signatures) : mes_batiments, batiment_construire,
--    batiments_visibles, bonus_batiments, batiments_changement_proprio.
--  Recréée avec deux colonnes de plus : batiments_effet (bombe, bombe_sur).
--  Rejouable. Contrôle attendu : true | 40 | 45 | 0 | true | true
-- ===========================================================================
begin;

-- 1. Réglages ---------------------------------------------------------------
update public.config_jeu
   set valeur = (valeur::jsonb || '{"bombes_ouvertes": 1, "centre_prix": 40, "centre_fonderies": 2,
       "bombe_prix": 45, "bombe_portee_km": 50, "bombe_bonus": 0.15, "bombe_duree_h": 24,
       "bombe_ecart_km": 20, "bombe_devoile_h": 48, "bombe_niv1_h": 24, "bombe_niv2_h": 48,
       "bombe_niv3_h": 72, "bombe_rayon1": 10, "bombe_rayon2": 15, "bombe_rayon3": 20}'::jsonb)::text
 where cle = 'batiments' and not (valeur::jsonb ? 'bombe_prix');

create or replace function public.batiment_reglage(p_cle text)
 returns numeric language sql stable security definer set search_path to 'public'
as $f$
  select coalesce(
    (select (c.valeur::jsonb ->> p_cle)::numeric from config_jeu c where c.cle = 'batiments'),
    case p_cle when 'fonderie_production' then 10 when 'fonderie_max' then 30 when 'construction_h' then 24
               when 'forteresse_prix' then 20 when 'forteresse_max' then 3 when 'forteresse_defense' then 0.15
               when 'forteresse_appui' then 0.05 when 'forteresse_rayon_km' then 20 when 'pillage' then 0.5
               when 'fonderies_max' then 2 when 'fonderie2_prix' then 30 when 'fonderie_max2' then 45
               when 'bombes_ouvertes' then 1 when 'centre_prix' then 40 when 'centre_fonderies' then 2
               when 'bombe_prix' then 45 when 'bombe_portee_km' then 50 when 'bombe_bonus' then 0.15
               when 'bombe_duree_h' then 24 when 'bombe_ecart_km' then 20 when 'bombe_devoile_h' then 48
               when 'bombe_niv1_h' then 24 when 'bombe_niv2_h' then 48 when 'bombe_niv3_h' then 72
               when 'bombe_rayon1' then 10 when 'bombe_rayon2' then 15 when 'bombe_rayon3' then 20 end);
$f$;

create or replace function public.bombes_ouvertes()
 returns boolean language sql stable security definer set search_path to 'public'
as $f$ select batiments_ouverts() and batiment_reglage('bombes_ouvertes') = 1; $f$;

-- distance en km (assez précise à l'échelle d'un département)
create or replace function public.dist_km(a_lat double precision, a_lon double precision,
                                          b_lat double precision, b_lon double precision)
 returns double precision language sql immutable
as $f$
  select 111.19 * sqrt(power(a_lat - b_lat, 2) + power((a_lon - b_lon) * cos(radians((a_lat + b_lat) / 2)), 2));
$f$;

-- 2. Tables -------------------------------------------------------------------
do $$
declare c record;
begin
  for c in select conname from pg_constraint
            where conrelid = 'public.batiments'::regclass and contype = 'c'
              and pg_get_constraintdef(oid) like '%fonderie%' loop
    execute format('alter table public.batiments drop constraint %I', c.conname);
  end loop;
end $$;
alter table public.batiments add constraint batiments_type_check check (type in ('fonderie', 'forteresse', 'centre'));
create unique index if not exists batiments_un_centre on public.batiments(joueur_id) where type = 'centre';

create table if not exists public.bombes_preparations(
  id           bigserial primary key,
  joueur_id    uuid not null references public.joueurs(id) on delete cascade,
  centre_code  text not null,
  dept         text,
  commence_le  timestamptz not null default now(),
  etat         text not null default 'en_cours' check (etat in ('en_cours', 'lachee', 'perdue')),
  fini_le      timestamptz
);
create unique index if not exists bombes_prep_une on public.bombes_preparations(joueur_id) where etat = 'en_cours';
create index if not exists bombes_prep_le on public.bombes_preparations(commence_le);

create table if not exists public.bombes(
  id             bigserial primary key,
  lanceur        uuid not null references public.joueurs(id) on delete cascade,
  preparation_id bigint references public.bombes_preparations(id) on delete set null,
  centre_code    text,
  cible_code     text not null references public.communes(code),
  lat            double precision not null,
  lon            double precision not null,
  niveau         integer not null,
  rayon_km       numeric not null,
  le             timestamptz not null default now(),
  fin            timestamptz not null,
  communes       integer not null default 0,
  garnisons      integer not null default 0,
  forteresses    integer not null default 0
);
create index if not exists bombes_fin on public.bombes(fin);
create index if not exists bombes_lanceur on public.bombes(lanceur, le);

create table if not exists public.bombes_degats(
  bombe_id     bigint not null references public.bombes(id) on delete cascade,
  joueur_id    uuid not null references public.joueurs(id) on delete cascade,
  garnisons    integer not null default 0,
  energie      integer not null default 0,
  forteresses  integer not null default 0,
  primary key (bombe_id, joueur_id)
);

alter table public.bombes_preparations enable row level security;
alter table public.bombes enable row level security;
alter table public.bombes_degats enable row level security;
revoke all on public.bombes_preparations, public.bombes, public.bombes_degats from public, anon, authenticated;
revoke all on sequence public.bombes_preparations_id_seq, public.bombes_id_seq from public, anon, authenticated;

-- 3. Aides ---------------------------------------------------------------------
-- niveau d'une préparation commencée à p_debut : 0 (pas prête), 1, 2 ou 3
create or replace function public.bombe_niveau(p_debut timestamptz)
 returns integer language sql stable security definer set search_path to 'public'
as $f$
  select case when p_debut is null then 0
              when now() - p_debut >= make_interval(hours => batiment_reglage('bombe_niv3_h')::integer) then 3
              when now() - p_debut >= make_interval(hours => batiment_reglage('bombe_niv2_h')::integer) then 2
              when now() - p_debut >= make_interval(hours => batiment_reglage('bombe_niv1_h')::integer) then 1
              else 0 end;
$f$;

create or replace function public.bombe_rayon(p_niveau integer)
 returns numeric language sql stable security definer set search_path to 'public'
as $f$
  select case p_niveau when 1 then batiment_reglage('bombe_rayon1') when 2 then batiment_reglage('bombe_rayon2')
                       when 3 then batiment_reglage('bombe_rayon3') else 0 end;
$f$;

-- le centre de p_uid (sur p_code) est-il visible de tous ?
create or replace function public.centre_devoile(p_uid uuid, p_code text)
 returns boolean language sql stable security definer set search_path to 'public'
as $f$
  select exists (select 1 from bombes_preparations p
                  where p.joueur_id = p_uid and p.etat = 'en_cours' and p.centre_code = p_code
                    and now() - p.commence_le >= make_interval(hours => batiment_reglage('bombe_devoile_h')::integer))
      or exists (select 1 from bombes b
                  where b.lanceur = p_uid and b.centre_code = p_code
                    and b.le > now() - make_interval(hours => batiment_reglage('bombe_duree_h')::integer));
$f$;

-- distance (km) entre une commune et la plus proche des communes de p_uid
create or replace function public.dist_mes_communes(p_uid uuid, p_lat double precision, p_lon double precision)
 returns double precision language sql stable security definer set search_path to 'public'
as $f$
  select min(dist_km(m.latitude, m.longitude, p_lat, p_lon))
    from possessions p join communes m on m.code = p.commune_code
   where p.joueur_id = p_uid and m.latitude is not null;
$f$;

-- 4. Ce que voit le joueur -------------------------------------------------------
create or replace function public.mes_batiments()
 returns jsonb language plpgsql stable security definer set search_path to 'public'
as $f$
declare
  v_uid uuid := auth.uid();
  v numeric;
  v_prod numeric := batiment_reglage('fonderie_production');
  v_max numeric;
  v_pretes integer;
  v_tot numeric;
begin
  if v_uid is null then raise exception 'Non connecte'; end if;
  v := coalesce(lingots_lire(v_uid), 0);
  v_max := lingots_max(v_uid);
  select count(*) into v_pretes from batiments b where b.joueur_id = v_uid and b.type = 'fonderie' and b.pret_le <= now();
  v_tot := v_prod * v_pretes;
  return jsonb_build_object(
    'ouverts', batiments_ouverts(),
    'lingots', floor(v)::integer,
    'max', v_max::integer,
    'production', v_prod::integer,
    'production_totale', v_tot::integer,
    'prochain_dans', case when v_tot > 0 and v < v_max then ceil((1 - (v - floor(v))) * 86400.0 / v_tot)::integer end,
    'fonderie', (select jsonb_build_object('code', b.commune_code, 'nom', c.nom, 'dept', c.departement,
                        'pret_le', b.pret_le, 'pret', b.pret_le <= now())
                   from batiments b join communes c on c.code = b.commune_code
                  where b.joueur_id = v_uid and b.type = 'fonderie' order by b.cree_le limit 1),
    'fonderies', coalesce((select jsonb_agg(jsonb_build_object(
        'code', b.commune_code, 'nom', c.nom, 'dept', c.departement,
        'pret_le', b.pret_le, 'pret', b.pret_le <= now()) order by b.cree_le)
        from batiments b join communes c on c.code = b.commune_code
       where b.joueur_id = v_uid and b.type = 'fonderie'), '[]'::jsonb),
    'forteresses', coalesce((select jsonb_agg(jsonb_build_object(
        'code', b.commune_code, 'nom', c.nom, 'dept', c.departement,
        'pret_le', b.pret_le, 'pret', b.pret_le <= now()) order by b.cree_le)
        from batiments b join communes c on c.code = b.commune_code
       where b.joueur_id = v_uid and b.type = 'forteresse'), '[]'::jsonb),
    -- s2-59 : le centre, la préparation en cours, la dernière bombe
    'bombes_ouvertes', bombes_ouvertes(),
    'centre', (select jsonb_build_object('code', b.commune_code, 'nom', c.nom, 'dept', c.departement,
                      'pret_le', b.pret_le, 'pret', b.pret_le <= now(),
                      'devoile', centre_devoile(v_uid, b.commune_code))
                 from batiments b join communes c on c.code = b.commune_code
                where b.joueur_id = v_uid and b.type = 'centre'),
    'preparation', (select jsonb_build_object('commence_le', p.commence_le,
                           'ecoule', floor(extract(epoch from now() - p.commence_le))::integer,
                           'niveau', bombe_niveau(p.commence_le), 'rayon', bombe_rayon(bombe_niveau(p.commence_le))::integer)
                      from bombes_preparations p where p.joueur_id = v_uid and p.etat = 'en_cours'),
    'derniere_bombe', (select jsonb_build_object('le', b.le, 'fin', b.fin, 'cible', c.nom, 'dept', c.departement, 'code', b.cible_code)
                         from bombes b join communes c on c.code = b.cible_code
                        where b.lanceur = v_uid order by b.le desc limit 1),
    'reglages', jsonb_build_object(
        'forteresse_prix', batiment_reglage('forteresse_prix')::integer,
        'forteresse_max', batiment_reglage('forteresse_max')::integer,
        'forteresse_defense', round(batiment_reglage('forteresse_defense') * 100)::integer,
        'forteresse_appui', round(batiment_reglage('forteresse_appui') * 100)::integer,
        'rayon_km', batiment_reglage('forteresse_rayon_km')::integer,
        'construction_h', batiment_reglage('construction_h')::integer,
        'pillage', round(batiment_reglage('pillage') * 100)::integer,
        'fonderies_max', batiment_reglage('fonderies_max')::integer,
        'fonderie2_prix', batiment_reglage('fonderie2_prix')::integer,
        'fonderie_max2', batiment_reglage('fonderie_max2')::integer,
        'centre_prix', batiment_reglage('centre_prix')::integer,
        'centre_fonderies', batiment_reglage('centre_fonderies')::integer,
        'bombe_prix', batiment_reglage('bombe_prix')::integer,
        'bombe_portee_km', batiment_reglage('bombe_portee_km')::integer,
        'bombe_bonus', round(batiment_reglage('bombe_bonus') * 100)::integer,
        'bombe_duree_h', batiment_reglage('bombe_duree_h')::integer,
        'bombe_ecart_km', batiment_reglage('bombe_ecart_km')::integer,
        'bombe_devoile_h', batiment_reglage('bombe_devoile_h')::integer,
        'bombe_heures', jsonb_build_array(batiment_reglage('bombe_niv1_h')::integer, batiment_reglage('bombe_niv2_h')::integer, batiment_reglage('bombe_niv3_h')::integer),
        'bombe_rayons', jsonb_build_array(batiment_reglage('bombe_rayon1')::integer, batiment_reglage('bombe_rayon2')::integer, batiment_reglage('bombe_rayon3')::integer)));
end;
$f$;

create or replace function public.batiment_construire(p_code text, p_type text)
 returns jsonb language plpgsql security definer set search_path to 'public'
as $f$
declare
  v_uid uuid := auth.uid();
  v numeric;
  v_prix numeric;
  v_nf integer;
begin
  if v_uid is null then raise exception 'Non connecte'; end if;
  if not batiments_ouverts() then raise exception 'Les bâtiments ne sont pas encore ouverts'; end if;
  if p_type not in ('fonderie', 'forteresse', 'centre') then raise exception 'Bâtiment inconnu'; end if;
  perform 1 from joueurs where id = v_uid for update;
  if not exists (select 1 from possessions p where p.commune_code = p_code and p.joueur_id = v_uid) then
    raise exception 'Cette commune ne t''appartient pas';
  end if;
  if exists (select 1 from batiments b where b.commune_code = p_code and b.type = p_type) then
    raise exception 'Il y a déjà ce bâtiment ici';
  end if;
  select count(*) into v_nf from batiments b where b.joueur_id = v_uid and b.type = 'fonderie';

  if p_type = 'fonderie' then
    if v_nf >= batiment_reglage('fonderies_max') then
      raise exception 'Tu as déjà % Fonderies', batiment_reglage('fonderies_max')::integer;
    end if;
    v := lingots_figer(v_uid);
    if v_nf >= 1 then
      v_prix := batiment_reglage('fonderie2_prix');
      if v < v_prix then raise exception 'Il te faut % lingots (tu en as %)', v_prix::integer, floor(v)::integer; end if;
      update joueurs set lingots = lingots - v_prix where id = v_uid;
    end if;
  elsif p_type = 'centre' then
    if not bombes_ouvertes() then raise exception 'Le Centre de recherche n''est pas encore ouvert'; end if;
    if v_nf < batiment_reglage('centre_fonderies') then
      raise exception 'Il te faut d''abord % Fonderies', batiment_reglage('centre_fonderies')::integer;
    end if;
    if exists (select 1 from batiments b where b.joueur_id = v_uid and b.type = 'centre') then
      raise exception 'Tu as déjà un Centre de recherche';
    end if;
    v_prix := batiment_reglage('centre_prix');
    v := lingots_figer(v_uid);
    if v < v_prix then raise exception 'Il te faut % lingots (tu en as %)', v_prix::integer, floor(v)::integer; end if;
    update joueurs set lingots = lingots - v_prix where id = v_uid;
  else
    if v_nf = 0 then raise exception 'Il te faut d''abord une Fonderie'; end if;
    if (select count(*) from batiments b where b.joueur_id = v_uid and b.type = 'forteresse')
       >= batiment_reglage('forteresse_max') then
      raise exception 'Tu as déjà % forteresses', batiment_reglage('forteresse_max')::integer;
    end if;
    v_prix := batiment_reglage('forteresse_prix');
    v := lingots_figer(v_uid);
    if v < v_prix then raise exception 'Il te faut % lingots (tu en as %)', v_prix::integer, floor(v)::integer; end if;
    update joueurs set lingots = lingots - v_prix where id = v_uid;
  end if;

  insert into batiments(joueur_id, commune_code, type, pret_le)
  values (v_uid, p_code, p_type, now() + make_interval(hours => batiment_reglage('construction_h')::integer));
  return mes_batiments();
end;
$f$;

-- La carte : les centres des autres n'apparaissent que dévoilés
create or replace function public.batiments_visibles()
 returns table(commune_code text, type text, joueur_id uuid, pret boolean)
 language sql stable security definer set search_path to 'public'
as $f$
  select b.commune_code, b.type, b.joueur_id, b.pret_le <= now()
    from batiments b
   where auth.uid() is not null and batiments_ouverts()
     and (b.type <> 'centre' or b.joueur_id = auth.uid() or centre_devoile(b.joueur_id, b.commune_code));
$f$;

-- Les chances : forteresses (s2-48) + zone bombardée (+15 % pour tous)
create or replace function public.bonus_batiments(p_uid uuid, p_code text)
 returns numeric language sql stable security definer set search_path to 'public'
as $f$
  select case when not batiments_ouverts() or p_uid is null then 0 else
    coalesce((select -batiment_reglage('forteresse_defense')
                from batiments b
               where b.commune_code = p_code and b.type = 'forteresse'
                 and b.pret_le <= now() and b.joueur_id <> p_uid
               limit 1), 0)
  + coalesce((select batiment_reglage('forteresse_appui')
                from batiments b
                join communes f on f.code = b.commune_code
                join communes c on c.code = p_code
               where b.joueur_id = p_uid and b.type = 'forteresse'
                 and b.pret_le <= now() and b.commune_code <> p_code
                 and 111.19 * sqrt(power(f.latitude - c.latitude, 2)
                     + power((f.longitude - c.longitude) * cos(radians(c.latitude)), 2))
                     <= batiment_reglage('forteresse_rayon_km')
               limit 1), 0)
  + coalesce((select batiment_reglage('bombe_bonus')
                from bombes z join communes c on c.code = p_code
               where z.fin > now() and dist_km(z.lat, z.lon, c.latitude, c.longitude) <= z.rayon_km
               limit 1), 0)
  end;
$f$;

-- Pour le panneau d'attaque : ce qui joue, en clair (+ la bombe)
drop function if exists public.batiments_effet(text);
create function public.batiments_effet(p_code text)
 returns table(defense integer, appui integer, appui_de text, bombe integer, bombe_sur text)
 language sql stable security definer set search_path to 'public'
as $f$
  with c as (select latitude lat, longitude lon from communes where code = p_code),
  d as (select 1 from batiments b where b.commune_code = p_code and b.type = 'forteresse'
                and b.pret_le <= now() and b.joueur_id <> auth.uid() limit 1),
  a as (select f.nom
          from batiments b join communes f on f.code = b.commune_code, c
         where b.joueur_id = auth.uid() and b.type = 'forteresse' and b.pret_le <= now()
           and b.commune_code <> p_code
           and 111.19 * sqrt(power(f.latitude - c.lat, 2) + power((f.longitude - c.lon) * cos(radians(c.lat)), 2))
               <= batiment_reglage('forteresse_rayon_km')
         order by power(f.latitude - c.lat, 2) + power((f.longitude - c.lon) * cos(radians(c.lat)), 2)
         limit 1),
  z as (select k.nom from bombes b join communes k on k.code = b.cible_code, c
         where b.fin > now() and dist_km(b.lat, b.lon, c.lat, c.lon) <= b.rayon_km
         order by b.le desc limit 1)
  select case when exists (select 1 from d) then round(batiment_reglage('forteresse_defense') * 100)::integer else 0 end,
         case when exists (select 1 from a) then round(batiment_reglage('forteresse_appui') * 100)::integer else 0 end,
         (select nom from a),
         case when exists (select 1 from z) then round(batiment_reglage('bombe_bonus') * 100)::integer else 0 end,
         (select nom from z)
   where auth.uid() is not null and batiments_ouverts();
$f$;

-- 5. La bombe -------------------------------------------------------------------------
create or replace function public.bombe_preparer()
 returns jsonb language plpgsql security definer set search_path to 'public'
as $f$
declare
  v_uid uuid := auth.uid();
  v numeric;
  v_prix numeric := batiment_reglage('bombe_prix');
  v_centre record;
begin
  if v_uid is null then raise exception 'Non connecte'; end if;
  if not bombes_ouvertes() then raise exception 'Les bombes ne sont pas encore ouvertes'; end if;
  perform 1 from joueurs where id = v_uid for update;
  select b.commune_code, b.pret_le, c.departement into v_centre
    from batiments b join communes c on c.code = b.commune_code
   where b.joueur_id = v_uid and b.type = 'centre';
  if v_centre.commune_code is null then raise exception 'Il te faut d''abord un Centre de recherche'; end if;
  if v_centre.pret_le > now() then raise exception 'Ton Centre de recherche est encore en construction'; end if;
  if exists (select 1 from bombes_preparations p where p.joueur_id = v_uid and p.etat = 'en_cours') then
    raise exception 'Une bombe est déjà en préparation';
  end if;
  v := lingots_figer(v_uid);
  if v < v_prix then raise exception 'Il te faut % lingots (tu en as %)', v_prix::integer, floor(v)::integer; end if;
  update joueurs set lingots = lingots - v_prix where id = v_uid;
  insert into bombes_preparations(joueur_id, centre_code, dept) values (v_uid, v_centre.commune_code, v_centre.departement);
  return mes_batiments();
end;
$f$;

-- pourquoi on ne peut pas viser cette commune (null : on peut)
create or replace function public.bombe_refus(p_uid uuid, p_lat double precision, p_lon double precision)
 returns text language plpgsql stable security definer set search_path to 'public'
as $f$
declare
  v_d double precision;
  z record;
begin
  v_d := dist_mes_communes(p_uid, p_lat, p_lon);
  if v_d is null then return 'Tu n''as aucune commune dans le Front'; end if;
  if v_d > batiment_reglage('bombe_portee_km') then
    return format('Hors de portée : %s km de ta commune la plus proche (%s km au plus)',
                  round(v_d::numeric), batiment_reglage('bombe_portee_km')::integer);
  end if;
  select k.nom, b.rayon_km, dist_km(b.lat, b.lon, p_lat, p_lon) - b.rayon_km as bord into z
    from bombes b join communes k on k.code = b.cible_code
   where b.fin > now() and dist_km(b.lat, b.lon, p_lat, p_lon) - b.rayon_km < batiment_reglage('bombe_ecart_km')
   order by 3 limit 1;
  if z.nom is not null then
    return format('Trop près de la zone bombardée de %s (moins de %s km)', z.nom, batiment_reglage('bombe_ecart_km')::integer);
  end if;
  return null;
end;
$f$;

-- La mallette : les communes qui correspondent à ce qu'on tape, avec la portée
drop function if exists public.bombe_chercher(text);
create function public.bombe_chercher(p_texte text)
 returns table(code text, nom text, dept text, distance_km integer, ok boolean, raison text,
               lat double precision, lon double precision)
 language plpgsql stable security definer set search_path to 'public', 'extensions'
as $f$
#variable_conflict use_column
declare
  v_uid uuid := auth.uid();
  v_m text := regexp_replace(unaccent(lower(btrim(coalesce(p_texte, '')))), '[^a-z]+', ' ', 'g');
begin
  if v_uid is null then raise exception 'Non connecte'; end if;
  v_m := btrim(v_m);
  if length(v_m) < 2 then return; end if;
  return query
  with t as (
    select c.code, c.nom, c.departement, c.population, c.latitude::double precision lat, c.longitude::double precision lon,
           regexp_replace(unaccent(lower(c.nom)), '[^a-z]+', ' ', 'g') k
      from communes c
     where c.latitude is not null
  ), m as (
    select t.*, (t.k like v_m || '%') debut
      from t
     where t.k like v_m || '%' or (length(v_m) >= 3 and t.k like '% ' || v_m || '%')
     order by (t.k like v_m || '%') desc, t.population desc nulls last
     limit 6
  )
  select m.code, m.nom, m.departement, round(dist_mes_communes(v_uid, m.lat, m.lon))::integer,
         bombe_refus(v_uid, m.lat, m.lon) is null, bombe_refus(v_uid, m.lat, m.lon), m.lat, m.lon
    from m
   order by m.debut desc, m.population desc nulls last;
end;
$f$;

-- La mallette : ce que toucherait la bombe sur p_code (avec le niveau actuel)
create or replace function public.bombe_apercu(p_code text)
 returns jsonb language plpgsql stable security definer set search_path to 'public'
as $f$
declare
  v_uid uuid := auth.uid();
  v_c record;
  v_prep record;
  v_n integer;
  v_r numeric;
begin
  if v_uid is null then raise exception 'Non connecte'; end if;
  select code, nom, departement, latitude::double precision lat, longitude::double precision lon into v_c from communes where code = p_code;
  if v_c.code is null then raise exception 'Commune inconnue'; end if;
  select * into v_prep from bombes_preparations where joueur_id = v_uid and etat = 'en_cours';
  v_n := bombe_niveau(v_prep.commence_le);
  v_r := bombe_rayon(greatest(v_n, 1));
  return jsonb_build_object(
    'code', v_c.code, 'nom', v_c.nom, 'dept', v_c.departement, 'lat', v_c.lat, 'lon', v_c.lon,
    'niveau', v_n, 'rayon', v_r::integer,
    'refus', bombe_refus(v_uid, v_c.lat, v_c.lon),
    'communes', (select count(*) from communes k where k.latitude between v_c.lat - v_r / 110.0 and v_c.lat + v_r / 110.0
                    and dist_km(k.latitude, k.longitude, v_c.lat, v_c.lon) <= v_r),
    'garnisons', (select count(*) from front_garnisons g join communes k on k.code = g.commune_code
                   where dist_km(k.latitude, k.longitude, v_c.lat, v_c.lon) <= v_r),
    'garnisons_moi', (select count(*) from front_garnisons g join communes k on k.code = g.commune_code
                       where g.joueur_id = v_uid and dist_km(k.latitude, k.longitude, v_c.lat, v_c.lon) <= v_r),
    'forteresses', (select count(*) from batiments b join communes k on k.code = b.commune_code
                     where b.type = 'forteresse' and dist_km(k.latitude, k.longitude, v_c.lat, v_c.lon) <= v_r),
    'forteresses_moi', (select count(*) from batiments b join communes k on k.code = b.commune_code
                         where b.type = 'forteresse' and b.joueur_id = v_uid and dist_km(k.latitude, k.longitude, v_c.lat, v_c.lon) <= v_r));
end;
$f$;

create or replace function public.bombe_lacher(p_code text)
 returns jsonb language plpgsql security definer set search_path to 'public'
as $f$
declare
  v_uid uuid := auth.uid();
  v_c record;
  v_prep record;
  v_n integer;
  v_r numeric;
  v_refus text;
  v_id bigint;
  v_g integer; v_f integer; v_nb integer;
begin
  if v_uid is null then raise exception 'Non connecte'; end if;
  if not bombes_ouvertes() then raise exception 'Les bombes ne sont pas encore ouvertes'; end if;
  perform 1 from joueurs where id = v_uid for update;
  select * into v_prep from bombes_preparations where joueur_id = v_uid and etat = 'en_cours' for update;
  if v_prep.id is null then raise exception 'Aucune bombe en préparation'; end if;
  if not exists (select 1 from batiments b where b.joueur_id = v_uid and b.type = 'centre' and b.commune_code = v_prep.centre_code) then
    update bombes_preparations set etat = 'perdue', fini_le = now() where id = v_prep.id;
    raise exception 'Ton Centre de recherche a été détruit : la bombe est perdue';
  end if;
  v_n := bombe_niveau(v_prep.commence_le);
  if v_n < 1 then raise exception 'La bombe n''est pas encore prête'; end if;
  v_r := bombe_rayon(v_n);
  select code, nom, departement, latitude::double precision lat, longitude::double precision lon into v_c from communes where code = p_code;
  if v_c.code is null or v_c.lat is null then raise exception 'Commune inconnue'; end if;
  -- une seule bombe à la fois sur la carte (les deux lâchers simultanés passent l'un après l'autre)
  perform pg_advisory_xact_lock(hashtext('bombe_lacher'));
  v_refus := bombe_refus(v_uid, v_c.lat, v_c.lon);
  if v_refus is not null then raise exception '%', v_refus; end if;

  insert into bombes(lanceur, preparation_id, centre_code, cible_code, lat, lon, niveau, rayon_km, fin)
  values (v_uid, v_prep.id, v_prep.centre_code, v_c.code, v_c.lat, v_c.lon, v_n, v_r,
          now() + make_interval(hours => batiment_reglage('bombe_duree_h')::integer))
  returning id into v_id;

  with d as (
    delete from front_garnisons g using communes k
     where k.code = g.commune_code and dist_km(k.latitude, k.longitude, v_c.lat, v_c.lon) <= v_r
    returning g.joueur_id, g.energie)
  insert into bombes_degats(bombe_id, joueur_id, garnisons, energie)
  select v_id, d.joueur_id, count(*), coalesce(sum(d.energie), 0) from d group by d.joueur_id;

  with d as (
    delete from batiments b using communes k
     where k.code = b.commune_code and b.type = 'forteresse' and dist_km(k.latitude, k.longitude, v_c.lat, v_c.lon) <= v_r
    returning b.joueur_id)
  insert into bombes_degats(bombe_id, joueur_id, forteresses)
  select v_id, d.joueur_id, count(*) from d group by d.joueur_id
  on conflict (bombe_id, joueur_id) do update set forteresses = excluded.forteresses;

  select coalesce(sum(garnisons), 0), coalesce(sum(forteresses), 0) into v_g, v_f from bombes_degats where bombe_id = v_id;
  select count(*) into v_nb from communes k
   where k.latitude between v_c.lat - v_r / 110.0 and v_c.lat + v_r / 110.0
     and dist_km(k.latitude, k.longitude, v_c.lat, v_c.lon) <= v_r;
  update bombes set garnisons = v_g, forteresses = v_f, communes = v_nb where id = v_id;
  update bombes_preparations set etat = 'lachee', fini_le = now() where id = v_prep.id;

  return jsonb_build_object('id', v_id, 'code', v_c.code, 'nom', v_c.nom, 'dept', v_c.departement,
    'niveau', v_n, 'rayon', v_r::integer, 'communes', v_nb, 'garnisons', v_g, 'forteresses', v_f,
    'garnisons_moi', coalesce((select garnisons from bombes_degats where bombe_id = v_id and joueur_id = v_uid), 0),
    'forteresses_moi', coalesce((select forteresses from bombes_degats where bombe_id = v_id and joueur_id = v_uid), 0),
    'bonus', round(batiment_reglage('bombe_bonus') * 100)::integer,
    'fin', now() + make_interval(hours => batiment_reglage('bombe_duree_h')::integer));
end;
$f$;

-- Les zones bombardées en cours (pour la carte)
create or replace function public.bombes_actives()
 returns table(id bigint, cible_code text, cible_nom text, dept text, lat double precision, lon double precision,
               rayon_km integer, fin timestamptz, lanceur_pseudo text, moi boolean)
 language sql stable security definer set search_path to 'public'
as $f$
  select b.id, b.cible_code, c.nom, c.departement, b.lat, b.lon, b.rayon_km::integer, b.fin, j.pseudo, b.lanceur = auth.uid()
    from bombes b join communes c on c.code = b.cible_code left join joueurs j on j.id = b.lanceur
   where auth.uid() is not null and b.fin > now()
   order by b.le desc;
$f$;

-- Les annonces : préparations (sans nom, juste le département) et impacts
create or replace function public.bombes_alertes(p_jours integer default 2)
 returns table(type text, id bigint, le timestamptz, dept text, cible_code text, cible_nom text, lanceur_pseudo text,
               rayon_km integer, garnisons integer, forteresses integer, mes_garnisons integer, mes_forteresses integer,
               moi boolean, etat text)
 language sql stable security definer set search_path to 'public'
as $f$
  select * from (
    select 'preparation'::text, p.id, p.commence_le, p.dept, null::text, null::text, null::text,
           null::integer, null::integer, null::integer, null::integer, null::integer,
           p.joueur_id = auth.uid(), p.etat
      from bombes_preparations p
     where p.commence_le > now() - make_interval(days => least(greatest(p_jours, 1), 14))
    union all
    select 'bombe', b.id, b.le, c.departement, b.cible_code, c.nom, j.pseudo,
           b.rayon_km::integer, b.garnisons, b.forteresses, coalesce(d.garnisons, 0), coalesce(d.forteresses, 0),
           b.lanceur = auth.uid(), case when b.fin > now() then 'active' else 'finie' end
      from bombes b join communes c on c.code = b.cible_code left join joueurs j on j.id = b.lanceur
      left join bombes_degats d on d.bombe_id = b.id and d.joueur_id = auth.uid()
     where b.le > now() - make_interval(days => least(greatest(p_jours, 1), 14))
  ) x
  where auth.uid() is not null
  order by 3 desc
  limit 40;
$f$;

-- 6. Destruction quand la commune change de main : le centre et sa préparation ------------
create or replace function public.batiments_changement_proprio()
 returns trigger language plpgsql security definer set search_path to 'public'
as $f$
declare
  b record;
  v numeric;
  v_nf integer;
  v_pille integer;
  v_conquete boolean;
begin
  if tg_op = 'UPDATE' and new.joueur_id is not distinct from old.joueur_id then return null; end if;
  v_conquete := tg_op = 'UPDATE' and new.joueur_id is not null
                and new.conquise_le is distinct from old.conquise_le and new.conquise_le is not null;
  for b in select * from batiments where commune_code = old.commune_code loop
    if b.type = 'fonderie' then
      v := lingots_figer(b.joueur_id);
      select count(*) into v_nf from batiments f where f.joueur_id = b.joueur_id and f.type = 'fonderie';
      delete from batiments where id = b.id;
      if v_conquete and v > 0 then
        v_pille := floor(v * batiment_reglage('pillage') / greatest(v_nf, 1))::integer;
        update joueurs set lingots = lingots - v_pille where id = b.joueur_id;
        perform lingots_figer(new.joueur_id);
        update joueurs set lingots = lingots + v_pille where id = new.joueur_id;
      end if;
      update joueurs set lingots = least(lingots, lingots_max(b.joueur_id)) where id = b.joueur_id;
    elsif b.type = 'centre' then
      delete from batiments where id = b.id;
      update bombes_preparations set etat = 'perdue', fini_le = now()
       where joueur_id = b.joueur_id and etat = 'en_cours';
    else
      delete from batiments where id = b.id;
    end if;
  end loop;
  return null;
exception when others then
  raise warning 'batiments_changement_proprio : %', sqlerrm;
  return null;
end;
$f$;

-- 7. Droits ---------------------------------------------------------------------------------
revoke all on function public.bombes_ouvertes(), public.bombe_niveau(timestamptz), public.bombe_rayon(integer),
  public.centre_devoile(uuid, text), public.dist_mes_communes(uuid, double precision, double precision),
  public.bombe_refus(uuid, double precision, double precision), public.lingots_lire(uuid),
  public.lingots_max(uuid), public.bonus_batiments(uuid, text), public.batiments_changement_proprio()
  from public, anon, authenticated;
revoke all on function public.mes_batiments(), public.batiment_construire(text, text), public.batiments_visibles(),
  public.batiments_effet(text), public.bombe_preparer(), public.bombe_chercher(text), public.bombe_apercu(text),
  public.bombe_lacher(text), public.bombes_actives(), public.bombes_alertes(integer) from public, anon;
grant execute on function public.mes_batiments(), public.batiment_construire(text, text), public.batiments_visibles(),
  public.batiments_effet(text), public.bombe_preparer(), public.bombe_chercher(text), public.bombe_apercu(text),
  public.bombe_lacher(text), public.bombes_actives(), public.bombes_alertes(integer) to authenticated;

commit;

-- Contrôle
select public.bombes_ouvertes()                                          as ouvertes,
       public.batiment_reglage('centre_prix')::int                       as prix_centre,
       public.batiment_reglage('bombe_prix')::int                        as prix_bombe,
       (select count(*) from public.bombes)                              as bombes,
       has_function_privilege('authenticated', 'public.bombe_lacher(text)', 'execute') as lacher_ok,
       exists (select 1 from pg_constraint where conname = 'batiments_type_check'
                and pg_get_constraintdef(oid) like '%centre%')           as type_centre;
