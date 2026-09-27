-- =====================================================================
--  TerraFront — un échange ne doit plus produire quatre lignes de journal
--
--  Oshannir : « il y a des doublons de notif sur le même échange ». Un
--  échange accepté écrit quatre lignes au lieu de deux :
--
--    Tu as reçu Villefranche-sur-Saône de Maroli en échange     <- juste
--    Maroli a reçu Malakoff de toi en échange                   <- juste
--    Tu as acheté Villefranche-sur-Saône à Maroli               <- faux
--    Maroli a acheté Malakoff à toi                             <- faux
--
--  Les deux dernières viennent du déclencheur trg_journal_possession, qui
--  journalise tout changement de propriétaire. Sa fonction écrit
--  « conquete » si conquise_le a changé, « achat » sinon — et pendant un
--  échange conquise_le ne change pas, d'où « achat ».
--
--  On ne supprime pas les lignes de accepter_echange : ce sont les bonnes,
--  elles disent « en échange » et le déclencheur ne saurait pas le deviner.
--  On fait taire le déclencheur pendant un échange, avec un drapeau qui ne
--  vit que le temps de la transaction.
--
--  Idempotent. Rien à redéployer côté site.
-- =====================================================================

-- ---------------------------------------------------------------------
-- 1. Le déclencheur s'abstient quand le drapeau est levé
-- ---------------------------------------------------------------------
create or replace function public.journal_possession()
returns trigger
language plpgsql
security definer
set search_path to 'public'
as $function$
declare v_tier text;
begin
  -- current_setting(nom, true) renvoie NULL au lieu de lever une erreur
  -- quand le reglage n'existe pas — c'est le cas de toutes les autres
  -- transactions, qui continuent donc comme avant.
  if coalesce(current_setting('terrafront.echange', true), '') = 'on' then
    return null;
  end if;

  if new.joueur_id is distinct from old.joueur_id then
    select tier into v_tier from communes where code = new.commune_code;
    if new.conquise_le is distinct from old.conquise_le and new.conquise_le is not null then
      perform noter_journal('conquete', new.joueur_id, old.joueur_id, new.commune_code, v_tier);
    else
      perform noter_journal('achat', new.joueur_id, old.joueur_id, new.commune_code, v_tier);
    end if;
  end if;
  return null;
end;
$function$;

-- ---------------------------------------------------------------------
-- 2. accepter_echange lève le drapeau avant d'échanger
-- ---------------------------------------------------------------------
-- Fonction reprise telle qu'elle est déployée, avec une seule ligne ajoutée.

create or replace function public.accepter_echange(p_id bigint)
returns table(message text, commission integer)
language plpgsql
security definer
set search_path to 'public'
as $function$
declare
  e            echanges%rowtype;
  v_uid        uuid := auth.uid();
  v_tier       text;
  v_comm       integer;
  v_nom_p      text;
  v_nom_d      text;
  v_solde_p    integer;
  v_solde_d    integer;
begin
  if v_uid is null then
    raise exception 'Connecte-toi pour accepter cet echange.';
  end if;

  -- on verrouille la proposition le temps de l'echange
  select * into e from echanges where id = p_id for update;
  if e.id is null then
    raise exception 'Cette proposition n''existe plus.';
  end if;
  if e.destinataire <> v_uid then
    raise exception 'Cette proposition ne t''est pas adressee.';
  end if;
  if e.etat <> 'en_attente' then
    raise exception 'Cette proposition a deja ete traitee.';
  end if;
  if e.expire_le <= now() then
    update echanges set etat = 'expire', repondu_le = now() where id = p_id;
    raise exception 'Cette proposition a expire.';
  end if;

  -- les deux communes ont pu changer de main entre-temps : on reverifie tout
  perform 1 from possessions
    where commune_code = e.commune_proposant and joueur_id = e.proposant for update;
  if not found then
    update echanges set etat = 'annule', repondu_le = now() where id = p_id;
    raise exception 'La commune proposee a change de proprietaire.';
  end if;

  perform 1 from possessions
    where commune_code = e.commune_destinataire and joueur_id = v_uid for update;
  if not found then
    update echanges set etat = 'annule', repondu_le = now() where id = p_id;
    raise exception 'Tu ne possedes plus cette commune.';
  end if;

  if exists (select 1 from possessions
              where commune_code in (e.commune_proposant, e.commune_destinataire)
                and bouclier_jusqua is not null and bouclier_jusqua > now()) then
    raise exception 'Une des deux communes est protegee par un bouclier.';
  end if;

  if exists (select 1 from annonces
              where commune_code in (e.commune_proposant, e.commune_destinataire)) then
    raise exception 'Une des deux communes est en vente a la bourse.';
  end if;

  select c.tier, c.nom into v_tier, v_nom_p from communes c where c.code = e.commune_proposant;
  select c.nom into v_nom_d from communes c where c.code = e.commune_destinataire;
  v_comm := commission_echange(v_tier);

  select solde into v_solde_p from joueurs where id = e.proposant for update;
  select solde into v_solde_d from joueurs where id = v_uid        for update;
  if v_solde_d < v_comm then
    raise exception 'Il te manque % pts pour la commission.', v_comm - v_solde_d;
  end if;
  if v_solde_p < v_comm then
    raise exception 'L''autre joueur n''a plus de quoi payer la commission.';
  end if;

  -- Le declencheur trg_journal_possession journalise tout changement de
  -- proprietaire comme un achat. Pendant un echange c'est faux, et ca
  -- doublonne avec les deux lignes « en echange » ecrites plus bas. On pose
  -- un drapeau valable le temps de la transaction : le declencheur le lit et
  -- s'abstient. Le troisieme argument à true limite la portee a la
  -- transaction, donc rien ne fuit d'un appel à l'autre.
  perform set_config('terrafront.echange', 'on', true);

  -- l'echange proprement dit : remise a zero de la protection, des boucliers
  -- et de la conquete, comme pour toute commune qui change de main
  update possessions
     set joueur_id = v_uid, acquired_at = now(),
         bouclier_debut = null, bouclier_jusqua = null, conquise_le = null
   where commune_code = e.commune_proposant;

  update possessions
     set joueur_id = e.proposant, acquired_at = now(),
         bouclier_debut = null, bouclier_jusqua = null, conquise_le = null
   where commune_code = e.commune_destinataire;

  -- ------------------------------------------------------------------
  -- AJOUT : le journal de propriete doit suivre l'echange
  -- ------------------------------------------------------------------
  -- On ferme la ligne de celui qui cede, on en ouvre une pour celui qui
  -- recoit. Sans ca, « Ma France » perd la trace de la commune des qu'elle
  -- change de main une seconde fois.
  update historique set released_at = now()
   where commune_code = e.commune_proposant
     and joueur_id = e.proposant and released_at is null;

  update historique set released_at = now()
   where commune_code = e.commune_destinataire
     and joueur_id = v_uid and released_at is null;

  insert into historique (commune_code, joueur_id, saison, acquired_at) values
    (e.commune_proposant,    v_uid,      'saison-1', now()),
    (e.commune_destinataire, e.proposant, 'saison-1', now());
  -- ------------------------------------------------------------------

  update joueurs set solde = solde - v_comm where id in (e.proposant, v_uid);

  -- les sieges en cours sur ces deux communes n'ont plus de sens
  if to_regclass('public.sieges') is not null then
    execute 'delete from sieges where commune_code in ($1, $2)'
      using e.commune_proposant, e.commune_destinataire;
  end if;

  update echanges set etat = 'accepte', repondu_le = now() where id = p_id;

  insert into journal (type, acteur, cible, commune_code, commune_nom, tier)
  values ('echange', v_uid,        e.proposant, e.commune_proposant,    v_nom_p, v_tier),
         ('echange', e.proposant,  v_uid,       e.commune_destinataire, v_nom_d, v_tier);

  return query select
    'Echange conclu : ' || v_nom_p || ' contre ' || v_nom_d,
    v_comm;
end;
$function$;

grant execute on function public.accepter_echange(bigint) to authenticated;

-- ---------------------------------------------------------------------
-- 3. Les doublons déjà écrits
-- ---------------------------------------------------------------------
-- À REGARDER avant de supprimer quoi que ce soit : cette requête liste les
-- lignes « achat » qui coïncident avec une ligne « echange » sur la même
-- commune, les mêmes joueurs et la même seconde. Ce sont les doublons.
--
-- select a.id, a.cree_le, a.commune_nom
--   from journal a
--  where a.type = 'achat'
--    and exists (select 1 from journal e
--                 where e.type = 'echange'
--                   and e.commune_code = a.commune_code
--                   and e.acteur = a.acteur and e.cible = a.cible
--                   and abs(extract(epoch from (e.cree_le - a.cree_le))) < 2)
--  order by a.cree_le desc;
--
-- Si la liste ne contient que des échanges, alors seulement :
--
-- delete from journal a
--  where a.type = 'achat'
--    and exists (select 1 from journal e
--                 where e.type = 'echange'
--                   and e.commune_code = a.commune_code
--                   and e.acteur = a.acteur and e.cible = a.cible
--                   and abs(extract(epoch from (e.cree_le - a.cree_le))) < 2);
-- =====================================================================
