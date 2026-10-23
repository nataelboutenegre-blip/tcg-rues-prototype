-- ===========================================================================
--  TerraFront — parrainage et titre choisi (23 octobre 2026)
--  Décidé avec Nataël le 23 octobre (aperçu « Parrainage TerraFront » validé).
--
--  Le lien : terrafront.fr/?ref=<pseudo du parrain>.
--
--  1. Tables parrainages (un parrain au plus par compte) et jours_joues
--     (un jour par joueur, noté à chaque ouverture du jeu).
--  2. declarer_parrain(p_ref) : appelé par le jeu à la première connexion
--     de l'invité. Refuse si le compte a plus de 48 h, s'il a déjà un
--     parrain, si le parrain n'existe pas, si c'est soi-même, ou si le
--     compte du parrain a moins de 3 jours. Cadeau de l'invité, tout de
--     suite : 1 paquet Terra gratuit en plus (il peut dépasser la réserve
--     de 3) et 10 énergie en Front (jusqu'à 60, comme les quêtes).
--  3. parrainage_jour() : note le jour ; quand l'invité a joué 3 jours
--     différents (et a au moins une carte), son parrainage est validé :
--       - le parrain reçoit 10 énergie, pour 5 amis au plus par saison ;
--       - badges du parrain (saison « parrainage ») : recruteur (1 ami),
--         parrain (5 amis, donne le titre « Le Parrain »), ambassadeur (10).
--  4. mon_parrainage() : le bloc « Inviter des amis » du profil, et les
--     récompenses pas encore montrées (marquées vues à la lecture).
--  5. Titre choisi : joueurs.titre (null = le titre de région habituel).
--     mes_titres(), choisir_titre(p_titre), titre_joueur(p_joueur).
--  6. terra_jetons_lire : une réserve AU-DESSUS de 3 (cadeau) est gardée
--     telle quelle jusqu'à ce qu'on la dépense, comme l'énergie des quêtes.
--     Même cadence que s2-25 (30 min).
--
--  Ne touche ni à l'inscription (handle_new_user) ni aux combats.
--  Rejouable. Finit par un contrôle (une ligne).
-- ===========================================================================

begin;

-- 1. Tables ---------------------------------------------------------------------
create table if not exists public.parrainages(
  filleul_id       uuid primary key references public.joueurs(id) on delete cascade,
  parrain_id       uuid not null references public.joueurs(id) on delete cascade,
  cree_le          timestamptz not null default now(),
  valide_le        timestamptz,
  saison_valide    text,
  energie_versee   integer not null default 0,
  vu_par_parrain   boolean not null default false,
  check (filleul_id <> parrain_id)
);
create index if not exists parrainages_parrain on public.parrainages(parrain_id);
alter table public.parrainages enable row level security;
revoke all on public.parrainages from public, anon, authenticated;

create table if not exists public.jours_joues(
  joueur_id  uuid not null references public.joueurs(id) on delete cascade,
  jour       date not null,
  primary key (joueur_id, jour)
);
alter table public.jours_joues enable row level security;
revoke all on public.jours_joues from public, anon, authenticated;

alter table public.joueurs add column if not exists titre text;

-- 6. Réserve Terra au-dessus de 3 (cadeau d'invitation) ---------------------------
create or replace function public.terra_jetons_lire(p_val numeric, p_maj timestamptz)
 returns numeric
 language sql
 stable
 set search_path to 'public'
as $f$
  select case when p_val >= 3 then p_val
              else least(3, p_val + extract(epoch from (now() - p_maj)) / 1800.0) end;
$f$;
revoke all on function public.terra_jetons_lire(numeric, timestamptz) from public, anon, authenticated;

-- Saison en cours (pour le plafond de 5 amis récompensés par saison)
create or replace function public.parrainage_saison()
 returns text language sql stable security definer set search_path to 'public'
as $f$
  select coalesce((select sa.id from saisons sa where sa.etat <> 'terminee' order by sa.debut desc limit 1), 'hors-saison');
$f$;
revoke all on function public.parrainage_saison() from public, anon, authenticated;

-- 2. Déclarer son parrain ------------------------------------------------------------
create or replace function public.declarer_parrain(p_ref text)
 returns table(statut text, parrain text)
 language plpgsql
 security definer
 set search_path to 'public'
as $f$
declare
  v_uid uuid := auth.uid();
  moi joueurs%rowtype;
  p   joueurs%rowtype;
  v   numeric;
begin
  if v_uid is null then raise exception 'Non connecte'; end if;
  select * into moi from joueurs where id = v_uid for update;
  if not found then raise exception 'Joueur inconnu'; end if;

  if exists (select 1 from parrainages where filleul_id = v_uid) then
    return query select 'deja'::text, null::text; return;
  end if;
  if moi.created_at is null or moi.created_at < now() - interval '48 hours' then
    return query select 'trop_tard'::text, null::text; return;
  end if;

  select * into p from joueurs where lower(pseudo) = lower(btrim(coalesce(p_ref, ''))) limit 1;
  if not found then return query select 'inconnu'::text, null::text; return; end if;
  if p.id = v_uid then return query select 'soi_meme'::text, null::text; return; end if;
  if p.created_at is null or p.created_at > now() - interval '3 days' then
    return query select 'parrain_trop_recent'::text, null::text; return;
  end if;

  insert into parrainages(filleul_id, parrain_id) values (v_uid, p.id);

  -- le cadeau de l'invité : 1 paquet Terra en plus, 10 énergie en Front
  v := terra_jetons_lire(moi.terra_jetons, moi.terra_jetons_maj);
  update joueurs set terra_jetons = v + 1, terra_jetons_maj = now() where id = v_uid;
  v := front_energie_lire(moi.front_energie, moi.front_energie_maj);
  update joueurs set front_energie = least(60, v + 10), front_energie_maj = now() where id = v_uid;

  return query select 'ok'::text, p.pseudo;
end;
$f$;
revoke all on function public.declarer_parrain(text) from public, anon;
grant execute on function public.declarer_parrain(text) to authenticated;

-- 3. Le jour joué, et la validation ----------------------------------------------------
create or replace function public.parrainage_jour()
 returns void
 language plpgsql
 security definer
 set search_path to 'public'
as $f$
declare
  v_uid uuid := auth.uid();
  r parrainages%rowtype;
  v_jours integer;
  v_saison text;
  v_payes integer;
  v_e integer := 0;
  v numeric;
  n integer;
begin
  if v_uid is null then return; end if;
  insert into jours_joues(joueur_id, jour)
  values (v_uid, (now() at time zone 'Europe/Paris')::date)
  on conflict do nothing;

  select * into r from parrainages where filleul_id = v_uid and valide_le is null for update;
  if not found then return; end if;

  select count(*) into v_jours from jours_joues where joueur_id = v_uid;
  if v_jours < 3 then return; end if;
  -- il faut avoir vraiment joué : au moins une carte, en Terra ou en Front
  if not (exists (select 1 from terra_collection where joueur_id = v_uid)
          or exists (select 1 from historique where joueur_id = v_uid)) then
    return;
  end if;

  v_saison := parrainage_saison();
  -- verrou sur le parrain : deux amis validés en même temps ne dépassent pas 5
  select front_energie_lire(j.front_energie, j.front_energie_maj) into v
    from joueurs j where j.id = r.parrain_id for update;
  select count(*) into v_payes from parrainages
   where parrain_id = r.parrain_id and saison_valide = v_saison and energie_versee > 0;
  if v_payes < 5 and v is not null then
    v_e := 10;
    update joueurs set front_energie = least(60, v + v_e), front_energie_maj = now() where id = r.parrain_id;
  end if;

  update parrainages set valide_le = now(), saison_valide = v_saison, energie_versee = v_e
   where filleul_id = v_uid;

  -- badges du parrain, d'après tous ses amis validés
  select count(*) into n from parrainages where parrain_id = r.parrain_id and valide_le is not null;
  insert into joueur_badges(joueur_id, badge, saison, valeur)
  select r.parrain_id, b.badge, 'parrainage', n
    from (values ('recruteur', 1), ('parrain', 5), ('ambassadeur', 10)) as b(badge, seuil)
   where n >= b.seuil
  on conflict (joueur_id, badge, saison) do update set valeur = excluded.valeur;
end;
$f$;
revoke all on function public.parrainage_jour() from public, anon;
grant execute on function public.parrainage_jour() to authenticated;

-- 4. Le bloc du profil ---------------------------------------------------------------
create or replace function public.mon_parrainage()
 returns jsonb
 language plpgsql
 security definer
 set search_path to 'public'
as $f$
declare
  v_uid uuid := auth.uid();
  v_saison text := parrainage_saison();
  v_out jsonb;
begin
  if v_uid is null then raise exception 'Non connecte'; end if;
  select jsonb_build_object(
    'pseudo',  (select pseudo from joueurs where id = v_uid),
    'peut_parrainer', (select created_at <= now() - interval '3 days' from joueurs where id = v_uid),
    'actifs',  (select count(*) from parrainages where parrain_id = v_uid and valide_le is not null),
    'payes_saison', (select count(*) from parrainages where parrain_id = v_uid and saison_valide = v_saison and energie_versee > 0),
    'amis', coalesce((
      select jsonb_agg(jsonb_build_object(
               'pseudo', j.pseudo,
               'jours', least(3, (select count(*) from jours_joues d where d.joueur_id = pa.filleul_id)),
               'valide', pa.valide_le is not null,
               'energie', pa.energie_versee)
             order by pa.valide_le is null, pa.cree_le desc)
        from parrainages pa join joueurs j on j.id = pa.filleul_id
       where pa.parrain_id = v_uid), '[]'::jsonb),
    'nouveaux', coalesce((
      select jsonb_agg(jsonb_build_object('pseudo', j.pseudo, 'energie', pa.energie_versee) order by pa.valide_le)
        from parrainages pa join joueurs j on j.id = pa.filleul_id
       where pa.parrain_id = v_uid and pa.valide_le is not null and not pa.vu_par_parrain), '[]'::jsonb)
  ) into v_out;
  update parrainages set vu_par_parrain = true
   where parrain_id = v_uid and valide_le is not null and not vu_par_parrain;
  return v_out;
end;
$f$;
revoke all on function public.mon_parrainage() from public, anon;
grant execute on function public.mon_parrainage() to authenticated;

-- 5. Le titre choisi -------------------------------------------------------------------
-- Les titres qu'on peut choisir, à côté du titre de région (toujours possible).
-- Pour en ajouter un : une ligne ici (badge qui le donne) et son nom dans le jeu.
create or replace function public.titres_possibles(p_joueur uuid)
 returns text[] language sql stable security definer set search_path to 'public'
as $f$
  select coalesce(array_agg(t.titre order by t.titre), '{}')
    from (values ('parrain', 'parrain')) as t(titre, badge)
   where exists (select 1 from joueur_badges b where b.joueur_id = p_joueur and b.badge = t.badge);
$f$;
revoke all on function public.titres_possibles(uuid) from public, anon, authenticated;

create or replace function public.mes_titres()
 returns jsonb language plpgsql stable security definer set search_path to 'public'
as $f$
declare v_uid uuid := auth.uid();
begin
  if v_uid is null then raise exception 'Non connecte'; end if;
  return jsonb_build_object(
    'choisi', (select case when j.titre = any(titres_possibles(v_uid)) then j.titre end from joueurs j where j.id = v_uid),
    'disponibles', to_jsonb(titres_possibles(v_uid)));
end;
$f$;
revoke all on function public.mes_titres() from public, anon;
grant execute on function public.mes_titres() to authenticated;

create or replace function public.choisir_titre(p_titre text)
 returns text language plpgsql security definer set search_path to 'public'
as $f$
declare v_uid uuid := auth.uid();
begin
  if v_uid is null then raise exception 'Non connecte'; end if;
  if p_titre is null or p_titre = '' or p_titre = 'region' then
    update joueurs set titre = null where id = v_uid; return null;
  end if;
  if not (p_titre = any(titres_possibles(v_uid))) then raise exception 'Titre pas encore obtenu'; end if;
  update joueurs set titre = p_titre where id = v_uid;
  return p_titre;
end;
$f$;
revoke all on function public.choisir_titre(text) from public, anon;
grant execute on function public.choisir_titre(text) to authenticated;

-- le titre affiché d'un joueur (null = son titre de région)
create or replace function public.titre_joueur(p_joueur uuid)
 returns text language sql stable security definer set search_path to 'public'
as $f$
  select case when j.titre = any(titres_possibles(j.id)) then j.titre end from joueurs j where j.id = p_joueur;
$f$;
revoke all on function public.titre_joueur(uuid) from public, anon;
grant execute on function public.titre_joueur(uuid) to authenticated;

commit;

-- Contrôle : tout doit valoir true
select (to_regclass('public.parrainages') is not null
        and to_regclass('public.jours_joues') is not null) as tables,
       exists (select 1 from information_schema.columns where table_name = 'joueurs' and column_name = 'titre') as colonne_titre,
       (select count(*) from pg_proc where proname in
          ('declarer_parrain','parrainage_jour','mon_parrainage','mes_titres','choisir_titre','titre_joueur','titres_possibles','parrainage_saison')) = 8 as fonctions,
       pg_get_functiondef('public.terra_jetons_lire(numeric, timestamptz)'::regprocedure) like '%p_val >= 3%1800.0%' as reserve_terra;
