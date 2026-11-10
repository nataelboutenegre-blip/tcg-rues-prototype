-- s3-7-siege.sql (10/11/2026) : le siège à la place des dés, pour la saison 3 (décidé le 10/11).
-- ÉTEINT tant que config_jeu 'siege' a "actif": 0 : aucune règle du Front ne change.
-- Le jour J (après la clôture de la saison 2) : update public.config_jeu
--   set valeur = (valeur::jsonb || '{"actif": 1}'::jsonb)::text where cle = 'siege';
-- Règles : claude/idee-siege.md (v2 du 10/11). Tous les chiffres sont dans config_jeu 'siege'.
--
-- Principe
--   * poser un siège coûte 2 ⚡ ; chaque énergie envoyée fait 10 points de dégâts × aléa 80-120 %
--     × proximité (0,8 sans commune à soi à moins de 20 km, 1,1 avec deux ou plus) × bombe (1,15)
--     × appui d'une Forteresse à soi à moins de 20 km (1,1) × débutant (1,5 hors épique et légendaire) ;
--   * la garnison est un bouclier (10 points par énergie) à casser d'abord ;
--   * la commune tombe quand la jauge atteint sa résistance (55, 55, 65, 125, 250 ; × 1,5 avec une
--     Forteresse ; jusqu'à −15 % face à un rebelle) ;
--   * siège éclair tant que personne ne défend ; siège long dès que le propriétaire renforce, qu'il y a
--     une garnison ou un bâtiment visible, et toujours pour une légendaire : la jauge ne peut alors
--     monter plus vite que la résistance sur 1 h, 1 h 30, 2 h, 6 h ou 15 h (10 % tout de suite) ;
--     l'énergie au-delà attend (« en attente ») et part toute seule (tâche toutes les 5 min) ;
--   * le défenseur renforce : son énergie fait reculer la jauge, +20 % à domicile ;
--   * le siège tombe après 24 h sans vague ; défense réussie (+10 au classement, quête, 10 TP)
--     si le défenseur a renforcé ou si sa garnison a encaissé ;
--   * 8 sièges longs en même temps, +1 par type de bâtiment prêt (12 au plus) ; sièges éclair illimités.

begin;

-- 1. les réglages
insert into public.config_jeu(cle, valeur) values ('siege', jsonb_build_object(
  'actif', 0,
  'pose', 2,
  'points_par_energie', 10,
  'alea_min', 0.8, 'alea_max', 1.2,
  'resistance', jsonb_build_object('commun', 55, 'peucommun', 55, 'rare', 65, 'epique', 125, 'legendaire', 250),
  'duree_long_min', jsonb_build_object('commun', 60, 'peucommun', 90, 'rare', 120, 'epique', 360, 'legendaire', 900),
  'eclair_min', jsonb_build_object('epique', 60),
  'depart_long', 0.1,
  'defense_bonus', 1.2,
  'bouclier_par_energie', 10,
  'forteresse_mult', 1.5,
  'appui_mult', 1.1,
  'prox_aucune', 0.8, 'prox_deux', 1.1,
  'bombe_mult', 1.15,
  'debutant_mult', 1.5,
  'expiration_h', 24,
  'immunite_h', 3,
  'places_base', 8, 'places_par_type', 1, 'places_max', 12,
  'vague_max', 60
)::text)
on conflict (cle) do nothing;

create or replace function public.siege_cfg() returns jsonb
language sql stable security definer set search_path to 'public' as $$
  select coalesce((select c.valeur::jsonb from config_jeu c where c.cle = 'siege'), '{}'::jsonb);
$$;

create or replace function public.siege_actif() returns boolean
language sql stable security definer set search_path to 'public' as $$
  select coalesce((siege_cfg()->>'actif')::int, 0) = 1;
$$;

create or replace function public.siege_n(p_cle text) returns numeric
language sql stable security definer set search_path to 'public' as $$
  select (siege_cfg()->>p_cle)::numeric;
$$;

create or replace function public.siege_tier_n(p_cle text, p_tier text) returns numeric
language sql stable security definer set search_path to 'public' as $$
  select (siege_cfg()->p_cle->>p_tier)::numeric;
$$;

-- 2. les sièges (lecture seulement par les fonctions ci-dessous)
create table if not exists public.front_sieges (
  id bigserial primary key,
  attaquant uuid not null,
  commune_code text not null references public.communes(code),
  defenseur uuid,                                   -- propriétaire au moment de la pose
  tier text not null,
  degats numeric not null default 0,               -- la jauge, en points
  envoyes_long numeric not null default 0,         -- dégâts (bouclier compris) depuis que le siège est long
  attente integer not null default 0,              -- énergie payée qui attend le rythme d'un siège long
  long_depuis timestamptz,                          -- null : siège éclair
  defendu boolean not null default false,           -- le défenseur a renforcé
  garnison_touchee boolean not null default false,  -- la garnison a encaissé
  energie_mise integer not null default 0,
  energie_defense integer not null default 0,
  alerte_danger boolean not null default false,     -- la notification « en danger » est partie
  cree_le timestamptz not null default now(),
  derniere_vague timestamptz not null default now(),
  fini_le timestamptz,
  resultat text                                     -- conquise, tombee, abandon, prise_par_autre, proprio_change, liberee
);
create unique index if not exists front_sieges_actif on public.front_sieges(attaquant, commune_code) where fini_le is null;
create index if not exists front_sieges_commune on public.front_sieges(commune_code) where fini_le is null;
create index if not exists front_sieges_defenseur on public.front_sieges(defenseur) where fini_le is null;
alter table public.front_sieges enable row level security;
revoke all on public.front_sieges from anon, authenticated;

-- la garnison : les points déjà encaissés sur l'énergie entamée (le bouclier est en points, la garnison en énergie)
alter table public.front_garnisons add column if not exists entame numeric not null default 0;

-- 3. le calcul
-- résistance face à cet attaquant : base × Forteresse × (1 − rébellion)
create or replace function public.siege_resistance(p_code text, p_attaquant uuid) returns numeric
language sql stable security definer set search_path to 'public' as $$
  select siege_tier_n('resistance', c.tier)
         * case when exists (select 1 from batiments b
                              where b.commune_code = p_code and b.type = 'forteresse'
                                and b.joueur_id = po.joueur_id and b.pret_le <= now())
                then siege_n('forteresse_mult') else 1 end
         * (1 - coalesce((select rebellion_pct(r.fonds) / 100.0
                            from rebellions r
                           where r.financeur = p_attaquant and r.commune_code = p_code and r.victime = po.joueur_id
                             and r.fin > now() and r.fonds > 0 and r.etouffee_le is null
                           limit 1), 0))
    from communes c join possessions po on po.commune_code = c.code
   where c.code = p_code;
$$;

-- multiplicateur des dégâts de cet attaquant sur cette commune
create or replace function public.siege_mult(p_uid uuid, p_code text) returns numeric
language plpgsql stable security definer set search_path to 'public' as $$
declare
  v_proches integer := communes_proches(p_uid, p_code, 20);
  v_m numeric := 1;
  v_tier text;
begin
  select tier into v_tier from communes where code = p_code;
  v_m := case when v_proches <= 0 then siege_n('prox_aucune') when v_proches = 1 then 1 else siege_n('prox_deux') end;
  if exists (select 1 from bombes z join communes c on c.code = p_code
              where z.fin > now() and dist_km(z.lat, z.lon, c.latitude, c.longitude) <= z.rayon_km) then
    v_m := v_m * siege_n('bombe_mult');
  end if;
  if exists (select 1 from batiments b join communes f on f.code = b.commune_code join communes c on c.code = p_code
              where b.joueur_id = p_uid and b.type = 'forteresse' and b.pret_le <= now() and b.commune_code <> p_code
                and dist_km(f.latitude, f.longitude, c.latitude, c.longitude) <= batiment_reglage('forteresse_rayon_km')) then
    v_m := v_m * siege_n('appui_mult');
  end if;
  if debutant_actif(p_uid) and v_tier not in ('epique', 'legendaire') and not garnison_active(p_code) then
    v_m := v_m * siege_n('debutant_mult');
  end if;
  return v_m;
end; $$;

-- énergie de garnison du propriétaire actuel
create or replace function public.siege_garnison(p_code text) returns integer
language sql stable security definer set search_path to 'public' as $$
  select coalesce((select g.energie from front_garnisons g
                     join possessions po on po.commune_code = g.commune_code and po.joueur_id = g.joueur_id
                    where g.commune_code = p_code), 0);
$$;

-- un bâtiment visible de l'attaquant (pas la Banque, secrète) rend le siège long
create or replace function public.siege_batiment_visible(p_code text, p_proprio uuid) returns boolean
language sql stable security definer set search_path to 'public' as $$
  select exists (select 1 from batiments b
                  where b.commune_code = p_code and b.joueur_id = p_proprio
                    and b.pret_le <= now() and b.type <> 'banque');
$$;

create or replace function public.siege_doit_etre_long(p_code text, p_tier text, p_proprio uuid, p_defendu boolean) returns boolean
language sql stable security definer set search_path to 'public' as $$
  select p_tier = 'legendaire' or coalesce(p_defendu, false)
      or siege_garnison(p_code) > 0 or siege_batiment_visible(p_code, p_proprio);
$$;

-- places de sièges longs : 8, +1 par type de bâtiment prêt, 12 au plus
create or replace function public.siege_places(p_uid uuid) returns integer
language sql stable security definer set search_path to 'public' as $$
  select least(siege_n('places_max'),
               siege_n('places_base') + siege_n('places_par_type')
                 * (select count(distinct b.type) from batiments b where b.joueur_id = p_uid and b.pret_le <= now()))::integer;
$$;

create or replace function public.siege_longs_en_cours(p_uid uuid) returns integer
language sql stable security definer set search_path to 'public' as $$
  select count(*)::integer from front_sieges s where s.attaquant = p_uid and s.fini_le is null and s.long_depuis is not null;
$$;

-- jusqu'où la jauge peut monter maintenant (siège long, ou épique en éclair) : null = pas de limite
create or replace function public.siege_plafond(p_id bigint) returns numeric
language plpgsql stable security definer set search_path to 'public' as $$
declare s front_sieges; v_r numeric; v_d numeric; v_debut timestamptz;
begin
  select * into s from front_sieges where id = p_id;
  if s.long_depuis is not null then
    v_d := siege_tier_n('duree_long_min', s.tier); v_debut := s.long_depuis;
  else
    v_d := siege_tier_n('eclair_min', s.tier); v_debut := s.cree_le;
    if v_d is null then return null; end if;
  end if;
  v_r := siege_resistance(s.commune_code, s.attaquant);
  return v_r * (siege_n('depart_long') + extract(epoch from now() - v_debut) / 60.0 / v_d);
end; $$;

-- rendre de l'énergie (sans dépasser le plafond de la réserve)
create or replace function public.siege_rendre_energie(p_uid uuid, p_n integer) returns void
language plpgsql security definer set search_path to 'public' as $$
declare v numeric;
begin
  if coalesce(p_n, 0) <= 0 then return; end if;
  select front_energie_lire(front_energie, front_energie_maj) into v from joueurs where id = p_uid for update;
  if v is null then return; end if;
  update joueurs set front_energie = greatest(v, least(front_energie_reglage('plafond'), v + p_n)), front_energie_maj = now()
   where id = p_uid;
end; $$;

-- fermer un siège (rend l'énergie en attente) ; défense réussie si demandé et mérité
create or replace function public.siege_fermer(p_id bigint, p_resultat text) returns void
language plpgsql security definer set search_path to 'public' as $$
declare s front_sieges;
begin
  select * into s from front_sieges where id = p_id and fini_le is null for update;
  if s.id is null then return; end if;
  update front_sieges set fini_le = now(), resultat = p_resultat, attente = 0 where id = p_id;
  perform siege_rendre_energie(s.attaquant, s.attente);
  if p_resultat in ('tombee', 'abandon') and (s.defendu or s.garnison_touchee) and s.defenseur is not null
     and exists (select 1 from possessions po where po.commune_code = s.commune_code and po.joueur_id = s.defenseur) then
    perform noter_journal('defense', s.defenseur, s.attaquant, s.commune_code, s.tier);   -- +10 au classement (plafonné)
    perform ajouter_compteur(s.defenseur, 'defenses', 1);
    perform quete_noter(s.defenseur, 'defense', 1);
    perform front_gagner(s.defenseur, 10, 'front_defense');
  end if;
end; $$;

-- la conquête (mêmes effets que attaquer() au 3e round gagné)
create or replace function public.siege_conquerir(p_id bigint) returns void
language plpgsql security definer set search_path to 'public' as $$
declare s front_sieges; v_def uuid; o record;
begin
  select * into s from front_sieges where id = p_id and fini_le is null for update;
  if s.id is null then return; end if;
  select joueur_id into v_def from possessions where commune_code = s.commune_code for update;
  update front_sieges set fini_le = now(), resultat = 'conquise' where id = p_id;
  perform siege_rendre_energie(s.attaquant, s.attente);
  update front_sieges set attente = 0 where id = p_id;
  update possessions set joueur_id = s.attaquant, acquired_at = now(), conquise_le = now()
   where commune_code = s.commune_code;
  perform front_gain_conquete(s.attaquant, v_def, s.commune_code, s.tier);
  update historique set released_at = now()
   where commune_code = s.commune_code and joueur_id = v_def and released_at is null;
  insert into historique (commune_code, joueur_id, saison, acquired_at)
  values (s.commune_code, s.attaquant, saison_en_cours_id(), now());
  delete from front_garnisons where commune_code = s.commune_code;
  perform quete_noter(s.attaquant, 'conquete', 1);
  perform ajouter_compteur(s.attaquant, 'conquetes', 1);
  for o in select id from front_sieges where commune_code = s.commune_code and fini_le is null loop
    perform siege_fermer(o.id, 'prise_par_autre');
  end loop;
end; $$;

-- appliquer une énergie (unité par unité) : bouclier, puis jauge ; renvoie l'énergie qui n'a pas pu partir
create or replace function public.siege_appliquer(p_id bigint, p_energie integer) returns integer
language plpgsql security definer set search_path to 'public' as $$
declare
  s front_sieges;
  v_mult numeric; v_res numeric; v_plafond numeric; v_proprio uuid; v_bouclier numeric := siege_n('bouclier_par_energie');
  v_pts numeric := siege_n('points_par_energie'); v_d numeric; v_reste integer := coalesce(p_energie, 0);
  g front_garnisons; v_seuil numeric; v_nom text; v_pseudo text;
begin
  select * into s from front_sieges where id = p_id and fini_le is null for update;
  if s.id is null then return v_reste; end if;
  select joueur_id into v_proprio from possessions where commune_code = s.commune_code;
  if v_proprio is null or v_proprio = s.attaquant then
    perform siege_fermer(p_id, 'proprio_change');
    perform siege_rendre_energie(s.attaquant, v_reste);   -- l'énergie qu'on allait envoyer revient
    return 0;
  end if;
  -- le siège devient long dès qu'il doit l'être
  if s.long_depuis is null and siege_doit_etre_long(s.commune_code, s.tier, v_proprio, s.defendu) then
    update front_sieges set long_depuis = now(), envoyes_long = 0 where id = p_id;
    s.long_depuis := now(); s.envoyes_long := 0;
  end if;
  v_mult := siege_mult(s.attaquant, s.commune_code);
  v_res := siege_resistance(s.commune_code, s.attaquant);
  v_plafond := siege_plafond(p_id);
  while v_reste > 0 loop
    if v_plafond is not null and s.envoyes_long >= v_plafond then exit; end if;
    v_d := v_pts * v_mult * (siege_n('alea_min') + random() * (siege_n('alea_max') - siege_n('alea_min')));
    v_reste := v_reste - 1;
    if v_plafond is not null then s.envoyes_long := s.envoyes_long + v_d; end if;
    -- le bouclier de la garnison d'abord
    select * into g from front_garnisons where commune_code = s.commune_code and joueur_id = v_proprio for update;
    if g.commune_code is not null and g.energie > 0 then
      g.entame := g.entame + v_d;
      while g.entame >= v_bouclier and g.energie > 0 loop
        g.entame := g.entame - v_bouclier; g.energie := g.energie - 1;
      end loop;
      if g.energie > 0 then v_d := 0; else v_d := g.entame; g.entame := 0; end if;
      update front_garnisons set energie = g.energie, entame = g.entame where commune_code = s.commune_code;
      s.garnison_touchee := true;
    end if;
    s.degats := s.degats + v_d;
    if s.degats >= v_res then
      update front_sieges set degats = s.degats, envoyes_long = s.envoyes_long, garnison_touchee = s.garnison_touchee,
             attente = attente + v_reste where id = p_id;
      perform siege_conquerir(p_id);
      return 0;
    end if;
  end loop;
  update front_sieges set degats = s.degats, envoyes_long = s.envoyes_long, garnison_touchee = s.garnison_touchee
   where id = p_id;
  -- « en danger » aux deux tiers, une seule fois
  if not s.alerte_danger and s.degats >= v_res * 2 / 3 then
    update front_sieges set alerte_danger = true where id = p_id;
    select c.nom into v_nom from communes c where c.code = s.commune_code;
    select pseudo into v_pseudo from joueurs where id = s.attaquant;
    perform notifier_joueur(v_proprio, v_nom || ' est en danger',
      coalesce(v_pseudo, 'Un joueur') || ' a rempli les deux tiers de son siège. Renforce-la vite.',
      './?onglet=defense', 'danger-' || s.commune_code);
  end if;
  return v_reste;
end; $$;

-- l'état d'un siège pour le jeu
create or replace function public.siege_vue(p_id bigint) returns jsonb
language plpgsql stable security definer set search_path to 'public' as $$
declare s front_sieges; v_res numeric; v_pl numeric; v_d numeric; v_debut timestamptz;
begin
  select * into s from front_sieges where id = p_id;
  if s.id is null then return null; end if;
  v_res := siege_resistance(s.commune_code, s.attaquant);
  v_pl := case when s.fini_le is null then siege_plafond(p_id) end;
  v_d := coalesce(siege_tier_n('duree_long_min', s.tier), 60);
  return jsonb_build_object(
    'id', s.id, 'commune', s.commune_code, 'tier', s.tier, 'attaquant', s.attaquant, 'defenseur', s.defenseur,
    'attaquant_pseudo', (select pseudo from joueurs where id = s.attaquant),
    'degats', round(s.degats), 'resistance', round(coalesce(v_res, 0)),
    'bouclier', siege_garnison(s.commune_code) * siege_n('bouclier_par_energie'),
    'long', s.long_depuis is not null, 'long_depuis', s.long_depuis,
    'rythme_h', case when s.long_depuis is not null then round(coalesce(v_res, 0) * 60 / v_d) end,
    'plafond', round(v_pl), 'envoyes_long', round(s.envoyes_long),
    'attente', s.attente, 'defendu', s.defendu, 'garnison_touchee', s.garnison_touchee,
    'energie_mise', s.energie_mise, 'energie_defense', s.energie_defense,
    'cree_le', s.cree_le, 'derniere_vague', s.derniere_vague,
    'tombe_le', s.derniere_vague + make_interval(hours => siege_n('expiration_h')::int),
    'fini_le', s.fini_le, 'resultat', s.resultat);
end; $$;

-- 4. ce que le jeu appelle
-- avant d'attaquer : tout ce qu'il faut pour la fiche
create or replace function public.siege_apercu(p_code text) returns jsonb
language plpgsql stable security definer set search_path to 'public' as $$
declare v_uid uuid := auth.uid(); c communes; po possessions; v_id bigint; v_long boolean; v_mult numeric;
begin
  if v_uid is null then raise exception 'Non connecté'; end if;
  select * into c from communes where code = p_code;
  if c.code is null then raise exception 'Commune inconnue'; end if;
  select * into po from possessions where commune_code = p_code;
  select id into v_id from front_sieges where attaquant = v_uid and commune_code = p_code and fini_le is null;
  v_long := po.joueur_id is not null and siege_doit_etre_long(p_code, c.tier, po.joueur_id, false);
  v_mult := siege_mult(v_uid, p_code);
  return jsonb_build_object(
    'actif', siege_actif(), 'commune', p_code, 'tier', c.tier,
    'proprio', po.joueur_id, 'proprio_pseudo', (select pseudo from joueurs where id = po.joueur_id),
    'resistance', round(coalesce(siege_resistance(p_code, v_uid), 0)),
    'resistance_base', siege_tier_n('resistance', c.tier),
    'forteresse', exists (select 1 from batiments b where b.commune_code = p_code and b.type = 'forteresse'
                           and b.joueur_id = po.joueur_id and b.pret_le <= now()),
    'bouclier', siege_garnison(p_code) * siege_n('bouclier_par_energie'),
    'mult', round(v_mult, 2), 'proches', communes_proches(v_uid, p_code, 20),
    'long', v_long, 'duree_long_min', siege_tier_n('duree_long_min', c.tier),
    'eclair_min', siege_tier_n('eclair_min', c.tier),
    'energie_estimee', ceil((coalesce(siege_resistance(p_code, v_uid), 0)
                              + siege_garnison(p_code) * siege_n('bouclier_par_energie'))
                             / (siege_n('points_par_energie') * v_mult)),
    'pose', siege_n('pose'), 'vague_max', siege_n('vague_max'),
    'places', siege_places(v_uid), 'longs', siege_longs_en_cours(v_uid),
    'autres', (select count(*) from front_sieges s where s.commune_code = p_code and s.fini_le is null and s.attaquant <> v_uid),
    'immunite_jusqua', case when po.acquired_at > now() - make_interval(hours => siege_n('immunite_h')::int)
                            then po.acquired_at + make_interval(hours => siege_n('immunite_h')::int) end,
    'bouclier_jusqua', case when po.bouclier_jusqua > now() then po.bouclier_jusqua end,
    'siege', case when v_id is not null then siege_vue(v_id) end);
end; $$;

-- poser le siège (si besoin) et envoyer une vague
create or replace function public.siege_vague(p_code text, p_energie integer) returns jsonb
language plpgsql security definer set search_path to 'public' as $$
declare
  v_uid uuid := auth.uid(); v_tier text; po possessions; v_id bigint; v_cout integer; v_neuf boolean := false;
  v_reste integer; v_att integer; v_nom text; v_pseudo text;
begin
  if v_uid is null then raise exception 'Non connecté'; end if;
  if not siege_actif() then raise exception 'Le siège arrive avec la saison 3'; end if;
  if p_energie is null or p_energie < 1 then raise exception 'Mets au moins 1 énergie'; end if;
  if p_energie > siege_n('vague_max') then raise exception 'Au plus % énergies par vague', siege_n('vague_max')::int; end if;
  select tier, nom into v_tier, v_nom from communes where code = p_code;
  if v_tier is null then raise exception 'Commune inconnue'; end if;
  select * into po from possessions where commune_code = p_code for update;
  if po.joueur_id is null then raise exception 'Cette commune n''appartient à personne'; end if;
  if po.joueur_id = v_uid then raise exception 'C''est ta commune'; end if;
  if meme_clan(v_uid, po.joueur_id) then raise exception 'Tu ne peux pas assiéger un membre de ton clan'; end if;
  if po.bouclier_jusqua is not null and po.bouclier_jusqua > now() then
    raise exception 'Cette commune est protégée par un bouclier';
  end if;

  select id into v_id from front_sieges where attaquant = v_uid and commune_code = p_code and fini_le is null for update;
  if v_id is null then
    if po.acquired_at > now() - make_interval(hours => siege_n('immunite_h')::int) then
      raise exception 'Cette commune vient de changer de main : protégée jusqu''à %',
        to_char((po.acquired_at + make_interval(hours => siege_n('immunite_h')::int)) at time zone 'Europe/Paris', 'HH24"h"MI');
    end if;
    if siege_doit_etre_long(p_code, v_tier, po.joueur_id, false)
       and siege_longs_en_cours(v_uid) >= siege_places(v_uid) then
      raise exception 'Tes % places de sièges longs sont prises : finis-en un ou abandonne-le', siege_places(v_uid);
    end if;
    v_cout := siege_n('pose')::int + p_energie; v_neuf := true;
  else
    v_cout := p_energie;
  end if;
  if not front_energie_depenser(v_uid, v_cout) then
    raise exception 'Énergie insuffisante (% requise)', v_cout;
  end if;
  if v_neuf then
    insert into front_sieges(attaquant, commune_code, defenseur, tier) values (v_uid, p_code, po.joueur_id, v_tier)
    returning id into v_id;
    if notif_alerte_dep(po.joueur_id, p_code) then
      select pseudo into v_pseudo from joueurs where id = v_uid;
      perform notifier_joueur(po.joueur_id, v_nom || ' est assiégée',
        coalesce(v_pseudo, 'Un joueur') || ' assiège ta commune. Renforce-la, ou laisse filer.',
        './?onglet=defense', 'danger-' || p_code);
    end if;
  end if;
  update front_sieges set energie_mise = energie_mise + p_energie, derniere_vague = now() where id = v_id;
  -- l'énergie déjà en attente part d'abord, puis la nouvelle ; ce qui dépasse le rythme attend
  select attente into v_att from front_sieges where id = v_id;
  update front_sieges set attente = 0 where id = v_id;
  v_reste := siege_appliquer(v_id, p_energie + coalesce(v_att, 0));
  update front_sieges set attente = attente + v_reste where id = v_id and fini_le is null;
  return siege_vue(v_id);
end; $$;

-- le défenseur renforce contre un assiégeant
create or replace function public.siege_renforcer(p_code text, p_attaquant uuid, p_energie integer) returns jsonb
language plpgsql security definer set search_path to 'public' as $$
declare v_uid uuid := auth.uid(); s front_sieges; v_pts numeric := siege_n('points_par_energie'); v_recul numeric := 0; i integer;
begin
  if v_uid is null then raise exception 'Non connecté'; end if;
  if not siege_actif() then raise exception 'Le siège arrive avec la saison 3'; end if;
  if p_energie is null or p_energie < 1 then raise exception 'Mets au moins 1 énergie'; end if;
  if p_energie > siege_n('vague_max') then raise exception 'Au plus % énergies à la fois', siege_n('vague_max')::int; end if;
  if not exists (select 1 from possessions where commune_code = p_code and joueur_id = v_uid) then
    raise exception 'Cette commune ne t''appartient pas';
  end if;
  select * into s from front_sieges where commune_code = p_code and attaquant = p_attaquant and fini_le is null for update;
  if s.id is null then raise exception 'Ce siège est déjà fini'; end if;
  if not front_energie_depenser(v_uid, p_energie) then
    raise exception 'Énergie insuffisante (% requise)', p_energie;
  end if;
  for i in 1..p_energie loop
    v_recul := v_recul + v_pts * siege_n('defense_bonus')
               * (siege_n('alea_min') + random() * (siege_n('alea_max') - siege_n('alea_min')));
  end loop;
  update front_sieges
     set degats = greatest(0, degats - v_recul), defendu = true, energie_defense = energie_defense + p_energie,
         defenseur = v_uid,
         long_depuis = coalesce(long_depuis, now()),
         envoyes_long = case when long_depuis is null then 0 else envoyes_long end,
         alerte_danger = case when greatest(0, degats - v_recul) < siege_resistance(p_code, p_attaquant) * 2 / 3 then false else alerte_danger end
   where id = s.id;
  return siege_vue(s.id);
end; $$;

-- l'attaquant abandonne (l'énergie en attente lui revient)
create or replace function public.siege_abandonner(p_code text) returns jsonb
language plpgsql security definer set search_path to 'public' as $$
declare v_uid uuid := auth.uid(); v_id bigint;
begin
  if v_uid is null then raise exception 'Non connecté'; end if;
  select id into v_id from front_sieges where attaquant = v_uid and commune_code = p_code and fini_le is null;
  if v_id is null then raise exception 'Aucun siège en cours ici'; end if;
  perform siege_fermer(v_id, 'abandon');
  return siege_vue(v_id);
end; $$;

-- mes sièges (attaquant)
create or replace function public.mes_sieges() returns jsonb
language sql stable security definer set search_path to 'public' as $$
  select coalesce(jsonb_agg(siege_vue(s.id) || jsonb_build_object('nom', c.nom, 'dept', c.departement,
                    'proprio_pseudo', (select pseudo from joueurs j where j.id = po.joueur_id))
                  order by s.long_depuis is null, s.derniere_vague desc), '[]'::jsonb)
    from front_sieges s join communes c on c.code = s.commune_code
    left join possessions po on po.commune_code = s.commune_code
   where s.attaquant = auth.uid() and s.fini_le is null;
$$;

-- les sièges contre moi (défenseur)
create or replace function public.sieges_contre_moi_v2() returns jsonb
language sql stable security definer set search_path to 'public' as $$
  select coalesce(jsonb_agg(siege_vue(s.id) || jsonb_build_object('nom', c.nom, 'dept', c.departement,
                    'garnison', siege_garnison(s.commune_code))
                  order by s.degats / greatest(1, siege_resistance(s.commune_code, s.attaquant)) desc), '[]'::jsonb)
    from front_sieges s join communes c on c.code = s.commune_code
    join possessions po on po.commune_code = s.commune_code and po.joueur_id = auth.uid()
   where s.fini_le is null;
$$;

-- les sièges d'une commune (fiche de la carte) : qui assiège, où en est la jauge
create or replace function public.sieges_commune(p_code text) returns jsonb
language sql stable security definer set search_path to 'public' as $$
  select coalesce(jsonb_agg(jsonb_build_object('attaquant', s.attaquant,
                    'pseudo', (select pseudo from joueurs j where j.id = s.attaquant),
                    'pct', least(100, round(100 * s.degats / greatest(1, siege_resistance(s.commune_code, s.attaquant)))),
                    'long', s.long_depuis is not null)
                  order by s.degats desc), '[]'::jsonb)
    from front_sieges s where s.commune_code = p_code and s.fini_le is null and auth.uid() is not null;
$$;

-- 5. la tâche toutes les 5 minutes : énergie en attente, sièges tombés
create or replace function public.siege_tick() returns integer
language plpgsql security definer set search_path to 'public' as $$
declare r record; v_reste integer; n integer := 0;
begin
  if not siege_actif() then return 0; end if;
  for r in select id, attente from front_sieges where fini_le is null and attente > 0 order by id loop
    update front_sieges set attente = 0 where id = r.id;
    v_reste := siege_appliquer(r.id, r.attente);
    update front_sieges set attente = attente + v_reste where id = r.id and fini_le is null;
    n := n + 1;
  end loop;
  for r in select id from front_sieges
            where fini_le is null and derniere_vague < now() - make_interval(hours => siege_n('expiration_h')::int) loop
    perform siege_fermer(r.id, 'tombee');
    n := n + 1;
  end loop;
  return n;
end; $$;

-- 6. la commune change de main autrement que par un siège : les sièges s'adaptent
create or replace function public.siege_proprio_change() returns trigger
language plpgsql security definer set search_path to 'public' as $$
declare r record;
begin
  if tg_op = 'DELETE' then
    for r in select id from front_sieges where commune_code = old.commune_code and fini_le is null loop
      perform siege_fermer(r.id, 'liberee');
    end loop;
  elsif new.joueur_id is distinct from old.joueur_id then
    -- le nouveau propriétaire ne s'assiège pas lui-même, ni un coéquipier
    for r in select id from front_sieges
              where commune_code = new.commune_code and fini_le is null
                and (attaquant = new.joueur_id or meme_clan(attaquant, new.joueur_id)) loop
      perform siege_fermer(r.id, 'proprio_change');
    end loop;
    update front_sieges set defenseur = new.joueur_id, defendu = false, garnison_touchee = false
     where commune_code = new.commune_code and fini_le is null;
  end if;
  return null;
end; $$;
drop trigger if exists trg_siege_proprio on public.possessions;
create trigger trg_siege_proprio after update of joueur_id or delete on public.possessions
  for each row execute function public.siege_proprio_change();

-- 7. droits : les joueurs n'appellent que les fonctions du jeu
revoke all on function public.siege_cfg(), public.siege_n(text), public.siege_tier_n(text, text),
  public.siege_resistance(text, uuid), public.siege_mult(uuid, text), public.siege_garnison(text),
  public.siege_batiment_visible(text, uuid), public.siege_doit_etre_long(text, text, uuid, boolean),
  public.siege_places(uuid), public.siege_longs_en_cours(uuid), public.siege_plafond(bigint),
  public.siege_rendre_energie(uuid, integer), public.siege_fermer(bigint, text), public.siege_conquerir(bigint),
  public.siege_appliquer(bigint, integer), public.siege_vue(bigint), public.siege_tick(),
  public.siege_proprio_change() from public, anon, authenticated;
revoke all on function public.siege_actif(), public.siege_apercu(text), public.siege_vague(text, integer),
  public.siege_renforcer(text, uuid, integer), public.siege_abandonner(text), public.mes_sieges(),
  public.sieges_contre_moi_v2(), public.sieges_commune(text) from public, anon;
grant execute on function public.siege_actif(), public.siege_apercu(text), public.siege_vague(text, integer),
  public.siege_renforcer(text, uuid, integer), public.siege_abandonner(text), public.mes_sieges(),
  public.sieges_contre_moi_v2(), public.sieges_commune(text) to authenticated;

-- 8. l'ancien combat refuse quand le siège est allumé (sinon on pourrait jouer aux dés à côté)
do $$
declare d text;
begin
  d := pg_get_functiondef('public.attaquer(text, text)'::regprocedure);
  if position('s3-7' in d) = 0 then
    d := replace(d, $a$if v_attaquant_id is null then raise exception 'Non connecte'; end if;$a$,
                    $a$if v_attaquant_id is null then raise exception 'Non connecte'; end if;
  if siege_actif() then raise exception 'Au Front, on attaque maintenant par siège : mets à jour le jeu'; end if;   -- s3-7$a$);
    if position('s3-7' in d) = 0 then raise exception 'attaquer : repère introuvable'; end if;
    execute d;
  end if;
  d := pg_get_functiondef('public.defendre(text, uuid, text)'::regprocedure);
  if position('s3-7' in d) = 0 then
    d := replace(d, $a$if v_uid is null then raise exception 'Non connecté'; end if;$a$,
                    $a$if v_uid is null then raise exception 'Non connecté'; end if;
  if siege_actif() then raise exception 'Au Front, on défend maintenant en renforçant : mets à jour le jeu'; end if;   -- s3-7$a$);
    if position('s3-7' in d) = 0 then raise exception 'defendre : repère introuvable'; end if;
    execute d;
  end if;
end $$;

-- 9. la tâche périodique (ne fait rien tant que le siège est éteint)
select cron.unschedule(jobid) from cron.job where jobname = 'siege-tick';
select cron.schedule('siege-tick', '*/5 * * * *', 'select public.siege_tick()');

commit;

-- contrôle : actif | fonctions | table | attaquer gardé | defendre gardé | tâche
select (siege_cfg()->>'actif')::int as actif,
       (select count(*) from pg_proc where proname like 'siege%' or proname in ('mes_sieges', 'sieges_contre_moi_v2', 'sieges_commune')) as fonctions,
       to_regclass('public.front_sieges') is not null as table_ok,
       position('s3-7' in pg_get_functiondef('public.attaquer(text, text)'::regprocedure)) > 0 as attaquer_garde,
       position('s3-7' in pg_get_functiondef('public.defendre(text, uuid, text)'::regprocedure)) > 0 as defendre_garde,
       (select count(*) from cron.job where jobname = 'siege-tick') as tache;
