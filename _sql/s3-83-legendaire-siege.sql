-- s3-83 : légendaires plus prenables face à un défenseur actif (26/11).
-- A. Sur une légendaire, l'assaut final ne s'annule que si la jauge repasse sous la MOITIÉ (au lieu des deux tiers).
-- B. Sur une légendaire, le renfort du propriétaire vaut × 1 (au lieu de × 1,2).
-- Réglages dans config_jeu 'siege' : defense_bonus_tier {legendaire: 1}, assaut_seuil {legendaire: 0.5}. Retour arrière : supprimer ces deux clés.
update config_jeu set valeur = (valeur::jsonb || '{"defense_bonus_tier": {"legendaire": 1.0}, "assaut_seuil": {"legendaire": 0.5}}'::jsonb)::text where cle = 'siege';

do $$
declare d text; d2 text;
begin
  -- B : siege_renforcer
  d := pg_get_functiondef('public.siege_renforcer(text, uuid, integer)'::regprocedure);
  d2 := replace(d, 'else siege_n(''defense_bonus'') end)',
                   'else coalesce(siege_tier_n(''defense_bonus_tier'', s.tier), siege_n(''defense_bonus'')) end)   /* s3-83 */');
  if d2 = d then raise exception 's3-83 : renforcer inchangé'; end if;
  execute d2;
  -- A : siege_appliquer (le seuil qui annule l'assaut, et le texte de la notification)
  d := pg_get_functiondef('public.siege_appliquer(bigint, integer)'::regprocedure);
  d2 := replace(d, 'if s.assaut_le is not null and s.degats < v_res * 2 / 3 then',
                   'if s.assaut_le is not null and s.degats < v_res * coalesce(siege_tier_n(''assaut_seuil'', s.tier), 2.0 / 3) then   /* s3-83 */');
  if d2 = d then raise exception 's3-83 : seuil assaut inchangé'; end if;
  d := d2;
  d2 := replace(d, ''' min si tu ne la repousses pas sous les deux tiers.''',
                   ''' min si tu ne la repousses pas sous '' || case when siege_tier_n(''assaut_seuil'', s.tier) = 0.5 then ''la moitié.'' else ''les deux tiers.'' end');
  if d2 = d then raise exception 's3-83 : texte assaut inchangé'; end if;
  execute d2;
end $$;
