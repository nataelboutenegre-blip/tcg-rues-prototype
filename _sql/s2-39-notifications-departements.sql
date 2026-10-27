-- ===========================================================================
--  TerraFront — notifications par département (27 octobre 2026)
--  (aperçu « Par département » montré à Nataël le 27/10)
--
--  Complète s2-38 (déjà passé). Deux listes de départements dans les réglages :
--    sourdine_dep : plus aucune alerte d'attaque pour mes communes de ces
--                   départements (cloche et téléphone) ;
--    alerte_dep   : prévenu DÈS LE 1er ROUND gagné contre moi, quelle que soit
--                   la rareté (le seuil ne s'applique pas).
--  Un département est dans l'une OU l'autre liste (en ajouter un dans une
--  liste le retire de l'autre). 120 au plus par liste.
--
--  Téléphone : aujourd'hui « X est en danger » part au 2e round
--  (notif_danger_siege). Pour les départements « dès la 1re attaque », une
--  2e fonction, COPIÉE EN BASE depuis notif_danger_siege (jamais lue ici),
--  part au 1er round : « X est attaquée ». Même étiquette, donc l'alerte du
--  2e round remplace celle du 1er sur le téléphone. Si un texte attendu n'est
--  pas trouvé exactement une fois, cette étape est SAUTÉE (NOTICE) et le
--  reste passe : contrôle tel_premier_round false. Rejouable.
-- ===========================================================================

-- les préférences, avec les deux listes de départements
create or replace function public.notif_prefs_de(p_joueur uuid)
 returns jsonb language sql stable security definer set search_path to 'public'
as $f$
  select jsonb_build_object(
    'jeu',          (notif_defaut() -> 'jeu') || coalesce(np.prefs -> 'jeu', '{}'::jsonb),
    'tel',          (notif_defaut() -> 'tel') || coalesce(np.prefs -> 'tel', '{}'::jsonb),
    'seuil',        coalesce(np.prefs -> 'seuil', notif_defaut() -> 'seuil'),
    'sourdine',     coalesce(np.prefs -> 'sourdine', '[]'::jsonb),
    'sourdine_dep', coalesce(np.prefs -> 'sourdine_dep', '[]'::jsonb),
    'alerte_dep',   coalesce(np.prefs -> 'alerte_dep', '[]'::jsonb))
  from (select p_joueur as id) moi
  left join notif_preferences np on np.joueur_id = moi.id;
$f$;

-- mettre un département dans une liste (ou l'en sortir)
create or replace function public.notif_departement(p_liste text, p_dep text, p_on boolean)
 returns jsonb language plpgsql security definer set search_path to 'public'
as $f$
declare v_uid uuid := auth.uid(); v_cle text; v_autre text; v_l jsonb; v_a jsonb;
begin
  if v_uid is null then raise exception 'Non connecte'; end if;
  if p_liste not in ('sourdine', 'alerte') or p_on is null then raise exception 'Réglage inconnu'; end if;
  if not exists (select 1 from communes c where c.departement = p_dep) then raise exception 'Département inconnu'; end if;
  v_cle   := case p_liste when 'sourdine' then 'sourdine_dep' else 'alerte_dep' end;
  v_autre := case p_liste when 'sourdine' then 'alerte_dep' else 'sourdine_dep' end;
  insert into notif_preferences(joueur_id) values (v_uid) on conflict do nothing;
  select coalesce(prefs -> v_cle, '[]'::jsonb), coalesce(prefs -> v_autre, '[]'::jsonb) into v_l, v_a
    from notif_preferences where joueur_id = v_uid for update;
  v_l := coalesce((select jsonb_agg(x) from jsonb_array_elements_text(v_l) x where x <> p_dep), '[]'::jsonb);
  if p_on then
    if jsonb_array_length(v_l) >= 120 then raise exception '120 départements au maximum'; end if;
    v_l := v_l || to_jsonb(p_dep);
    v_a := coalesce((select jsonb_agg(x) from jsonb_array_elements_text(v_a) x where x <> p_dep), '[]'::jsonb);
  end if;
  update notif_preferences set prefs = prefs || jsonb_build_object(v_cle, v_l, v_autre, v_a), maj = now() where joueur_id = v_uid;
  return notif_prefs_de(v_uid);
end;
$f$;

-- vrai si la commune est dans un département « dès la 1re attaque » du joueur
create or replace function public.notif_alerte_dep(p_joueur uuid, p_code text)
 returns boolean language sql stable security definer set search_path to 'public'
as $f$
  select coalesce((select (np.prefs -> 'alerte_dep') ? c.departement
                     from notif_preferences np, communes c
                    where np.joueur_id = p_joueur and c.code = p_code), false);
$f$;

-- le filtre du téléphone, avec les départements
create or replace function public.notif_coupee(p_joueur uuid, p_tag text)
 returns boolean language plpgsql stable security definer set search_path to 'public'
as $f$
declare v_p jsonb; v_code text; v_tier text; v_dep text;
  v_ordre text[] := array['commun','peucommun','rare','epique','legendaire'];
begin
  if not exists (select 1 from notif_preferences np where np.joueur_id = p_joueur) then return false; end if;
  v_p := notif_prefs_de(p_joueur);
  if p_tag = 'paquet' then return not coalesce((v_p #>> '{tel,paquet}')::boolean, true); end if;
  if p_tag like 'danger-%' then
    if not coalesce((v_p #>> '{tel,attaque}')::boolean, true) then return true; end if;
    v_code := substr(p_tag, 8);
    if (v_p -> 'sourdine') ? v_code then return true; end if;
    select c.tier, c.departement into v_tier, v_dep from communes c where c.code = v_code;
    if (v_p -> 'sourdine_dep') ? v_dep then return true; end if;
    if (v_p -> 'alerte_dep') ? v_dep then return false; end if;   -- s2-39 : le seuil ne s'applique pas
    if v_tier is not null and array_position(v_ordre, v_tier) < array_position(v_ordre, coalesce(v_p ->> 'seuil', 'commun')) then
      return true;
    end if;
  end if;
  return false;
end;
$f$;

revoke all on function public.notif_prefs_de(uuid) from public, anon, authenticated;
revoke all on function public.notif_coupee(uuid, text) from public, anon, authenticated;
revoke all on function public.notif_alerte_dep(uuid, text) from public, anon, authenticated;
revoke all on function public.notif_departement(text, text, boolean) from public, anon;
grant execute on function public.notif_departement(text, text, boolean) to authenticated;

-- le téléphone dès le 1er round, pour les départements choisis
do $g$
declare
  v_def text; v_trg text; n integer; v_ok boolean := true;
  r text[];
  v_rempl text[][] := array[
    [$a$FUNCTION public.notif_danger_siege()$a$,
     $a$FUNCTION public.notif_premiere_attaque()$a$],
    [$a$new.victoires_consecutives = 2 and (tg_op = 'INSERT' or old.victoires_consecutives is distinct from 2)$a$,
     $a$new.victoires_consecutives = 1 and (tg_op = 'INSERT' or old.victoires_consecutives is distinct from 1)$a$],
    [$a$if v_proprio is not null and v_proprio <> new.attacker_id then$a$,
     $a$if v_proprio is not null and v_proprio <> new.attacker_id and notif_alerte_dep(v_proprio, new.commune_code) then$a$],
    [$a$' est en danger'$a$,
     $a$' est attaquée'$a$],
    [$a$' a gagné 2 rounds d''affilée. Plus qu''une victoire avant de la perdre : défends-la ou pose un bouclier.'$a$,
     $a$' a gagné un round. Encore 2 victoires d''affilée et elle tombe : défends-la ou pose un bouclier.'$a$]];
begin
  if to_regprocedure('public.notif_danger_siege()') is null then
    raise notice 's2-39 : notif_danger_siege absente, étape du téléphone sautée'; return;
  end if;
  v_def := pg_get_functiondef('public.notif_danger_siege()'::regprocedure);
  foreach r slice 1 in array v_rempl loop
    n := (length(v_def) - length(replace(v_def, r[1], ''))) / length(r[1]);
    if n <> 1 then
      raise notice 's2-39 : texte « % » trouvé % fois dans notif_danger_siege : étape du téléphone SAUTÉE (le reste est en place)', left(r[1], 40), n;
      return;
    end if;
    v_def := replace(v_def, r[1], r[2]);
  end loop;
  execute v_def;
  execute 'revoke all on function public.notif_premiere_attaque() from public, anon, authenticated';

  select pg_get_triggerdef(t.oid) into v_trg
    from pg_trigger t where t.tgname = 'trg_notif_danger' and t.tgrelid = 'public.sieges'::regclass;
  if v_trg is null then raise notice 's2-39 : déclencheur trg_notif_danger introuvable : étape du téléphone SAUTÉE'; return; end if;
  v_trg := replace(replace(v_trg, 'trg_notif_danger', 'trg_notif_premiere'), 'notif_danger_siege()', 'notif_premiere_attaque()');
  execute 'drop trigger if exists trg_notif_premiere on public.sieges';
  execute v_trg;
end
$g$;

-- Contrôle : tout doit être true (tel_premier_round false = étape sautée, le dire à Claude)
select
  (public.notif_prefs_de(gen_random_uuid()) ? 'alerte_dep')                                          as prefs_ok,
  has_function_privilege('authenticated', 'public.notif_departement(text,text,boolean)', 'execute')   as joueurs_ok,
  not has_function_privilege('anon', 'public.notif_departement(text,text,boolean)', 'execute')        as anon_ferme,
  not has_function_privilege('authenticated', 'public.notif_alerte_dep(uuid,text)', 'execute')        as interne_ferme,
  position('sourdine_dep' in pg_get_functiondef('public.notif_coupee(uuid,text)'::regprocedure)) > 0  as filtre_departements,
  exists (select 1 from pg_trigger where tgname = 'trg_notif_premiere')                               as tel_premier_round;
