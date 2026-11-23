-- s3-62 (23/11/2026) : Défendre — quand ma commune peut-elle tomber ? (idée de Cairnan217, choix B de Nataël)
-- siege_chute(id) : l'heure au plus tôt (rythme du siège long ou délai de l'éclair, la nuit repoussée à 7 h),
-- l'énergie qu'il faut encore à l'attaquant, celle qui attend déjà dans son siège, et si elle suffit
-- (alors la commune tombera vers cette heure-là sans autre vague). Ajouté à sieges_contre_moi_v2 (vue du défenseur).
create or replace function public.siege_chute(p_id bigint)
returns jsonb language plpgsql stable security definer set search_path to 'public' as $$
declare s front_sieges; v_res numeric; v_reste numeric; v_mult numeric; v_besoin integer; v_d numeric; v_debut timestamptz;
  v_t timestamptz; v_h numeric; v_cfg jsonb := siege_cfg();
begin
  select * into s from front_sieges where id = p_id and fini_le is null;
  if s.id is null then return null; end if;
  v_res := siege_resistance(s.commune_code, s.attaquant);
  v_reste := greatest(0, v_res - s.degats) + siege_garnison(s.commune_code) * siege_n('bouclier_par_energie');
  v_mult := greatest(0.1, coalesce(siege_mult(s.attaquant, s.commune_code), 1));
  v_besoin := ceil(v_reste / (siege_n('points_par_energie') * v_mult));
  -- le rythme : siège long (depuis long_depuis) ou éclair (depuis cree_le) ; sans délai, tout de suite
  if s.long_depuis is not null then v_d := siege_tier_n('duree_long_min', s.tier); v_debut := s.long_depuis;
  else v_d := siege_tier_n('eclair_min', s.tier); v_debut := s.cree_le; end if;
  if v_d is null or v_res <= 0 then v_t := now();
  else v_t := greatest(now(), v_debut + make_interval(secs => greatest(0, (coalesce(s.envoyes_long, 0) + v_reste) / v_res - siege_n('depart_long')) * v_d * 60)); end if;
  -- l'énergie en attente part toutes les 5 minutes
  if coalesce(s.attente, 0) >= v_besoin then v_t := v_t + interval '5 minutes'; end if;
  -- la nuit, le Front dort : repoussé à 7 h (heure de Paris)
  if coalesce((v_cfg->'nuit'->>'actif')::int, 0) = 1 then
    v_h := extract(hour from v_t at time zone 'Europe/Paris');
    if v_h >= coalesce((v_cfg->'nuit'->>'debut')::numeric, 0) and v_h < coalesce((v_cfg->'nuit'->>'fin')::numeric, 7) then
      v_t := ((v_t at time zone 'Europe/Paris')::date + make_interval(hours => coalesce((v_cfg->'nuit'->>'fin')::int, 7))) at time zone 'Europe/Paris' + interval '5 minutes';
    end if;
  end if;
  return jsonb_build_object('plus_tot', v_t, 'besoin', v_besoin, 'attente', coalesce(s.attente, 0), 'suffit', coalesce(s.attente, 0) >= v_besoin,
                            'maintenant', v_t <= now() + interval '1 minute');
end; $$;
revoke all on function public.siege_chute(bigint) from public, anon, authenticated;   -- lu seulement par sieges_contre_moi_v2

create or replace function public.sieges_contre_moi_v2()
returns jsonb language sql stable security definer set search_path to 'public' as $function$
  select coalesce(jsonb_agg(siege_vue(s.id) || jsonb_build_object('nom', c.nom, 'dept', c.departement, 'garnison', siege_garnison(s.commune_code),
                                                                  'chute', siege_chute(s.id))   -- s3-62
                  order by s.degats / greatest(1, siege_resistance(s.commune_code, s.attaquant)) desc), '[]'::jsonb)
    from front_sieges s join communes c on c.code = s.commune_code join possessions po on po.commune_code = s.commune_code and po.joueur_id = auth.uid()
   where s.fini_le is null; $function$;
