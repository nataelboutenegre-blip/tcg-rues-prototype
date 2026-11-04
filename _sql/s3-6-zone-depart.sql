-- ===========================================================================
--  TerraFront — s3-6 : la zone de départ (saison 3)
--
--  Décision de Nataël (4/11) : au début de la saison, chaque joueur choisit
--  une fois sa zone de départ (une des 13 régions de France ou la Suisse) ;
--  ses 3 premiers paquets du Front y tombent, puis le tirage reprend partout.
--  Une zone se ferme au choix quand les trois quarts de ses communes sont
--  prises (ceux qui l'ont déjà choisie continuent d'y tirer tant qu'il y
--  reste des communes libres).
--
--  ÉTEINT EN ARRIVANT (config_jeu 'zone_depart', ouvert = 0) : ne change rien
--  aujourd'hui, à lancer quand on veut. Le jour J, après s3-5 :
--    update public.config_jeu set valeur = (valeur::jsonb || '{"ouvert": 1}'::jsonb)::text
--     where cle = 'zone_depart';
--  (ouvert = 0 coupe tout d'un coup, y compris pour ceux qui ont déjà choisi.)
--
--  Ce que fait le fichier :
--    1. config_jeu 'zone_depart' : ouvert 0, paquets 3, seuil 0,75 ;
--    2. table zone_depart (joueur, saison, zone, cartes restantes : 3 paquets
--       = 15 cartes), invisible pour les joueurs ;
--    3. zone_depart_etat() et zone_depart_choisir(zone) pour le jeu ;
--    4. draw_commune : tant que le joueur a des cartes de zone et que sa zone
--       a des communes libres, la carte est tirée dans sa zone avec les chances
--       de rareté de toute la France (aucun avantage à partir en Suisse, plus
--       riche en rares), sans outre-mer ni commune hantée, et une carte de zone
--       est décomptée. Sinon, rien ne change.
--       Modifiée en place à partir de sa définition en production : si un
--       texte attendu manque, rien ne change.
--  Rejouable.
--  Contrôle attendu : true | 0 | 13 | 0   (14 zones une fois la Suisse entrée)
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

-- 1. le réglage, éteint ----------------------------------------------------------
insert into public.config_jeu (cle, valeur)
values ('zone_depart', '{"ouvert": 0, "paquets": 3, "seuil": 0.75}')
on conflict (cle) do nothing;

create or replace function public.zone_depart_reglage(p_cle text)
 returns numeric language sql stable security definer set search_path to 'public'
as $f$
  -- s3-6
  select coalesce((select (c.valeur::jsonb ->> p_cle)::numeric from config_jeu c where c.cle = 'zone_depart'),
                  case p_cle when 'ouvert' then 0 when 'paquets' then 3 when 'seuil' then 0.75 end);
$f$;

-- 2. la table ----------------------------------------------------------------------
create table if not exists public.zone_depart (
  joueur_id        uuid not null references public.joueurs(id) on delete cascade,
  saison           text not null,
  zone             text not null,
  cartes_restantes integer not null check (cartes_restantes >= 0),
  choisi_le        timestamptz not null default now(),
  primary key (joueur_id, saison)
);
create index if not exists zone_depart_saison_zone on public.zone_depart (saison, zone);
alter table public.zone_depart enable row level security;
revoke all on table public.zone_depart from anon, authenticated;

-- 3. les outils -----------------------------------------------------------------------
-- la saison en cours (celle qui n'est pas terminée)
create or replace function public.zone_depart_saison()
 returns text language sql stable security definer set search_path to 'public'
as $f$
  select id from saisons where etat <> 'terminee' order by debut desc nulls last limit 1;
$f$;

-- la zone d'un département : sa région en France métropolitaine, « Suisse » pour un canton
create or replace function public.zone_depart_zone(p_dep text)
 returns text language sql immutable set search_path to 'public'
as $f$
  select case when est_metropole(p_dep) or est_canton(p_dep) then cdj_region(p_dep) end;
$f$;

-- les départements (ou cantons) d'une zone
create or replace function public.zone_depart_deps(p_zone text)
 returns text[] language sql stable security definer set search_path to 'public'
as $f$
  -- materialized : la zone est calculée une fois par département, pas une fois par commune
  with x as materialized (select distinct departement as d from communes)
  select array_agg(x.d order by x.d) from x where zone_depart_zone(x.d) = p_zone;
$f$;

-- les départements de la zone où ce joueur tire encore, ou null
create or replace function public.zone_depart_en_cours(p_uid uuid)
 returns text[] language plpgsql stable security definer set search_path to 'public'
as $f$
declare
  v_zone text;
  v_deps text[];
begin
  if p_uid is null or zone_depart_reglage('ouvert') <> 1 then
    return null;
  end if;
  select z.zone into v_zone
    from zone_depart z
   where z.joueur_id = p_uid and z.saison = zone_depart_saison() and z.cartes_restantes > 0;
  if v_zone is null then
    return null;
  end if;
  v_deps := zone_depart_deps(v_zone);
  if v_deps is null or not exists (
       select 1 from communes c
        where c.departement = any(v_deps)
          and not exists (select 1 from possessions p where p.commune_code = c.code)) then
    return null;   -- zone pleine : le tirage reprend partout
  end if;
  return v_deps;
end;
$f$;

-- les poids de rareté dans une zone : les chances de toute la France (poids_tirage),
-- en retirant les raretés qui n'ont plus de commune libre dans la zone. Toutes les zones
-- donnent ainsi les mêmes chances de rareté (la Suisse compte 31 % de rares, la France 10 % :
-- sans ça, partir en Suisse donnerait deux fois plus de rares), comme le paquet Terra suisse.
create or replace function public.zone_depart_poids(p_deps text[])
 returns numeric[] language sql stable security definer set search_path to 'public'
as $f$
  with g as (select poids_tirage() as p),
  z as (
    select array[bool_or(c.tier = 'legendaire'), bool_or(c.tier = 'epique'), bool_or(c.tier = 'rare'),
                 bool_or(c.tier = 'peucommun'), bool_or(c.tier = 'commun')] as a
      from communes c
      left join possessions p on p.commune_code = c.code
     where p.commune_code is null and c.departement = any(p_deps))
  select array[
    case when coalesce(z.a[1], false) then g.p[1] else 0 end,
    case when coalesce(z.a[2], false) then g.p[2] else 0 end,
    case when coalesce(z.a[3], false) then g.p[3] else 0 end,
    case when coalesce(z.a[4], false) then g.p[4] else 0 end,
    case when coalesce(z.a[5], false) then coalesce(g.p[5], 0) else 0 end
  ]::numeric[]
  from g, z;
$f$;

-- ce que le jeu affiche : la zone choisie, ou les zones à choisir
create or replace function public.zone_depart_etat()
 returns jsonb language plpgsql stable security definer set search_path to 'public'
as $f$
declare
  v_uid    uuid := auth.uid();
  v_saison text := zone_depart_saison();
  v_ouvert boolean := zone_depart_reglage('ouvert') = 1;
  v_seuil  numeric := zone_depart_reglage('seuil');
  v_clan   public.clan_membres.clan_id%type;
  v_zone   text;
  v_cartes integer;
  v_zones  jsonb;
  v_res    jsonb;
begin
  if v_uid is null then raise exception 'Non connecté'; end if;
  v_res := jsonb_build_object(
    'ouvert', v_ouvert and v_saison is not null,
    'saison', v_saison,
    'saison_nom', (select nom from saisons where id = v_saison),
    'paquets', greatest(1, zone_depart_reglage('paquets'))::integer,
    'seuil', v_seuil);
  if not v_ouvert or v_saison is null then
    return v_res;
  end if;

  select z.zone, z.cartes_restantes into v_zone, v_cartes
    from zone_depart z where z.joueur_id = v_uid and z.saison = v_saison;
  if v_zone is not null then
    return v_res || jsonb_build_object(
      'choisi', v_zone,
      'cartes_restantes', v_cartes,
      'paquets_restants', ceil(v_cartes / 5.0)::integer,
      'actif', zone_depart_en_cours(v_uid) is not null);
  end if;

  select m.clan_id into v_clan from clan_membres m where m.joueur_id = v_uid limit 1;
  with d as materialized (
    select x.dep, zone_depart_zone(x.dep) as zone
      from (select distinct departement as dep from communes) x),
  z as (
    select d.zone, count(*) as total, count(*) filter (where p.commune_code is null) as libres
      from communes c
      join d on d.dep = c.departement
      left join possessions p on p.commune_code = c.code
     where d.zone is not null
     group by d.zone),
  j as (
    select zd.zone, count(*) as joueurs, count(m.joueur_id) as clan
      from zone_depart zd
      left join clan_membres m on m.joueur_id = zd.joueur_id and m.clan_id = v_clan
     where zd.saison = v_saison
     group by zd.zone)
  select jsonb_agg(jsonb_build_object(
           'zone', z.zone, 'total', z.total, 'libres', z.libres,
           'joueurs', coalesce(j.joueurs, 0), 'clan', coalesce(j.clan, 0),
           'fermee', (z.total - z.libres) >= v_seuil * z.total)
         order by z.zone)
    into v_zones
    from z left join j on j.zone = z.zone;

  return v_res || jsonb_build_object('choisi', null, 'zones', coalesce(v_zones, '[]'::jsonb));
end;
$f$;

-- le choix, une fois par saison
create or replace function public.zone_depart_choisir(p_zone text)
 returns jsonb language plpgsql volatile security definer set search_path to 'public'
as $f$
declare
  v_uid    uuid := auth.uid();
  v_saison text := zone_depart_saison();
  v_deps   text[];
  v_total  integer;
  v_libres integer;
begin
  if v_uid is null then raise exception 'Non connecté'; end if;
  if zone_depart_reglage('ouvert') <> 1 or v_saison is null then
    raise exception 'Le choix de la zone de départ n''est pas ouvert';
  end if;
  if exists (select 1 from zone_depart where joueur_id = v_uid and saison = v_saison) then
    raise exception 'Ta zone de départ est déjà choisie pour cette saison';
  end if;
  v_deps := zone_depart_deps(p_zone);
  if v_deps is null then
    raise exception 'Zone inconnue';
  end if;
  select count(*), count(*) filter (where p.commune_code is null) into v_total, v_libres
    from communes c left join possessions p on p.commune_code = c.code
   where c.departement = any(v_deps);
  if v_total - v_libres >= zone_depart_reglage('seuil') * v_total then
    raise exception 'Cette zone est complète : choisis-en une autre';
  end if;
  insert into zone_depart (joueur_id, saison, zone, cartes_restantes)
  values (v_uid, v_saison, p_zone, greatest(1, zone_depart_reglage('paquets'))::integer * 5)
  on conflict do nothing;
  if not found then
    raise exception 'Ta zone de départ est déjà choisie pour cette saison';
  end if;
  return zone_depart_etat();
end;
$f$;

revoke all on function public.zone_depart_reglage(text)   from public, anon, authenticated;
revoke all on function public.zone_depart_saison()        from public, anon, authenticated;
revoke all on function public.zone_depart_deps(text)      from public, anon, authenticated;
revoke all on function public.zone_depart_en_cours(uuid)  from public, anon, authenticated;
revoke all on function public.zone_depart_poids(text[])   from public, anon, authenticated;
revoke all on function public.zone_depart_etat()          from public, anon;
revoke all on function public.zone_depart_choisir(text)   from public, anon;
grant execute on function public.zone_depart_etat()        to authenticated;
grant execute on function public.zone_depart_choisir(text) to authenticated;

-- 4. le tirage du Front ------------------------------------------------------------------
do $$
declare
  d text := pg_get_functiondef('public.draw_commune(text)'::regprocedure);
begin
  if position('s3-6' in d) > 0 then raise notice 'draw_commune : déjà à jour'; return; end if;
  d := pg_temp.remp(d,
    '  v_attempt int;
begin',
    '  v_attempt int;
  v_zone_deps text[];   -- s3-6 : zone de départ
begin', 1, 'draw_commune (déclaration)');
  d := pg_temp.remp(d,
    '    v_poids := poids_tirage();',
    '    -- s3-6 : zone de départ, les premiers paquets de la saison tombent dans la zone choisie
    if v_attempt = 1 then v_zone_deps := zone_depart_en_cours(v_joueur_id); end if;
    v_poids := case when v_zone_deps is not null then zone_depart_poids(v_zone_deps) end;
    if v_poids is not null and coalesce(v_poids[1] + v_poids[2] + v_poids[3] + v_poids[4] + v_poids[5], 0) <= 0 then
      v_zone_deps := null;
      v_poids := null;
    end if;
    v_poids := coalesce(v_poids, poids_tirage());', 1, 'draw_commune (poids)');
  d := pg_temp.remp(d,
    'if random() < outremer_chance_front() then',
    'if v_zone_deps is null and random() < outremer_chance_front() then', 1, 'draw_commune (outre-mer)');
  d := pg_temp.remp(d,
    'if v_code is null and halloween_en_cours() and',
    'if v_code is null and v_zone_deps is null and halloween_en_cours() and', 1, 'draw_commune (Halloween)');
  d := pg_temp.remp(d,
    'where c.tier = v_tier and p.commune_code is null and length(c.departement) = 2 and',
    'where c.tier = v_tier and p.commune_code is null and length(c.departement) = 2 and (v_zone_deps is null or c.departement = any(v_zone_deps)) and',
    1, 'draw_commune (palier)');
  d := pg_temp.remp(d,
    '    if v_code is null then
      raise exception',
    '    if v_code is null and v_zone_deps is not null then   -- s3-6 : la zone vient de se vider, on retente partout
      v_zone_deps := null;
      continue;
    end if;
    if v_code is null then
      raise exception', 1, 'draw_commune (zone vide)');
  d := pg_temp.remp(d,
    '        values (v_code, v_joueur_id, p_saison, now());',
    '        values (v_code, v_joueur_id, p_saison, now());
      if v_zone_deps is not null then   -- s3-6 : une carte de zone en moins
        update zone_depart set cartes_restantes = cartes_restantes - 1
         where joueur_id = v_joueur_id and saison = zone_depart_saison() and cartes_restantes > 0;
      end if;', 1, 'draw_commune (décompte)');
  execute d;
end $$;

commit;

-- Contrôle : true | 0 | 13 | 0   (tirage à jour | éteint | zones | choix faits ; 14 zones avec la Suisse)
select position('s3-6' in pg_get_functiondef('public.draw_commune(text)'::regprocedure)) > 0 as tirage_ok,
       zone_depart_reglage('ouvert')::integer                                                 as ouvert,
       (select count(distinct zone_depart_zone(x.d)) from (select distinct departement as d from public.communes) x)::integer
                                                                                               as zones,
       (select count(*) from public.zone_depart)::integer                                       as choix;
