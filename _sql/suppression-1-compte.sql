-- =====================================================================
--  TerraFront — suppression de compte (6 octobre)
--
--  Décidé avec Nataël : les communes sont libérées, l'e-mail, le pseudo,
--  les amis, les échanges et leurs messages sont effacés ; ce qui sert à
--  l'histoire du jeu reste, sans lien avec la personne.
--
--  Ce qui se passe, dans l'ordre :
--  1. Radar : un duel qu'il avait commencé contre la partie d'un autre est
--     annulé et la partie de l'autre redevient jouable ; ses parties en
--     attente ne seront plus proposées à personne ; son Elo disparaît.
--     Ses parties déjà jouées restent, pour que ses anciens adversaires
--     gardent leurs résumés (il y apparaît comme « un joueur »).
--  2. Effacés : amis et blocages, notifications en attente.
--  3. Anonymisés : journal (« un joueur »), classements de saison
--     (« Joueur supprimé »).
--  4. Le compte de connexion est supprimé (auth.users). Par cascade,
--     Supabase efface la fiche joueur et tout ce qui y est lié : communes
--     possédées (elles retournent dans les paquets), échanges et messages,
--     annonces de la Bourse, sièges, historique, points, objectifs,
--     abonnements aux notifications, communes vues, exclusions de contrat.
--  Restent sans lien avec personne : ses essais de la Commune du jour et
--  ses tirages (compteurs du jeu). L'identifiant qu'ils portent ne
--  correspond plus à aucun compte.
--
--  Le tout se fait en une seule transaction : si une étape échoue, rien
--  n'est supprimé.
--
--  Trois fonctions :
--  - supprimer_mon_compte(confirmation) : appelée par le jeu, le joueur
--    doit retaper son pseudo ;
--  - supprimer_compte_essai(pseudo) : RÉPÉTITION À BLANC pour Nataël,
--    depuis l'éditeur SQL seulement. Fait toute la suppression puis
--    l'annule, et dit ce qui aurait été supprimé. À lancer une fois sur
--    son propre pseudo avant de pousser le bouton dans le jeu.
--  - supprimer_compte_interne(uuid) : le travail lui-même, appelable par
--    personne directement.
--
--  Rejouable. Ne supprime rien tant qu'on n'appelle pas les fonctions.
-- =====================================================================

create or replace function public.supprimer_compte_interne(p_uid uuid)
returns jsonb
language plpgsql security definer
set search_path to 'public'
as $$
declare
  v_communes int;
  v_echanges int;
  v_amis int;
  v_radar int;
begin
  if p_uid is null or not exists (select 1 from joueurs where id = p_uid) then
    raise exception 'Compte introuvable.';
  end if;

  select count(*) into v_communes from possessions where joueur_id = p_uid;
  select count(*) into v_echanges from echanges where proposant = p_uid or destinataire = p_uid;

  -- 1. Radar
  update radar_parties set utilisee = false
   where id in (select source_id from radar_parties
                 where joueur_id = p_uid and not fini and source_id is not null);
  delete from radar_parties where joueur_id = p_uid and not fini;
  update radar_parties set utilisee = true
   where joueur_id = p_uid and fini and source_id is null and not utilisee;
  get diagnostics v_radar = row_count;
  delete from radar_joueurs where joueur_id = p_uid;

  -- 2. effacés
  delete from amis where joueur_id = p_uid or ami_id = p_uid;
  get diagnostics v_amis = row_count;
  delete from notifications_a_envoyer where joueur_id = p_uid;

  -- 3. anonymisés
  update journal set acteur = null where acteur = p_uid;
  update journal set cible = null where cible = p_uid;
  update classement_saisons set pseudo = 'Joueur supprimé' where joueur_id = p_uid;

  -- 4. le compte, et tout ce qui en dépend par cascade
  delete from auth.users where id = p_uid;
  -- filet : si la fiche joueur n'était pas liée au compte, on l'efface aussi
  delete from joueurs where id = p_uid;

  return jsonb_build_object(
    'communes_liberees', v_communes,
    'echanges_effaces', v_echanges,
    'liens_amis_effaces', v_amis,
    'parties_radar_retirees', v_radar);
end;
$$;

-- Ce que le jeu appelle : le joueur connecté, qui retape son pseudo
create or replace function public.supprimer_mon_compte(p_confirmation text)
returns jsonb
language plpgsql security definer
set search_path to 'public'
as $$
declare
  v_uid uuid := auth.uid();
  v_pseudo text;
begin
  if v_uid is null then raise exception 'Connecte-toi pour supprimer ton compte.'; end if;
  select pseudo into v_pseudo from joueurs where id = v_uid;
  if v_pseudo is null or lower(trim(coalesce(p_confirmation, ''))) <> lower(trim(v_pseudo)) then
    raise exception 'Le pseudo ne correspond pas : rien n''a été supprimé.';
  end if;
  return supprimer_compte_interne(v_uid);
end;
$$;

-- Répétition à blanc : tout est fait puis annulé
create or replace function public.supprimer_compte_essai(p_pseudo text)
returns jsonb
language plpgsql security definer
set search_path to 'public'
as $$
declare
  v_uid uuid;
  v jsonb;
begin
  select id into v_uid from joueurs where lower(pseudo) = lower(trim(p_pseudo));
  if v_uid is null then raise exception 'Pseudo inconnu : %', p_pseudo; end if;
  begin
    v := supprimer_compte_interne(v_uid);
    raise exception 'essai-termine:%', v::text;
  exception when others then
    if sqlerrm like 'essai-termine:%' then
      return jsonb_build_object('repetition', 'réussie, rien n''a été supprimé')
             || substr(sqlerrm, length('essai-termine:') + 1)::jsonb;
    end if;
    return jsonb_build_object('repetition', 'ÉCHEC, rien n''a été supprimé', 'erreur', sqlerrm);
  end;
end;
$$;

revoke all on function public.supprimer_compte_interne(uuid) from public, anon, authenticated;
revoke all on function public.supprimer_compte_essai(text)   from public, anon, authenticated;
revoke all on function public.supprimer_mon_compte(text)     from public, anon;
grant execute on function public.supprimer_mon_compte(text) to authenticated;

-- ---------------------------------------------------------------------
-- Vérification : trois « oui » attendus
-- ---------------------------------------------------------------------
select case when has_function_privilege('authenticated', 'public.supprimer_mon_compte(text)', 'execute')
             and not has_function_privilege('anon', 'public.supprimer_mon_compte(text)', 'execute')
            then 'oui' else 'NON' end as bouton_reserve_aux_joueurs,
       case when not has_function_privilege('authenticated', 'public.supprimer_compte_interne(uuid)', 'execute')
            then 'oui' else 'NON' end as interne_protegee,
       case when not has_function_privilege('authenticated', 'public.supprimer_compte_essai(text)', 'execute')
            then 'oui' else 'NON' end as essai_protege;

-- ---------------------------------------------------------------------
-- ENSUITE, à lancer à part (remplace TonPseudo par ton pseudo) :
--   select supprimer_compte_essai('TonPseudo');
-- Réponse attendue : "repetition": "réussie, rien n'a été supprimé",
-- avec le nombre de communes qui auraient été libérées.
-- ---------------------------------------------------------------------
