-- s2-134 (10/11/2026) : la diplomatie entre clans (demande de Nataël, 10/11 0 h 31 heure du Maroc :
-- « des channels sur le discord pour que les guildes parlent entre elles, qu'elles puissent choisir avec qui »).
-- Dans le jeu (onglet Clan › Diplomatie), le chef propose un salon à un autre clan ; le chef de l'autre clan
-- accepte ou refuse ; chacun des deux chefs peut le fermer. Le bot des clans (fonction discord-clans, toutes les
-- 10 min) crée le salon privé « 🤝│a-b » dans la catégorie « 🤝 Diplomatie », visible des deux rôles de clan,
-- et le supprime quand il est fermé. 5 salons (ouverts ou proposés) au plus par clan. Une proposition attend 3 jours.

create table if not exists clan_diplomatie (
  id bigserial primary key,
  clan_a uuid not null references clans(id) on delete cascade,     -- le clan qui propose
  clan_b uuid not null references clans(id) on delete cascade,
  propose_par uuid references joueurs(id) on delete set null,
  etat text not null default 'en_attente' check (etat in ('en_attente', 'ouvert', 'refuse', 'ferme', 'annule', 'expire')),
  cree_le timestamptz not null default now(),
  expire_le timestamptz not null default now() + interval '3 days',
  ouvert_le timestamptz,
  ferme_le timestamptz,
  ferme_par uuid references joueurs(id) on delete set null,
  check (clan_a <> clan_b)
);
create unique index if not exists clan_diplomatie_paire_active
  on clan_diplomatie (least(clan_a, clan_b), greatest(clan_a, clan_b)) where etat in ('en_attente', 'ouvert');
alter table clan_diplomatie enable row level security;   -- aucune règle : seulement par les fonctions

-- salons ouverts ou propositions encore valables d'un clan
create or replace function public.clan_diplo_compte(p_clan uuid)
returns integer language sql stable security definer set search_path to 'public'
as $f$
  select count(*)::integer from clan_diplomatie d
   where p_clan in (d.clan_a, d.clan_b) and (d.etat = 'ouvert' or (d.etat = 'en_attente' and d.expire_le > now()));
$f$;

create or replace function public.clan_diplo_etat()
returns jsonb language plpgsql security definer set search_path to 'public'
as $f$
declare v_uid uuid := auth.uid(); v_clan uuid; v_chef boolean;
begin
  if v_uid is null then raise exception 'Non connecte'; end if;
  update clan_diplomatie set etat = 'expire', ferme_le = now() where etat = 'en_attente' and expire_le <= now();
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
                        and least(d.clan_a, d.clan_b) = least(c.id, v_clan) and greatest(d.clan_a, d.clan_b) = greatest(c.id, v_clan))), '[]'::jsonb));
end; $f$;

create or replace function public.clan_diplo_proposer(p_clan uuid)
returns text language plpgsql security definer set search_path to 'public'
as $f$
declare v_uid uuid := auth.uid(); v_clan uuid; v_tag text;
begin
  if v_uid is null then raise exception 'Non connecte'; end if;
  select c.id into v_clan from clans c where c.chef = v_uid;
  if v_clan is null then raise exception 'Seul le chef du clan peut ouvrir un salon de diplomatie.'; end if;
  if p_clan is null or p_clan = v_clan then raise exception 'Choisis un autre clan.'; end if;
  select tag into v_tag from clans where id = p_clan;
  if v_tag is null then raise exception 'Ce clan n''existe plus.'; end if;
  perform pg_advisory_xact_lock(hashtext('clan_diplo'));
  update clan_diplomatie set etat = 'expire', ferme_le = now() where etat = 'en_attente' and expire_le <= now();
  if exists (select 1 from clan_diplomatie d where d.etat in ('en_attente', 'ouvert')
              and least(d.clan_a, d.clan_b) = least(p_clan, v_clan) and greatest(d.clan_a, d.clan_b) = greatest(p_clan, v_clan)) then
    raise exception 'Un salon avec [%] est déjà ouvert ou proposé.', v_tag;
  end if;
  if clan_diplo_compte(v_clan) >= 5 then raise exception 'Ton clan a déjà 5 salons de diplomatie (ouverts ou proposés).'; end if;
  if clan_diplo_compte(p_clan) >= 5 then raise exception 'Le clan [%] a déjà 5 salons de diplomatie.', v_tag; end if;
  insert into clan_diplomatie(clan_a, clan_b, propose_par) values (v_clan, p_clan, v_uid);
  return 'Proposition envoyée au clan [' || v_tag || ']';
end; $f$;

create or replace function public.clan_diplo_repondre(p_id bigint, p_accepter boolean)
returns text language plpgsql security definer set search_path to 'public'
as $f$
declare v_uid uuid := auth.uid(); d clan_diplomatie%rowtype; v_tag text;
begin
  if v_uid is null then raise exception 'Non connecte'; end if;
  perform pg_advisory_xact_lock(hashtext('clan_diplo'));
  select * into d from clan_diplomatie where id = p_id for update;
  if d.id is null or not exists (select 1 from clans c where c.id = d.clan_b and c.chef = v_uid) then
    raise exception 'Seul le chef du clan invité peut répondre.';
  end if;
  if d.etat <> 'en_attente' then raise exception 'Cette proposition a déjà été traitée.'; end if;
  if d.expire_le <= now() then
    update clan_diplomatie set etat = 'expire', ferme_le = now() where id = p_id;
    raise exception 'Cette proposition a expiré.';
  end if;
  select tag into v_tag from clans where id = d.clan_a;
  if not p_accepter then
    update clan_diplomatie set etat = 'refuse', ferme_le = now(), ferme_par = v_uid where id = p_id;
    return 'Proposition refusée';
  end if;
  update clan_diplomatie set etat = 'ouvert', ouvert_le = now() where id = p_id;
  return 'Salon ouvert avec [' || coalesce(v_tag, '?') || '] : il apparaît sur le Discord dans les 10 minutes';
end; $f$;

create or replace function public.clan_diplo_fermer(p_id bigint)
returns text language plpgsql security definer set search_path to 'public'
as $f$
declare v_uid uuid := auth.uid(); d clan_diplomatie%rowtype; v_a boolean; v_b boolean;
begin
  if v_uid is null then raise exception 'Non connecte'; end if;
  select * into d from clan_diplomatie where id = p_id for update;
  if d.id is null then raise exception 'Salon introuvable.'; end if;
  v_a := exists (select 1 from clans c where c.id = d.clan_a and c.chef = v_uid);
  v_b := exists (select 1 from clans c where c.id = d.clan_b and c.chef = v_uid);
  if not (v_a or v_b) then raise exception 'Seul un des deux chefs peut fermer ce salon.'; end if;
  if d.etat = 'ouvert' then
    update clan_diplomatie set etat = 'ferme', ferme_le = now(), ferme_par = v_uid where id = p_id;
    return 'Salon fermé : il disparaît du Discord dans les 10 minutes';
  elsif d.etat = 'en_attente' then
    update clan_diplomatie set etat = case when v_a then 'annule' else 'refuse' end, ferme_le = now(), ferme_par = v_uid where id = p_id;
    return case when v_a then 'Proposition annulée' else 'Proposition refusée' end;
  end if;
  raise exception 'Ce salon est déjà fermé.';
end; $f$;

revoke execute on function public.clan_diplo_compte(uuid) from public, anon;
revoke execute on function public.clan_diplo_etat() from public, anon;
revoke execute on function public.clan_diplo_proposer(uuid) from public, anon;
revoke execute on function public.clan_diplo_repondre(bigint, boolean) from public, anon;
revoke execute on function public.clan_diplo_fermer(bigint) from public, anon;
grant execute on function public.clan_diplo_etat() to authenticated;
grant execute on function public.clan_diplo_proposer(uuid) to authenticated;
grant execute on function public.clan_diplo_repondre(bigint, boolean) to authenticated;
grant execute on function public.clan_diplo_fermer(bigint) to authenticated;

-- le bot : les salons ouverts (par les sigles des clans)
create or replace function public.discord_clans_donnees()
 returns jsonb language sql stable security definer set search_path to 'public'
as $function$
  select jsonb_build_object(
    'clans', coalesce((select jsonb_agg(jsonb_build_object(
        'tag', c.tag, 'nom', c.nom, 'couleur', c.couleur,
        'chef', (select j.pseudo from joueurs j where j.id = c.chef),
        'membres', coalesce((select jsonb_agg(j.pseudo order by j.pseudo)
                               from clan_membres m join joueurs j on j.id = m.joueur_id
                              where m.clan_id = c.id), '[]'::jsonb))
      order by c.tag) from clans c), '[]'::jsonb),
    'correspondances', coalesce((select jsonb_object_agg(pseudo, discord) from discord_correspondances), '{}'::jsonb),
    'diplo', coalesce((select jsonb_agg(jsonb_build_object('id', d.id, 'a', ca.tag, 'b', cb.tag, 'nom_a', ca.nom, 'nom_b', cb.nom) order by d.id)
                         from clan_diplomatie d join clans ca on ca.id = d.clan_a join clans cb on cb.id = d.clan_b
                        where d.etat = 'ouvert'), '[]'::jsonb));   -- s2-134
$function$;

notify pgrst, 'reload schema';
