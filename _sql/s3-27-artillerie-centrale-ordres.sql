-- s3-27 : saison 3 — l'Artillerie, la Centrale de clan et les ordres du chef (règles validées par Nataël le 18/11/2026).
-- TOUT EST ÉTEINT à la sortie de ce fichier. Trois interrupteurs indépendants :
--   config_jeu 'batiments'.artilleries_ouvertes = 1   (l'Artillerie)
--   config_jeu 'centrale_clan'.ouverte = 1            (la Centrale de clan)
--   config_jeu 'ordres_chef'.ouverts = 1              (les ordres du chef)
-- On peut relancer le fichier : chaque retouche d'une fonction existante est marquée et ne se fait qu'une fois.
--
-- L'Artillerie (bâtiment de joueur) : 20 lingots, 6 h, une par joueur, une Fonderie demandée. Dans un rayon de 50 km,
-- elle supprime le malus de distance du siège (× 0,8 quand on n'a aucune commune à moins de 20 km de la cible) ;
-- les vagues qui en profitent coûtent 10 % d'énergie en plus, soit × 1 / 1,1 ≈ 0,91 au lieu de × 0,8.
-- Secrète tant qu'elle n'a pas tiré, puis visible 24 h après chaque vague qui en profite. Soufflée par une bombe,
-- prise avec sa commune, vue par les Radars. Déplaçable (10 lingots, 6 h).
--
-- La Centrale de clan : une par clan, posée par le chef ou un bras droit sur une de ses communes, à partir de 3 membres
-- actifs, payée par la caisse du clan (dons des membres) : 10 lingots par membre actif (30 au moins). Chaque membre
-- présent depuis 48 h ramasse 8 énergie par jour (sa part ; pas de réserve commune). Visible, soufflée par une bombe,
-- prise avec sa commune ; détruite si celui qui l'a posée quitte le clan. Le prix d'une Centrale annulée retourne
-- dans la caisse.
--
-- Les ordres du chef : le chef ou un bras droit pose jusqu'à 3 cibles pour 24 h, visibles par le clan ; un appel à
-- l'assaut prévient les membres (une fois toutes les 3 h par cible). Aucun bonus de combat.

begin;

-- 0. l'outil de retouche : remplace un passage d'une fonction s'il y est exactement une fois
create or replace function pg_temp.retoucher(p_sig text, p_marque text, p_ancien text, p_nouveau text)
returns void language plpgsql as $f$
declare d text; n integer;
begin
  d := pg_get_functiondef(p_sig::regprocedure);
  if position(p_marque in d) > 0 then return; end if;   -- déjà fait
  n := (length(d) - length(replace(d, p_ancien, ''))) / length(p_ancien);
  if n <> 1 then raise exception 's3-27 : % a changé (« % » trouvé % fois)', p_sig, left(p_ancien, 70), n; end if;
  if position(p_marque in p_nouveau) = 0 then raise exception 's3-27 : marque % absente du nouveau texte', p_marque; end if;
  execute replace(d, p_ancien, p_nouveau);
end $f$;

-- 1. réglages (éteints)
update public.config_jeu
   set valeur = ((valeur::jsonb) || jsonb_build_object(
         'artilleries_ouvertes', coalesce((valeur::jsonb)->'artilleries_ouvertes', '0'::jsonb),
         'artillerie_prix', 20, 'artillerie_portee_km', 50, 'artillerie_cout', 0.1,
         'artillerie_deplacer_prix', 10, 'artillerie_devoile_h', 24))::text
 where cle = 'batiments';
insert into public.config_jeu (cle, valeur)
values ('centrale_clan', '{"ouverte": 0, "part": 8, "prix_actif": 10, "actifs_min": 3, "anciennete_h": 48}')
on conflict (cle) do nothing;
insert into public.config_jeu (cle, valeur)
values ('ordres_chef', '{"ouverts": 0, "max": 3, "duree_h": 24, "appel_h": 3}')
on conflict (cle) do nothing;
update public.config_jeu
   set valeur = ((valeur::jsonb) || '{"artillerie": ["canon"], "centrale": ["turbine"]}'::jsonb)::text
 where cle = 'batiments_styles';

-- 2. la table des bâtiments : deux types de plus, et le clan d'une Centrale
alter table public.batiments drop constraint if exists batiments_type_check;
alter table public.batiments add constraint batiments_type_check
  check (type = any (array['fonderie', 'forteresse', 'centre', 'banque', 'radar', 'artillerie', 'centrale']));
alter table public.batiments add column if not exists clan_id uuid references public.clans(id) on delete cascade;
create unique index if not exists batiments_centrale_par_clan on public.batiments (clan_id) where type = 'centrale';

-- 3. tables de la Centrale et des ordres (lues seulement par les fonctions)
create table if not exists public.clan_caisses (
  clan_id uuid primary key references public.clans(id) on delete cascade,
  lingots integer not null default 0 check (lingots >= 0));
create table if not exists public.clan_dons (
  id bigserial primary key,
  clan_id uuid not null references public.clans(id) on delete cascade,
  joueur_id uuid not null,
  lingots integer not null check (lingots > 0),
  le timestamptz not null default now());
create index if not exists clan_dons_clan on public.clan_dons (clan_id, le desc);
create table if not exists public.centrale_ramassages (
  joueur_id uuid not null,
  jour date not null,
  clan_id uuid,
  energie integer not null,
  le timestamptz not null default now(),
  primary key (joueur_id, jour));
create table if not exists public.clan_ordres (
  id bigserial primary key,
  clan_id uuid not null references public.clans(id) on delete cascade,
  commune_code text not null,
  pose_par uuid,
  pose_le timestamptz not null default now(),
  fin timestamptz not null,
  appel_le timestamptz,
  retire boolean not null default false);
create index if not exists clan_ordres_clan on public.clan_ordres (clan_id, fin desc);
alter table public.clan_caisses enable row level security;
alter table public.clan_dons enable row level security;
alter table public.centrale_ramassages enable row level security;
alter table public.clan_ordres enable row level security;
revoke all on public.clan_caisses, public.clan_dons, public.centrale_ramassages, public.clan_ordres from anon, authenticated;

-- 4. l'Artillerie
create or replace function public.artilleries_ouvertes()
returns boolean language sql stable security definer set search_path to 'public' as $$
  select batiments_ouverts() and coalesce(batiment_reglage('artilleries_ouvertes'), 0) >= 1;
$$;

-- l'Artillerie prête de p_uid la plus proche de la cible, si elle est à portée (sinon null)
create or replace function public.artillerie_couvre(p_uid uuid, p_code text)
returns jsonb language sql stable security definer set search_path to 'public' as $$
  select jsonb_build_object('code', b.commune_code, 'nom', a.nom, 'dept', a.departement,
                            'km', round(dist_km(a.latitude, a.longitude, c.latitude, c.longitude)::numeric, 1),
                            'cout', round(coalesce(batiment_reglage('artillerie_cout'), 0.1) * 100)::integer)
    from batiments b join communes a on a.code = b.commune_code, communes c
   where artilleries_ouvertes() and b.joueur_id = p_uid and b.type = 'artillerie' and b.pret_le <= now()
     and c.code = p_code and b.commune_code <> p_code
     and dist_km(a.latitude, a.longitude, c.latitude, c.longitude) <= coalesce(batiment_reglage('artillerie_portee_km'), 50)
   order by dist_km(a.latitude, a.longitude, c.latitude, c.longitude)
   limit 1;
$$;

create or replace function public.artillerie_infos(p_uid uuid)
returns jsonb language sql stable security definer set search_path to 'public' as $$
  select jsonb_build_object(
    'artilleries_ouvertes', artilleries_ouvertes(),
    'artillerie', (select jsonb_build_object('code', b.commune_code, 'nom', c.nom, 'dept', c.departement,
                          'pret_le', b.pret_le, 'pret', b.pret_le <= now(),
                          'style', coalesce(b.style, batiment_styles() -> 'artillerie' ->> 0),
                          'deplacee', b.deplacee_le is not null and b.pret_le > now(),
                          'devoilee', coalesce(b.devoile_jusqua > now(), false), 'devoile_jusqua', b.devoile_jusqua)
                     from batiments b join communes c on c.code = b.commune_code
                    where b.joueur_id = p_uid and b.type = 'artillerie'),
    'artillerie_reglages', jsonb_build_object(
        'prix', coalesce(batiment_reglage('artillerie_prix'), 20)::integer,
        'portee_km', coalesce(batiment_reglage('artillerie_portee_km'), 50)::integer,
        'cout', round(coalesce(batiment_reglage('artillerie_cout'), 0.1) * 100)::integer,
        'deplacer_prix', coalesce(batiment_reglage('artillerie_deplacer_prix'), 10)::integer,
        'devoile_h', coalesce(batiment_reglage('artillerie_devoile_h'), 24)::integer,
        'malus', round(coalesce(siege_n('prox_aucune'), 0.8), 2)));
$$;

create or replace function public.artillerie_deplacer(p_depuis text, p_vers text)
returns jsonb language plpgsql security definer set search_path to 'public' as $$
-- s3-27 : l'Artillerie va sur une autre de ses communes ; 10 lingots, 6 h sans effet, ne s'annule pas
declare
  v_uid uuid := auth.uid();
  b record;
  v numeric;
  v_prix numeric := coalesce(batiment_reglage('artillerie_deplacer_prix'), 10);
begin
  if v_uid is null then raise exception 'Non connecte'; end if;
  if not artilleries_ouvertes() then raise exception 'L''Artillerie n''est pas encore ouverte'; end if;
  perform 1 from joueurs where id = v_uid for update;
  select * into b from batiments where joueur_id = v_uid and type = 'artillerie' and commune_code = p_depuis;
  if b.id is null then raise exception 'Cette Artillerie n''existe pas (ou plus)'; end if;
  if b.pret_le > now() then raise exception 'Ton Artillerie est encore en chantier : attends qu''elle soit prête pour la déplacer'; end if;
  if p_vers = p_depuis then raise exception 'Ton Artillerie est déjà ici'; end if;
  if not exists (select 1 from possessions p where p.commune_code = p_vers and p.joueur_id = v_uid) then
    raise exception 'Cette commune ne t''appartient pas';
  end if;
  if exists (select 1 from batiments x where x.commune_code = p_vers and x.type = 'artillerie') then
    raise exception 'Il y a déjà une Artillerie ici';
  end if;
  v := lingots_figer(v_uid);
  if v < v_prix then raise exception 'Il te faut % lingots (tu en as %)', v_prix::integer, floor(v)::integer; end if;
  update batiments
     set commune_code = p_vers,
         pret_le = now() + make_interval(hours => batiment_reglage('construction_h')::integer),
         deplacee_le = now()
   where id = b.id;
  if v_prix > 0 then update joueurs set lingots = lingots - v_prix where id = v_uid; end if;
  return mes_batiments();
end;
$$;

-- construire : le type de plus
select pg_temp.retoucher('public.batiment_construire(text, text)', 's3-27a',
  $a$if p_type not in ('fonderie', 'forteresse', 'centre', 'banque', 'radar') then raise exception 'Bâtiment inconnu'; end if;$a$,
  $b$if p_type not in ('fonderie', 'forteresse', 'centre', 'banque', 'radar', 'artillerie') then raise exception 'Bâtiment inconnu'; end if;   -- s3-27a$b$);
select pg_temp.retoucher('public.batiment_construire(text, text)', 's3-27b',
  $a$  else
    if v_nf = 0 then raise exception 'Il te faut d''abord une Fonderie'; end if;
    if (select count(*)$a$,
  $b$  elsif p_type = 'artillerie' then   -- s3-27b : l'Artillerie
    if not artilleries_ouvertes() then raise exception 'L''Artillerie n''est pas encore ouverte'; end if;
    if v_nf = 0 then raise exception 'Il te faut d''abord une Fonderie'; end if;
    if exists (select 1 from batiments b where b.joueur_id = v_uid and b.type = 'artillerie') then
      raise exception 'Tu as déjà une Artillerie';
    end if;
    v_prix := coalesce(batiment_reglage('artillerie_prix'), 20);
    v := lingots_figer(v_uid);
    if v < v_prix then raise exception 'Il te faut % lingots (tu en as %)', v_prix::integer, floor(v)::integer; end if;
    update joueurs set lingots = lingots - v_prix where id = v_uid;
  else
    if v_nf = 0 then raise exception 'Il te faut d''abord une Fonderie'; end if;
    if (select count(*)$b$);

-- annuler : le remboursement de l'Artillerie ; une Centrale rend son prix à la caisse du clan
select pg_temp.retoucher('public.batiment_annuler(text, text)', 's3-27c',
  $a$    when 'radar'      then coalesce(batiment_reglage('radar_prix'), 30)   -- s2-115$a$,
  $b$    when 'radar'      then coalesce(batiment_reglage('radar_prix'), 30)   -- s2-115
    when 'artillerie' then coalesce(batiment_reglage('artillerie_prix'), 20)   -- s3-27c$b$);
select pg_temp.retoucher('public.batiment_annuler(text, text)', 's3-27d',
  $a$  if b.type in ('forteresse', 'banque', 'fonderie') and b.deplacee_le is not null then$a$,
  $b$  if b.type in ('forteresse', 'banque', 'fonderie', 'artillerie') and b.deplacee_le is not null then   -- s3-27d$b$);
select pg_temp.retoucher('public.batiment_annuler(text, text)', 's3-27e',
  $a$  v := lingots_figer(v_uid);          -- la réserve à jour avant de rembourser$a$,
  $b$  if b.type = 'centrale' then   -- s3-27e : le prix payé retourne dans la caisse du clan
    delete from batiments where id = b.id;
    if b.clan_id is not null and coalesce(b.contenu, 0) > 0 then
      insert into clan_caisses (clan_id, lingots) values (b.clan_id, floor(b.contenu)::integer)
      on conflict (clan_id) do update set lingots = clan_caisses.lingots + excluded.lingots;
    end if;
    return jsonb_build_object('type', 'centrale', 'rembourse', floor(coalesce(b.contenu, 0))::integer, 'caisse', true);
  end if;
  v := lingots_figer(v_uid);          -- la réserve à jour avant de rembourser$b$);

-- ce que je vois : l'Artillerie est secrète, sauf 24 h après avoir tiré, ou pour un Radar
select pg_temp.retoucher('public.batiments_visibles()', 's3-27f',
  $a$     and (b.type not in ('centre', 'banque') or b.joueur_id = auth.uid()$a$,
  $b$     and (b.type not in ('centre', 'banque', 'artillerie') or b.joueur_id = auth.uid()
          or (b.type = 'artillerie' and b.devoile_jusqua > now())   -- s3-27f$b$);
select pg_temp.retoucher('public.batiments_visibles()', 's3-27g',
  $a$          or (b.type in ('centre', 'banque') /* s2-117 */ and radar_voit(auth.uid(), b.commune_code, b.joueur_id)));$a$,
  $b$          or (b.type in ('centre', 'banque', 'artillerie') /* s2-117, s3-27g */ and radar_voit(auth.uid(), b.commune_code, b.joueur_id)));$b$);
select pg_temp.retoucher('public.batiments_autres(text, text[], text, text, integer, integer)', 's3-27h',
  $a$       and (p_type is null or b.type = p_type)$a$,
  $b$       and (b.type <> 'artillerie' or b.devoile_jusqua > now() or radar_voit(v_uid, b.commune_code, b.joueur_id))   -- s3-27h
       and (p_type is null or b.type = p_type)$b$);

-- mes bâtiments : l'Artillerie et ses réglages
select pg_temp.retoucher('public.mes_batiments()', 's3-27i',
  $a$|| radar_infos(v_uid);$a$,
  $b$|| radar_infos(v_uid) || artillerie_infos(v_uid);   -- s3-27i$b$);

-- le siège : l'Artillerie remplace le malus de distance
select pg_temp.retoucher('public.siege_mult(uuid, text)', 's3-27j',
  $a$  v_m := case when v_proches <= 0 then siege_n('prox_aucune') when$a$,
  $b$  v_m := case when v_proches <= 0 then (case when artillerie_couvre(p_uid, p_code) is not null   -- s3-27j : l'Artillerie
                                              then round(1 / (1 + coalesce(batiment_reglage('artillerie_cout'), 0.1)), 3)
                                              else siege_n('prox_aucune') end) when$b$);
select pg_temp.retoucher('public.siege_apercu(text)', 's3-27k',
  $a$    'pose', siege_n('pose'),$a$,
  $b$    'artillerie', case when communes_proches(v_uid, p_code, 20) <= 0 then artillerie_couvre(v_uid, p_code) end,   -- s3-27k
    'pose', siege_n('pose'),$b$);
select pg_temp.retoucher('public.siege_vague(text, integer)', 's3-27l',
  $a$  if not front_energie_depenser(v_uid, v_cout) then raise exception 'Énergie insuffisante (% requise)', v_cout; end if;$a$,
  $b$  if not front_energie_depenser(v_uid, v_cout) then raise exception 'Énergie insuffisante (% requise)', v_cout; end if;
  if communes_proches(v_uid, p_code, 20) <= 0 and artillerie_couvre(v_uid, p_code) is not null then   -- s3-27l : elle a tiré, elle se montre
    update batiments set devoile_jusqua = now() + make_interval(hours => coalesce(batiment_reglage('artillerie_devoile_h'), 24)::integer)
     where joueur_id = v_uid and type = 'artillerie';
  end if;$b$);

-- la bombe souffle aussi l'Artillerie et la Centrale
select pg_temp.retoucher('public.bombe_lacher(text)', 's3-27m',
  $a$  -- s2-104 : les Banques de la zone perdent$a$,
  $b$  delete from batiments b using communes k   -- s3-27m : l'Artillerie et la Centrale de clan sont soufflées
   where k.code = b.commune_code and b.type in ('artillerie', 'centrale') and dist_km(k.latitude, k.longitude, v_c.lat, v_c.lon) <= v_r;

  -- s2-104 : les Banques de la zone perdent$b$);

-- 5. la Centrale de clan
create or replace function public.centrale_n(p_cle text)
returns numeric language sql stable security definer set search_path to 'public' as $$
  select (select (c.valeur::jsonb ->> p_cle)::numeric from config_jeu c where c.cle = 'centrale_clan');
$$;
create or replace function public.centrale_ouverte()
returns boolean language sql stable security definer set search_path to 'public' as $$
  select batiments_ouverts() and clans_ouverts() and coalesce(centrale_n('ouverte'), 0) >= 1;
$$;
create or replace function public.clan_de(p_uid uuid)
returns uuid language sql stable security definer set search_path to 'public' as $$
  select m.clan_id from clan_membres m where m.joueur_id = p_uid limit 1;
$$;
-- membres actifs : ont joué dans les 7 derniers jours (comme le classement des clans)
create or replace function public.clan_actifs(p_clan uuid)
returns integer language sql stable security definer set search_path to 'public' as $$
  select count(*)::integer from clan_membres m
   where m.clan_id = p_clan and exists (select 1 from jours_joues d where d.joueur_id = m.joueur_id and d.jour >= quete_jour() - 6);
$$;
create or replace function public.centrale_prix(p_clan uuid)
returns integer language sql stable security definer set search_path to 'public' as $$
  select (coalesce(centrale_n('prix_actif'), 10) * greatest(clan_actifs(p_clan), coalesce(centrale_n('actifs_min'), 3)::integer))::integer;
$$;

create or replace function public.clan_centrale_etat()
returns jsonb language plpgsql stable security definer set search_path to 'public' as $$
declare v_uid uuid := auth.uid(); v_clan uuid; v_depuis timestamptz; v_anc integer; b record; v_r record;
begin
  if v_uid is null then raise exception 'Non connecte'; end if;
  v_clan := clan_de(v_uid);
  if v_clan is null or not centrale_ouverte() then
    return jsonb_build_object('ouverte', centrale_ouverte(), 'clan', v_clan is not null);
  end if;
  select m.depuis into v_depuis from clan_membres m where m.joueur_id = v_uid and m.clan_id = v_clan;
  v_anc := coalesce(centrale_n('anciennete_h'), 48)::integer;
  select x.*, c.nom, c.departement, j.pseudo into b
    from batiments x join communes c on c.code = x.commune_code left join joueurs j on j.id = x.joueur_id
   where x.type = 'centrale' and x.clan_id = v_clan;
  select * into v_r from centrale_ramassages r where r.joueur_id = v_uid and r.jour = quete_jour();
  return jsonb_build_object(
    'ouverte', true, 'clan', true,
    'je_gere', clan_que_je_gere(v_uid) = v_clan,
    'part', coalesce(centrale_n('part'), 8)::integer,
    'prix', centrale_prix(v_clan),
    'prix_actif', coalesce(centrale_n('prix_actif'), 10)::integer,
    'actifs', clan_actifs(v_clan),
    'actifs_min', coalesce(centrale_n('actifs_min'), 3)::integer,
    'anciennete_h', v_anc,
    'caisse', coalesce((select k.lingots from clan_caisses k where k.clan_id = v_clan), 0),
    'mes_lingots', floor(coalesce(lingots_lire(v_uid), 0))::integer,
    'construction_h', batiment_reglage('construction_h')::integer,
    'centrale', case when b.id is not null then jsonb_build_object('code', b.commune_code, 'nom', b.nom, 'dept', b.departement,
                       'pret', b.pret_le <= now(), 'pret_le', b.pret_le, 'poseur', b.pseudo, 'a_moi', b.joueur_id = v_uid,
                       'style', coalesce(b.style, batiment_styles() -> 'centrale' ->> 0)) end,
    'ramasse', v_r.joueur_id is not null, 'ramasse_energie', coalesce(v_r.energie, 0),
    'ancien_dans', greatest(0, ceil(extract(epoch from (v_depuis + make_interval(hours => v_anc) - now()))))::integer,
    'dons', coalesce((select jsonb_agg(jsonb_build_object('pseudo', j.pseudo, 'lingots', d.lingots, 'le', d.le) order by d.le desc)
                        from (select * from clan_dons where clan_id = v_clan order by le desc limit 8) d left join joueurs j on j.id = d.joueur_id), '[]'::jsonb));
end;
$$;

create or replace function public.clan_centrale_donner(p_lingots integer)
returns jsonb language plpgsql security definer set search_path to 'public' as $$
declare v_uid uuid := auth.uid(); v_clan uuid; v numeric; v_caisse integer; v_prix integer; v_n integer;
begin
  if v_uid is null then raise exception 'Non connecte'; end if;
  if not centrale_ouverte() then raise exception 'La Centrale de clan n''est pas encore ouverte'; end if;
  v_clan := clan_de(v_uid);
  if v_clan is null then raise exception 'Il faut être dans un clan'; end if;
  if p_lingots is null or p_lingots < 1 then raise exception 'Donne au moins 1 lingot'; end if;
  if exists (select 1 from batiments b where b.type = 'centrale' and b.clan_id = v_clan) then
    raise exception 'Ton clan a déjà sa Centrale';
  end if;
  perform 1 from joueurs where id = v_uid for update;
  insert into clan_caisses (clan_id) values (v_clan) on conflict (clan_id) do nothing;
  select lingots into v_caisse from clan_caisses where clan_id = v_clan for update;
  v_prix := centrale_prix(v_clan);
  v_n := least(p_lingots, greatest(0, v_prix - v_caisse));
  if v_n < 1 then raise exception 'La caisse est pleine : le chef peut poser la Centrale'; end if;
  v := lingots_figer(v_uid);
  if v < v_n then raise exception 'Il te faut % lingots (tu en as %)', v_n, floor(v)::integer; end if;
  update joueurs set lingots = lingots - v_n where id = v_uid;
  update clan_caisses set lingots = lingots + v_n where clan_id = v_clan;
  insert into clan_dons (clan_id, joueur_id, lingots) values (v_clan, v_uid, v_n);
  return clan_centrale_etat() || jsonb_build_object('donne', v_n);
end;
$$;

create or replace function public.clan_centrale_construire(p_code text)
returns jsonb language plpgsql security definer set search_path to 'public' as $$
declare v_uid uuid := auth.uid(); v_clan uuid; v_caisse integer; v_prix integer;
begin
  if v_uid is null then raise exception 'Non connecte'; end if;
  if not centrale_ouverte() then raise exception 'La Centrale de clan n''est pas encore ouverte'; end if;
  v_clan := clan_de(v_uid);
  if v_clan is null or clan_que_je_gere(v_uid) is distinct from v_clan then
    raise exception 'Seuls le chef et un bras droit peuvent poser la Centrale';
  end if;
  if not exists (select 1 from possessions p where p.commune_code = p_code and p.joueur_id = v_uid) then
    raise exception 'Pose-la sur une de tes communes';
  end if;
  if clan_actifs(v_clan) < coalesce(centrale_n('actifs_min'), 3) then
    raise exception 'Il faut % membres actifs (joué dans les 7 derniers jours)', coalesce(centrale_n('actifs_min'), 3)::integer;
  end if;
  perform 1 from clans where id = v_clan for update;
  if exists (select 1 from batiments b where b.type = 'centrale' and b.clan_id = v_clan) then
    raise exception 'Ton clan a déjà sa Centrale';
  end if;
  if exists (select 1 from batiments b where b.commune_code = p_code and b.type = 'centrale') then
    raise exception 'Il y a déjà une Centrale ici';
  end if;
  select coalesce(lingots, 0) into v_caisse from clan_caisses where clan_id = v_clan for update;
  v_prix := centrale_prix(v_clan);
  if coalesce(v_caisse, 0) < v_prix then raise exception 'La caisse du clan a % lingots sur %', coalesce(v_caisse, 0), v_prix; end if;
  update clan_caisses set lingots = lingots - v_prix where clan_id = v_clan;
  insert into batiments (joueur_id, commune_code, type, pret_le, clan_id, contenu)
  values (v_uid, p_code, 'centrale', now() + make_interval(hours => batiment_reglage('construction_h')::integer), v_clan, v_prix);
  return clan_centrale_etat();
end;
$$;

create or replace function public.clan_centrale_ramasser()
returns jsonb language plpgsql security definer set search_path to 'public' as $$
declare v_uid uuid := auth.uid(); v_clan uuid; v_depuis timestamptz; v_part integer; v numeric; v_reel integer;
begin
  if v_uid is null then raise exception 'Non connecte'; end if;
  if not centrale_ouverte() then raise exception 'La Centrale de clan n''est pas encore ouverte'; end if;
  v_clan := clan_de(v_uid);
  if v_clan is null then raise exception 'Il faut être dans un clan'; end if;
  if not exists (select 1 from batiments b where b.type = 'centrale' and b.clan_id = v_clan and b.pret_le <= now()) then
    raise exception 'Ton clan n''a pas de Centrale prête';
  end if;
  select m.depuis into v_depuis from clan_membres m where m.joueur_id = v_uid and m.clan_id = v_clan;
  if v_depuis > now() - make_interval(hours => coalesce(centrale_n('anciennete_h'), 48)::integer) then
    raise exception 'Ta part arrive % h après ton entrée dans le clan', coalesce(centrale_n('anciennete_h'), 48)::integer;
  end if;
  perform 1 from joueurs where id = v_uid for update;
  if exists (select 1 from centrale_ramassages r where r.joueur_id = v_uid and r.jour = quete_jour()) then
    raise exception 'Part déjà ramassée aujourd''hui, reviens demain';
  end if;
  v_part := coalesce(centrale_n('part'), 8)::integer;
  select front_energie_lire(j.front_energie, j.front_energie_maj) into v from joueurs j where j.id = v_uid;
  v_reel := greatest(0, least(front_energie_reglage('plafond'), floor(v + v_part)) - floor(v))::integer;
  update joueurs set front_energie = least(front_energie_reglage('plafond'), v + v_part), front_energie_maj = now() where id = v_uid;
  insert into centrale_ramassages (joueur_id, jour, clan_id, energie) values (v_uid, quete_jour(), v_clan, v_reel);
  return clan_centrale_etat() || jsonb_build_object('gagne', v_reel, 'part', v_part, 'plafond', front_energie_reglage('plafond')::integer);
end;
$$;

-- celui qui a posé la Centrale quitte le clan : elle disparaît
create or replace function public.centrale_poseur_parti()
returns trigger language plpgsql security definer set search_path to 'public' as $$
begin
  delete from batiments where type = 'centrale' and joueur_id = old.joueur_id and clan_id = old.clan_id;
  return null;
end;
$$;
drop trigger if exists trg_centrale_poseur on public.clan_membres;
create trigger trg_centrale_poseur after delete on public.clan_membres
  for each row execute function public.centrale_poseur_parti();

-- 6. les ordres du chef
create or replace function public.ordres_n(p_cle text)
returns numeric language sql stable security definer set search_path to 'public' as $$
  select (select (c.valeur::jsonb ->> p_cle)::numeric from config_jeu c where c.cle = 'ordres_chef');
$$;
create or replace function public.ordres_ouverts()
returns boolean language sql stable security definer set search_path to 'public' as $$
  select clans_ouverts() and coalesce(ordres_n('ouverts'), 0) >= 1;
$$;

create or replace function public.clan_ordres_etat()
returns jsonb language plpgsql stable security definer set search_path to 'public' as $$
declare v_uid uuid := auth.uid(); v_clan uuid; v_appel integer := coalesce(ordres_n('appel_h'), 3)::integer;
begin
  if v_uid is null then raise exception 'Non connecte'; end if;
  v_clan := clan_de(v_uid);
  if v_clan is null or not ordres_ouverts() then return jsonb_build_object('ouverts', ordres_ouverts(), 'clan', v_clan is not null, 'ordres', '[]'::jsonb); end if;
  return jsonb_build_object(
    'ouverts', true, 'clan', true,
    'je_gere', clan_que_je_gere(v_uid) = v_clan,
    'max', coalesce(ordres_n('max'), 3)::integer,
    'duree_h', coalesce(ordres_n('duree_h'), 24)::integer,
    'appel_h', v_appel,
    'ordres', coalesce((
      select jsonb_agg(jsonb_build_object(
               'id', o.id, 'code', o.commune_code, 'nom', c.nom, 'dept', c.departement, 'tier', c.tier,
               'lat', c.latitude, 'lon', c.longitude,
               'proprio', j.pseudo, 'prise', p.joueur_id is not null and meme_clan(v_uid, p.joueur_id),
               'a_moi', p.joueur_id = v_uid,
               'pose_par', pp.pseudo, 'pose_le', o.pose_le, 'fin', o.fin, 'appel_le', o.appel_le,
               'appel_dans', case when o.appel_le is null then 0
                                  else greatest(0, ceil(extract(epoch from (o.appel_le + make_interval(hours => v_appel) - now()))))::integer end,
               'membres_siege', (select count(*) from front_sieges s join clan_membres m on m.joueur_id = s.attaquant and m.clan_id = v_clan
                                  where s.commune_code = o.commune_code and s.fini_le is null),
               'mon_siege', exists (select 1 from front_sieges s where s.commune_code = o.commune_code and s.attaquant = v_uid and s.fini_le is null))
             order by o.pose_le)
        from clan_ordres o
        join communes c on c.code = o.commune_code
        left join possessions p on p.commune_code = o.commune_code
        left join joueurs j on j.id = p.joueur_id
        left join joueurs pp on pp.id = o.pose_par
       where o.clan_id = v_clan and not o.retire and o.fin > now()), '[]'::jsonb));
end;
$$;

create or replace function public.clan_ordre_poser(p_code text)
returns jsonb language plpgsql security definer set search_path to 'public' as $$
declare v_uid uuid := auth.uid(); v_clan uuid; po possessions;
begin
  if v_uid is null then raise exception 'Non connecte'; end if;
  if not ordres_ouverts() then raise exception 'Les ordres du chef ne sont pas encore ouverts'; end if;
  v_clan := clan_de(v_uid);
  if v_clan is null or clan_que_je_gere(v_uid) is distinct from v_clan then
    raise exception 'Seuls le chef et un bras droit donnent les ordres';
  end if;
  if not exists (select 1 from communes c where c.code = p_code) then raise exception 'Commune inconnue'; end if;
  select * into po from possessions where commune_code = p_code;
  if po.joueur_id is null then raise exception 'Cette commune n''appartient à personne : rien à assiéger'; end if;
  if meme_clan(v_uid, po.joueur_id) then raise exception 'Cette commune est déjà à ton clan'; end if;
  perform 1 from clans where id = v_clan for update;
  if exists (select 1 from clan_ordres o where o.clan_id = v_clan and o.commune_code = p_code and not o.retire and o.fin > now()) then
    raise exception 'C''est déjà une cible du clan';
  end if;
  if (select count(*) from clan_ordres o where o.clan_id = v_clan and not o.retire and o.fin > now()) >= coalesce(ordres_n('max'), 3) then
    raise exception 'Déjà % cibles : retires-en une', coalesce(ordres_n('max'), 3)::integer;
  end if;
  insert into clan_ordres (clan_id, commune_code, pose_par, fin)
  values (v_clan, p_code, v_uid, now() + make_interval(hours => coalesce(ordres_n('duree_h'), 24)::integer));
  return clan_ordres_etat();
end;
$$;

create or replace function public.clan_ordre_retirer(p_id bigint)
returns jsonb language plpgsql security definer set search_path to 'public' as $$
declare v_uid uuid := auth.uid(); v_clan uuid;
begin
  if v_uid is null then raise exception 'Non connecte'; end if;
  v_clan := clan_de(v_uid);
  if v_clan is null or clan_que_je_gere(v_uid) is distinct from v_clan then
    raise exception 'Seuls le chef et un bras droit donnent les ordres';
  end if;
  update clan_ordres set retire = true where id = p_id and clan_id = v_clan;
  return clan_ordres_etat();
end;
$$;

create or replace function public.clan_ordre_appel(p_id bigint)
returns jsonb language plpgsql security definer set search_path to 'public' as $$
declare v_uid uuid := auth.uid(); v_clan uuid; o record; v_pseudo text; v_tag text; v_n integer := 0; m record;
begin
  if v_uid is null then raise exception 'Non connecte'; end if;
  if not ordres_ouverts() then raise exception 'Les ordres du chef ne sont pas encore ouverts'; end if;
  v_clan := clan_de(v_uid);
  if v_clan is null or clan_que_je_gere(v_uid) is distinct from v_clan then
    raise exception 'Seuls le chef et un bras droit lancent un appel';
  end if;
  select x.*, c.nom, c.departement into o from clan_ordres x join communes c on c.code = x.commune_code
   where x.id = p_id and x.clan_id = v_clan and not x.retire and x.fin > now() for update of x;
  if o.id is null then raise exception 'Cette cible n''existe plus'; end if;
  if o.appel_le is not null and o.appel_le > now() - make_interval(hours => coalesce(ordres_n('appel_h'), 3)::integer) then
    raise exception 'Un appel toutes les % h par cible', coalesce(ordres_n('appel_h'), 3)::integer;
  end if;
  update clan_ordres set appel_le = now() where id = o.id;
  select pseudo into v_pseudo from joueurs where id = v_uid;
  select tag into v_tag from clans where id = v_clan;
  for m in select joueur_id from clan_membres where clan_id = v_clan and joueur_id <> v_uid loop
    v_n := v_n + least(1, notifier_joueur(m.joueur_id, '📯 Appel à l''assaut : ' || o.nom,
             coalesce(v_pseudo, 'Ton chef') || ' appelle ' || coalesce('[' || v_tag || ']', 'le clan') || ' à assiéger ' || o.nom || ' (' || o.departement || ').',
             './?onglet=combat', 'ordre-' || o.id));
  end loop;
  return clan_ordres_etat() || jsonb_build_object('prevenus', v_n);
end;
$$;

-- 7. droits : les joueurs n'appellent que les fonctions du jeu
revoke all on function public.artillerie_couvre(uuid, text), public.artillerie_infos(uuid), public.centrale_n(text),
  public.clan_de(uuid), public.clan_actifs(uuid), public.centrale_prix(uuid), public.centrale_poseur_parti(),
  public.ordres_n(text) from public, anon, authenticated;
revoke all on function public.artilleries_ouvertes(), public.artillerie_deplacer(text, text), public.centrale_ouverte(),
  public.clan_centrale_etat(), public.clan_centrale_donner(integer), public.clan_centrale_construire(text),
  public.clan_centrale_ramasser(), public.ordres_ouverts(), public.clan_ordres_etat(), public.clan_ordre_poser(text),
  public.clan_ordre_retirer(bigint), public.clan_ordre_appel(bigint) from public, anon;
grant execute on function public.artilleries_ouvertes(), public.artillerie_deplacer(text, text), public.centrale_ouverte(),
  public.clan_centrale_etat(), public.clan_centrale_donner(integer), public.clan_centrale_construire(text),
  public.clan_centrale_ramasser(), public.ordres_ouverts(), public.clan_ordres_etat(), public.clan_ordre_poser(text),
  public.clan_ordre_retirer(bigint), public.clan_ordre_appel(bigint) to authenticated;

commit;

-- Contrôle : false | false | false | 7 | 11 retouches
select artilleries_ouvertes() as artillerie, centrale_ouverte() as centrale, ordres_ouverts() as ordres,
       (select count(*) from unnest(array['fonderie','forteresse','centre','banque','radar','artillerie','centrale']) t
         where pg_get_constraintdef((select oid from pg_constraint where conname = 'batiments_type_check')) like '%' || t || '%') as types,
       (select count(*) from unnest(array[
          position('s3-27a' in pg_get_functiondef('public.batiment_construire(text, text)'::regprocedure)),
          position('s3-27b' in pg_get_functiondef('public.batiment_construire(text, text)'::regprocedure)),
          position('s3-27c' in pg_get_functiondef('public.batiment_annuler(text, text)'::regprocedure)),
          position('s3-27e' in pg_get_functiondef('public.batiment_annuler(text, text)'::regprocedure)),
          position('s3-27f' in pg_get_functiondef('public.batiments_visibles()'::regprocedure)),
          position('s3-27h' in pg_get_functiondef('public.batiments_autres(text, text[], text, text, integer, integer)'::regprocedure)),
          position('s3-27i' in pg_get_functiondef('public.mes_batiments()'::regprocedure)),
          position('s3-27j' in pg_get_functiondef('public.siege_mult(uuid, text)'::regprocedure)),
          position('s3-27k' in pg_get_functiondef('public.siege_apercu(text)'::regprocedure)),
          position('s3-27l' in pg_get_functiondef('public.siege_vague(text, integer)'::regprocedure)),
          position('s3-27m' in pg_get_functiondef('public.bombe_lacher(text)'::regprocedure))]) x where x > 0) as retouches;

-- Le jour J (après le « ok » de Nataël, chacun séparément) :
-- update public.config_jeu set valeur = ((valeur::jsonb) || '{"artilleries_ouvertes": 1}'::jsonb)::text where cle = 'batiments';
-- update public.config_jeu set valeur = ((valeur::jsonb) || '{"ouverte": 1}'::jsonb)::text where cle = 'centrale_clan';
-- update public.config_jeu set valeur = ((valeur::jsonb) || '{"ouverts": 1}'::jsonb)::text where cle = 'ordres_chef';
-- Pour éteindre : la même ligne avec 0.
