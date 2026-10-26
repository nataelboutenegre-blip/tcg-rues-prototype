-- ===========================================================================
--  s2-29-clans-echanges.sql — les échanges entre membres d'un clan, en Front
--  (26 octobre 2026, aperçu validé par Nataël : « parfait »)
--
--  Règles (garde-fous décidés avec Nataël) :
--   - seulement entre membres du même clan, une commune contre une commune
--     de MÊME rareté, sans don ;
--   - 2 échanges conclus par jour et par joueur (jour de Paris) ;
--   - impossible pour une commune prise il y a moins de 24 h, en garnison, ou
--     échangée il y a moins de 48 h ;
--   - il faut être dans le clan depuis 48 h ;
--   - aucun point de combat (rien n'est écrit dans front_victoires) ;
--   - une proposition expire au bout de 24 h ; 5 en attente au plus.
--  Le passage de main reprend celui de accepter_echange (saison 1) : drapeau
--  terrafront.echange, possessions remises à zéro (bouclier, conquête),
--  historique fermé / ouvert, journal « echange ». Les sièges suivent la
--  commune (on n'y touche pas). Saison 2 seulement.
--
--  Fonctions pour le jeu : clan_ech_etat(), clan_ech_communes(joueur),
--  clan_ech_proposer(cible, ma, sa), clan_ech_repondre(id, accepter),
--  clan_ech_annuler(id). Rejouable.
--  Contrôle attendu : true | true | 0
-- ===========================================================================
begin;

create table if not exists public.clan_echanges(
  id                   bigserial primary key,
  clan_id              uuid not null references public.clans(id) on delete cascade,
  proposant            uuid not null references public.joueurs(id) on delete cascade,
  destinataire         uuid not null references public.joueurs(id) on delete cascade,
  commune_proposant    text not null references public.communes(code),
  commune_destinataire text not null references public.communes(code),
  tier                 text not null,
  etat                 text not null default 'en_attente'
                       check (etat in ('en_attente', 'accepte', 'refuse', 'annule', 'expire')),
  cree_le              timestamptz not null default now(),
  expire_le            timestamptz not null default now() + interval '24 hours',
  repondu_le           timestamptz
);
create index if not exists clan_echanges_dest on public.clan_echanges(destinataire, etat);
create index if not exists clan_echanges_prop on public.clan_echanges(proposant, etat);
create index if not exists clan_echanges_communes on public.clan_echanges(commune_proposant, commune_destinataire, repondu_le);
alter table public.clan_echanges enable row level security;
revoke all on public.clan_echanges from public, anon, authenticated;

-- pourquoi une commune ne peut pas être échangée (null = elle peut)
create or replace function public.clan_ech_raison(p_code text, p_joueur uuid)
 returns text language plpgsql stable security definer set search_path to 'public'
as $f$
declare p possessions%rowtype; h integer;
begin
  select * into p from possessions where commune_code = p_code;
  if p.commune_code is null or p.joueur_id <> p_joueur then return 'elle a changé de main'; end if;
  if exists (select 1 from front_garnisons g where g.commune_code = p_code) then return 'en garnison'; end if;
  if p.conquise_le is not null and p.conquise_le > now() - interval '24 hours' then
    h := greatest(1, floor(extract(epoch from now() - p.conquise_le) / 3600)::int);
    return 'prise il y a ' || h || ' h';
  end if;
  if exists (select 1 from clan_echanges e where e.etat = 'accepte' and e.repondu_le > now() - interval '48 hours'
              and p_code in (e.commune_proposant, e.commune_destinataire)) then
    return 'échangée récemment';
  end if;
  return null;
end; $f$;

-- les échanges conclus aujourd'hui par un joueur
create or replace function public.clan_ech_du_jour(p_joueur uuid)
 returns integer language sql stable security definer set search_path to 'public'
as $f$
  select count(*)::integer from clan_echanges e
   where e.etat = 'accepte' and p_joueur in (e.proposant, e.destinataire)
     and e.repondu_le >= (quete_jour()::timestamp at time zone 'Europe/Paris');
$f$;

-- le clan d'un joueur, s'il y est depuis 48 h (sinon null)
create or replace function public.clan_ech_clan(p_joueur uuid)
 returns uuid language sql stable security definer set search_path to 'public'
as $f$
  select m.clan_id from clan_membres m where m.joueur_id = p_joueur and m.depuis <= now() - interval '48 hours';
$f$;

-- les communes Front d'un joueur de MON clan (moi compris), avec la raison si bloquée
create or replace function public.clan_ech_communes(p_joueur uuid)
 returns table(code text, nom text, departement text, tier text, raison text)
 language plpgsql stable security definer set search_path to 'public'
as $f$
declare v_uid uuid := auth.uid(); v_clan uuid;
begin
  if v_uid is null then raise exception 'Non connecte'; end if;
  select m.clan_id into v_clan from clan_membres m where m.joueur_id = v_uid;
  if v_clan is null or not exists (select 1 from clan_membres m where m.joueur_id = p_joueur and m.clan_id = v_clan) then
    raise exception 'Ce joueur n''est pas dans ton clan.';
  end if;
  return query
  select c.code::text, c.nom::text, c.departement::text, c.tier::text, clan_ech_raison(c.code, p_joueur)
    from possessions p join communes c on c.code = p.commune_code
   where p.joueur_id = p_joueur
   order by array_position(array['legendaire','epique','rare','peucommun','commun'], c.tier::text), c.nom;
end; $f$;

-- tout ce qu'il faut à l'écran
create or replace function public.clan_ech_etat()
 returns jsonb language plpgsql security definer set search_path to 'public'
as $f$
declare v_uid uuid := auth.uid(); v_clan uuid; v_depuis timestamptz;
begin
  if v_uid is null then raise exception 'Non connecte'; end if;
  update clan_echanges set etat = 'expire', repondu_le = now() where etat = 'en_attente' and expire_le <= now();
  select m.clan_id, m.depuis into v_clan, v_depuis from clan_membres m where m.joueur_id = v_uid;
  if v_clan is null then return jsonb_build_object('clan', false); end if;
  return jsonb_build_object(
    'clan', true,
    'pret_le', case when v_depuis > now() - interval '48 hours' then v_depuis + interval '48 hours' end,
    'faits', clan_ech_du_jour(v_uid), 'max', 2,
    'membres', coalesce((select jsonb_agg(jsonb_build_object('id', j.id, 'pseudo', j.pseudo) order by j.pseudo)
                  from clan_membres m join joueurs j on j.id = m.joueur_id
                 where m.clan_id = v_clan and m.joueur_id <> v_uid), '[]'::jsonb),
    'recus', coalesce((select jsonb_agg(x order by x->>'cree_le' desc) from (
        select jsonb_build_object('id', e.id, 'pseudo', j.pseudo, 'cree_le', e.cree_le, 'expire_le', e.expire_le, 'tier', e.tier,
               'donne', jsonb_build_object('code', c1.code, 'nom', c1.nom, 'dept', c1.departement),
               'recoit', jsonb_build_object('code', c2.code, 'nom', c2.nom, 'dept', c2.departement)) x
          from clan_echanges e join joueurs j on j.id = e.proposant
          join communes c1 on c1.code = e.commune_destinataire join communes c2 on c2.code = e.commune_proposant
         where e.destinataire = v_uid and e.etat = 'en_attente') r), '[]'::jsonb),
    'envoyes', coalesce((select jsonb_agg(x order by x->>'cree_le' desc) from (
        select jsonb_build_object('id', e.id, 'pseudo', j.pseudo, 'cree_le', e.cree_le, 'expire_le', e.expire_le, 'tier', e.tier,
               'donne', jsonb_build_object('code', c1.code, 'nom', c1.nom, 'dept', c1.departement),
               'recoit', jsonb_build_object('code', c2.code, 'nom', c2.nom, 'dept', c2.departement)) x
          from clan_echanges e join joueurs j on j.id = e.destinataire
          join communes c1 on c1.code = e.commune_proposant join communes c2 on c2.code = e.commune_destinataire
         where e.proposant = v_uid and e.etat = 'en_attente') r), '[]'::jsonb));
end; $f$;

create or replace function public.clan_ech_proposer(p_cible uuid, p_ma text, p_sa text)
 returns text language plpgsql security definer set search_path to 'public'
as $f$
declare v_uid uuid := auth.uid(); v_clan uuid; t1 text; t2 text; r text;
begin
  if v_uid is null then raise exception 'Non connecte'; end if;
  if not saison2_active() then raise exception 'Les échanges de clan arrivent avec la saison 2.'; end if;
  if p_cible = v_uid then raise exception 'Choisis un coéquipier.'; end if;
  v_clan := clan_ech_clan(v_uid);
  if v_clan is null then raise exception 'Il faut être dans un clan depuis 48 h pour échanger.'; end if;
  if clan_ech_clan(p_cible) is distinct from v_clan then
    raise exception 'Ce joueur n''est pas dans ton clan, ou il y est depuis moins de 48 h.';
  end if;
  if clan_ech_du_jour(v_uid) >= 2 then raise exception 'Tu as déjà fait tes 2 échanges du jour.'; end if;
  if (select count(*) from clan_echanges where proposant = v_uid and etat = 'en_attente' and expire_le > now()) >= 5 then
    raise exception 'Tu as déjà 5 propositions en attente.';
  end if;
  if not exists (select 1 from possessions where commune_code = p_ma and joueur_id = v_uid) then
    raise exception 'Cette commune n''est pas à toi.';
  end if;
  if not exists (select 1 from possessions where commune_code = p_sa and joueur_id = p_cible) then
    raise exception 'Cette commune n''est pas à ton coéquipier.';
  end if;
  r := clan_ech_raison(p_ma, v_uid);
  if r is not null then raise exception 'Ta commune ne peut pas être échangée (%).', r; end if;
  r := clan_ech_raison(p_sa, p_cible);
  if r is not null then raise exception 'Sa commune ne peut pas être échangée (%).', r; end if;
  select tier into t1 from communes where code = p_ma;
  select tier into t2 from communes where code = p_sa;
  if t1 is distinct from t2 then raise exception 'Les deux communes doivent être de même rareté.'; end if;
  if exists (select 1 from clan_echanges where etat = 'en_attente' and expire_le > now()
              and proposant = v_uid and commune_proposant = p_ma and commune_destinataire = p_sa) then
    raise exception 'Tu as déjà proposé cet échange.';
  end if;
  insert into clan_echanges(clan_id, proposant, destinataire, commune_proposant, commune_destinataire, tier)
  values (v_clan, v_uid, p_cible, p_ma, p_sa, t1);
  return 'Proposition envoyée';
end; $f$;

create or replace function public.clan_ech_repondre(p_id bigint, p_accepter boolean)
 returns text language plpgsql security definer set search_path to 'public'
as $f$
declare v_uid uuid := auth.uid(); e clan_echanges%rowtype; r text; t1 text; t2 text; n1 text; n2 text;
begin
  if v_uid is null then raise exception 'Non connecte'; end if;
  select * into e from clan_echanges where id = p_id for update;
  if e.id is null or e.destinataire <> v_uid then raise exception 'Cette proposition ne t''est pas adressée.'; end if;
  if e.etat <> 'en_attente' then raise exception 'Cette proposition a déjà été traitée.'; end if;
  if e.expire_le <= now() then
    update clan_echanges set etat = 'expire', repondu_le = now() where id = p_id;
    raise exception 'Cette proposition a expiré.';
  end if;
  if not p_accepter then
    update clan_echanges set etat = 'refuse', repondu_le = now() where id = p_id;
    return 'Proposition refusée';
  end if;
  if not saison2_active() then raise exception 'Les échanges de clan arrivent avec la saison 2.'; end if;
  -- tout se revérifie au moment d'accepter
  perform 1 from joueurs where id in (e.proposant, v_uid) order by id for update;
  perform 1 from possessions where commune_code in (e.commune_proposant, e.commune_destinataire) for update;
  if clan_ech_clan(v_uid) is distinct from e.clan_id or clan_ech_clan(e.proposant) is distinct from e.clan_id then
    update clan_echanges set etat = 'annule', repondu_le = now() where id = p_id;
    raise exception 'Vous n''êtes plus dans le même clan.';
  end if;
  if clan_ech_du_jour(v_uid) >= 2 then raise exception 'Tu as déjà fait tes 2 échanges du jour.'; end if;
  if clan_ech_du_jour(e.proposant) >= 2 then raise exception 'Ton coéquipier a déjà fait ses 2 échanges du jour.'; end if;
  r := clan_ech_raison(e.commune_proposant, e.proposant);
  if r is not null then
    update clan_echanges set etat = 'annule', repondu_le = now() where id = p_id;
    raise exception 'Sa commune ne peut plus être échangée (%).', r;
  end if;
  r := clan_ech_raison(e.commune_destinataire, v_uid);
  if r is not null then
    if r = 'elle a changé de main' then update clan_echanges set etat = 'annule', repondu_le = now() where id = p_id; end if;
    raise exception 'Ta commune ne peut pas être échangée (%).', r;
  end if;
  select tier, nom into t1, n1 from communes where code = e.commune_proposant;
  select tier, nom into t2, n2 from communes where code = e.commune_destinataire;
  if t1 is distinct from t2 then
    update clan_echanges set etat = 'annule', repondu_le = now() where id = p_id;
    raise exception 'Les deux communes ne sont plus de même rareté.';
  end if;

  perform set_config('terrafront.echange', 'on', true);
  update possessions set joueur_id = v_uid, acquired_at = now(), bouclier_debut = null, bouclier_jusqua = null, conquise_le = null
   where commune_code = e.commune_proposant;
  update possessions set joueur_id = e.proposant, acquired_at = now(), bouclier_debut = null, bouclier_jusqua = null, conquise_le = null
   where commune_code = e.commune_destinataire;
  update historique set released_at = now() where commune_code = e.commune_proposant and joueur_id = e.proposant and released_at is null;
  update historique set released_at = now() where commune_code = e.commune_destinataire and joueur_id = v_uid and released_at is null;
  insert into historique (commune_code, joueur_id, saison, acquired_at) values
    (e.commune_proposant, v_uid, saison_en_cours_id(), now()),
    (e.commune_destinataire, e.proposant, saison_en_cours_id(), now());
  perform noter_journal('echange', v_uid, e.proposant, e.commune_proposant, t1);
  perform noter_journal('echange', e.proposant, v_uid, e.commune_destinataire, t1);

  update clan_echanges set etat = 'accepte', repondu_le = now() where id = p_id;
  -- les autres propositions qui portaient sur ces communes tombent
  update clan_echanges set etat = 'annule', repondu_le = now()
   where etat = 'en_attente' and id <> p_id
     and (commune_proposant in (e.commune_proposant, e.commune_destinataire)
       or commune_destinataire in (e.commune_proposant, e.commune_destinataire));
  return 'Échange conclu : tu reçois ' || n1 || ', ' || (select pseudo from joueurs where id = e.proposant) || ' reçoit ' || n2;
end; $f$;

create or replace function public.clan_ech_annuler(p_id bigint)
 returns text language plpgsql security definer set search_path to 'public'
as $f$
declare v_uid uuid := auth.uid();
begin
  if v_uid is null then raise exception 'Non connecte'; end if;
  update clan_echanges set etat = 'annule', repondu_le = now()
   where id = p_id and proposant = v_uid and etat = 'en_attente';
  if not found then raise exception 'Cette proposition n''est plus en attente.'; end if;
  return 'Proposition annulée';
end; $f$;

revoke all on function public.clan_ech_raison(text, uuid)            from public, anon, authenticated;
revoke all on function public.clan_ech_du_jour(uuid)                 from public, anon, authenticated;
revoke all on function public.clan_ech_clan(uuid)                    from public, anon, authenticated;
revoke all on function public.clan_ech_communes(uuid)                from public, anon;
revoke all on function public.clan_ech_etat()                        from public, anon;
revoke all on function public.clan_ech_proposer(uuid, text, text)    from public, anon;
revoke all on function public.clan_ech_repondre(bigint, boolean)     from public, anon;
revoke all on function public.clan_ech_annuler(bigint)               from public, anon;
grant execute on function public.clan_ech_communes(uuid)             to authenticated;
grant execute on function public.clan_ech_etat()                     to authenticated;
grant execute on function public.clan_ech_proposer(uuid, text, text) to authenticated;
grant execute on function public.clan_ech_repondre(bigint, boolean)  to authenticated;
grant execute on function public.clan_ech_annuler(bigint)            to authenticated;

commit;

-- contrôle : fonctions ouvertes aux joueurs | interne fermée | échanges enregistrés
select has_function_privilege('authenticated', 'public.clan_ech_repondre(bigint, boolean)', 'execute') as ouvert,
       not has_function_privilege('authenticated', 'public.clan_ech_raison(text, uuid)', 'execute')  as interne_fermee,
       (select count(*) from public.clan_echanges)                                                    as echanges;
