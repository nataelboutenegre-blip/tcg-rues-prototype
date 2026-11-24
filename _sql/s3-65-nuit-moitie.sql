-- s3-65 (24/11/2026) : la nuit (0 h – 7 h, Paris), le Front ne dort plus : les attaques font moitié moins de dégâts.
-- Décision de Nataël à 8 h 58, après les plaintes sur la coupure (Saaslil, Arkhannou) et la ruée de 7 h
-- (97 conquêtes entre 7 h et 8 h le 24/11, contre 50 la veille).
-- config siege.nuit.mode : 'moitie' (dégâts × nuit.mult), 'plafond' (sièges ouverts, jauge arrêtée aux 2/3, version A),
--                          'ferme' (ni siège ni vague, version B du 23/11). Changer de mode est maintenant un réglage.
-- En mode 'moitie' : siege_mult × 0,5 la nuit (donc dégâts, estimations et fiches suivent) ; l'énergie mise en attente
-- avant minuit attend 7 h pour garder sa valeur, sauf si le joueur relance ce siège pendant la nuit.
-- Retour à la coupure : update config_jeu set valeur = jsonb_set(valeur::jsonb, '{nuit,mode}', '"ferme"')::text where cle = 'siege';
-- Tout couper       : update config_jeu set valeur = jsonb_set(valeur::jsonb, '{nuit,actif}', '0')::text where cle = 'siege';

update config_jeu set valeur = jsonb_set(valeur::jsonb, '{nuit}', (valeur::jsonb->'nuit') || '{"mode": "moitie", "mult": 0.5}'::jsonb)::text where cle = 'siege';

create or replace function public.siege_nuit_mode() returns text
language sql stable security definer set search_path to 'public' as $$
  select case when siege_nuit() then coalesce(siege_cfg()->'nuit'->>'mode', 'ferme') end;
$$;
create or replace function public.siege_nuit_debut() returns timestamptz
language sql stable security definer set search_path to 'public' as $$
  select ((now() at time zone 'Europe/Paris')::date + make_interval(hours => coalesce((siege_cfg()->'nuit'->>'debut')::int, 0))) at time zone 'Europe/Paris';
$$;
revoke all on function public.siege_nuit_mode(), public.siege_nuit_debut() from public, anon, authenticated;

do $do$
declare d text; n text;
begin
  d := pg_get_functiondef('public.siege_vague(text, integer)'::regprocedure);
  n := replace(d, 'if siege_nuit() then raise exception ''Le Front dort entre 0 h et 7 h : reviens à 7 h''; end if;',
                  'if siege_nuit_mode() = ''ferme'' then raise exception ''Le Front dort entre 0 h et 7 h : reviens à 7 h''; end if;   -- s3-65');
  if n = d then raise exception 's3-65 : siege_vague introuvable'; end if;
  execute n;
  d := pg_get_functiondef('public.siege_appliquer(bigint, integer)'::regprocedure);
  n := replace(d, 'if siege_nuit() then v_nuit_cap := ceil(', 'if siege_nuit_mode() in (''ferme'', ''plafond'') then v_nuit_cap := ceil(');
  if n = d then raise exception 's3-65 : siege_appliquer introuvable'; end if;
  execute n;
  d := pg_get_functiondef('public.siege_tick()'::regprocedure);
  n := replace(d, 'and attente > 0 and not siege_nuit() order by id loop',
                  'and attente > 0 and (siege_nuit_mode() is null or (siege_nuit_mode() = ''moitie'' and derniere_vague >= siege_nuit_debut())) order by id loop');
  if n = d then raise exception 's3-65 : siege_tick introuvable'; end if;
  execute n;
  d := pg_get_functiondef('public.siege_mult(uuid, text)'::regprocedure);
  n := replace(d, E'  return v_m;\nend;',
                  E'  if siege_nuit_mode() = ''moitie'' then v_m := v_m * coalesce((siege_cfg()->''nuit''->>''mult'')::numeric, 0.5); end if;   -- s3-65 : la nuit, moitié moins\n  return v_m;\nend;');
  if n = d then raise exception 's3-65 : siege_mult introuvable'; end if;
  execute n;
end $do$;

-- l'heure de chute (s3-62) : en mode « moitié », une commune peut tomber la nuit ; seule l'énergie qui dort attend 7 h
create or replace function public.siege_chute(p_id bigint)
returns jsonb language plpgsql stable security definer set search_path to 'public' as $$
declare s front_sieges; v_res numeric; v_reste numeric; v_mult numeric; v_besoin integer; v_d numeric; v_debut timestamptz;
  v_t timestamptz; v_h numeric; v_cfg jsonb := siege_cfg(); v_mode text; v_nuit_deb timestamptz;
begin
  select * into s from front_sieges where id = p_id and fini_le is null;
  if s.id is null then return null; end if;
  v_res := siege_resistance(s.commune_code, s.attaquant);
  v_reste := greatest(0, v_res - s.degats) + siege_garnison(s.commune_code) * siege_n('bouclier_par_energie');
  v_mult := greatest(0.1, coalesce(siege_mult(s.attaquant, s.commune_code), 1));
  v_besoin := ceil(v_reste / (siege_n('points_par_energie') * v_mult));
  if s.long_depuis is not null then v_d := siege_tier_n('duree_long_min', s.tier); v_debut := s.long_depuis;
  else v_d := siege_tier_n('eclair_min', s.tier); v_debut := s.cree_le; end if;
  if v_d is null or v_res <= 0 then v_t := now();
  else v_t := greatest(now(), v_debut + make_interval(secs => greatest(0, (coalesce(s.envoyes_long, 0) + v_reste) / v_res - siege_n('depart_long')) * v_d * 60)); end if;
  if coalesce(s.attente, 0) >= v_besoin then v_t := v_t + interval '5 minutes'; end if;
  if coalesce((v_cfg->'nuit'->>'actif')::int, 0) = 1 then
    v_mode := coalesce(v_cfg->'nuit'->>'mode', 'ferme');
    v_h := extract(hour from v_t at time zone 'Europe/Paris');
    v_nuit_deb := ((v_t at time zone 'Europe/Paris')::date + make_interval(hours => coalesce((v_cfg->'nuit'->>'debut')::int, 0))) at time zone 'Europe/Paris';
    if v_h >= coalesce((v_cfg->'nuit'->>'debut')::numeric, 0) and v_h < coalesce((v_cfg->'nuit'->>'fin')::numeric, 7)
       and (v_mode <> 'moitie' or (coalesce(s.attente, 0) >= v_besoin and s.derniere_vague < v_nuit_deb)) then   -- s3-65
      v_t := ((v_t at time zone 'Europe/Paris')::date + make_interval(hours => coalesce((v_cfg->'nuit'->>'fin')::int, 7))) at time zone 'Europe/Paris' + interval '5 minutes';
    end if;
  end if;
  return jsonb_build_object('plus_tot', v_t, 'besoin', v_besoin, 'attente', coalesce(s.attente, 0), 'suffit', coalesce(s.attente, 0) >= v_besoin,
                            'maintenant', v_t <= now() + interval '1 minute');
end; $$;
revoke all on function public.siege_chute(bigint) from public, anon, authenticated;
