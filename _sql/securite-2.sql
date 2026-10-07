-- =====================================================================
--  TerraFront — Sécurité, 2 (7 octobre)
--
--  Deux points restés ouverts depuis l'audit du 3 octobre :
--
--  1. handle_new_user() : à l'inscription, le pseudo n'était que coupé à
--     20 caractères. N'importe quel caractère passait (émojis, signes,
--     caractères invisibles), alors que changer_pseudo() les refuse.
--     Désormais, même règle qu'au changement de pseudo : lettres (accents
--     compris), chiffres, espace, - _ . ; commence par une lettre ou un
--     chiffre ; 3 à 20 caractères. Ce qui ne passe pas est retiré ; s'il
--     ne reste rien d'utilisable, le joueur reçoit « Joueur-XXXXX », qu'il
--     pourra changer.
--
--  2. demarrer_paquet() : si une des colonnes de jetons, de solde ou
--     d'achats du jour était vide (null), les contrôles « pas de paquet
--     disponible », « limite de 5 », « solde insuffisant » ne se
--     déclenchaient pas : paquets gratuits ou achetés sans limite. Les
--     valeurs vides comptent désormais comme 0 (et « maintenant » pour la
--     date des jetons). Rien ne change pour un compte normal.
--
--  SÉCURITÉ DU REMPLACEMENT : chaque fonction n'est remplacée que si la
--  version en base est bien celle du 3 octobre (repères vérifiés). Sinon,
--  rien n'est touché et le résultat final le dit.
--
--  Les pseudos déjà existants ne sont PAS modifiés : la dernière requête
--  les compte seulement.
--  Rejouable.
-- =====================================================================

do $bloc$
declare
  v_def text := pg_get_functiondef('public.handle_new_user()'::regprocedure);
begin
  if v_def not like '%Pas de repli sur l''e-mail%' and v_def not like '%securite-2%' then
    raise notice 'handle_new_user : version inattendue, NON remplacée';
    return;
  end if;
  execute $f$
create or replace function public.handle_new_user()
 returns trigger
 language plpgsql
 security definer
 set search_path to 'public'
as $fn$
declare
  v_pseudo text;
  v_base   text;
  v_essai  integer := 0;
begin
  -- securite-2 : même règle que changer_pseudo()
  v_pseudo := coalesce(new.raw_user_meta_data->>'pseudo', '');
  v_pseudo := regexp_replace(v_pseudo, '[[:space:]]+', ' ', 'g');
  v_pseudo := regexp_replace(v_pseudo, '[^[:alnum:]À-ÿ ._-]', '', 'g');
  v_pseudo := regexp_replace(v_pseudo, '^[^[:alnum:]À-ÿ]+', '');
  v_pseudo := btrim(v_pseudo);
  if length(v_pseudo) > 20 then
    v_pseudo := btrim(substr(v_pseudo, 1, 20));
  end if;

  -- Pas de repli sur l'e-mail : « prenom.nom » deviendrait public.
  -- Un nom neutre, que le joueur pourra changer lui-meme ensuite.
  if length(v_pseudo) < 3 then
    v_pseudo := 'Joueur-' || upper(substr(replace(new.id::text, '-', ''), 1, 5));
  end if;

  -- Deux joueurs du meme nom rendraient le classement et le journal
  -- illisibles. On suffixe jusqu'a trouver libre.
  v_base := v_pseudo;
  while exists (select 1 from public.joueurs where lower(pseudo) = lower(v_pseudo)) loop
    v_essai := v_essai + 1;
    if v_essai > 99 then
      v_pseudo := 'Joueur-' || upper(substr(replace(new.id::text, '-', ''), 1, 8));
      exit;
    end if;
    v_pseudo := substr(v_base, 1, 17) || '-' || v_essai::text;
  end loop;

  insert into public.joueurs (id, pseudo) values (new.id, v_pseudo);
  return new;
end;
$fn$;
$f$;
  raise notice 'handle_new_user : remplacée';
end;
$bloc$;

do $bloc$
declare
  v_def text := pg_get_functiondef('public.demarrer_paquet(text)'::regprocedure);
begin
  if v_def not like '%v_jetons_actuels := least(3, v_jetons + extract(epoch from (now() - v_maj)) / 1200.0)%'
     and v_def not like '%securite-2%' then
    raise notice 'demarrer_paquet : version inattendue, NON remplacée';
    return;
  end if;
  execute $f$
create or replace function public.demarrer_paquet(p_type text)
 returns table(jetons_restants numeric, solde_restant integer)
 language plpgsql
 security definer
 set search_path to 'public', 'extensions'
as $fn$
declare
  v_joueur_id uuid := auth.uid();
  v_jetons numeric;
  v_maj timestamptz;
  v_jetons_actuels numeric;
  v_solde integer;
  v_achetes_jour integer;
  v_achetes_date date;
begin
  if v_joueur_id is null then raise exception 'Non connecte'; end if;

  select jetons_gratuits, jetons_maj, solde, paquets_achetes_jour, paquets_achetes_date
    into v_jetons, v_maj, v_solde, v_achetes_jour, v_achetes_date
    from joueurs where id = v_joueur_id for update;
  if not found then raise exception 'Joueur introuvable'; end if;

  -- securite-2 : une valeur vide ne doit jamais faire sauter un controle
  v_jetons := coalesce(v_jetons, 0);
  v_maj := coalesce(v_maj, now());
  v_solde := coalesce(v_solde, 0);
  v_achetes_jour := coalesce(v_achetes_jour, 0);

  v_jetons_actuels := least(3, v_jetons + extract(epoch from (now() - v_maj)) / 1200.0);

  if p_type = 'gratuit' then
    if v_jetons_actuels < 1 then
      raise exception 'Pas de paquet gratuit disponible pour le moment';
    end if;
    update joueurs set jetons_gratuits = v_jetons_actuels - 1, jetons_maj = now()
      where id = v_joueur_id;
    return query select (v_jetons_actuels - 1), v_solde;

  elsif p_type = 'achete' then
    if v_achetes_date is distinct from current_date then
      v_achetes_jour := 0;
      v_achetes_date := current_date;
    end if;
    if v_achetes_jour >= 5 then
      raise exception 'Limite quotidienne de paquets achetes atteinte (5/jour)';
    end if;
    if v_solde < 200 then
      raise exception 'Solde insuffisant (200 points necessaires)';
    end if;
    update joueurs set
      solde = v_solde - 200,
      paquets_achetes_jour = v_achetes_jour + 1,
      paquets_achetes_date = v_achetes_date,
      jetons_gratuits = v_jetons_actuels,
      jetons_maj = now()
      where id = v_joueur_id;
    return query select v_jetons_actuels, (v_solde - 200);

  else
    raise exception 'Type de paquet invalide';
  end if;
end;
$fn$;
$f$;
  raise notice 'demarrer_paquet : remplacée';
end;
$bloc$;

-- Les droits ne changent pas : on les repose à l'identique par prudence
revoke all on function public.handle_new_user() from public, anon, authenticated;
revoke all on function public.demarrer_paquet(text) from public, anon;

-- ---------------------------------------------------------------------
-- Résultat : deux « oui » attendus. Les deux dernières colonnes sont
-- pour information (rien n'est modifié).
-- ---------------------------------------------------------------------
select case when pg_get_functiondef('public.handle_new_user()'::regprocedure) like '%securite-2%'
            then 'oui' else 'NON' end as pseudo_filtre_a_inscription,
       case when pg_get_functiondef('public.demarrer_paquet(text)'::regprocedure) like '%securite-2%'
            then 'oui' else 'NON' end as paquets_sans_valeur_vide,
       (select count(*) from joueurs
         where jetons_gratuits is null or jetons_maj is null or solde is null
            or paquets_achetes_jour is null) as comptes_avec_valeur_vide,
       (select count(*) from joueurs
         where pseudo !~ '^[[:alnum:]À-ÿ][[:alnum:]À-ÿ ._-]*$' or length(pseudo) not between 3 and 20)
         as pseudos_hors_regle;
