-- ===========================================================================
--  TerraFront — s2-99b : la discussion, plus d'options de modération, avatars
--  et blasons (4/11/2026, aperçus validés « parfait » et « parfait ! »).
--  À lancer APRÈS s2-99.
--
--  1. discussion_json : l'avatar du joueur et la couleur de son clan (pour le
--     blason) ; pour la modération, sa sanction en cours.
--  2. discussion_moi : réglages en cours (ouvert, délai) ; le modérateur peut
--     écrire même quand la discussion est fermée.
--  3. discussion_moderer : + muet7j, + retirer24h (tous les messages de
--     l'auteur des dernières 24 h, chacun noté au journal).
--  4. discussion_lever(joueur) : lever un muet ou une exclusion.
--  5. discussion_sanctions_liste() : les sanctions en cours.
--  6. discussion_journal() : les 50 dernières actions de modération.
--  7. discussion_regler(cle, valeur) : mode lent (delai_s 5 ou 30) et
--     ouverture (ouvert 1 ou 0), depuis le jeu.
--  Remplace des fonctions de s2-99 en entier (même signature). Rejouable.
--  Contrôle attendu : true | true | true | true | true
-- ===========================================================================
begin;

-- 1. un message vu par un joueur ---------------------------------------------
create or replace function public.discussion_json(p_m public.discussion_messages, p_uid uuid, p_modo boolean, p_pseudo_moi text)
 returns jsonb language sql stable security definer set search_path to 'public' as $f$
  /* s2-99b */
  select jsonb_build_object(
    'id', p_m.id, 'auteur', p_m.auteur, 'pseudo', j.pseudo, 'avatar', j.avatar,
    'clan', k.tag, 'clan_couleur', k.couleur,
    'texte', case when p_m.retire then '' when p_m.masque and not p_modo and p_m.auteur <> p_uid then '' else p_m.texte end,
    'le', p_m.le, 'retire', p_m.retire, 'masque', p_m.masque,
    'moi', p_m.auteur = p_uid,
    'modo', exists (select 1 from discussion_moderateurs dm where dm.joueur_id = p_m.auteur),
    'cite', p_pseudo_moi is not null and not p_m.retire and p_m.auteur <> p_uid
            and p_m.texte ~* ('@' || regexp_replace(p_pseudo_moi, '([.\-\[\]\\^$*+?(){}|])', '\\\1', 'g') || '($|[^[:alnum:]_À-ÿ])'),
    'signale', case when p_modo then (select count(*) from discussion_signalements s where s.message_id = p_m.id and not s.traite) else null end,
    'sanction', case when p_modo then (select s.type from discussion_sanctions s where s.joueur_id = p_m.auteur and (s.jusqua is null or s.jusqua > now())) end,
    'jusqua', case when p_modo then (select s.jusqua from discussion_sanctions s where s.joueur_id = p_m.auteur and (s.jusqua is null or s.jusqua > now())) end)
  from joueurs j
  left join clan_membres cm on cm.joueur_id = j.id
  left join clans k on k.id = cm.clan_id
  where j.id = p_m.auteur
  limit 1;
$f$;

-- 2. ce que le joueur peut faire ----------------------------------------------
create or replace function public.discussion_moi(p_uid uuid)
 returns jsonb language plpgsql stable security definer set search_path to 'public' as $f$
declare
  s discussion_sanctions%rowtype;
  v_cree timestamptz;
  v_h numeric := coalesce((discussion_reglage('anciennete_h'))::numeric, 24);
  v_modo boolean := discussion_est_moderateur(p_uid);
  v_ouvert boolean := coalesce((discussion_reglage('ouvert'))::int, 1) = 1;
begin
  /* s2-99b */
  select * into s from discussion_sanctions where joueur_id = p_uid and (jusqua is null or jusqua > now());
  select u.created_at into v_cree from auth.users u where u.id = p_uid;
  return jsonb_build_object(
    'moderateur', v_modo,
    'signalements', case when v_modo then (select count(distinct message_id) from discussion_signalements where not traite) else 0 end,
    'sanctions', case when v_modo then (select count(*) from discussion_sanctions where jusqua is null or jusqua > now()) else 0 end,
    'ouvert', v_ouvert,
    'delai_s', coalesce((discussion_reglage('delai_s'))::int, 5),
    'peut_ecrire', (v_ouvert or v_modo) and s.joueur_id is null
                   and (v_modo or v_cree is null or v_cree <= now() - make_interval(hours => v_h::int)),
    'sanction', s.type, 'jusqua', s.jusqua,
    'ouvre_le', case when not v_modo and v_cree is not null and v_cree > now() - make_interval(hours => v_h::int)
                     then v_cree + make_interval(hours => v_h::int) end);
end; $f$;

-- 3. modérer : + muet 7 jours, + retirer tous ses messages des dernières 24 h --
create or replace function public.discussion_moderer(p_id bigint, p_action text)
 returns jsonb language plpgsql volatile security definer set search_path to 'public' as $f$
declare
  v_uid uuid := auth.uid();
  m discussion_messages%rowtype;
  x discussion_messages%rowtype;
begin
  /* s2-99b */
  if not discussion_est_moderateur(v_uid) then raise exception 'Réservé à la modération'; end if;
  select * into m from discussion_messages where id = p_id for update;
  if m.id is null then raise exception 'Message introuvable'; end if;
  if p_action = 'retirer' then
    insert into discussion_moderation (message_id, auteur, action, texte, par) values (m.id, m.auteur, 'retirer', m.texte, v_uid);
    update discussion_messages set retire = true, masque = false, texte = '' where id = m.id;
    update discussion_signalements set traite = true where message_id = m.id;
  elsif p_action = 'retirer24h' then
    for x in select * from discussion_messages where auteur = m.auteur and not retire and le > now() - interval '24 hours' for update loop
      insert into discussion_moderation (message_id, auteur, action, texte, par) values (x.id, x.auteur, 'retirer', x.texte, v_uid);
      update discussion_messages set retire = true, masque = false, texte = '' where id = x.id;
      update discussion_signalements set traite = true where message_id = x.id;
    end loop;
  elsif p_action in ('muet1h', 'muet24h', 'muet7j', 'exclure') then
    if m.auteur = v_uid then raise exception 'Pas sur toi-même'; end if;
    insert into discussion_moderation (message_id, auteur, action, texte, par) values (m.id, m.auteur, p_action, m.texte, v_uid);
    insert into discussion_sanctions (joueur_id, type, jusqua, par)
    values (m.auteur, case when p_action = 'exclure' then 'exclu' else 'muet' end,
            case p_action when 'muet1h' then now() + interval '1 hour' when 'muet24h' then now() + interval '24 hours'
                          when 'muet7j' then now() + interval '7 days' end, v_uid)
    on conflict (joueur_id) do update set type = excluded.type, jusqua = excluded.jusqua, par = excluded.par, le = now();
  elsif p_action = 'classer' then
    insert into discussion_moderation (message_id, auteur, action, texte, par) values (m.id, m.auteur, 'classer', m.texte, v_uid);
    update discussion_messages set masque = false where id = m.id;
    update discussion_signalements set traite = true where message_id = m.id;
  else
    raise exception 'Action inconnue';
  end if;
  select * into m from discussion_messages where id = p_id;
  return discussion_json(m, v_uid, true, (select pseudo from joueurs where id = v_uid));
end; $f$;

-- 4. lever une sanction -------------------------------------------------------
create or replace function public.discussion_lever(p_joueur uuid)
 returns void language plpgsql volatile security definer set search_path to 'public' as $f$
declare v_uid uuid := auth.uid(); v_type text;
begin
  /* s2-99b */
  if not discussion_est_moderateur(v_uid) then raise exception 'Réservé à la modération'; end if;
  delete from discussion_sanctions where joueur_id = p_joueur returning type into v_type;
  if v_type is not null then
    insert into discussion_moderation (message_id, auteur, action, texte, par) values (null, p_joueur, 'lever', v_type, v_uid);
  end if;
end; $f$;

-- 5. les sanctions en cours ---------------------------------------------------
create or replace function public.discussion_sanctions_liste()
 returns jsonb language plpgsql stable security definer set search_path to 'public' as $f$
declare v_uid uuid := auth.uid();
begin
  /* s2-99b */
  if not discussion_est_moderateur(v_uid) then raise exception 'Réservé à la modération'; end if;
  return coalesce((
    select jsonb_agg(jsonb_build_object('joueur_id', s.joueur_id, 'pseudo', j.pseudo, 'avatar', j.avatar, 'type', s.type,
                                        'jusqua', s.jusqua, 'le', s.le, 'par', (select pseudo from joueurs where id = s.par),
                                        'par_moi', s.par = v_uid) order by s.le desc)
      from discussion_sanctions s join joueurs j on j.id = s.joueur_id
     where s.jusqua is null or s.jusqua > now()), '[]'::jsonb);
end; $f$;

-- 6. le journal de modération ---------------------------------------------------
create or replace function public.discussion_journal()
 returns jsonb language plpgsql stable security definer set search_path to 'public' as $f$
declare v_uid uuid := auth.uid();
begin
  /* s2-99b */
  if not discussion_est_moderateur(v_uid) then raise exception 'Réservé à la modération'; end if;
  return coalesce((
    select jsonb_agg(jsonb_build_object('le', x.le, 'action', x.action, 'texte', left(x.texte, 120),
                                        'pseudo', (select pseudo from joueurs where id = x.auteur),
                                        'par', (select pseudo from joueurs where id = x.par)) order by x.id desc)
      from (select * from discussion_moderation order by id desc limit 50) x), '[]'::jsonb);
end; $f$;

-- 7. régler la discussion depuis le jeu (mode lent, ouverture) -------------------
create or replace function public.discussion_regler(p_cle text, p_valeur int)
 returns jsonb language plpgsql volatile security definer set search_path to 'public' as $f$
declare v_uid uuid := auth.uid();
begin
  /* s2-99b */
  if not discussion_est_moderateur(v_uid) then raise exception 'Réservé à la modération'; end if;
  if not ((p_cle = 'ouvert' and p_valeur in (0, 1)) or (p_cle = 'delai_s' and p_valeur between 1 and 120)) then
    raise exception 'Réglage refusé';
  end if;
  update config_jeu set valeur = (valeur::jsonb || jsonb_build_object(p_cle, p_valeur)) where cle = 'discussion';
  insert into discussion_moderation (message_id, auteur, action, texte, par) values (null, null, 'regler', p_cle || ' = ' || p_valeur, v_uid);
  return discussion_moi(v_uid);
end; $f$;

revoke all on function public.discussion_json(public.discussion_messages, uuid, boolean, text), public.discussion_moi(uuid)
  from public, anon, authenticated;
revoke all on function public.discussion_lever(uuid), public.discussion_sanctions_liste(), public.discussion_journal(),
  public.discussion_regler(text, int), public.discussion_moderer(bigint, text) from public, anon;
grant execute on function public.discussion_lever(uuid), public.discussion_sanctions_liste(), public.discussion_journal(),
  public.discussion_regler(text, int), public.discussion_moderer(bigint, text) to authenticated;

commit;

-- Contrôle : true | true | true | true | true
select has_function_privilege('authenticated', 'public.discussion_lever(uuid)', 'execute')          as lever_ok,
       has_function_privilege('authenticated', 'public.discussion_sanctions_liste()', 'execute')    as sanctions_ok,
       has_function_privilege('authenticated', 'public.discussion_journal()', 'execute')            as journal_ok,
       has_function_privilege('authenticated', 'public.discussion_regler(text, integer)', 'execute') as regler_ok,
       position('s2-99b' in pg_get_functiondef('public.discussion_json(public.discussion_messages, uuid, boolean, text)'::regprocedure)) > 0 as avatars_ok;
