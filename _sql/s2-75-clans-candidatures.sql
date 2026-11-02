-- ===========================================================================
--  TerraFront — s2-75 : postuler dans un clan depuis le jeu (2/11/2026)
--  Décidé avec Nataël le 2/11 (aperçu « Premiers pas et candidatures » validé).
--
--  - clans.recrute : le chef (ou un bras droit qui peut inviter) ferme ou
--    ouvre le recrutement. Fermé = personne ne peut postuler ; les
--    invitations marchent toujours.
--  - clan_candidatures : un joueur sans clan postule, avec un mot facultatif
--    (140 caractères). 3 candidatures en attente au plus ; sans réponse,
--    elles expirent au bout de 3 jours.
--  - Le chef ou un bras droit qui peut inviter accepte ou refuse. Accepter =
--    mêmes règles qu'une invitation (8 membres au plus, 48 h après un
--    départ) ; le joueur entre tout de suite et ses autres candidatures
--    sont annulées. Le candidat voit la réponse (acceptée ou refusée).
--
--  Fonctions (toutes renvoient l'état, sauf indiqué) :
--    clan_candidatures_etat()                     → jsonb
--    clan_postuler(p_clan, p_message)             → mon_clan()
--    clan_candidature_retirer(p_clan)             → mon_clan()
--    clan_candidature_repondre(p_joueur, p_oui)   → mon_clan()
--    clan_recrutement(p_ouvert)                   → mon_clan()
--  Ne touche à aucune fonction existante. Rejouable. Contrôle en une ligne.
-- ===========================================================================
begin;

alter table public.clans add column if not exists recrute boolean not null default true;

create table if not exists public.clan_candidatures(
  clan_id    uuid not null references public.clans(id) on delete cascade,
  joueur_id  uuid not null references public.joueurs(id) on delete cascade,
  message    text,
  le         timestamptz not null default now(),
  statut     text not null default 'attente' check (statut in ('attente', 'acceptee', 'refusee')),
  decide_le  timestamptz,
  decide_par uuid references public.joueurs(id) on delete set null,
  primary key (clan_id, joueur_id)
);
create index if not exists clan_candidatures_joueur on public.clan_candidatures(joueur_id);
alter table public.clan_candidatures enable row level security;
revoke all on public.clan_candidatures from public, anon, authenticated;

-- le clan que je gère (chef, ou bras droit qui peut inviter), sinon null
create or replace function public.clan_que_je_gere(p_uid uuid)
 returns uuid language sql stable security definer set search_path to 'public' as $f$
  select coalesce(
    (select c.id from clans c where c.chef = p_uid),
    (select m.clan_id from clan_membres m where m.joueur_id = p_uid and m.bras_droit and m.peut_inviter));
$f$;
revoke all on function public.clan_que_je_gere(uuid) from public, anon, authenticated;

create or replace function public.clan_candidatures_etat()
 returns jsonb language plpgsql stable security definer set search_path to 'public' as $f$
declare
  v_uid uuid := auth.uid();
  v_clan uuid;
begin
  if v_uid is null then raise exception 'Non connecte'; end if;
  v_clan := clan_que_je_gere(v_uid);
  return jsonb_build_object(
    -- mes candidatures : en attente (3 jours), et les réponses des 3 derniers jours
    'mes', coalesce((select jsonb_agg(jsonb_build_object('clan_id', k.clan_id, 'nom', c.nom, 'tag', c.tag,
                                      'statut', k.statut, 'le', k.le, 'decide_le', k.decide_le) order by k.le desc)
                       from clan_candidatures k join clans c on c.id = k.clan_id
                      where k.joueur_id = v_uid
                        and ((k.statut = 'attente' and k.le > now() - interval '3 days')
                          or (k.statut <> 'attente' and k.decide_le > now() - interval '3 days'))), '[]'::jsonb),
    -- les clans fermés au recrutement
    'fermes', coalesce((select jsonb_agg(c.id) from clans c where not c.recrute), '[]'::jsonb),
    'gere', v_clan is not null,
    'recrute', (select c.recrute from clans c where c.id = v_clan),
    -- les candidatures reçues par le clan que je gère
    'recues', case when v_clan is null then '[]'::jsonb else coalesce((
      select jsonb_agg(jsonb_build_object('joueur_id', j.id, 'pseudo', j.pseudo, 'message', k.message, 'le', k.le,
                       'communes', (select count(*) from possessions p where p.joueur_id = j.id),
                       'inscrit_le', (select u.created_at from auth.users u where u.id = j.id),
                       'dernier_jour', (select max(jj.jour) from jours_joues jj where jj.joueur_id = j.id))
                       order by k.le)
        from clan_candidatures k join joueurs j on j.id = k.joueur_id
       where k.clan_id = v_clan and k.statut = 'attente' and k.le > now() - interval '3 days'
         and not exists (select 1 from clan_membres m where m.joueur_id = k.joueur_id)), '[]'::jsonb) end);
end; $f$;
revoke all on function public.clan_candidatures_etat() from public, anon;
grant execute on function public.clan_candidatures_etat() to authenticated;

create or replace function public.clan_postuler(p_clan uuid, p_message text default null)
 returns jsonb language plpgsql security definer set search_path to 'public' as $f$
declare
  v_uid uuid := auth.uid();
  c clans%rowtype;
  v_msg text := nullif(btrim(coalesce(p_message, '')), '');
begin
  if v_uid is null then raise exception 'Non connecte'; end if;
  if not clans_ouverts() then raise exception 'Les clans ouvrent bientot'; end if;
  perform 1 from joueurs where id = v_uid for update;
  select * into c from clans where id = p_clan;
  if c.id is null then raise exception 'Ce clan n''existe plus'; end if;
  if exists (select 1 from clan_membres where joueur_id = v_uid) then raise exception 'Tu es deja dans un clan'; end if;
  if clan_attente(v_uid) is not null then raise exception 'Attente de 48 h apres un depart'; end if;
  if not c.recrute then raise exception 'Ce clan ne recrute pas en ce moment'; end if;
  if (select count(*) from clan_membres where clan_id = p_clan) >= 8 then raise exception 'Le clan est complet (8 membres)'; end if;
  if char_length(coalesce(v_msg, '')) > 140 then raise exception 'Ton mot est trop long (140 caracteres au plus)'; end if;
  -- les vieilles candidatures (expirées, ou réponses de plus de 3 jours) partent
  delete from clan_candidatures where joueur_id = v_uid
     and ((statut = 'attente' and le <= now() - interval '3 days') or (statut <> 'attente' and decide_le <= now() - interval '3 days'));
  if exists (select 1 from clan_candidatures where clan_id = p_clan and joueur_id = v_uid and statut = 'refusee') then
    raise exception 'Ce clan a refusé ta candidature : réessaie dans quelques jours';
  end if;
  if (select count(*) from clan_candidatures where joueur_id = v_uid and statut = 'attente' and clan_id <> p_clan) >= 3 then
    raise exception 'Tu as deja 3 candidatures en attente : retire-en une';
  end if;
  insert into clan_candidatures(clan_id, joueur_id, message) values (p_clan, v_uid, v_msg)
  on conflict (clan_id, joueur_id) do update set message = excluded.message, le = now(), statut = 'attente', decide_le = null, decide_par = null;
  return mon_clan();
end; $f$;
revoke all on function public.clan_postuler(uuid, text) from public, anon;
grant execute on function public.clan_postuler(uuid, text) to authenticated;

create or replace function public.clan_candidature_retirer(p_clan uuid)
 returns jsonb language plpgsql security definer set search_path to 'public' as $f$
declare v_uid uuid := auth.uid();
begin
  if v_uid is null then raise exception 'Non connecte'; end if;
  delete from clan_candidatures where clan_id = p_clan and joueur_id = v_uid and statut = 'attente';
  return mon_clan();
end; $f$;
revoke all on function public.clan_candidature_retirer(uuid) from public, anon;
grant execute on function public.clan_candidature_retirer(uuid) to authenticated;

create or replace function public.clan_candidature_repondre(p_joueur uuid, p_accepter boolean)
 returns jsonb language plpgsql security definer set search_path to 'public' as $f$
declare
  v_uid uuid := auth.uid();
  v_clan uuid;
begin
  if v_uid is null then raise exception 'Non connecte'; end if;
  if not clans_ouverts() then raise exception 'Les clans ouvrent bientot'; end if;
  v_clan := clan_que_je_gere(v_uid);
  if v_clan is null then raise exception 'Seul le chef (ou un bras droit qui peut inviter) répond aux candidatures'; end if;
  if not exists (select 1 from clan_candidatures where clan_id = v_clan and joueur_id = p_joueur
                  and statut = 'attente' and le > now() - interval '3 days') then
    raise exception 'Candidature introuvable ou expiree';
  end if;
  if not p_accepter then
    update clan_candidatures set statut = 'refusee', decide_le = now(), decide_par = v_uid
     where clan_id = v_clan and joueur_id = p_joueur;
    return mon_clan();
  end if;
  -- mêmes verrous et mêmes règles qu'une invitation acceptée
  perform 1 from clans where id = v_clan for update;
  perform 1 from joueurs where id = p_joueur for update;
  if exists (select 1 from clan_membres where joueur_id = p_joueur) then
    delete from clan_candidatures where joueur_id = p_joueur and statut = 'attente';
    raise exception 'Ce joueur est deja dans un clan';
  end if;
  if clan_attente(p_joueur) is not null then raise exception 'Ce joueur a quitte un clan il y a moins de 48 h'; end if;
  if (select count(*) from clan_membres where clan_id = v_clan) >= 8 then raise exception 'Le clan est complet (8 membres)'; end if;
  perform clan_entrer(p_joueur, v_clan);
  delete from clan_candidatures where joueur_id = p_joueur and clan_id <> v_clan and statut = 'attente';
  update clan_candidatures set statut = 'acceptee', decide_le = now(), decide_par = v_uid
   where clan_id = v_clan and joueur_id = p_joueur;
  return mon_clan();
end; $f$;
revoke all on function public.clan_candidature_repondre(uuid, boolean) from public, anon;
grant execute on function public.clan_candidature_repondre(uuid, boolean) to authenticated;

create or replace function public.clan_recrutement(p_ouvert boolean)
 returns jsonb language plpgsql security definer set search_path to 'public' as $f$
declare v_uid uuid := auth.uid(); v_clan uuid;
begin
  if v_uid is null then raise exception 'Non connecte'; end if;
  v_clan := clan_que_je_gere(v_uid);
  if v_clan is null then raise exception 'Seul le chef (ou un bras droit qui peut inviter) gère le recrutement'; end if;
  update clans set recrute = coalesce(p_ouvert, true) where id = v_clan;
  return mon_clan();
end; $f$;
revoke all on function public.clan_recrutement(boolean) from public, anon;
grant execute on function public.clan_recrutement(boolean) to authenticated;

commit;

-- Contrôle : true | true | true | (nombre de clans qui recrutent)
select to_regclass('public.clan_candidatures') is not null                                           as table_ok,
       has_function_privilege('authenticated', 'public.clan_postuler(uuid, text)', 'execute')       as postuler_ok,
       has_function_privilege('authenticated', 'public.clan_candidature_repondre(uuid, boolean)', 'execute') as repondre_ok,
       (select count(*) from clans where recrute)                                                    as clans_qui_recrutent;
