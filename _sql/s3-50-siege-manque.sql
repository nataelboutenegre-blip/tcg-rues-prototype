-- s3-50 (22/11/2026, question de Cairnan217, « oui vas-y » de Nataël 18 h 27) : l'attaquant est prévenu quand une
-- défense fait que l'énergie qui attend dans son siège ne suffit plus pour finir. Une notification à chaque bascule
-- (« suffit » → « ne suffit plus »), pas à chaque défense. La cloche garde « il manque ≈ N ⚡ ».
-- Estimation : besoin = ⌈(résistance − jauge + bouclier) / (10 × multiplicateur)⌉, comme la fiche du siège.

alter table public.front_siege_alertes add column if not exists manque integer;

do $$
declare d text; n text;
begin
  d := pg_get_functiondef('public.siege_renforcer(text,uuid,integer)'::regprocedure);
  n := replace(d, $a$  v_premier boolean;   -- s3-43
$a$, $a$  v_premier boolean;   -- s3-43
  v_besoin_av integer; v_besoin_ap integer; v_att integer; v_manque integer; v_div numeric; v_res numeric; v_bcl numeric;   -- s3-50
$a$);
  n := replace(n, $a$  v_premier := not exists (select 1 from front_siege_alertes where siege_id = s.id and type = 'defendu');
  insert into front_siege_alertes (attaquant, siege_id, commune_code, type, defenseur, recul, degats_apres, resistance, devient_long)
  values (s.attaquant, s.id, p_code, 'defendu', v_uid, round(v_recul), round(greatest(0, s.degats - v_recul)),
          round(siege_resistance(p_code, p_attaquant)), s.long_depuis is null);
  if v_premier then
    perform notifier_joueur(s.attaquant,
      '🛡️ ' || coalesce((select pseudo from joueurs where id = v_uid), 'Le défenseur') || ' défend ' || coalesce((select nom from communes where code = p_code), 'ta cible'),
      '−' || round(v_recul) || ' sur ta jauge' || case when s.long_depuis is null then ' · le siège devient long' else '' end,
      './?onglet=combat', 'defendu-' || s.id);
  end if;$a$, $a$  v_premier := not exists (select 1 from front_siege_alertes where siege_id = s.id and type = 'defendu');
  -- s3-50 : l'énergie qui attend suffit-elle encore ?
  v_res := siege_resistance(p_code, p_attaquant); v_bcl := siege_garnison(p_code) * siege_n('bouclier_par_energie');
  v_div := greatest(0.1, v_pts * coalesce(siege_mult(s.attaquant, p_code), 1));
  v_att := coalesce(s.attente, 0);
  v_besoin_av := ceil(greatest(0, v_res - s.degats + v_bcl) / v_div);
  v_besoin_ap := ceil(greatest(0, v_res - greatest(0, s.degats - v_recul) + v_bcl) / v_div);
  v_manque := case when v_att > 0 and v_att < v_besoin_ap then v_besoin_ap - v_att end;
  insert into front_siege_alertes (attaquant, siege_id, commune_code, type, defenseur, recul, degats_apres, resistance, devient_long, manque)
  values (s.attaquant, s.id, p_code, 'defendu', v_uid, round(v_recul), round(greatest(0, s.degats - v_recul)),
          round(v_res), s.long_depuis is null, v_manque);
  if v_premier then
    perform notifier_joueur(s.attaquant,
      '🛡️ ' || coalesce((select pseudo from joueurs where id = v_uid), 'Le défenseur') || ' défend ' || coalesce((select nom from communes where code = p_code), 'ta cible'),
      '−' || round(v_recul) || ' sur ta jauge' || case when s.long_depuis is null then ' · le siège devient long' else '' end
        || case when v_manque is not null and v_att >= v_besoin_av then ' · il manque ≈ ' || v_manque || ' ⚡ pour finir' else '' end,
      './?onglet=combat', 'defendu-' || s.id);
  elsif v_manque is not null and v_att >= v_besoin_av then   -- s3-50 : la bascule, même après la première défense
    perform notifier_joueur(s.attaquant,
      '⚠️ Ton siège de ' || coalesce((select nom from communes where code = p_code), 'ta cible') || ' ne finira plus tout seul',
      coalesce((select pseudo from joueurs where id = v_uid), 'Le défenseur') || ' a renforcé : tes ' || v_att || ' ⚡ en attente ne suffisent plus, il manque ≈ ' || v_manque || ' ⚡',
      './?onglet=combat', 'manque-' || s.id);
  end if;$a$);
  if n = d or position('s3-50 : la bascule' in n) = 0 then raise exception 's3-50 : siege_renforcer inchangée'; end if;
  execute n;

  d := pg_get_functiondef('public.mes_alertes_siege()'::regprocedure);
  n := replace(d, $a$bool_or(a.devient_long) as devient_long,$a$, $a$bool_or(a.devient_long) as devient_long, (array_agg(a.manque order by a.le desc, a.id desc))[1] as manque,$a$);
  if n = d then raise exception 's3-50 : mes_alertes_siege inchangée'; end if;
  execute n;
end $$;
