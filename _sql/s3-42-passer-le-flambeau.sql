-- s3-42 : « Passer le flambeau » (idée d'Arkhannou, aperçu validé par Nataël le 22/11 à 10 h 46).
-- Le chef donne son titre à un membre sans quitter le clan. L'ancien chef devient bras droit avec
-- tous les droits, ou simple membre s'il y a déjà 2 bras droits. Message dans le tchat du clan et
-- notification au nouveau chef. Va avec patch484.
-- Retour arrière : drop function clan_passer_flambeau(uuid);

create or replace function public.clan_passer_flambeau(p_joueur uuid)
returns jsonb
language plpgsql security definer set search_path to 'public' as $$
declare
  v_uid uuid := auth.uid();
  v_clan uuid; v_nom text; v_moi text; v_lui text; v_bras integer;
begin
  if v_uid is null then raise exception 'Non connecte'; end if;
  if not clans_ouverts() then raise exception 'Les clans ouvrent bientot'; end if;
  select id, nom into v_clan, v_nom from clans where chef = v_uid for update;
  if v_clan is null then raise exception 'Seul le chef peut passer le flambeau'; end if;
  if p_joueur is null or p_joueur = v_uid then raise exception 'Choisis un autre membre du clan'; end if;
  if not exists(select 1 from clan_membres where joueur_id = p_joueur and clan_id = v_clan) then
    raise exception 'Ce joueur n''est pas dans ton clan';
  end if;
  -- le nouveau chef : plus bras droit (comme dans clan_sortir)
  update clans set chef = p_joueur where id = v_clan;
  update clan_membres set bras_droit = false, peut_inviter = true, peut_exclure = false, peut_modifier = false
   where joueur_id = p_joueur;
  -- l'ancien chef : bras droit avec tous les droits, s'il reste une place
  select count(*) into v_bras from clan_membres where clan_id = v_clan and bras_droit and joueur_id <> v_uid;
  update clan_membres
     set bras_droit = v_bras < 2, peut_inviter = true, peut_exclure = v_bras < 2, peut_modifier = v_bras < 2
   where joueur_id = v_uid;
  select pseudo into v_moi from joueurs where id = v_uid;
  select pseudo into v_lui from joueurs where id = p_joueur;
  insert into clan_messages (clan_id, auteur, texte)
  values (v_clan, v_uid, '🔥 ' || coalesce(v_moi, 'Le chef') || ' a passé le flambeau : ' || coalesce(v_lui, 'un membre')
                         || ' est le nouveau chef du clan.');
  perform notifier_joueur(p_joueur, '🔥 Tu es le chef de ' || coalesce(v_nom, 'ton clan'),
    coalesce(v_moi, 'Ton chef') || ' t''a passé le flambeau.', './?onglet=clan', 'flambeau-' || v_clan);
  return mon_clan();
end $$;

revoke all on function public.clan_passer_flambeau(uuid) from public, anon;
grant execute on function public.clan_passer_flambeau(uuid) to authenticated;

-- contrôle : true
select to_regprocedure('public.clan_passer_flambeau(uuid)') is not null as ok;
