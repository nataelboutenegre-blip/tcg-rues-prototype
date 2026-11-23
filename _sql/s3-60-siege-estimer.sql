-- s3-60 (23/11/2026) : l'énergie qu'il faut vraiment pour prendre une commune, pour la liste Attaquer.
-- Avant, le jeu affichait un chiffre fixe par rareté (8, 8, 9, 15, 27 ⚡), sans la proximité, le rempart,
-- la Forteresse, la garnison ni un siège déjà commencé. Ici : ceil((résistance − dégâts déjà faits + garnison) / (10 × mult))
-- + 2 ⚡ de pose si le siège n'existe pas, − l'énergie qui attend déjà dans mon siège. 60 communes au plus par appel
-- (≈ 0,4 s mesuré sur 60).
create or replace function public.siege_estimer(p_codes text[])
returns jsonb language plpgsql stable security definer set search_path to 'public' as $$
declare v_uid uuid := auth.uid(); r jsonb := '{}'::jsonb; c text; v_res numeric; v_mult numeric; v_pts numeric := siege_n('points_par_energie'); v_pose numeric := siege_n('pose');
  s front_sieges; v_proprio uuid;
begin
  if v_uid is null or p_codes is null then return r; end if;
  foreach c in array p_codes[1:60] loop
    select joueur_id into v_proprio from possessions where commune_code = c;
    if v_proprio is null or v_proprio = v_uid then continue; end if;
    v_res := siege_resistance(c, v_uid); v_mult := greatest(0.1, coalesce(siege_mult(v_uid, c), 1));
    s := null; select * into s from front_sieges where commune_code = c and attaquant = v_uid and fini_le is null;
    r := r || jsonb_build_object(c, jsonb_build_object(
      'e', greatest(1, ceil(greatest(0, v_res - coalesce(s.degats, 0) + siege_garnison(c) * siege_n('bouclier_par_energie')) / (v_pts * v_mult))
                       + case when s.id is null then v_pose else 0 end - coalesce(s.attente, 0)),
      'res', round(v_res), 'mult', round(v_mult, 2), 'rempart', round(siege_rempart(c, v_proprio), 2), 'en_cours', s.id is not null));
  end loop;
  return r;
end; $$;
revoke all on function public.siege_estimer(text[]) from public, anon;
grant execute on function public.siege_estimer(text[]) to authenticated;
-- Contrôle : select siege_estimer(array['16015']);  → {} hors connexion
