-- s3-70 (24/11/2026, après la question de D.C.A) : deux protections pour le défenseur.
-- 1. ASSAUT FINAL ANNONCÉ : sur un siège long déjà défendu, la jauge s'arrête juste sous le plein ;
--    le défenseur est prévenu (« tombe dans 30 min ») ; s'il la repousse sous les 2/3, l'assaut est annulé ;
--    sinon la commune tombe au bout des 30 min (siege_tick), ou à la vague suivante après ce délai.
-- 2. GROSSE VAGUE : une vague qui remplit au moins la moitié de la jauge d'un siège en cours prévient le défenseur.
--    Et l'alerte « en danger » (2/3) se réarme quand la jauge est repoussée sous les 2/3.
-- Réglage : config_jeu 'siege' → assaut_min (30). 0 = assaut final coupé.
alter table front_sieges add column if not exists assaut_le timestamptz;
update config_jeu set valeur = (valeur::jsonb || '{"assaut_min": 30}')::text where cle = 'siege' and not (valeur::jsonb ? 'assaut_min');

do $m$
declare d text; n text;
begin
  -- siege_appliquer
  d := pg_get_functiondef('public.siege_appliquer(bigint,integer)'::regprocedure); n := d;
  n := replace(n, $a$g front_garnisons; v_nom text; v_pseudo text;$a$, $b$g front_garnisons; v_nom text; v_pseudo text; v_cap numeric; v_assaut boolean := false;   /* s3-70 */$b$);
  n := replace(n, $a$v_res := siege_resistance(s.commune_code, s.attaquant); v_plafond := siege_plafond(p_id);
$a$, $b$v_res := siege_resistance(s.commune_code, s.attaquant); v_plafond := siege_plafond(p_id);
  if s.long_depuis is not null and s.defendu and coalesce(siege_n('assaut_min'), 0) > 0 then   -- s3-70 : assaut final annoncé
    if s.assaut_le is not null and s.degats < v_res * 2 / 3 then s.assaut_le := null; update front_sieges set assaut_le = null where id = p_id; end if;
    if s.assaut_le is null or s.assaut_le > now() then v_cap := v_res - 0.5; end if;
  end if;
  if s.alerte_danger and s.degats < v_res * 2 / 3 then s.alerte_danger := false; update front_sieges set alerte_danger = false where id = p_id; end if;   -- s3-70 : l'alerte se réarme
$b$);
  n := replace(n, $a$    if v_nuit_cap is not null and s.degats >= v_nuit_cap then exit; end if;   -- s3-58
$a$, $b$    if v_nuit_cap is not null and s.degats >= v_nuit_cap then exit; end if;   -- s3-58
    if v_cap is not null and s.degats >= v_cap then exit; end if;   -- s3-70
$a$);
  n := replace(n, $a$    if v_nuit_cap is not null then v_d := least(v_d, greatest(0, v_nuit_cap - s.degats)); end if;   -- s3-58
$a$, $b$    if v_nuit_cap is not null then v_d := least(v_d, greatest(0, v_nuit_cap - s.degats)); end if;   -- s3-58
    if v_cap is not null then v_d := least(v_d, greatest(0, v_cap - s.degats)); end if;   -- s3-70
$b$);
  n := replace(n, $a$  if not s.alerte_danger and s.degats >= v_res * 2 / 3 then$a$, $b$  if v_cap is not null and s.degats >= v_cap and s.assaut_le is null then   -- s3-70 : l'assaut final est annoncé
    v_assaut := true;
    update front_sieges set assaut_le = now() + make_interval(mins => siege_n('assaut_min')::int), alerte_danger = true where id = p_id;
    select c.nom into v_nom from communes c where c.code = s.commune_code; select pseudo into v_pseudo from joueurs where id = s.attaquant;
    perform notifier_joueur(v_proprio, 'Assaut final sur ' || v_nom, coalesce(v_pseudo, 'Un joueur') || ' a rempli sa jauge : ' || v_nom || ' tombe dans '
      || siege_n('assaut_min')::int || ' min si tu ne la repousses pas sous les deux tiers.', './?onglet=defense', 'danger-' || s.commune_code);
    perform clan_appel_aide(v_proprio, s.commune_code, v_nom, v_pseudo);
  end if;
  if not s.alerte_danger and not v_assaut and s.degats >= v_res * 2 / 3 then$b$);
  if (length(n) - length(replace(n, 's3-70', ''))) / 5 < 6 then raise exception 's3-70 : siege_appliquer, remplacements incomplets'; end if;
  execute n;

  -- siege_tick : l'assaut arrivé à son heure
  d := pg_get_functiondef('public.siege_tick()'::regprocedure);
  n := replace(d, $a$  for r in select id from front_sieges where fini_le is null and derniere_vague < now()$a$,
    $b$  for r in select f.id from front_sieges f where f.fini_le is null and f.assaut_le is not null and f.assaut_le <= now()
                and f.degats >= siege_resistance(f.commune_code, f.attaquant) - 0.51 loop   -- s3-70
    perform siege_conquerir(r.id); n := n + 1; end loop;
  for r in select id from front_sieges where fini_le is null and derniere_vague < now()$b$);
  if n = d then raise exception 's3-70 : siege_tick introuvable'; end if;
  execute n;

  -- siege_vue : l'heure de l'assaut
  d := pg_get_functiondef('public.siege_vue(bigint)'::regprocedure);
  n := replace(d, $a$'fini_le', s.fini_le, 'resultat', s.resultat);$a$, $b$'fini_le', s.fini_le, 'resultat', s.resultat, 'assaut_le', s.assaut_le);   -- s3-70$b$);
  if n = d then raise exception 's3-70 : siege_vue introuvable'; end if;
  execute n;

  -- siege_vague : la grosse vague prévient
  d := pg_get_functiondef('public.siege_vague(text,integer)'::regprocedure);
  n := replace(d, $a$v_nom text; v_pseudo text;
begin$a$, $b$v_nom text; v_pseudo text;
  v_avant numeric; v_alerte boolean; v_assaut timestamptz; s2 front_sieges; v_r numeric;   -- s3-70
begin$b$);
  n := replace(n, $a$  v_reste := siege_appliquer(v_id, p_energie + coalesce(v_att, 0));
  update front_sieges set attente = attente + v_reste where id = v_id and fini_le is null;
$a$, $b$  select degats, alerte_danger, assaut_le into v_avant, v_alerte, v_assaut from front_sieges where id = v_id;   -- s3-70
  v_reste := siege_appliquer(v_id, p_energie + coalesce(v_att, 0));
  update front_sieges set attente = attente + v_reste where id = v_id and fini_le is null;
  if not v_neuf then   -- s3-70 : une vague qui remplit la moitié de la jauge prévient le défenseur
    select * into s2 from front_sieges where id = v_id;
    v_r := siege_resistance(s2.commune_code, s2.attaquant);
    if s2.fini_le is null and v_r > 0 and s2.degats - coalesce(v_avant, 0) >= v_r / 2
       and s2.alerte_danger is not distinct from v_alerte and s2.assaut_le is not distinct from v_assaut then
      select pseudo into v_pseudo from joueurs where id = v_uid;
      perform notifier_joueur(s2.defenseur, 'Grosse vague sur ' || v_nom, coalesce(v_pseudo, 'Un joueur') || ' vient de remplir la jauge de ' || v_nom
        || ' à ' || least(99, round(100 * s2.degats / v_r))::int || ' %. Renforce-la.', './?onglet=defense', 'danger-' || p_code);
    end if;
  end if;
$b$);
  if (length(n) - length(replace(n, 's3-70', ''))) / 5 < 3 then raise exception 's3-70 : siege_vague, remplacements incomplets'; end if;
  execute n;
end $m$;
