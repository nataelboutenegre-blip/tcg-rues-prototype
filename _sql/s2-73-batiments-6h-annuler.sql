-- ===========================================================================
--  s2-73 — Bâtiments : construction en 6 h, et annulation remboursée
--  Décisions de Nataël, 2 novembre 2026 (« 24 heures c'est trop pénalisant »,
--  « ok très bien pour remboursement total », « six heures très bien »).
--
--  1. Construction : 6 h au lieu de 24 pour TOUS les bâtiments (réglage
--     construction_h de config_jeu 'batiments'). La préparation d'une bombe
--     (24 / 48 / 72 h) ne change pas.
--  2. Chantiers en cours : ramenés à 6 h depuis leur début (un bâtiment lancé
--     il y a 2 h est prêt dans 4 h ; lancé il y a plus de 6 h : prêt tout de suite).
--  3. batiment_annuler(commune, type) : annule un bâtiment ENCORE EN
--     CONSTRUCTION et rembourse son prix EN ENTIER (même au-dessus du plafond
--     de la réserve) : Fonderie 0 (la 1re) ou fonderie2_prix (la 2e),
--     Forteresse forteresse_prix, Centre centre_prix.
--     Refusé si la commune est assiégée (un attaquant a au moins une victoire
--     dessus) : on ne récupère pas ses lingots juste avant de se faire piller.
--     Pour « déplacer » : annuler puis reconstruire ailleurs (6 h).
--  Rejouable. Contrôle attendu : 6 | 0 | true | true
-- ===========================================================================
begin;

-- 1. 6 heures --------------------------------------------------------------------
update public.config_jeu
   set valeur = (valeur::jsonb || '{"construction_h": 6}'::jsonb)::text
 where cle = 'batiments';

-- 2. les chantiers en cours suivent ------------------------------------------------
update public.batiments
   set pret_le = cree_le + make_interval(hours => 6)
 where pret_le > now() and pret_le > cree_le + make_interval(hours => 6);

-- 3. annuler une construction ------------------------------------------------------
create or replace function public.batiment_annuler(p_code text, p_type text)
 returns jsonb language plpgsql security definer set search_path to 'public'
as $f$
declare
  v_uid  uuid := auth.uid();
  b      record;
  v_prix numeric := 0;
  v      numeric;
begin
  if v_uid is null then raise exception 'Non connecte'; end if;
  perform 1 from joueurs where id = v_uid for update;   -- deux clics ne remboursent pas deux fois
  select * into b from batiments where commune_code = p_code and type = p_type and joueur_id = v_uid;
  if b.id is null then raise exception 'Ce bâtiment n''existe pas (ou plus)'; end if;
  if b.pret_le <= now() then raise exception 'Ce bâtiment est déjà construit : on ne peut plus l''annuler'; end if;
  if exists (select 1 from sieges s where s.commune_code = p_code and coalesce(s.victoires_consecutives, 0) > 0) then
    raise exception 'Cette commune est attaquée : impossible d''annuler pendant l''assaut';
  end if;

  v_prix := case b.type
    when 'forteresse' then batiment_reglage('forteresse_prix')
    when 'centre'     then batiment_reglage('centre_prix')
    when 'fonderie'   then case when exists (select 1 from batiments f where f.joueur_id = v_uid and f.type = 'fonderie'
                                                and f.id <> b.id and f.cree_le <= b.cree_le)
                                then batiment_reglage('fonderie2_prix') else 0 end
    else 0 end;

  v := lingots_figer(v_uid);          -- la réserve à jour avant de rembourser
  delete from batiments where id = b.id;
  if v_prix > 0 then update joueurs set lingots = lingots + v_prix where id = v_uid; end if;
  return jsonb_build_object('type', b.type, 'rembourse', floor(v_prix)::integer,
                            'lingots', floor(coalesce(lingots_lire(v_uid), 0))::integer);
end;
$f$;
revoke all on function public.batiment_annuler(text, text) from public, anon;
grant execute on function public.batiment_annuler(text, text) to authenticated;

commit;

-- Contrôle : 6 | 0 | true | true
select batiment_reglage('construction_h')::integer                                           as construction_h,
       (select count(*) from public.batiments where pret_le > now() + interval '6 hours 1 minute') as chantiers_trop_longs,
       has_function_privilege('authenticated', 'public.batiment_annuler(text, text)', 'execute') as joueurs_peuvent_annuler,
       not has_function_privilege('anon', 'public.batiment_annuler(text, text)', 'execute')     as ferme_aux_visiteurs;
