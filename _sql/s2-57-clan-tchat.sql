-- ===========================================================================
--  s2-57 — Le tchat du clan (28/10, aperçu validé par Nataël : « Parfait ! »)
--  - clan_messages : 300 caractères au plus, gardés 7 jours (effacés au fil
--    des lectures et des envois, pas besoin de tâche planifiée).
--  - Lecture : seulement les membres du clan (règle RLS) ; c'est aussi elle qui
--    filtre le temps réel (Supabase Realtime, table ajoutée à la publication).
--  - Envoi : un message toutes les 2 secondes au plus par joueur.
--  - Supprimer : l'auteur, le chef, ou un bras droit qui peut exclure ou modifier.
--    Le texte d'un message supprimé est effacé pour de bon.
--  - Signaler : clan_signalements (lecture pour Nataël, voir la fin du fichier).
--  Fonctions : clan_tchat_lire(), clan_tchat_envoyer(texte),
--  clan_tchat_supprimer(id), clan_tchat_signaler(id).
--  Rejouable. Contrôle attendu : true | true | true | true
-- ===========================================================================
begin;

create table if not exists public.clan_messages(
  id           bigserial primary key,
  clan_id      uuid not null references public.clans(id) on delete cascade,
  auteur       uuid not null references public.joueurs(id) on delete cascade,
  texte        text not null,
  le           timestamptz not null default now(),
  supprime     boolean not null default false,
  supprime_par uuid,
  check (supprime or char_length(texte) between 1 and 300)
);
create index if not exists clan_messages_clan on public.clan_messages(clan_id, id desc);
create index if not exists clan_messages_auteur on public.clan_messages(auteur, le desc);

create table if not exists public.clan_signalements(
  id         bigserial primary key,
  message_id bigint references public.clan_messages(id) on delete set null,   -- le signalement reste après l'effacement
  par        uuid not null references public.joueurs(id) on delete cascade,
  texte      text not null,               -- copie du message au moment du signalement
  le         timestamptz not null default now(),
  unique (message_id, par)
);

alter table public.clan_messages enable row level security;
alter table public.clan_signalements enable row level security;
revoke all on public.clan_messages, public.clan_signalements from public, anon, authenticated;
-- le temps réel a besoin de pouvoir lire la table : seulement les lignes de MON clan
-- (clan_membres est fermée aux joueurs : on passe par une fonction)
create or replace function public.mon_clan_id()
 returns uuid language sql stable security definer set search_path to 'public'
as $f$ select clan_id from clan_membres where joueur_id = auth.uid(); $f$;
revoke all on function public.mon_clan_id() from public, anon;
grant execute on function public.mon_clan_id() to authenticated;
grant select on public.clan_messages to authenticated;
drop policy if exists clan_messages_lire on public.clan_messages;
create policy clan_messages_lire on public.clan_messages for select to authenticated
  using (clan_id = public.mon_clan_id());

do $$ begin
  if not exists (select 1 from pg_publication_tables where pubname = 'supabase_realtime'
                   and schemaname = 'public' and tablename = 'clan_messages') then
    execute 'alter publication supabase_realtime add table public.clan_messages';
  end if;
end $$;

create or replace function public.clan_tchat_lire()
 returns jsonb language plpgsql security definer set search_path to 'public'
as $f$
declare v_uid uuid := auth.uid(); v_clan uuid;
begin
  if v_uid is null then raise exception 'Non connecte'; end if;
  select clan_id into v_clan from clan_membres where joueur_id = v_uid;
  if v_clan is null then return jsonb_build_object('clan_id', null, 'messages', '[]'::jsonb); end if;
  delete from clan_messages where clan_id = v_clan and le < now() - interval '7 days';
  return jsonb_build_object('clan_id', v_clan, 'messages', coalesce((
    select jsonb_agg(jsonb_build_object('id', x.id, 'auteur', x.auteur, 'pseudo', x.pseudo, 'texte', x.texte,
                                        'le', x.le, 'supprime', x.supprime) order by x.id)
      from (select m.id, m.auteur, j.pseudo, m.texte, m.le, m.supprime
              from clan_messages m join joueurs j on j.id = m.auteur
             where m.clan_id = v_clan order by m.id desc limit 150) x), '[]'::jsonb));
end;
$f$;

create or replace function public.clan_tchat_envoyer(p_texte text)
 returns jsonb language plpgsql security definer set search_path to 'public'
as $f$
declare v_uid uuid := auth.uid(); v_clan uuid; v_t text := btrim(coalesce(p_texte, '')); v_id bigint; v_le timestamptz;
begin
  if v_uid is null then raise exception 'Non connecte'; end if;
  select clan_id into v_clan from clan_membres where joueur_id = v_uid;
  if v_clan is null then raise exception 'Tu n''es dans aucun clan'; end if;
  if char_length(v_t) = 0 then raise exception 'Message vide'; end if;
  if char_length(v_t) > 300 then raise exception 'Message trop long (300 caractères au plus)'; end if;
  perform 1 from joueurs where id = v_uid for update;
  if exists (select 1 from clan_messages where auteur = v_uid and le > now() - interval '2 seconds') then
    raise exception 'Doucement : un message toutes les 2 secondes';
  end if;
  insert into clan_messages(clan_id, auteur, texte) values (v_clan, v_uid, v_t) returning id, le into v_id, v_le;
  delete from clan_messages where clan_id = v_clan and le < now() - interval '7 days';
  return jsonb_build_object('id', v_id, 'auteur', v_uid, 'pseudo', (select pseudo from joueurs where id = v_uid),
                            'texte', v_t, 'le', v_le, 'supprime', false);
end;
$f$;

create or replace function public.clan_tchat_supprimer(p_id bigint)
 returns void language plpgsql security definer set search_path to 'public'
as $f$
declare v_uid uuid := auth.uid(); m clan_messages%rowtype; v_ok boolean;
begin
  if v_uid is null then raise exception 'Non connecte'; end if;
  select * into m from clan_messages where id = p_id;
  if m.id is null or m.supprime then return; end if;
  v_ok := m.auteur = v_uid
       or exists (select 1 from clans c where c.id = m.clan_id and c.chef = v_uid)
       or exists (select 1 from clan_membres cm where cm.joueur_id = v_uid and cm.clan_id = m.clan_id
                    and cm.bras_droit and (cm.peut_exclure or cm.peut_modifier));
  if not v_ok then raise exception 'Seuls l''auteur, le chef et les bras droits peuvent supprimer un message'; end if;
  update clan_messages set supprime = true, texte = '', supprime_par = v_uid where id = p_id;
end;
$f$;

create or replace function public.clan_tchat_signaler(p_id bigint)
 returns void language plpgsql security definer set search_path to 'public'
as $f$
declare v_uid uuid := auth.uid(); m clan_messages%rowtype;
begin
  if v_uid is null then raise exception 'Non connecte'; end if;
  select * into m from clan_messages where id = p_id;
  if m.id is null or m.supprime then return; end if;
  if not exists (select 1 from clan_membres where joueur_id = v_uid and clan_id = m.clan_id) then
    raise exception 'Message introuvable';
  end if;
  insert into clan_signalements(message_id, par, texte) values (p_id, v_uid, m.texte) on conflict do nothing;
end;
$f$;

revoke all on function public.clan_tchat_lire(), public.clan_tchat_envoyer(text),
  public.clan_tchat_supprimer(bigint), public.clan_tchat_signaler(bigint) from public, anon;
grant execute on function public.clan_tchat_lire(), public.clan_tchat_envoyer(text),
  public.clan_tchat_supprimer(bigint), public.clan_tchat_signaler(bigint) to authenticated;

commit;

select has_function_privilege('authenticated', 'public.clan_tchat_envoyer(text)', 'execute')      as envoyer_ok,
       has_function_privilege('authenticated', 'public.clan_tchat_lire()', 'execute')              as lire_ok,
       exists (select 1 from pg_policies where tablename = 'clan_messages' and policyname = 'clan_messages_lire') as regle_ok,
       exists (select 1 from pg_publication_tables where pubname = 'supabase_realtime' and tablename = 'clan_messages') as temps_reel_ok;

-- Pour lire les signalements (Nataël) :
-- select s.le, (select pseudo from joueurs where id = s.par) as signale_par,
--        (select pseudo from joueurs where id = m.auteur) as auteur, s.texte, (select nom from clans where id = m.clan_id) as clan
--   from clan_signalements s join clan_messages m on m.id = s.message_id order by s.le desc;
