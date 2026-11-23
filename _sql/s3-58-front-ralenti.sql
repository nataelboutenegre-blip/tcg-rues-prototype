-- s3-58 (23/11/2026, décisions de Nataël 11 h 39 – 11 h 52, discussion Discord H34VEN / Bonjean / Maroli / Cairnan217)
--  1. Le Front dort la nuit (0 h – 7 h, heure de Paris, choix B de Nataël à 12 h 49) : pas de nouveau siège ni de vague
--     (siege_vague refuse), et siege_tick laisse l'énergie en attente jusqu'à 7 h. Renforcer reste possible.
--     Filet : si siege_appliquer tournait quand même la nuit, la jauge s'arrête juste au-dessus des 2/3.
--  2. Proximité graduée (siege_mult) : 0 commune à 20 km ×0,8 (ou Artillerie) ; 1-2 ×0,9 ; 3-5 ×1 ; 6+ ×1,1.
--     Avant : 0 ×0,8 ; 1 ×1 ; 2+ ×1,1 (64 % des conquêtes du 22/11 avaient le maximum).
--  3. Rempart (siege_resistance) : +5 % de résistance par commune du propriétaire à moins de 10 km au-delà de 3,
--     plafonné à +50 % (13 voisines). En outre-mer, communes_proches compte tout le département.
--  Tout se règle dans config_jeu 'siege' (clés nuit, prox_paliers, rempart). Retour arrière :
--    update config_jeu set valeur = (valeur::jsonb || '{"nuit": {"actif": 0}, "rempart": {"actif": 0}, "prox_paliers": [[1, 1], [2, 1.1]]}')::text where cle = 'siege';
--  (prox_paliers [[1,1],[2,1.1]] redonne exactement l'ancien barème.)

update config_jeu set valeur = (valeur::jsonb
  || '{"nuit": {"actif": 1, "debut": 0, "fin": 7, "plafond": 0.667},
       "prox_paliers": [[1, 0.9], [3, 1.0], [6, 1.1]],
       "rempart": {"actif": 1, "rayon_km": 10, "seuil": 3, "par_commune": 0.05, "max": 0.5}}'::jsonb)::text
 where cle = 'siege';

create or replace function public.siege_nuit() returns boolean
language sql stable security definer set search_path to 'public' as $$
  select coalesce((c->'nuit'->>'actif')::int, 0) = 1
     and (coalesce((c->'nuit'->>'force')::int, 0) = 1
          or extract(hour from now() at time zone 'Europe/Paris') >= coalesce((c->'nuit'->>'debut')::numeric, 0)
         and extract(hour from now() at time zone 'Europe/Paris') <  coalesce((c->'nuit'->>'fin')::numeric, 7))
  from (select siege_cfg() c) x;
$$;

create or replace function public.siege_rempart(p_code text, p_proprio uuid) returns numeric
language sql stable security definer set search_path to 'public' as $$
  select case when coalesce((c->'rempart'->>'actif')::int, 0) <> 1 or p_proprio is null then 1
    else 1 + least(coalesce((c->'rempart'->>'max')::numeric, 0.5),
                   coalesce((c->'rempart'->>'par_commune')::numeric, 0.05)
                   * greatest(0, communes_proches(p_proprio, p_code, coalesce((c->'rempart'->>'rayon_km')::numeric, 10))
                                 - coalesce((c->'rempart'->>'seuil')::numeric, 3))) end
  from (select siege_cfg() c) x;
$$;

create or replace function public.siege_prox(p_n integer) returns numeric
language sql stable security definer set search_path to 'public' as $$
  select coalesce((select (e->>1)::numeric from jsonb_array_elements(siege_cfg()->'prox_paliers') e
                    where p_n >= (e->>0)::int order by (e->>0)::int desc limit 1), 1);
$$;

revoke all on function public.siege_nuit(), public.siege_rempart(text, uuid), public.siege_prox(integer) from public, anon;
grant execute on function public.siege_nuit(), public.siege_rempart(text, uuid), public.siege_prox(integer) to authenticated;

do $do$
declare d text; n text;
begin
  -- siege_mult : la proximité graduée
  d := pg_get_functiondef('public.siege_mult(uuid, text)'::regprocedure);
  n := replace(d, 'else siege_n(''prox_aucune'') end) when v_proches = 1 then 1 else siege_n(''prox_deux'') end;',
                  'else siege_n(''prox_aucune'') end) else siege_prox(v_proches) end;   -- s3-58 : proximité graduée');
  if n = d then raise exception 's3-58 : siege_mult introuvable'; end if;
  execute n;
  -- siege_resistance : le rempart
  d := pg_get_functiondef('public.siege_resistance(text, uuid)'::regprocedure);
  n := replace(d, '                             and r.fin > now() and r.fonds > 0 and r.etouffee_le is null limit 1), 0))',
                  '                             and r.fin > now() and r.fonds > 0 and r.etouffee_le is null limit 1), 0))
         * siege_rempart(p_code, po.joueur_id)   -- s3-58 : le rempart');
  if n = d then raise exception 's3-58 : siege_resistance introuvable'; end if;
  execute n;
  -- siege_appliquer : pas de prise la nuit
  d := pg_get_functiondef('public.siege_appliquer(bigint, integer)'::regprocedure);
  n := replace(d, 'v_pts numeric := siege_n(''points_par_energie''); v_d numeric;',
                  'v_pts numeric := siege_n(''points_par_energie''); v_d numeric; v_nuit_cap numeric; /* s3-58 */');
  n := replace(n, '  while v_reste > 0 loop
    if v_plafond is not null and s.envoyes_long >= v_plafond then exit; end if;',
                  '  if siege_nuit() then v_nuit_cap := ceil(v_res * coalesce((siege_cfg()->''nuit''->>''plafond'')::numeric, 0.667)); end if;   -- s3-58 : la nuit, la jauge s''arrête aux 2/3
  while v_reste > 0 loop
    if v_plafond is not null and s.envoyes_long >= v_plafond then exit; end if;
    if v_nuit_cap is not null and s.degats >= v_nuit_cap then exit; end if;   -- s3-58');
  n := replace(n, '    s.degats := s.degats + v_d;
    if s.degats >= v_res then',
                  '    if v_nuit_cap is not null then v_d := least(v_d, greatest(0, v_nuit_cap - s.degats)); end if;   -- s3-58
    s.degats := s.degats + v_d;
    if s.degats >= v_res then');
  if n = d or position('v_nuit_cap := ceil' in n) = 0 or position('least(v_d, greatest(0, v_nuit_cap' in n) = 0 then raise exception 's3-58 : siege_appliquer introuvable'; end if;
  execute n;
  -- siege_vague : le Front dort
  d := pg_get_functiondef('public.siege_vague(text, integer)'::regprocedure);
  n := replace(d, '  if p_energie is null or p_energie < 1 then raise exception ''Mets au moins 1 énergie''; end if;',
                  '  if siege_nuit() then raise exception ''Le Front dort entre 0 h et 7 h : reviens à 7 h''; end if;   -- s3-58
  if p_energie is null or p_energie < 1 then raise exception ''Mets au moins 1 énergie''; end if;');
  if n = d then raise exception 's3-58 : siege_vague introuvable'; end if;
  execute n;
  -- siege_tick : l'énergie en attente ne part pas la nuit
  d := pg_get_functiondef('public.siege_tick()'::regprocedure);
  n := replace(d, 'for r in select id, attente from front_sieges where fini_le is null and attente > 0 order by id loop',
                  'for r in select id, attente from front_sieges where fini_le is null and attente > 0 and not siege_nuit() order by id loop   -- s3-58');
  if n = d then raise exception 's3-58 : siege_tick introuvable'; end if;
  execute n;
end $do$;
