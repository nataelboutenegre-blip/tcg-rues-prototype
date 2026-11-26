-- s3-87 (26/11) : améliorer les bâtiments (niveaux 2 et 3, payés en lingots, 6 h de chantier).
-- Fonderie : réserve +10 par niveau · Banque : réserve 60/90/120 · Radar : portée 50/70/90 km
-- Artillerie : portée 50/65/80 km · Forteresse : rayon d'appui 20/25/30 km. +20 au classement par niveau.
-- Interrupteur : config_jeu 'batiments'.ameliorations_ouvertes (0 = tout revient aux valeurs de base).

alter table batiments add column if not exists niveau integer not null default 1;
alter table batiments add column if not exists niveau_pret_le timestamptz;

create table if not exists batiments_ameliorations (
  id bigserial primary key,
  joueur_id uuid not null,
  batiment_id bigint,
  type text not null,
  commune_code text,
  niveau integer not null,
  prix integer not null,
  le timestamptz not null default now(),
  pret_le timestamptz not null,
  saison text
);
alter table batiments_ameliorations enable row level security;
create index if not exists batiments_ameliorations_joueur on batiments_ameliorations (joueur_id, saison);

update config_jeu set valeur = (valeur::jsonb || '{"ameliorations_ouvertes": 1, "amelioration_h": 6, "ameliorations": {
  "fonderie":   {"prix": [15, 30], "val": [0, 10, 20]},
  "banque":     {"prix": [15, 30], "val": [60, 90, 120]},
  "radar":      {"prix": [20, 35], "val": [50, 70, 90]},
  "artillerie": {"prix": [20, 35], "val": [50, 65, 80]},
  "forteresse": {"prix": [15, 30], "val": [20, 25, 30]}}}'::jsonb)::text
 where cle = 'batiments';

-- le niveau qui agit (pendant le chantier : l'ancien)
create or replace function public.batiment_niv(b batiments) returns integer
 language sql stable set search_path to 'public'
as $$ select case when b.niveau_pret_le is not null and b.niveau_pret_le > now() then greatest(1, coalesce(b.niveau, 1) - 1) else coalesce(b.niveau, 1) end $$;

-- la valeur d'un niveau (null si les améliorations sont fermées : on retombe sur les réglages de base)
create or replace function public.batiment_val(p_type text, p_niv integer) returns numeric
 language sql stable security definer set search_path to 'public'
as $$ select (c.valeur::jsonb -> 'ameliorations' -> p_type -> 'val' ->> (greatest(1, least(3, p_niv)) - 1))::numeric
        from config_jeu c where c.cle = 'batiments' and coalesce((c.valeur::jsonb ->> 'ameliorations_ouvertes')::int, 0) = 1 $$;

-- portée (Radar, Artillerie) ou rayon d'appui (Forteresse) d'un bâtiment
create or replace function public.batiment_portee(b batiments) returns numeric
 language sql stable security definer set search_path to 'public'
as $$ select coalesce(batiment_val(b.type, batiment_niv(b)),
                      case b.type when 'radar' then coalesce(batiment_reglage('radar_portee_km'), 50)
                                  when 'artillerie' then coalesce(batiment_reglage('artillerie_portee_km'), 50)
                                  when 'forteresse' then batiment_reglage('forteresse_rayon_km') end) $$;

do $do$
declare d text; d2 text;
  procedure_remplacer text;
begin
  -- Fonderie : réserve +10 par niveau
  d := pg_get_functiondef('public.lingots_max_fonderies(uuid)'::regprocedure);
  d2 := replace(d, $a$then batiment_reglage('fonderie_max2') else batiment_reglage('fonderie_max') end;$a$,
    $b$then batiment_reglage('fonderie_max2') else batiment_reglage('fonderie_max') end
       + coalesce((select sum(coalesce(batiment_val('fonderie', batiment_niv(f)), 0)) from batiments f where f.joueur_id = p_uid and f.type = 'fonderie'), 0);   -- s3-87$b$);
  if d2 = d then raise exception 's3-87 : lingots_max_fonderies'; end if; execute d2;

  -- Banque : réserve selon le niveau
  d := pg_get_functiondef('public.banque_deposer(integer)'::regprocedure);
  d2 := replace(d, $a$  if b.pret_le > now() then raise exception 'Ta Banque n''est pas encore construite'; end if;$a$,
    $b$  if b.pret_le > now() then raise exception 'Ta Banque n''est pas encore construite'; end if;
  v_max := coalesce(batiment_val('banque', batiment_niv(b)), v_max)::integer;   -- s3-87$b$);
  if d2 = d then raise exception 's3-87 : banque_deposer'; end if; execute d2;
  d := pg_get_functiondef('public.banque_interets()'::regprocedure);
  d2 := replace(d, $a$set contenu = least(coalesce(batiment_reglage('banque_reserve'), 60),$a$,
    $b$set contenu = least(coalesce(batiment_val('banque', batiment_niv(batiments)), batiment_reglage('banque_reserve'), 60),   /* s3-87 */$b$);
  if d2 = d then raise exception 's3-87 : banque_interets'; end if; execute d2;

  -- Artillerie : portée
  d := pg_get_functiondef('public.artillerie_couvre(uuid, text)'::regprocedure);
  d2 := replace(d, $a$<= coalesce(batiment_reglage('artillerie_portee_km'), 50)$a$, $b$<= batiment_portee(b)   /* s3-87 */$b$);
  if d2 = d then raise exception 's3-87 : artillerie_couvre'; end if; execute d2;
  d := pg_get_functiondef('public.artillerie_infos(uuid)'::regprocedure);
  d2 := replace(d, $a$'style', coalesce(b.style, batiment_styles() -> 'artillerie' ->> 0),$a$,
    $b$'style', coalesce(b.style, batiment_styles() -> 'artillerie' ->> 0), 'portee_km', batiment_portee(b)::integer,   /* s3-87 */$b$);
  if d2 = d then raise exception 's3-87 : artillerie_infos'; end if; execute d2;

  -- Radar : portée
  d := pg_get_functiondef('public.radar_voit(uuid, text, uuid)'::regprocedure);
  d2 := replace(d, $a$<= coalesce(batiment_reglage('radar_portee_km'), 50)$a$, $b$<= batiment_portee(r)   /* s3-87 */$b$);
  if d2 = d then raise exception 's3-87 : radar_voit'; end if; execute d2;
  d := pg_get_functiondef('public.radar_reperer()'::regprocedure);
  d2 := replace(replace(d, $a$k.latitude between a.latitude - v_portee / 110.0 and a.latitude + v_portee / 110.0$a$,
                           $b$k.latitude between a.latitude - batiment_portee(r) / 110.0 and a.latitude + batiment_portee(r) / 110.0   /* s3-87 */$b$),
                $a$dist_km(a.latitude, a.longitude, k.latitude, k.longitude) <= v_portee$a$, $b$dist_km(a.latitude, a.longitude, k.latitude, k.longitude) <= batiment_portee(r)$b$);
  if d2 = d or d2 ~ '<= v_portee' then raise exception 's3-87 : radar_reperer'; end if; execute d2;
  d := pg_get_functiondef('public.radar_infos(uuid)'::regprocedure);
  d2 := replace(replace(d, $a$<= coalesce(batiment_reglage('radar_portee_km'), 50)),$a$, $b$<= batiment_portee(r)),$b$),
                $a$'style', coalesce(r.style, batiment_styles() -> 'radar' ->> 0),$a$,
                $b$'style', coalesce(r.style, batiment_styles() -> 'radar' ->> 0), 'portee_km', batiment_portee(r)::integer,   /* s3-87 */$b$);
  if d2 = d or d2 ~ 'batiment_reglage\(''radar_portee_km''\), 50\)\),' then raise exception 's3-87 : radar_infos'; end if; execute d2;

  -- Forteresse : rayon d'appui
  foreach procedure_remplacer in array array['public.siege_mult(uuid, text)', 'public.bonus_batiments(uuid, text)', 'public.batiments_effet(text)'] loop
    d := pg_get_functiondef(procedure_remplacer::regprocedure);
    d2 := replace(d, $a$batiment_reglage('forteresse_rayon_km')$a$, $b$batiment_portee(b)$b$);
    if d2 = d then raise exception 's3-87 : %', procedure_remplacer; end if; execute d2;
  end loop;

  -- Classement : +20 par niveau terminé cette saison
  d := pg_get_functiondef('public.score_batiments()'::regprocedure);
  d2 := replace(d, $a$  ids as (select joueur_id from bat union select joueur_id from bo union select joueur_id from re)$a$,
    $b$  niv as (   -- s3-87 : +20 par niveau d'amélioration terminé
    select a.joueur_id, count(*) * coalesce(score_reglage('bat_niveau'), 20) as pts
      from batiments_ameliorations a where a.saison = (select id from s) and a.pret_le <= now() group by a.joueur_id
  ),
  ids as (select joueur_id from bat union select joueur_id from bo union select joueur_id from re union select joueur_id from niv)$b$);
  d2 := replace(d2, $a$(coalesce(bat.pts, 0) + coalesce(bo.pts, 0) + coalesce(re.pts, 0))::integer$a$,
                    $b$(coalesce(bat.pts, 0) + coalesce(bo.pts, 0) + coalesce(re.pts, 0) + coalesce(niv.pts, 0))::integer$b$);
  d2 := replace(d2, $a$    left join re  on re.joueur_id  = i.joueur_id$a$, $b$    left join re  on re.joueur_id  = i.joueur_id
    left join niv on niv.joueur_id = i.joueur_id$b$);
  if d2 = d or d2 !~ 'niv.pts' or d2 !~ 'left join niv' then raise exception 's3-87 : score_batiments'; end if; execute d2;
end $do$;

-- Améliorer
create or replace function public.batiment_ameliorer(p_code text, p_type text)
 returns jsonb language plpgsql security definer set search_path to 'public'
as $function$
declare
  v_uid uuid := auth.uid();
  cfg jsonb := (select valeur::jsonb from config_jeu where cle = 'batiments');
  b batiments;
  v_prix integer;
  v numeric;
  v_pret timestamptz;
begin
  if v_uid is null then raise exception 'Non connecte'; end if;
  if coalesce((cfg ->> 'ameliorations_ouvertes')::int, 0) <> 1 then raise exception 'Les améliorations ne sont pas ouvertes'; end if;
  if cfg -> 'ameliorations' -> p_type is null then raise exception 'Ce bâtiment ne s''améliore pas'; end if;
  perform 1 from joueurs where id = v_uid for update;
  select * into b from batiments where joueur_id = v_uid and commune_code = p_code and type = p_type for update;
  if b.id is null then raise exception 'Ce bâtiment n''est pas à toi'; end if;
  if b.pret_le > now() then raise exception 'Attends que le bâtiment soit prêt (construction ou déplacement en cours)'; end if;
  if b.niveau_pret_le is not null and b.niveau_pret_le > now() then raise exception 'Une amélioration est déjà en cours'; end if;
  if coalesce(b.niveau, 1) >= 3 then raise exception 'Ce bâtiment est déjà au niveau maximum'; end if;
  v_prix := (cfg -> 'ameliorations' -> p_type -> 'prix' ->> (coalesce(b.niveau, 1) - 1))::integer;
  if v_prix is null then raise exception 'Prix introuvable'; end if;
  v := lingots_figer(v_uid);
  if v < v_prix then raise exception 'Il te faut % lingots (tu en as %)', v_prix, floor(v)::integer; end if;
  update joueurs set lingots = lingots - v_prix where id = v_uid;
  v_pret := now() + make_interval(hours => coalesce((cfg ->> 'amelioration_h')::int, 6));
  update batiments set niveau = coalesce(niveau, 1) + 1, niveau_pret_le = v_pret where id = b.id;
  insert into batiments_ameliorations (joueur_id, batiment_id, type, commune_code, niveau, prix, pret_le, saison)
  values (v_uid, b.id, p_type, p_code, coalesce(b.niveau, 1) + 1, v_prix, v_pret, saison_en_cours_id());
  return jsonb_build_object('niveau', coalesce(b.niveau, 1) + 1, 'pret_le', v_pret, 'lingots', floor(v - v_prix)::integer);
end;
$function$;
revoke all on function public.batiment_ameliorer(text, text) from public, anon;
grant execute on function public.batiment_ameliorer(text, text) to authenticated;

-- Mes niveaux (pour l'écran)
create or replace function public.mes_batiments_niveaux()
 returns jsonb language sql stable security definer set search_path to 'public'
as $function$
  select jsonb_build_object(
    'ouvertes', coalesce(((select valeur::jsonb from config_jeu where cle = 'batiments') ->> 'ameliorations_ouvertes')::int, 0) = 1,
    'heures', coalesce(((select valeur::jsonb from config_jeu where cle = 'batiments') ->> 'amelioration_h')::int, 6),
    'points', coalesce(score_reglage('bat_niveau'), 20)::integer,
    'regles', (select valeur::jsonb -> 'ameliorations' from config_jeu where cle = 'batiments'),
    'liste', coalesce((select jsonb_agg(jsonb_build_object('code', b.commune_code, 'type', b.type, 'niveau', batiment_niv(b),
                         'vise', case when b.niveau_pret_le > now() then b.niveau end, 'pret_le', case when b.niveau_pret_le > now() then b.niveau_pret_le end,
                         'actif', b.pret_le <= now()))
                         from batiments b where b.joueur_id = auth.uid()
                          and b.type in ('fonderie', 'banque', 'radar', 'artillerie', 'forteresse')), '[]'::jsonb));
$function$;
revoke all on function public.mes_batiments_niveaux() from public, anon;
grant execute on function public.mes_batiments_niveaux() to authenticated;
