-- ===========================================================================
--  s2-148 (16/11/2026) — les alliances : un salon de diplomatie à plusieurs clans
--  Demande de Nataël (16/11 23 h 07 : « maintenant, sinon les joueurs vont aller
--  ailleurs pour se parler »).
--
--  Dans le jeu (Clan › Diplomatie), le chef d'un clan crée une alliance (un nom)
--  et invite de 1 à 4 autres clans (5 clans au plus, invitations comprises).
--  Le chef d'un clan invité rejoint ou refuse (3 jours pour répondre). Le chef
--  d'un clan membre peut inviter d'autres clans ou faire sortir son clan.
--  Dès que 2 clans sont membres, le bot des clans (fonction discord-clans, toutes
--  les 10 min) crée le salon privé « 🤝│nom-de-l-alliance » dans « 🤝 Diplomatie »,
--  visible des rôles de tous les clans membres ; il suit les entrées et sorties,
--  et supprime le salon quand l'alliance se ferme (moins de 2 clans).
--  Une alliance occupe une des 5 places de diplomatie de chaque clan membre ou
--  invité (comme un salon à deux). Aucun effet sur le combat.
--
--  Contrôle attendu (dernière ligne) : true | true | true | 0
-- ===========================================================================

create table if not exists public.clan_alliances (
  id bigserial primary key,
  nom text not null check (char_length(nom) between 3 and 32),
  fondateur uuid references public.clans(id) on delete set null,
  cree_par uuid references public.joueurs(id) on delete set null,
  etat text not null default 'ouvert' check (etat in ('ouvert', 'ferme')),
  cree_le timestamptz not null default now(),
  ferme_le timestamptz
);
create unique index if not exists clan_alliances_nom_ouvert on public.clan_alliances (lower(nom)) where etat = 'ouvert';

create table if not exists public.clan_alliance_membres (
  alliance_id bigint not null references public.clan_alliances(id) on delete cascade,
  clan_id uuid not null references public.clans(id) on delete cascade,
  etat text not null check (etat in ('membre', 'invite', 'refuse', 'parti', 'expire', 'annule')),
  invite_par uuid references public.joueurs(id) on delete set null,
  invite_le timestamptz not null default now(),
  expire_le timestamptz,
  rejoint_le timestamptz,
  parti_le timestamptz,
  primary key (alliance_id, clan_id)
);
alter table public.clan_alliances enable row level security;          -- seulement par les fonctions
alter table public.clan_alliance_membres enable row level security;

-- ---------- ménage : invitations expirées, alliances à moins de 2 clans ----------
create or replace function public.clan_alli_nettoyer()
 returns void language plpgsql security definer set search_path to 'public'
as $f$
begin
  update clan_alliance_membres set etat = 'expire' where etat = 'invite' and expire_le <= now();
  -- fermée quand il ne reste aucun membre, ou un seul sans invitation en cours
  with a_fermer as (
    select a.id from clan_alliances a
     where a.etat = 'ouvert'
       and (select count(*) from clan_alliance_membres m where m.alliance_id = a.id and m.etat = 'membre') < 2
       and ((select count(*) from clan_alliance_membres m where m.alliance_id = a.id and m.etat = 'membre') = 0
            or not exists (select 1 from clan_alliance_membres m where m.alliance_id = a.id and m.etat = 'invite')))
  update clan_alliances a set etat = 'ferme', ferme_le = now() from a_fermer f where f.id = a.id;
  update clan_alliance_membres m set etat = 'annule'
    from clan_alliances a where a.id = m.alliance_id and a.etat = 'ferme' and m.etat = 'invite';
end $f$;
revoke all on function public.clan_alli_nettoyer() from public, anon, authenticated;

-- ---------- les places de diplomatie : salons à deux + alliances ----------
create or replace function public.clan_diplo_compte(p_clan uuid)
 returns integer language sql stable security definer set search_path to 'public'
as $f$
  select (select count(*)::integer from clan_diplomatie d
           where p_clan in (d.clan_a, d.clan_b) and (d.etat = 'ouvert' or (d.etat = 'en_attente' and d.expire_le > now())))
       + (select count(*)::integer from clan_alliance_membres m join clan_alliances a on a.id = m.alliance_id
           where m.clan_id = p_clan and a.etat = 'ouvert'
             and (m.etat = 'membre' or (m.etat = 'invite' and m.expire_le > now())));   -- s2-148
$f$;

-- ---------- créer ----------
create or replace function public.clan_alli_creer(p_nom text, p_clans uuid[])
 returns text language plpgsql security definer set search_path to 'public'
as $f$
declare v_uid uuid := auth.uid(); v_clan uuid; v_nom text := btrim(regexp_replace(coalesce(p_nom, ''), '\s+', ' ', 'g'));
        v_ids uuid[]; v_id bigint; x uuid; v_tag text; v_tags text := '';
begin
  if v_uid is null then raise exception 'Non connecte'; end if;
  select c.id into v_clan from clans c where c.chef = v_uid;
  if v_clan is null then raise exception 'Seul le chef du clan peut créer une alliance.'; end if;
  if char_length(v_nom) < 3 or char_length(v_nom) > 32 then raise exception 'Le nom de l''alliance fait de 3 à 32 caractères.'; end if;
  select coalesce(array_agg(distinct u), '{}') into v_ids from unnest(coalesce(p_clans, '{}')) u where u is not null and u <> v_clan;
  if cardinality(v_ids) < 1 then raise exception 'Invite au moins un clan.'; end if;
  if cardinality(v_ids) > 4 then raise exception 'Une alliance réunit 5 clans au plus : invite 4 clans au plus.'; end if;
  perform pg_advisory_xact_lock(hashtext('clan_diplo'));
  perform clan_alli_nettoyer();
  if clan_diplo_compte(v_clan) >= 5 then raise exception 'Ton clan a déjà 5 salons ou alliances (ouverts ou proposés).'; end if;
  if exists (select 1 from clan_alliances a where a.etat = 'ouvert' and lower(a.nom) = lower(v_nom)) then
    raise exception 'Une alliance porte déjà ce nom.';
  end if;
  foreach x in array v_ids loop
    select tag into v_tag from clans where id = x;
    if v_tag is null then raise exception 'Un des clans invités n''existe plus.'; end if;
    if clan_diplo_compte(x) >= 5 then raise exception 'Le clan [%] a déjà 5 salons ou alliances.', v_tag; end if;
    v_tags := v_tags || case when v_tags = '' then '' else ', ' end || '[' || v_tag || ']';
  end loop;
  insert into clan_alliances(nom, fondateur, cree_par) values (v_nom, v_clan, v_uid) returning id into v_id;
  insert into clan_alliance_membres(alliance_id, clan_id, etat, invite_par, rejoint_le) values (v_id, v_clan, 'membre', v_uid, now());
  insert into clan_alliance_membres(alliance_id, clan_id, etat, invite_par, expire_le)
    select v_id, u, 'invite', v_uid, now() + interval '3 days' from unnest(v_ids) u;
  return 'Alliance « ' || v_nom || ' » créée : invitation envoyée à ' || v_tags;
end $f$;

-- ---------- inviter un clan de plus ----------
create or replace function public.clan_alli_inviter(p_alliance bigint, p_clan uuid)
 returns text language plpgsql security definer set search_path to 'public'
as $f$
declare v_uid uuid := auth.uid(); v_clan uuid; a clan_alliances%rowtype; v_tag text;
begin
  if v_uid is null then raise exception 'Non connecte'; end if;
  select c.id into v_clan from clans c where c.chef = v_uid;
  perform pg_advisory_xact_lock(hashtext('clan_diplo'));
  perform clan_alli_nettoyer();
  select * into a from clan_alliances where id = p_alliance;
  if a.id is null or a.etat <> 'ouvert' then raise exception 'Cette alliance est fermée.'; end if;
  if v_clan is null or not exists (select 1 from clan_alliance_membres m where m.alliance_id = a.id and m.clan_id = v_clan and m.etat = 'membre') then
    raise exception 'Seul le chef d''un clan membre peut inviter.';
  end if;
  select tag into v_tag from clans where id = p_clan;
  if v_tag is null then raise exception 'Ce clan n''existe plus.'; end if;
  if exists (select 1 from clan_alliance_membres m where m.alliance_id = a.id and m.clan_id = p_clan and m.etat in ('membre', 'invite')) then
    raise exception 'Le clan [%] est déjà dans l''alliance ou déjà invité.', v_tag;
  end if;
  if (select count(*) from clan_alliance_membres m where m.alliance_id = a.id and m.etat in ('membre', 'invite')) >= 5 then
    raise exception 'L''alliance a déjà 5 clans (invitations comprises).';
  end if;
  if clan_diplo_compte(p_clan) >= 5 then raise exception 'Le clan [%] a déjà 5 salons ou alliances.', v_tag; end if;
  insert into clan_alliance_membres(alliance_id, clan_id, etat, invite_par, invite_le, expire_le)
    values (a.id, p_clan, 'invite', v_uid, now(), now() + interval '3 days')
  on conflict (alliance_id, clan_id) do update
    set etat = 'invite', invite_par = excluded.invite_par, invite_le = now(), expire_le = excluded.expire_le, rejoint_le = null, parti_le = null;
  return 'Invitation envoyée au clan [' || v_tag || ']';
end $f$;

-- ---------- rejoindre ou refuser ----------
create or replace function public.clan_alli_repondre(p_alliance bigint, p_accepter boolean)
 returns text language plpgsql security definer set search_path to 'public'
as $f$
declare v_uid uuid := auth.uid(); v_clan uuid; m clan_alliance_membres%rowtype; v_nom text;
begin
  if v_uid is null then raise exception 'Non connecte'; end if;
  select c.id into v_clan from clans c where c.chef = v_uid;
  if v_clan is null then raise exception 'Seul le chef du clan invité peut répondre.'; end if;
  perform pg_advisory_xact_lock(hashtext('clan_diplo'));
  perform clan_alli_nettoyer();
  select * into m from clan_alliance_membres where alliance_id = p_alliance and clan_id = v_clan for update;
  select nom into v_nom from clan_alliances where id = p_alliance and etat = 'ouvert';
  if m.alliance_id is null or m.etat <> 'invite' or v_nom is null then
    raise exception 'Cette invitation n''est plus valable (expirée, annulée ou alliance fermée).';
  end if;
  if not p_accepter then
    update clan_alliance_membres set etat = 'refuse', parti_le = now() where alliance_id = p_alliance and clan_id = v_clan;
    perform clan_alli_nettoyer();
    return 'Invitation refusée';
  end if;
  update clan_alliance_membres set etat = 'membre', rejoint_le = now() where alliance_id = p_alliance and clan_id = v_clan;
  return 'Ton clan a rejoint l''alliance « ' || v_nom || ' » : le salon est sur le Discord dans les 10 minutes';
end $f$;

-- ---------- sortir de l'alliance ----------
create or replace function public.clan_alli_quitter(p_alliance bigint)
 returns text language plpgsql security definer set search_path to 'public'
as $f$
declare v_uid uuid := auth.uid(); v_clan uuid; v_ferme boolean;
begin
  if v_uid is null then raise exception 'Non connecte'; end if;
  select c.id into v_clan from clans c where c.chef = v_uid;
  if v_clan is null then raise exception 'Seul le chef du clan peut faire sortir son clan.'; end if;
  perform pg_advisory_xact_lock(hashtext('clan_diplo'));
  update clan_alliance_membres set etat = 'parti', parti_le = now()
   where alliance_id = p_alliance and clan_id = v_clan and etat = 'membre';
  if not found then raise exception 'Ton clan n''est pas membre de cette alliance.'; end if;
  perform clan_alli_nettoyer();
  select etat = 'ferme' into v_ferme from clan_alliances where id = p_alliance;
  return case when v_ferme then 'Ton clan a quitté l''alliance : elle est fermée, son salon disparaît du Discord'
              else 'Ton clan a quitté l''alliance : il ne voit plus son salon' end;
end $f$;

revoke all on function public.clan_alli_creer(text, uuid[]) from public, anon;
revoke all on function public.clan_alli_inviter(bigint, uuid) from public, anon;
revoke all on function public.clan_alli_repondre(bigint, boolean) from public, anon;
revoke all on function public.clan_alli_quitter(bigint) from public, anon;
grant execute on function public.clan_alli_creer(text, uuid[]) to authenticated;
grant execute on function public.clan_alli_inviter(bigint, uuid) to authenticated;
grant execute on function public.clan_alli_repondre(bigint, boolean) to authenticated;
grant execute on function public.clan_alli_quitter(bigint) to authenticated;

-- ---------- l'état de la diplomatie : + les alliances ----------
create or replace function public.clan_diplo_etat()
 returns jsonb language plpgsql security definer set search_path to 'public'
as $f$
declare v_uid uuid := auth.uid(); v_clan uuid; v_chef boolean;
begin
  if v_uid is null then raise exception 'Non connecte'; end if;
  update clan_diplomatie set etat = 'expire', ferme_le = now() where etat = 'en_attente' and expire_le <= now();
  perform clan_alli_nettoyer();   -- s2-148
  select m.clan_id into v_clan from clan_membres m where m.joueur_id = v_uid;
  if v_clan is null then return jsonb_build_object('clan', false); end if;
  select (c.chef = v_uid) into v_chef from clans c where c.id = v_clan;
  return jsonb_build_object(
    'clan', true, 'chef', coalesce(v_chef, false), 'max', 5, 'utilises', clan_diplo_compte(v_clan),
    'salons', coalesce((select jsonb_agg(jsonb_build_object(
        'id', d.id, 'etat', d.etat, 'sens', case when d.etat = 'en_attente' then case when d.clan_a = v_clan then 'envoye' else 'recu' end end,
        'tag', o.tag, 'nom', o.nom, 'couleur', o.couleur, 'cree_le', d.cree_le, 'ouvert_le', d.ouvert_le, 'expire_le', d.expire_le)
        order by d.etat = 'ouvert', coalesce(d.ouvert_le, d.cree_le) desc)
      from clan_diplomatie d join clans o on o.id = case when d.clan_a = v_clan then d.clan_b else d.clan_a end
     where v_clan in (d.clan_a, d.clan_b) and d.etat in ('en_attente', 'ouvert')), '[]'::jsonb),
    'clans', coalesce((select jsonb_agg(jsonb_build_object('id', c.id, 'tag', c.tag, 'nom', c.nom, 'couleur', c.couleur,
                                                          'membres', (select count(*) from clan_membres m where m.clan_id = c.id),
                                                          'plein', clan_diplo_compte(c.id) >= 5) order by c.tag)
      from clans c
     where c.id <> v_clan
       and not exists (select 1 from clan_diplomatie d where d.etat in ('en_attente', 'ouvert')
                        and least(d.clan_a, d.clan_b) = least(c.id, v_clan) and greatest(d.clan_a, d.clan_b) = greatest(c.id, v_clan))), '[]'::jsonb),
    -- s2-148 : tous les autres clans, pour inviter dans une alliance
    'tous_clans', coalesce((select jsonb_agg(jsonb_build_object('id', c.id, 'tag', c.tag, 'nom', c.nom, 'couleur', c.couleur,
                                                          'membres', (select count(*) from clan_membres m where m.clan_id = c.id),
                                                          'plein', clan_diplo_compte(c.id) >= 5) order by c.tag)
      from clans c where c.id <> v_clan), '[]'::jsonb),
    -- s2-148 : les alliances où mon clan est membre ou invité
    'alliances', coalesce((select jsonb_agg(jsonb_build_object(
        'id', a.id, 'nom', a.nom, 'mon_etat', mm.etat, 'expire_le', mm.expire_le, 'cree_le', a.cree_le,
        'fondateur', (select f.tag from clans f where f.id = a.fondateur),
        'salon', (select count(*) from clan_alliance_membres x where x.alliance_id = a.id and x.etat = 'membre') >= 2,
        'clans', (select jsonb_agg(jsonb_build_object('id', c.id, 'tag', c.tag, 'nom', c.nom, 'couleur', c.couleur, 'etat', x.etat, 'moi', c.id = v_clan)
                                   order by x.etat <> 'membre', coalesce(x.rejoint_le, x.invite_le))
                    from clan_alliance_membres x join clans c on c.id = x.clan_id
                   where x.alliance_id = a.id and x.etat in ('membre', 'invite')))
        order by mm.etat = 'membre', a.cree_le desc)
      from clan_alliances a join clan_alliance_membres mm on mm.alliance_id = a.id and mm.clan_id = v_clan
     where a.etat = 'ouvert' and mm.etat in ('membre', 'invite')), '[]'::jsonb));
end $f$;

-- ---------- ce que le bot des clans reçoit : les alliances d'au moins 2 clans ----------
create or replace function public.discord_clans_donnees()
 returns jsonb language sql stable security definer set search_path to 'public'
as $f$
  select jsonb_build_object(
    'clans', coalesce((select jsonb_agg(jsonb_build_object(
        'tag', c.tag, 'nom', c.nom, 'couleur', c.couleur,
        'chef', (select j.pseudo from joueurs j where j.id = c.chef),
        'membres', coalesce((select jsonb_agg(j.pseudo order by j.pseudo)
                               from clan_membres m join joueurs j on j.id = m.joueur_id
                              where m.clan_id = c.id), '[]'::jsonb))
      order by c.tag) from clans c), '[]'::jsonb),
    'correspondances', coalesce((select jsonb_object_agg(pseudo, discord) from discord_correspondances), '{}'::jsonb),
    'diplo', coalesce((select jsonb_agg(x.o order by x.k) from (
        select d.id::text as k, jsonb_build_object('id', d.id, 'a', ca.tag, 'b', cb.tag, 'nom_a', ca.nom, 'nom_b', cb.nom) as o
          from clan_diplomatie d join clans ca on ca.id = d.clan_a join clans cb on cb.id = d.clan_b
         where d.etat = 'ouvert'
        union all   -- s2-148 : les alliances (id « a12 »)
        select 'a' || a.id, jsonb_build_object('id', 'a' || a.id, 'alliance', a.nom,
                 'clans', (select jsonb_agg(jsonb_build_object('tag', c.tag, 'nom', c.nom) order by m.rejoint_le, c.tag)
                             from clan_alliance_membres m join clans c on c.id = m.clan_id
                            where m.alliance_id = a.id and m.etat = 'membre'))
          from clan_alliances a
         where a.etat = 'ouvert'
           and (select count(*) from clan_alliance_membres m where m.alliance_id = a.id and m.etat = 'membre') >= 2) x), '[]'::jsonb));
$f$;

select exists (select 1 from pg_proc where proname = 'clan_alli_creer') as fonctions_ok,
       position('alliances' in pg_get_functiondef('public.clan_diplo_etat'::regproc)) > 0 as etat_ok,
       position('s2-148' in pg_get_functiondef('public.discord_clans_donnees'::regproc)) > 0 as discord_ok,
       (select count(*) from public.clan_alliances)::integer as alliances;
