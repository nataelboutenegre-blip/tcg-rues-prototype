-- ===========================================================================
--  s2-48 — Les bâtiments du Front, étape 1 : Fonderie, lingots, Forteresse
--  Décisions de Nataël du 27-28 octobre 2026 (plan : claude/plan-strategie-front.md).
--  À lancer APRÈS s2-46 (série gardée).
--
--  FONDERIE : gratuite, une seule par joueur, sur une de ses communes du
--    Front, prête en 24 h. Produit 10 lingots par jour, réserve de 30 au plus.
--    Si sa commune est CONQUISE : la Fonderie est détruite et l'attaquant
--    pille la moitié de la réserve du joueur. On peut en reconstruire une.
--  FORTERESSE : 20 lingots, prête en 24 h, 3 au plus par joueur.
--    Défense : −15 % aux chances des attaquants sur sa commune.
--    Point d'appui : +5 % aux chances de son propriétaire sur les communes
--    à moins de 20 km (une seule forteresse compte, pas de cumul).
--    Les chances restent entre 10 % et 90 %, comme avant.
--  Tout bâtiment disparaît quand sa commune change de propriétaire (conquête,
--  échange de clan) ou quitte le jeu (clôture). Pas de remboursement.
--  LINGOTS : ne servent qu'aux bâtiments ; ni échange, ni achat ; ils
--    repartent à zéro à chaque saison (comptés par saison) ; hors classement.
--  Les bâtiments sont visibles de tous ; les réserves de lingots, non.
--
--  1. Réglages (config_jeu 'batiments', modifiables sans toucher au code)
--  2. Table batiments, colonnes lingots sur joueurs
--  3. Fonctions : lire / figer les lingots, construire, mes_batiments,
--     batiments_visibles, batiments_effet, bonus_batiments
--  4. Déclencheur sur possessions : destruction + pillage
--  5. Les chances : attaquer, apercu_attaque, apercu_attaques ajoutent
--     bonus_batiments (modifiées à partir de leur définition en production ;
--     texte attendu une fois par fonction, sinon rien ne change)
--  Rejouable. Contrôle attendu : true | true | true | true | true | 0
-- ===========================================================================
begin;

-- 1. Réglages -----------------------------------------------------------------
insert into public.config_jeu (cle, valeur) values
  ('batiments', '{"ouverts": true, "fonderie_production": 10, "fonderie_max": 30, "construction_h": 24,
                  "forteresse_prix": 20, "forteresse_max": 3, "forteresse_defense": 0.15,
                  "forteresse_appui": 0.05, "forteresse_rayon_km": 20, "pillage": 0.5}')
on conflict (cle) do nothing;

create or replace function public.batiment_reglage(p_cle text)
 returns numeric language sql stable security definer set search_path to 'public'
as $f$
  select coalesce(
    (select (c.valeur::jsonb ->> p_cle)::numeric from config_jeu c where c.cle = 'batiments'),
    case p_cle when 'fonderie_production' then 10 when 'fonderie_max' then 30 when 'construction_h' then 24
               when 'forteresse_prix' then 20 when 'forteresse_max' then 3 when 'forteresse_defense' then 0.15
               when 'forteresse_appui' then 0.05 when 'forteresse_rayon_km' then 20 when 'pillage' then 0.5 end);
$f$;

create or replace function public.batiments_ouverts()
 returns boolean language sql stable security definer set search_path to 'public'
as $f$
  select saison2_active() and coalesce(
    (select (c.valeur::jsonb ->> 'ouverts')::boolean from config_jeu c where c.cle = 'batiments'), false);
$f$;

-- 2. Tables ---------------------------------------------------------------------
create table if not exists public.batiments(
  id            bigserial primary key,
  joueur_id     uuid not null references public.joueurs(id) on delete cascade,
  commune_code  text not null references public.communes(code),
  type          text not null check (type in ('fonderie', 'forteresse')),
  cree_le       timestamptz not null default now(),
  pret_le       timestamptz not null,
  unique (commune_code, type)
);
create unique index if not exists batiments_une_fonderie on public.batiments(joueur_id) where type = 'fonderie';
create index if not exists batiments_joueur on public.batiments(joueur_id);
alter table public.batiments enable row level security;
revoke all on public.batiments from public, anon, authenticated;
revoke all on sequence public.batiments_id_seq from public, anon, authenticated;

alter table public.joueurs add column if not exists lingots         numeric     not null default 0;
alter table public.joueurs add column if not exists lingots_maj     timestamptz not null default now();
alter table public.joueurs add column if not exists lingots_saison  text;

-- 3. Les lingots ------------------------------------------------------------------
-- Réserve actuelle : réserve enregistrée (si elle est de la saison en cours)
-- + production de la Fonderie prête depuis la dernière mise à jour, au plus
-- la réserve maximale. Une réserve déjà au-dessus (pillage) reste telle quelle.
create or replace function public.lingots_lire(p_uid uuid)
 returns numeric language sql stable security definer set search_path to 'public'
as $f$
  select case
    when base >= mx then base
    when f.pret_le is null then base   -- pas de Fonderie prête : rien ne rentre
    else least(mx, base + batiment_reglage('fonderie_production')
           * greatest(0, extract(epoch from (now() - greatest(j.lingots_maj, f.pret_le)))) / 86400.0)
  end
  from joueurs j
  cross join lateral (select case when j.lingots_saison is not distinct from saison_en_cours_id()
                                  then j.lingots else 0 end as base,
                             batiment_reglage('fonderie_max') as mx) x
  left join batiments f on f.joueur_id = j.id and f.type = 'fonderie' and f.pret_le <= now()
  where j.id = p_uid;
$f$;

create or replace function public.lingots_figer(p_uid uuid)
 returns numeric language plpgsql security definer set search_path to 'public'
as $f$
declare v numeric;
begin
  if p_uid is null then return 0; end if;
  v := coalesce(lingots_lire(p_uid), 0);
  update joueurs set lingots = v, lingots_maj = now(), lingots_saison = saison_en_cours_id() where id = p_uid;
  return v;
end;
$f$;

-- Ce que voit le joueur : sa réserve, sa Fonderie, ses forteresses, les règles
create or replace function public.mes_batiments()
 returns jsonb language plpgsql stable security definer set search_path to 'public'
as $f$
declare
  v_uid uuid := auth.uid();
  v numeric;
  v_fond record;
  v_prod numeric := batiment_reglage('fonderie_production');
  v_max numeric := batiment_reglage('fonderie_max');
begin
  if v_uid is null then raise exception 'Non connecte'; end if;
  v := coalesce(lingots_lire(v_uid), 0);
  select b.commune_code, c.nom, c.departement, b.pret_le into v_fond
    from batiments b join communes c on c.code = b.commune_code
   where b.joueur_id = v_uid and b.type = 'fonderie';
  return jsonb_build_object(
    'ouverts', batiments_ouverts(),
    'lingots', floor(v)::integer,
    'max', v_max::integer,
    'production', v_prod::integer,
    -- secondes avant le prochain lingot (null si pas de Fonderie prête ou réserve pleine)
    'prochain_dans', case when v_fond.pret_le is not null and v_fond.pret_le <= now() and v < v_max
                          then ceil((1 - (v - floor(v))) * 86400.0 / v_prod)::integer end,
    'fonderie', case when v_fond.commune_code is null then null else jsonb_build_object(
        'code', v_fond.commune_code, 'nom', v_fond.nom, 'dept', v_fond.departement,
        'pret_le', v_fond.pret_le, 'pret', v_fond.pret_le <= now()) end,
    'forteresses', coalesce((select jsonb_agg(jsonb_build_object(
        'code', b.commune_code, 'nom', c.nom, 'dept', c.departement,
        'pret_le', b.pret_le, 'pret', b.pret_le <= now()) order by b.cree_le)
        from batiments b join communes c on c.code = b.commune_code
       where b.joueur_id = v_uid and b.type = 'forteresse'), '[]'::jsonb),
    'reglages', jsonb_build_object(
        'forteresse_prix', batiment_reglage('forteresse_prix')::integer,
        'forteresse_max', batiment_reglage('forteresse_max')::integer,
        'forteresse_defense', round(batiment_reglage('forteresse_defense') * 100)::integer,
        'forteresse_appui', round(batiment_reglage('forteresse_appui') * 100)::integer,
        'rayon_km', batiment_reglage('forteresse_rayon_km')::integer,
        'construction_h', batiment_reglage('construction_h')::integer,
        'pillage', round(batiment_reglage('pillage') * 100)::integer));
end;
$f$;

create or replace function public.batiment_construire(p_code text, p_type text)
 returns jsonb language plpgsql security definer set search_path to 'public'
as $f$
declare
  v_uid uuid := auth.uid();
  v numeric;
  v_prix numeric := batiment_reglage('forteresse_prix');
begin
  if v_uid is null then raise exception 'Non connecte'; end if;
  if not batiments_ouverts() then raise exception 'Les bâtiments ne sont pas encore ouverts'; end if;
  if p_type not in ('fonderie', 'forteresse') then raise exception 'Bâtiment inconnu'; end if;
  perform 1 from joueurs where id = v_uid for update;
  if not exists (select 1 from possessions p where p.commune_code = p_code and p.joueur_id = v_uid) then
    raise exception 'Cette commune ne t''appartient pas';
  end if;
  if exists (select 1 from batiments b where b.commune_code = p_code and b.type = p_type) then
    raise exception 'Il y a déjà ce bâtiment ici';
  end if;

  if p_type = 'fonderie' then
    if exists (select 1 from batiments b where b.joueur_id = v_uid and b.type = 'fonderie') then
      raise exception 'Tu as déjà une Fonderie';
    end if;
    perform lingots_figer(v_uid);
  else
    if not exists (select 1 from batiments b where b.joueur_id = v_uid and b.type = 'fonderie') then
      raise exception 'Il te faut d''abord une Fonderie';
    end if;
    if (select count(*) from batiments b where b.joueur_id = v_uid and b.type = 'forteresse')
       >= batiment_reglage('forteresse_max') then
      raise exception 'Tu as déjà % forteresses', batiment_reglage('forteresse_max')::integer;
    end if;
    v := lingots_figer(v_uid);
    if v < v_prix then
      raise exception 'Il te faut % lingots (tu en as %)', v_prix::integer, floor(v)::integer;
    end if;
    update joueurs set lingots = lingots - v_prix where id = v_uid;
  end if;

  insert into batiments(joueur_id, commune_code, type, pret_le)
  values (v_uid, p_code, p_type, now() + make_interval(hours => batiment_reglage('construction_h')::integer));
  return mes_batiments();
end;
$f$;

-- Tous les bâtiments de la carte (pour les icônes) : visibles de tous
create or replace function public.batiments_visibles()
 returns table(commune_code text, type text, joueur_id uuid, pret boolean)
 language sql stable security definer set search_path to 'public'
as $f$
  select b.commune_code, b.type, b.joueur_id, b.pret_le <= now()
    from batiments b
   where auth.uid() is not null and batiments_ouverts();
$f$;

-- L'effet des forteresses sur les chances de p_uid contre p_code
-- (négatif : forteresse de la cible ; positif : point d'appui de p_uid)
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
  end;
$f$;

-- Pour le panneau d'attaque : ce qui joue, en clair
create or replace function public.batiments_effet(p_code text)
 returns table(defense integer, appui integer, appui_de text)
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
         limit 1)
  select case when exists (select 1 from d) then round(batiment_reglage('forteresse_defense') * 100)::integer else 0 end,
         case when exists (select 1 from a) then round(batiment_reglage('forteresse_appui') * 100)::integer else 0 end,
         (select nom from a)
   where auth.uid() is not null and batiments_ouverts();
$f$;

revoke all on function public.lingots_lire(uuid), public.lingots_figer(uuid),
                       public.bonus_batiments(uuid, text) from public, anon, authenticated;
revoke all on function public.mes_batiments(), public.batiment_construire(text, text),
                       public.batiments_visibles(), public.batiments_effet(text) from public, anon;
grant execute on function public.mes_batiments(), public.batiment_construire(text, text),
                          public.batiments_visibles(), public.batiments_effet(text) to authenticated;

-- 4. Destruction (et pillage) quand la commune change de main ---------------------------
create or replace function public.batiments_changement_proprio()
 returns trigger language plpgsql security definer set search_path to 'public'
as $f$
declare
  b record;
  v numeric;
  v_pille integer;
  v_conquete boolean;
begin
  if tg_op = 'UPDATE' and new.joueur_id is not distinct from old.joueur_id then return null; end if;
  v_conquete := tg_op = 'UPDATE' and new.joueur_id is not null
                and new.conquise_le is distinct from old.conquise_le and new.conquise_le is not null;
  for b in delete from batiments where commune_code = old.commune_code returning * loop
    if b.type = 'fonderie' then
      v := lingots_figer(b.joueur_id);
      if v_conquete and v > 0 then
        v_pille := floor(v * batiment_reglage('pillage'))::integer;
        update joueurs set lingots = lingots - v_pille where id = b.joueur_id;
        perform lingots_figer(new.joueur_id);
        update joueurs set lingots = lingots + v_pille where id = new.joueur_id;
      end if;
    end if;
  end loop;
  return null;
exception when others then
  -- un bâtiment ne doit JAMAIS bloquer une conquête : au pire, il reste en place
  raise warning 'batiments_changement_proprio : %', sqlerrm;
  return null;
end;
$f$;
revoke all on function public.batiments_changement_proprio() from public, anon, authenticated;

drop trigger if exists trg_batiments_proprio on public.possessions;
create trigger trg_batiments_proprio after update of joueur_id or delete on public.possessions
  for each row execute function public.batiments_changement_proprio();

-- 5. Les chances ------------------------------------------------------------------------
create or replace function pg_temp.remp(d text, avant text, apres text, quoi text)
 returns text language plpgsql as $f$
begin
  if (length(d) - length(replace(d, avant, ''))) / length(avant) <> 1 then
    raise exception '% : texte attendu introuvable (ou en double), rien n''a changé : %', quoi, avant;
  end if;
  return replace(d, avant, apres);
end;
$f$;

do $$
declare d text;
begin
  d := pg_get_functiondef('public.attaquer(text, text)'::regprocedure);
  if position('bonus_batiments' in d) = 0 then
    execute pg_temp.remp(d, 'v_chance + bonus_proximite(v_proches)',
      'v_chance + bonus_proximite(v_proches) + bonus_batiments(v_attaquant_id, p_commune_code)', 'attaquer');
  end if;

  d := pg_get_functiondef('public.apercu_attaque(text, text)'::regprocedure);
  if position('bonus_batiments' in d) = 0 then
    execute pg_temp.remp(d, 'v_chance + bonus_proximite(v_proches)',
      'v_chance + bonus_proximite(v_proches) + bonus_batiments(v_uid, p_commune_code)', 'apercu_attaque');
  end if;

  d := pg_get_functiondef('public.apercu_attaques(text[], text)'::regprocedure);
  if position('bonus_batiments' in d) = 0 then
    execute pg_temp.remp(d, 'v_base + bonus_proximite(p.nb)',
      'v_base + bonus_proximite(p.nb) + bonus_batiments(v_uid, c.code)', 'apercu_attaques');
  end if;
end $$;

commit;

-- Contrôle
select batiments_ouverts()                                                                         as ouverts,
       pg_get_functiondef('public.attaquer(text, text)'::regprocedure)           ~ 'bonus_batiments' as attaquer,
       pg_get_functiondef('public.apercu_attaque(text, text)'::regprocedure)     ~ 'bonus_batiments' as apercu,
       pg_get_functiondef('public.apercu_attaques(text[], text)'::regprocedure)  ~ 'bonus_batiments' as apercu_lot,
       exists (select 1 from pg_trigger where tgname = 'trg_batiments_proprio')                    as declencheur,
       (select count(*) from public.batiments)                                                     as batiments;
