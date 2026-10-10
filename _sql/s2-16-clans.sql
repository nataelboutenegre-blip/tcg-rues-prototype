-- ===========================================================================
--  TerraFront — les clans (construits maintenant, ouverts après le lancement S2)
--  (décisions du 3 octobre et du 10 octobre 2026)
--
--  - 3 à 5 joueurs ; un chef qui invite par pseudo ; le joueur accepte.
--  - Front : les membres d'un même clan ne peuvent pas s'attaquer.
--    Le territoire d'un coéquipier ne compte PAS dans les chances (rien ne
--    change au calcul de proximité).
--  - En rejoignant un clan, les sièges en cours entre le nouveau membre et
--    les autres membres sont annulés, sans remboursement.
--  - Classement des clans à la MOYENNE par membre (clans de 3 membres et
--    plus), jamais au total. Aucun bonus ne croît avec le nombre de membres.
--  - 48 h d'attente après avoir quitté (ou été exclu d'un) clan avant d'en
--    rejoindre ou d'en créer un autre.
--  - Couleur de clan dans une palette limitée ; sur la carte, affichée
--    seulement par un filtre (côté jeu).
--
--  FERMÉ tant que config_jeu 'clans_ouverts' n'est pas 'true' : toutes les
--  fonctions refusent, et l'attaque ne change pas. Pour ouvrir, le moment
--  venu : insert into config_jeu(cle, valeur) values ('clans_ouverts', 'true')
--  on conflict (cle) do update set valeur = excluded.valeur;
--
--  La fonction attaquer() est modifiée à partir de sa définition en
--  production (un seul ajout, vérifié). Rejouable. Finit par un contrôle.
-- ===========================================================================

create or replace function public.clans_ouverts()
 returns boolean language sql stable set search_path to 'public'
as $f$
  select exists (select 1 from config_jeu
                  where cle = 'clans_ouverts' and trim(both '"' from valeur::text) = 'true');
$f$;

create table if not exists public.clans(
  id       uuid primary key default gen_random_uuid(),
  nom      text not null check (char_length(nom) between 3 and 24),
  tag      text not null check (tag ~ '^[A-Z0-9]{2,4}$'),
  couleur  text not null check (couleur in ('#E07A2E','#4C9BE8','#C45BD6','#2BB673','#E5484D','#E8C547','#1ABC9C','#8E9AAF')),
  chef     uuid references public.joueurs(id) on delete set null,
  cree_le  timestamptz not null default now()
);
create unique index if not exists clans_nom_unique on public.clans(lower(nom));
create unique index if not exists clans_tag_unique on public.clans(tag);

create table if not exists public.clan_membres(
  joueur_id uuid primary key references public.joueurs(id) on delete cascade,
  clan_id   uuid not null references public.clans(id) on delete cascade,
  depuis    timestamptz not null default now()
);
create index if not exists clan_membres_clan on public.clan_membres(clan_id);

create table if not exists public.clan_invitations(
  clan_id   uuid not null references public.clans(id) on delete cascade,
  joueur_id uuid not null references public.joueurs(id) on delete cascade,
  par       uuid references public.joueurs(id) on delete set null,
  le        timestamptz not null default now(),
  primary key (clan_id, joueur_id)
);

create table if not exists public.clan_departs(
  joueur_id uuid primary key references public.joueurs(id) on delete cascade,
  le        timestamptz not null default now()
);

alter table public.clans            enable row level security;
alter table public.clan_membres     enable row level security;
alter table public.clan_invitations enable row level security;
alter table public.clan_departs     enable row level security;
revoke all on public.clans, public.clan_membres, public.clan_invitations, public.clan_departs from public, anon, authenticated;

-- deux joueurs du même clan ? (faux si les clans sont fermés)
create or replace function public.meme_clan(p_a uuid, p_b uuid)
 returns boolean language sql stable security definer set search_path to 'public'
as $f$
  select clans_ouverts() and exists (
    select 1 from clan_membres a join clan_membres b on b.clan_id = a.clan_id
     where a.joueur_id = p_a and b.joueur_id = p_b);
$f$;

-- attente après un départ : null si le joueur est libre
create or replace function public.clan_attente(p_uid uuid)
 returns timestamptz language sql stable security definer set search_path to 'public'
as $f$
  select d.le + interval '48 hours' from clan_departs d
   where d.joueur_id = p_uid and d.le + interval '48 hours' > now();
$f$;

-- entrée dans un clan : annule les sièges en cours avec les autres membres
create or replace function public.clan_entrer(p_uid uuid, p_clan uuid)
 returns void language plpgsql security definer set search_path to 'public'
as $f$
begin
  insert into clan_membres(joueur_id, clan_id) values (p_uid, p_clan);
  delete from clan_invitations where joueur_id = p_uid;
  delete from sieges s
   using possessions p
   where p.commune_code = s.commune_code
     and ((s.attacker_id = p_uid and p.joueur_id in (select joueur_id from clan_membres where clan_id = p_clan and joueur_id <> p_uid))
       or (p.joueur_id = p_uid and s.attacker_id in (select joueur_id from clan_membres where clan_id = p_clan and joueur_id <> p_uid)));
end;
$f$;

-- sortie : le chef passe au plus ancien ; un clan vide disparaît
create or replace function public.clan_sortir(p_uid uuid)
 returns void language plpgsql security definer set search_path to 'public'
as $f$
declare
  v_clan uuid;
  v_suivant uuid;
begin
  delete from clan_membres where joueur_id = p_uid returning clan_id into v_clan;
  if v_clan is null then return; end if;
  insert into clan_departs(joueur_id, le) values (p_uid, now())
  on conflict (joueur_id) do update set le = excluded.le;
  select joueur_id into v_suivant from clan_membres where clan_id = v_clan order by depuis, joueur_id limit 1;
  if v_suivant is null then
    delete from clans where id = v_clan;
  else
    update clans set chef = v_suivant where id = v_clan and (chef = p_uid or chef is null);
  end if;
end;
$f$;

create or replace function public.mon_clan()
 returns jsonb language plpgsql stable security definer set search_path to 'public'
as $f$
declare
  v_uid uuid := auth.uid();
  v_clan clans%rowtype;
begin
  if v_uid is null then raise exception 'Non connecte'; end if;
  if not clans_ouverts() then raise exception 'Les clans ouvrent bientot'; end if;
  select c.* into v_clan from clans c join clan_membres m on m.clan_id = c.id where m.joueur_id = v_uid;
  return jsonb_build_object(
    'attente_jusqua', clan_attente(v_uid),
    'invitations', coalesce((
      select jsonb_agg(jsonb_build_object('clan_id', c.id, 'nom', c.nom, 'tag', c.tag, 'couleur', c.couleur,
                                          'par', (select pseudo from joueurs where id = i.par),
                                          'membres', (select count(*) from clan_membres where clan_id = c.id))
                       order by i.le desc)
        from clan_invitations i join clans c on c.id = i.clan_id
       where i.joueur_id = v_uid and i.le > now() - interval '7 days'), '[]'::jsonb),
    'clan', case when v_clan.id is null then null else jsonb_build_object(
      'id', v_clan.id, 'nom', v_clan.nom, 'tag', v_clan.tag, 'couleur', v_clan.couleur, 'cree_le', v_clan.cree_le,
      'chef', v_clan.chef = v_uid,
      'membres', (select jsonb_agg(jsonb_build_object(
                      'id', j.id, 'pseudo', j.pseudo, 'chef', j.id = v_clan.chef, 'moi', j.id = v_uid,
                      'communes', (select count(*) from possessions p where p.joueur_id = j.id))
                    order by (select count(*) from possessions p where p.joueur_id = j.id) desc)
                    from clan_membres m join joueurs j on j.id = m.joueur_id where m.clan_id = v_clan.id),
      'invites', coalesce((select jsonb_agg(j.pseudo order by i.le desc)
                    from clan_invitations i join joueurs j on j.id = i.joueur_id
                   where i.clan_id = v_clan.id and i.le > now() - interval '7 days'), '[]'::jsonb)
    ) end);
end;
$f$;

-- classement : moyenne de communes du Front par membre, clans de 3 membres et plus
create or replace function public.clans_classement()
 returns table(clan_id uuid, nom text, tag text, couleur text, membres integer, communes integer, moyenne integer)
 language plpgsql stable security definer set search_path to 'public'
as $f$
begin
  if auth.uid() is null then raise exception 'Non connecte'; end if;
  if not clans_ouverts() then raise exception 'Les clans ouvrent bientot'; end if;
  return query
  select c.id, c.nom, c.tag, c.couleur, x.n::integer, x.total::integer,
         round(x.total::numeric / x.n)::integer
    from clans c
    join lateral (select count(*) n,
                         (select count(*) from possessions p where p.joueur_id in
                            (select m2.joueur_id from clan_membres m2 where m2.clan_id = c.id)) total
                    from clan_membres m where m.clan_id = c.id) x on true
   where x.n >= 3
   order by 7 desc, c.nom;
end;
$f$;

-- pour le filtre « Clans » de la carte : qui est dans quel clan
create or replace function public.clans_carte()
 returns table(joueur_id uuid, tag text, couleur text)
 language plpgsql stable security definer set search_path to 'public'
as $f$
begin
  if auth.uid() is null then raise exception 'Non connecte'; end if;
  if not clans_ouverts() then return; end if;
  return query select m.joueur_id, c.tag, c.couleur from clan_membres m join clans c on c.id = m.clan_id;
end;
$f$;

create or replace function public.clan_creer(p_nom text, p_tag text, p_couleur text)
 returns jsonb language plpgsql security definer set search_path to 'public'
as $f$
declare
  v_uid uuid := auth.uid();
  v_id uuid;
  v_nom text := btrim(regexp_replace(coalesce(p_nom, ''), '\s+', ' ', 'g'));
  v_tag text := upper(btrim(coalesce(p_tag, '')));
begin
  if v_uid is null then raise exception 'Non connecte'; end if;
  if not clans_ouverts() then raise exception 'Les clans ouvrent bientot'; end if;
  perform 1 from joueurs where id = v_uid for update;
  if exists(select 1 from clan_membres where joueur_id = v_uid) then raise exception 'Tu es deja dans un clan'; end if;
  if clan_attente(v_uid) is not null then raise exception 'Attente de 48 h apres un depart'; end if;
  if char_length(v_nom) not between 3 and 24 then raise exception 'Nom du clan : 3 a 24 caracteres'; end if;
  if v_tag !~ '^[A-Z0-9]{2,4}$' then raise exception 'Sigle : 2 a 4 lettres ou chiffres'; end if;
  if exists(select 1 from clans where lower(nom) = lower(v_nom)) then raise exception 'Ce nom de clan est deja pris'; end if;
  if exists(select 1 from clans where tag = v_tag) then raise exception 'Ce sigle est deja pris'; end if;
  insert into clans(nom, tag, couleur, chef) values (v_nom, v_tag, p_couleur, v_uid) returning id into v_id;
  perform clan_entrer(v_uid, v_id);
  return mon_clan();
end;
$f$;

create or replace function public.clan_inviter(p_pseudo text)
 returns jsonb language plpgsql security definer set search_path to 'public'
as $f$
declare
  v_uid uuid := auth.uid();
  v_clan uuid;
  v_cible uuid;
begin
  if v_uid is null then raise exception 'Non connecte'; end if;
  if not clans_ouverts() then raise exception 'Les clans ouvrent bientot'; end if;
  select c.id into v_clan from clans c where c.chef = v_uid;
  if v_clan is null then raise exception 'Seul le chef peut inviter'; end if;
  select id into v_cible from joueurs where lower(pseudo) = lower(btrim(p_pseudo));
  if v_cible is null then raise exception 'Joueur introuvable'; end if;
  if v_cible = v_uid then raise exception 'Tu es deja dans ton clan'; end if;
  if exists(select 1 from clan_membres where joueur_id = v_cible) then raise exception 'Ce joueur est deja dans un clan'; end if;
  if (select count(*) from clan_membres where clan_id = v_clan) >= 5 then raise exception 'Le clan est complet (5 membres)'; end if;
  insert into clan_invitations(clan_id, joueur_id, par) values (v_clan, v_cible, v_uid)
  on conflict (clan_id, joueur_id) do update set le = now(), par = excluded.par;
  return mon_clan();
end;
$f$;

create or replace function public.clan_repondre(p_clan uuid, p_accepter boolean)
 returns jsonb language plpgsql security definer set search_path to 'public'
as $f$
declare
  v_uid uuid := auth.uid();
begin
  if v_uid is null then raise exception 'Non connecte'; end if;
  if not clans_ouverts() then raise exception 'Les clans ouvrent bientot'; end if;
  if not exists(select 1 from clan_invitations where clan_id = p_clan and joueur_id = v_uid and le > now() - interval '7 days') then
    raise exception 'Invitation introuvable ou expiree';
  end if;
  if not p_accepter then
    delete from clan_invitations where clan_id = p_clan and joueur_id = v_uid;
    return mon_clan();
  end if;
  -- verrou sur le clan : deux acceptations simultanées ne dépassent pas 5
  perform 1 from clans where id = p_clan for update;
  perform 1 from joueurs where id = v_uid for update;
  if exists(select 1 from clan_membres where joueur_id = v_uid) then raise exception 'Tu es deja dans un clan'; end if;
  if clan_attente(v_uid) is not null then raise exception 'Attente de 48 h apres un depart'; end if;
  if (select count(*) from clan_membres where clan_id = p_clan) >= 5 then raise exception 'Le clan est complet (5 membres)'; end if;
  perform clan_entrer(v_uid, p_clan);
  return mon_clan();
end;
$f$;

create or replace function public.clan_quitter()
 returns jsonb language plpgsql security definer set search_path to 'public'
as $f$
declare
  v_uid uuid := auth.uid();
begin
  if v_uid is null then raise exception 'Non connecte'; end if;
  if not clans_ouverts() then raise exception 'Les clans ouvrent bientot'; end if;
  if not exists(select 1 from clan_membres where joueur_id = v_uid) then raise exception 'Tu n''es dans aucun clan'; end if;
  perform clan_sortir(v_uid);
  return mon_clan();
end;
$f$;

create or replace function public.clan_exclure(p_joueur uuid)
 returns jsonb language plpgsql security definer set search_path to 'public'
as $f$
declare
  v_uid uuid := auth.uid();
  v_clan uuid;
begin
  if v_uid is null then raise exception 'Non connecte'; end if;
  if not clans_ouverts() then raise exception 'Les clans ouvrent bientot'; end if;
  select id into v_clan from clans where chef = v_uid;
  if v_clan is null then raise exception 'Seul le chef peut exclure'; end if;
  if p_joueur = v_uid then raise exception 'Pour partir, quitte le clan'; end if;
  if not exists(select 1 from clan_membres where joueur_id = p_joueur and clan_id = v_clan) then
    raise exception 'Ce joueur n''est pas dans ton clan';
  end if;
  perform clan_sortir(p_joueur);
  return mon_clan();
end;
$f$;

-- attaquer() : refuser d'attaquer un membre de son clan --------------------------------------
do $g$
declare
  v_def text;
  v_avant text := $a$  if v_defenseur_id = v_attaquant_id then raise exception 'Tu ne peux pas attaquer ta propre commune'; end if;$a$;
  v_apres text := $a$  if v_defenseur_id = v_attaquant_id then raise exception 'Tu ne peux pas attaquer ta propre commune'; end if;
  -- clans : pas d'attaque entre membres d'un meme clan
  if meme_clan(v_attaquant_id, v_defenseur_id) then raise exception 'Tu ne peux pas attaquer un membre de ton clan'; end if;$a$;
  n integer;
begin
  v_def := pg_get_functiondef('public.attaquer(text,text)'::regprocedure);
  if position('meme_clan(' in v_def) > 0 then
    raise notice 'attaquer : deja en place';
    return;
  end if;
  n := (length(v_def) - length(replace(v_def, v_avant, ''))) / length(v_avant);
  if n <> 1 then
    raise exception 'attaquer : texte a remplacer present % fois au lieu de 1. Rien n''a ete modifie.', n;
  end if;
  execute replace(v_def, v_avant, v_apres);
end
$g$;

revoke all on function public.clans_ouverts()                   from public, anon, authenticated;
revoke all on function public.meme_clan(uuid, uuid)             from public, anon, authenticated;
revoke all on function public.clan_attente(uuid)                from public, anon, authenticated;
revoke all on function public.clan_entrer(uuid, uuid)           from public, anon, authenticated;
revoke all on function public.clan_sortir(uuid)                 from public, anon, authenticated;
revoke all on function public.mon_clan()                        from public, anon;
revoke all on function public.clans_classement()                from public, anon;
revoke all on function public.clans_carte()                     from public, anon;
revoke all on function public.clan_creer(text, text, text)      from public, anon;
revoke all on function public.clan_inviter(text)                from public, anon;
revoke all on function public.clan_repondre(uuid, boolean)      from public, anon;
revoke all on function public.clan_quitter()                    from public, anon;
revoke all on function public.clan_exclure(uuid)                from public, anon;
grant execute on function public.mon_clan()                     to authenticated;
grant execute on function public.clans_classement()             to authenticated;
grant execute on function public.clans_carte()                  to authenticated;
grant execute on function public.clan_creer(text, text, text)   to authenticated;
grant execute on function public.clan_inviter(text)             to authenticated;
grant execute on function public.clan_repondre(uuid, boolean)   to authenticated;
grant execute on function public.clan_quitter()                 to authenticated;
grant execute on function public.clan_exclure(uuid)             to authenticated;

-- Contrôle ------------------------------------------------------------------------------------
select public.clans_ouverts() as clans_ouverts_doit_etre_false,
       position('meme_clan(' in pg_get_functiondef('public.attaquer(text,text)'::regprocedure)) > 0 as attaque_protegee,
       (select count(*) from pg_proc where pronamespace = 'public'::regnamespace
          and proname in ('mon_clan','clans_classement','clans_carte','clan_creer','clan_inviter','clan_repondre','clan_quitter','clan_exclure')) as fonctions_doit_etre_8,
       has_function_privilege('anon', 'public.clan_creer(text,text,text)', 'execute') as anon_doit_etre_false;
