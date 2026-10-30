-- ===========================================================================
--  s2-68 — Halloween : les communes hantées (quête Terra + quête Front)
--  Décidé le 30/10 au soir avec Nataël (patch276 pour le jeu).
--
--  Les 3 communes hantées, les mêmes en Terra et en Front :
--    Brissac Loire Aubance (49050, épique), Queaux (86203, peu commune),
--    Marquay (24255, peu commune).
--
--  TERRA (quête « Les châteaux hantés ») : pendant Halloween, 1 paquet Terra
--  sur 3 (hasard pur) contient une des 3, tirée au hasard. Celui qui la tire
--  la garde HANTÉE pour toujours (brume + braises). Les 3 trouvées :
--  500 TP + le titre « Chasseur de fantômes », à réclamer.
--  Seuls les paquets Terra (gratuits et achetés en TP) : pas la boutique.
--
--  FRONT (quête « Tiens une commune hantée ») : les 3 communes portent la
--  brume, quel que soit leur propriétaire. Tant qu'elles sont libres, chaque
--  carte d'un paquet Front a 5 % de chance d'en être une. Celui qui en TIENT
--  une à la fin d'Halloween (2/11 à minuit) réussit : titre « Chasseur de
--  fantômes » + 30 d'énergie (plafond 60), à réclamer après la fin.
--  Qui tient quoi est noté par un déclencheur sur possessions.
--
--  Peut se lancer avant ou après s2-62 : sans la config 'halloween' (s2-62),
--  rien ne s'allume. Les dates sont celles d'Halloween (config 'halloween').
--  Réglages : config_jeu 'halloween_hantees' (ouvert, codes, proba,
--  front_proba, prime, energie, titre). Couper : s2-68-halloween-hantees-couper.sql
--
--  Modifie 3 fonctions à partir de leur texte en base (vérifié le 30/10 par
--  lecture-halloween-quete.sql) : terra_ouvrir_paquet, draw_commune,
--  titres_possibles. Si un repère manque, RIEN ne change (une transaction).
--  Rejouable. Contrôle attendu : true | true | true | true | true | 3
-- ===========================================================================
begin;

insert into public.config_jeu (cle, valeur)
values ('halloween_hantees', '{"ouvert": 1, "codes": ["49050", "86203", "24255"], "proba": 0.3333, "front_proba": 0.05, "prime": 500, "energie": 30, "titre": "halloween-2026"}')
on conflict (cle) do update set valeur = excluded.valeur;

-- 1. Tables ---------------------------------------------------------------------
create table if not exists public.halloween_hantees(       -- Terra : les cartes hantées de chacun
  joueur_id     uuid not null references public.joueurs(id) on delete cascade,
  commune_code  text not null,
  trouvee_le    timestamptz not null default now(),
  primary key (joueur_id, commune_code)
);
create table if not exists public.halloween_quete(         -- les récompenses réclamées
  joueur_id        uuid primary key references public.joueurs(id) on delete cascade,
  reclame_le       timestamptz,    -- quête Terra
  front_reclame_le timestamptz     -- quête Front
);
create table if not exists public.halloween_front_tenues(  -- Front : qui a tenu quelle commune hantée, et quand
  id            bigserial primary key,
  commune_code  text not null,
  joueur_id     uuid not null,
  depuis        timestamptz not null default now(),
  jusqua        timestamptz
);
create index if not exists halloween_front_tenues_ouvertes on public.halloween_front_tenues(commune_code) where jusqua is null;
alter table public.halloween_hantees      enable row level security;
alter table public.halloween_quete        enable row level security;
alter table public.halloween_front_tenues enable row level security;
revoke all on public.halloween_hantees, public.halloween_quete, public.halloween_front_tenues from public, anon, authenticated;

-- 2. Réglages -------------------------------------------------------------------
create or replace function public.halloween_hantees_cfg()
 returns jsonb language sql stable security definer set search_path to 'public'
as $f$
  select coalesce((select c.valeur::jsonb from config_jeu c where c.cle = 'halloween_hantees'), '{}'::jsonb);
$f$;
create or replace function public.halloween_fin()
 returns timestamptz language sql stable security definer set search_path to 'public'
as $f$
  select (select c.valeur::jsonb ->> 'fin' from config_jeu c where c.cle = 'halloween')::timestamptz;
$f$;
create or replace function public.halloween_en_cours()
 returns boolean language sql stable security definer set search_path to 'public'
as $f$
  select coalesce((select coalesce((h.v ->> 'ouvert')::int, 0) = 1
                          and now() >= (h.v ->> 'debut')::timestamptz
                          and now() <  (h.v ->> 'fin')::timestamptz
                     from (select c.valeur::jsonb as v from config_jeu c where c.cle = 'halloween') h), false)
     and coalesce((halloween_hantees_cfg() ->> 'ouvert')::int, 0) = 1;
$f$;
create or replace function public.halloween_codes()
 returns text[] language sql stable security definer set search_path to 'public'
as $f$
  select coalesce(array(select jsonb_array_elements_text(halloween_hantees_cfg() -> 'codes')), '{}'::text[]);
$f$;
-- pendant Halloween seulement : ces communes sortent par la porte hantée, pas au hasard
create or replace function public.halloween_codes_actifs()
 returns text[] language sql stable security definer set search_path to 'public'
as $f$
  select case when halloween_en_cours() then halloween_codes() else '{}'::text[] end;
$f$;

-- 3. Terra : 1 paquet sur 3 contient une commune hantée --------------------------
create or replace function public.halloween_tirage_terra()
 returns text language plpgsql volatile security definer set search_path to 'public'
as $f$
declare
  v_uid  uuid := auth.uid();
  v_code text;
begin
  if v_uid is null or not halloween_en_cours() then return null; end if;
  if random() >= coalesce((halloween_hantees_cfg() ->> 'proba')::numeric, 0.3333) then return null; end if;
  select x into v_code from unnest(halloween_codes()) x order by random() limit 1;
  if v_code is null then return null; end if;
  insert into halloween_hantees(joueur_id, commune_code) values (v_uid, v_code) on conflict do nothing;
  return v_code;
end;
$f$;

-- 4. Front : qui tient une commune hantée (déclencheur sur possessions) ---------
create or replace function public.halloween_front_suivi()
 returns trigger language plpgsql security definer set search_path to 'public'
as $f$
declare c text[] := halloween_codes();
begin
  if tg_op in ('UPDATE', 'DELETE') and old.commune_code = any(c)
     and (tg_op = 'DELETE' or new.joueur_id is distinct from old.joueur_id or new.commune_code is distinct from old.commune_code) then
    update halloween_front_tenues set jusqua = now() where commune_code = old.commune_code and jusqua is null;
  end if;
  if tg_op in ('INSERT', 'UPDATE') and new.commune_code = any(c)
     and (tg_op = 'INSERT' or new.joueur_id is distinct from old.joueur_id or new.commune_code is distinct from old.commune_code) then
    update halloween_front_tenues set jusqua = now() where commune_code = new.commune_code and jusqua is null;
    insert into halloween_front_tenues(commune_code, joueur_id) values (new.commune_code, new.joueur_id);
  end if;
  return null;
end;
$f$;
revoke all on function public.halloween_front_suivi() from public, anon, authenticated;
drop trigger if exists trg_halloween_front on public.possessions;
create trigger trg_halloween_front after insert or update or delete on public.possessions
  for each row execute function public.halloween_front_suivi();
-- ceux qui tiennent déjà une des 3 (aucune le 30/10 à 18 h)
insert into public.halloween_front_tenues(commune_code, joueur_id)
select p.commune_code, p.joueur_id from public.possessions p
 where p.commune_code = any(public.halloween_codes())
   and not exists (select 1 from public.halloween_front_tenues t where t.commune_code = p.commune_code and t.jusqua is null);

-- celui qui tenait une commune hantée au moment exact de la fin
create or replace function public.halloween_front_gagnant(p_uid uuid)
 returns boolean language sql stable security definer set search_path to 'public'
as $f$
  select halloween_fin() is not null and now() >= halloween_fin()
     and exists (select 1 from halloween_front_tenues t
                  where t.joueur_id = p_uid and t.commune_code = any(halloween_codes())
                    and t.depuis <= halloween_fin() and (t.jusqua is null or t.jusqua > halloween_fin()));
$f$;

-- 5. Ce que voit le joueur --------------------------------------------------------
create or replace function public.halloween_hantees_etat()
 returns jsonb language plpgsql stable security definer set search_path to 'public'
as $f$
declare
  v_uid uuid := auth.uid();
  cfg   jsonb := halloween_hantees_cfg();
  c     text[] := halloween_codes();
begin
  if v_uid is null then raise exception 'Non connecte'; end if;
  if coalesce((cfg ->> 'ouvert')::int, 0) = 0 or halloween_fin() is null then return jsonb_build_object('ouvert', 0); end if;
  return jsonb_build_object(
    'ouvert', 1,
    'actif', halloween_en_cours(),
    'fin', halloween_fin(),
    'termine', now() >= halloween_fin(),
    'codes', to_jsonb(c),
    'proba', coalesce((cfg ->> 'proba')::numeric, 0.3333),
    'prime', coalesce((cfg ->> 'prime')::int, 500),
    'energie', coalesce((cfg ->> 'energie')::int, 30),
    'titre', coalesce(cfg ->> 'titre', 'halloween-2026'),
    'communes', coalesce((select jsonb_agg(jsonb_build_object(
                    'code', cm.code, 'nom', cm.nom, 'departement', cm.departement, 'tier', cm.tier,
                    'proprietaire', jo.pseudo, 'a_moi', coalesce(p.joueur_id = v_uid, false))
                  order by array_position(c, cm.code::text))
                  from communes cm
                  left join possessions p on p.commune_code = cm.code
                  left join joueurs jo on jo.id = p.joueur_id
                 where cm.code = any(c)), '[]'::jsonb),
    'miennes', coalesce((select jsonb_agg(h.commune_code order by h.trouvee_le) from halloween_hantees h
                          where h.joueur_id = v_uid and h.commune_code = any(c)), '[]'::jsonb),
    'reclamee', exists(select 1 from halloween_quete q where q.joueur_id = v_uid and q.reclame_le is not null),
    'front_gagnant', halloween_front_gagnant(v_uid),
    'front_reclamee', exists(select 1 from halloween_quete q where q.joueur_id = v_uid and q.front_reclame_le is not null));
end;
$f$;

create or replace function public.halloween_quete_reclamer(p_quete text default 'terra')
 returns jsonb language plpgsql security definer set search_path to 'public'
as $f$
declare
  v_uid uuid := auth.uid();
  cfg   jsonb := halloween_hantees_cfg();
  v     numeric;
  v_n   integer;
begin
  if v_uid is null then raise exception 'Non connecte'; end if;
  if coalesce((cfg ->> 'ouvert')::int, 0) = 0 then raise exception 'La quête d''Halloween est fermée'; end if;
  perform 1 from joueurs where id = v_uid for update;   -- deux clics ne paient pas deux fois
  insert into halloween_quete(joueur_id) values (v_uid) on conflict do nothing;
  if p_quete = 'front' then
    if not halloween_front_gagnant(v_uid) then raise exception 'Il faut tenir une commune hantée à la fin d''Halloween'; end if;
    update halloween_quete set front_reclame_le = now() where joueur_id = v_uid and front_reclame_le is null;
    if not found then raise exception 'Récompense déjà récupérée'; end if;
    select front_energie_lire(j.front_energie, j.front_energie_maj) into v from joueurs j where j.id = v_uid;
    update joueurs set front_energie = least(60, v + coalesce((cfg ->> 'energie')::int, 30)), front_energie_maj = now() where id = v_uid;
  else
    select count(distinct h.commune_code) into v_n from halloween_hantees h
     where h.joueur_id = v_uid and h.commune_code = any(halloween_codes());
    if v_n < cardinality(halloween_codes()) then raise exception 'Il te manque encore des communes hantées'; end if;
    update halloween_quete set reclame_le = now() where joueur_id = v_uid and reclame_le is null;
    if not found then raise exception 'Récompense déjà récupérée'; end if;
    perform set_config('terrafront.motif', 'halloween_quete', true);
    update joueurs set solde = coalesce(solde, 0) + coalesce((cfg ->> 'prime')::int, 500) where id = v_uid;
  end if;
  return halloween_hantees_etat() || jsonb_build_object('solde', (select j.solde from joueurs j where j.id = v_uid));
end;
$f$;

revoke all on function public.halloween_hantees_cfg(), public.halloween_fin(), public.halloween_en_cours(), public.halloween_codes(),
  public.halloween_codes_actifs(), public.halloween_tirage_terra(), public.halloween_front_gagnant(uuid) from public, anon, authenticated;
revoke all on function public.halloween_hantees_etat(), public.halloween_quete_reclamer(text) from public, anon;
grant execute on function public.halloween_hantees_etat(), public.halloween_quete_reclamer(text) to authenticated;

-- 6. Les 3 fonctions retouchées ---------------------------------------------------
create or replace function pg_temp.remplacer(p_def text, p_avant text, p_apres text, p_etiquette text)
returns text language plpgsql as $$
declare n integer := (length(p_def) - length(replace(p_def, p_avant, ''))) / length(p_avant);
begin
  if n <> 1 then raise exception '% : repère trouvé % fois au lieu d''une, rien n''a changé', p_etiquette, n; end if;
  return replace(p_def, p_avant, p_apres);
end $$;

do $do$
declare d text;
begin
  -- 6a. terra_ouvrir_paquet : la commune hantée passe devant, et ne peut pas sortir une 2e fois dans le même paquet
  d := pg_get_functiondef('public.terra_ouvrir_paquet(boolean)'::regprocedure);
  if position('halloween_tirage_terra' in d) = 0 then
    d := pg_temp.remplacer(d,
      E'      from (select c.code from communes c order by random() limit 5) t0',
      E'      from (select x.code from (   -- s2-68 : Halloween, 1 paquet sur 3 contient une commune hantée\n'
   || E'              select h.code, 0 as o from (select halloween_tirage_terra() as code) h where h.code is not null\n'
   || E'              union all\n'
   || E'              (select c.code, 1 from communes c where c.code <> all(halloween_codes_actifs()) order by random() limit 5)\n'
   || E'            ) x order by x.o limit 5) t0',
      'terra_ouvrir_paquet');
    execute d;
  end if;

  -- 6b. draw_commune : tant qu'elle est libre, une petite chance qu'une commune hantée sorte
  d := pg_get_functiondef('public.draw_commune(text)'::regprocedure);
  if position('halloween_codes' in d) = 0 then
    d := pg_temp.remplacer(d,
      E'    for v_i in v_start_tier..5 loop\n      exit when v_code is not null;   -- s2-37 : un DOM vient d''être tiré',
      E'    -- s2-68 : Halloween, une commune hantée encore libre\n'
   || E'    if v_code is null and halloween_en_cours() and random() < coalesce((halloween_hantees_cfg() ->> ''front_proba'')::numeric, 0.05) then\n'
   || E'      select c.code into v_code\n'
   || E'        from communes c\n'
   || E'        left join possessions p on p.commune_code = c.code\n'
   || E'       where c.code = any(halloween_codes()) and p.commune_code is null and not exists (select 1 from front_liberations fl where fl.commune_code = c.code and fl.joueur_id = v_joueur_id and fl.jusqua > now())\n'
   || E'       order by random()\n'
   || E'       limit 1;\n'
   || E'    end if;\n'
   || E'    for v_i in v_start_tier..5 loop\n      exit when v_code is not null;   -- s2-37 : un DOM vient d''être tiré',
      'draw_commune');
    execute d;
  end if;

  -- 6c. titres_possibles : « Chasseur de fantômes »
  d := pg_get_functiondef('public.titres_possibles(uuid)'::regprocedure);
  if position('halloween_quete' in d) = 0 then
    d := pg_temp.remplacer(d,
      E'           where c.joueur_id = p_joueur and r.type = ''titre'') x;',
      E'           where c.joueur_id = p_joueur and r.type = ''titre''\n'
   || E'          union\n'
   || E'          -- s2-68 : la quête d''Halloween (Terra ou Front)\n'
   || E'          select coalesce(halloween_hantees_cfg() ->> ''titre'', ''halloween-2026'')\n'
   || E'            from halloween_quete q\n'
   || E'           where q.joueur_id = p_joueur and (q.reclame_le is not null or q.front_reclame_le is not null)) x;',
      'titres_possibles');
    execute d;
  end if;
end $do$;

commit;

-- Contrôle : true | true | true | true | true | 3
select position('halloween_tirage_terra' in pg_get_functiondef('public.terra_ouvrir_paquet(boolean)'::regprocedure)) > 0 as paquet_terra,
       position('halloween_codes' in pg_get_functiondef('public.draw_commune(text)'::regprocedure)) > 0                  as tirage_front,
       position('halloween_quete' in pg_get_functiondef('public.titres_possibles(uuid)'::regprocedure)) > 0              as titre,
       exists (select 1 from pg_trigger where tgname = 'trg_halloween_front')                                             as suivi_front,
       has_function_privilege('authenticated', 'public.halloween_hantees_etat()', 'execute')
         and not has_function_privilege('authenticated', 'public.halloween_tirage_terra()', 'execute')                   as droits,
       cardinality(public.halloween_codes())                                                                             as communes;
