-- ===========================================================================
--  TerraFront — s2-99 : la discussion générale (4/11/2026)
--  Décidé avec Nataël le 4/11 : un salon public plutôt que des messages
--  privés (« comme ça je peux surveiller ») ; aperçus validés (« parfait »).
--
--  - discussion_messages : 300 caractères, gardés 30 jours (effacés au fil
--    des envois, pas de tâche planifiée). Lisibles par tous les joueurs
--    connectés (règle RLS) : c'est aussi ce qui permet le temps réel.
--  - Écrire : compte d'au moins 24 h, un message toutes les 5 s, 300 par
--    jour au plus, pas de lien, pas de mot de la liste (config_jeu
--    'discussion', modifiable). Pas pour un joueur muet ou exclu.
--  - Signaler : un joueur de plus de 24 h, une fois par message ; à
--    3 signalements, le message est masqué en attendant la modération.
--  - Modération (discussion_moderateurs) : retirer, muet 1 h / 24 h,
--    exclure de la discussion (le joueur peut toujours jouer), classer.
--    Tout est noté dans discussion_moderation (avec le texte retiré), 1 an.
--  - Lu / non lu : enregistré sur le compte (dernier message lu).
--  - Les messages d'un joueur bloqué (Amis › Bloquer) ne sont pas montrés.
--  Fonctions : discussion_lire(apres), discussion_envoyer(texte),
--  discussion_signaler(id), discussion_moderer(id, action),
--  discussion_signales(), discussion_marquer_lu(id), discussion_etat().
--  Rejouable. Contrôle attendu : true | true | true | true | 3 | 0
--  ENSUITE : se déclarer modérateur (ligne donnée à part, avec ton pseudo).
-- ===========================================================================
begin;

-- 1. le réglage ---------------------------------------------------------------
insert into public.config_jeu (cle, valeur)
values ('discussion', '{"ouvert": 1, "longueur": 300, "delai_s": 5, "par_jour": 300, "anciennete_h": 24,
  "seuil_masque": 3, "garde_jours": 30,
  "mots": ["connard", "connards", "connasse", "conasse", "salope", "salopes", "salaud", "pute", "putes", "fils de pute",
           "fdp", "encule", "encules", "enculer", "ntm", "nique ta mere", "niquer ta mere", "ta mere la pute",
           "batard", "batards", "batarde", "pd", "pede", "pedes", "tapette", "gouine", "negro", "negre", "negres",
           "bougnoul", "bougnoule", "bicot", "youpin", "youpine", "chinetoque", "sale arabe", "sale noir", "sale juif",
           "suce ma", "suceur", "suceuse", "va te faire foutre", "tg", "ferme ta gueule", "nazi de merde"]}')
on conflict (cle) do nothing;

-- 2. les tables ---------------------------------------------------------------
create table if not exists public.discussion_messages (
  id        bigint generated always as identity primary key,
  auteur    uuid not null references public.joueurs(id) on delete cascade,
  texte     text not null,
  le        timestamptz not null default now(),
  retire    boolean not null default false,   -- retiré par la modération : texte effacé
  masque    boolean not null default false,   -- masqué en attendant (signalements)
  check (retire or char_length(texte) between 1 and 300)
);
create index if not exists discussion_messages_auteur on public.discussion_messages (auteur, le desc);
create index if not exists discussion_messages_le on public.discussion_messages (le);

create table if not exists public.discussion_signalements (
  message_id bigint references public.discussion_messages(id) on delete cascade,
  par        uuid not null references public.joueurs(id) on delete cascade,
  texte      text not null,                  -- copie au moment du signalement
  le         timestamptz not null default now(),
  traite     boolean not null default false,
  primary key (message_id, par)
);

create table if not exists public.discussion_sanctions (
  joueur_id uuid primary key references public.joueurs(id) on delete cascade,
  type      text not null check (type in ('muet', 'exclu')),
  jusqua    timestamptz,                      -- null : sans fin (exclu)
  par       uuid,
  le        timestamptz not null default now()
);

create table if not exists public.discussion_lecture (
  joueur_id  uuid primary key references public.joueurs(id) on delete cascade,
  dernier_id bigint not null default 0,
  le         timestamptz not null default now()
);

create table if not exists public.discussion_moderateurs (
  joueur_id uuid primary key references public.joueurs(id) on delete cascade
);

create table if not exists public.discussion_moderation (   -- journal, gardé 1 an
  id         bigint generated always as identity primary key,
  message_id bigint,
  auteur     uuid references public.joueurs(id) on delete set null,
  action     text not null,
  texte      text,
  par        uuid references public.joueurs(id) on delete set null,
  le         timestamptz not null default now()
);

alter table public.discussion_messages     enable row level security;
alter table public.discussion_signalements enable row level security;
alter table public.discussion_sanctions    enable row level security;
alter table public.discussion_lecture      enable row level security;
alter table public.discussion_moderateurs  enable row level security;
alter table public.discussion_moderation   enable row level security;
revoke all on public.discussion_messages, public.discussion_signalements, public.discussion_sanctions,
              public.discussion_lecture, public.discussion_moderateurs, public.discussion_moderation
  from public, anon, authenticated;

-- le temps réel a besoin de lire la table : tous les joueurs connectés (salon public)
grant select on public.discussion_messages to authenticated;
drop policy if exists discussion_messages_lire on public.discussion_messages;
create policy discussion_messages_lire on public.discussion_messages for select to authenticated using (true);
do $$ begin
  if exists (select 1 from pg_publication where pubname = 'supabase_realtime')
     and not exists (select 1 from pg_publication_tables where pubname = 'supabase_realtime'
                       and schemaname = 'public' and tablename = 'discussion_messages') then
    execute 'alter publication supabase_realtime add table public.discussion_messages';
  end if;
end $$;

-- 3. outils internes ----------------------------------------------------------
create or replace function public.discussion_reglage(p_cle text)
 returns jsonb language sql stable security definer set search_path to 'public' as $f$
  select coalesce((select c.valeur::jsonb from config_jeu c where c.cle = 'discussion'), '{}'::jsonb) -> p_cle;
$f$;

create or replace function public.discussion_est_moderateur(p_uid uuid)
 returns boolean language sql stable security definer set search_path to 'public' as $f$
  select p_uid is not null and exists (select 1 from discussion_moderateurs m where m.joueur_id = p_uid);
$f$;

-- texte simplifié pour le filtre : minuscules, sans accents, mots séparés par une espace
create or replace function public.discussion_simplifier(p_texte text)
 returns text language sql immutable set search_path to 'public' as $f$
  select ' ' || btrim(regexp_replace(
    translate(lower(coalesce(p_texte, '')), 'àâäáãåçéèêëíìîïñóòôöõúùûüýÿœæ', 'aaaaaaceeeeiiiinooooouuuuyyoa'),
    '[^a-z0-9]+', ' ', 'g')) || ' ';
$f$;

-- un message vu par un joueur (masqué/retiré : sans texte, sauf masqué pour un modérateur)
create or replace function public.discussion_json(p_m public.discussion_messages, p_uid uuid, p_modo boolean, p_pseudo_moi text)
 returns jsonb language sql stable security definer set search_path to 'public' as $f$
  select jsonb_build_object(
    'id', p_m.id, 'auteur', p_m.auteur, 'pseudo', j.pseudo,
    'clan', (select k.tag from clan_membres cm join clans k on k.id = cm.clan_id where cm.joueur_id = p_m.auteur limit 1),
    'texte', case when p_m.retire then '' when p_m.masque and not p_modo and p_m.auteur <> p_uid then '' else p_m.texte end,
    'le', p_m.le, 'retire', p_m.retire, 'masque', p_m.masque,
    'moi', p_m.auteur = p_uid,
    'modo', exists (select 1 from discussion_moderateurs dm where dm.joueur_id = p_m.auteur),
    'cite', p_pseudo_moi is not null and not p_m.retire and p_m.auteur <> p_uid
            and p_m.texte ~* ('@' || regexp_replace(p_pseudo_moi, '([.\-\[\]\\^$*+?(){}|])', '\\\1', 'g') || '($|[^[:alnum:]_À-ÿ])'),
    'signale', case when p_modo then (select count(*) from discussion_signalements s where s.message_id = p_m.id and not s.traite) else null end)
  from joueurs j where j.id = p_m.auteur;
$f$;

-- ce que le joueur peut faire
create or replace function public.discussion_moi(p_uid uuid)
 returns jsonb language plpgsql stable security definer set search_path to 'public' as $f$
declare
  s discussion_sanctions%rowtype;
  v_cree timestamptz;
  v_h numeric := coalesce((discussion_reglage('anciennete_h'))::numeric, 24);
  v_modo boolean := discussion_est_moderateur(p_uid);
begin
  select * into s from discussion_sanctions where joueur_id = p_uid and (jusqua is null or jusqua > now());
  select u.created_at into v_cree from auth.users u where u.id = p_uid;
  return jsonb_build_object(
    'moderateur', v_modo,
    'signalements', case when v_modo then (select count(distinct message_id) from discussion_signalements where not traite) else 0 end,
    'peut_ecrire', coalesce((discussion_reglage('ouvert'))::int, 1) = 1 and s.joueur_id is null
                   and (v_modo or v_cree is null or v_cree <= now() - make_interval(hours => v_h::int)),
    'sanction', s.type, 'jusqua', s.jusqua,
    'ouvre_le', case when not v_modo and v_cree is not null and v_cree > now() - make_interval(hours => v_h::int)
                     then v_cree + make_interval(hours => v_h::int) end);
end; $f$;

revoke all on function public.discussion_reglage(text), public.discussion_est_moderateur(uuid),
  public.discussion_simplifier(text), public.discussion_json(public.discussion_messages, uuid, boolean, text),
  public.discussion_moi(uuid) from public, anon, authenticated;

-- 4. lire -----------------------------------------------------------------------
-- p_apres null : les 100 derniers messages ; sinon ceux qui suivent ce numéro
create or replace function public.discussion_lire(p_apres bigint default null)
 returns jsonb language plpgsql stable security definer set search_path to 'public' as $f$
declare
  v_uid uuid := auth.uid();
  v_modo boolean;
  v_pseudo text;
begin
  /* s2-99 */
  if v_uid is null then raise exception 'Non connecté'; end if;
  v_modo := discussion_est_moderateur(v_uid);
  select pseudo into v_pseudo from joueurs where id = v_uid;
  return jsonb_build_object(
    'messages', coalesce((
      select jsonb_agg(discussion_json(m, v_uid, v_modo, v_pseudo) order by m.id)
        from discussion_messages m
       where m.id in (select m2.id from discussion_messages m2
                       where (p_apres is null or m2.id > p_apres)
                         and m2.le > now() - make_interval(days => coalesce((discussion_reglage('garde_jours'))::int, 30))
                         and not exists (select 1 from amis a where a.joueur_id = v_uid and a.ami_id = m2.auteur and a.etat = 'bloque')
                       order by m2.id desc limit 100)), '[]'::jsonb),
    'moi', discussion_moi(v_uid));
end; $f$;

-- 5. écrire ---------------------------------------------------------------------
create or replace function public.discussion_envoyer(p_texte text)
 returns jsonb language plpgsql volatile security definer set search_path to 'public' as $f$
declare
  v_uid  uuid := auth.uid();
  v_moi  jsonb;
  v_modo boolean;
  v_t    text;
  v_s    text;
  v_mot  text;
  v_der  timestamptz;
  v_d    integer := coalesce((discussion_reglage('delai_s'))::int, 5);
  m      discussion_messages%rowtype;
begin
  /* s2-99 */
  if v_uid is null then raise exception 'Non connecté'; end if;
  perform 1 from joueurs where id = v_uid for update;   -- un envoi à la fois par joueur
  if not found then raise exception 'Joueur introuvable'; end if;
  v_modo := discussion_est_moderateur(v_uid);
  v_moi := discussion_moi(v_uid);
  if not (v_moi->>'peut_ecrire')::boolean then
    if v_moi->>'sanction' = 'exclu' then raise exception 'Tu as été exclu de la discussion par la modération. Tu peux toujours jouer.'; end if;
    if v_moi->>'sanction' = 'muet' then
      raise exception 'Tu ne peux plus écrire dans la discussion jusqu''à % (modération).',
        to_char((v_moi->>'jusqua')::timestamptz at time zone 'Europe/Paris', 'HH24:MI');
    end if;
    if v_moi->>'ouvre_le' is not null then
      raise exception 'La discussion s''ouvre 24 h après ton inscription : tu pourras écrire le %.',
        to_char((v_moi->>'ouvre_le')::timestamptz at time zone 'Europe/Paris', 'DD/MM à HH24:MI');
    end if;
    raise exception 'La discussion est fermée pour le moment.';
  end if;

  v_t := btrim(regexp_replace(regexp_replace(coalesce(p_texte, ''), '[[:cntrl:]]+', ' ', 'g'), '[[:space:]]+', ' ', 'g'));
  if char_length(v_t) = 0 then raise exception 'Message vide'; end if;
  if char_length(v_t) > coalesce((discussion_reglage('longueur'))::int, 300) then
    raise exception 'Message trop long (% caractères au plus)', coalesce((discussion_reglage('longueur'))::int, 300);
  end if;
  if v_t ~* '(https?:|www\.|discord\.(gg|com)|[[:alnum:]-]+\.(com|fr|net|org|io|gg|xyz|be|ch|ly|me|co|tv|app|link|shop|info|biz|ru|cn)([/?#[:space:]]|$))' then
    raise exception 'Les liens ne sont pas autorisés dans la discussion.';
  end if;
  v_s := discussion_simplifier(v_t);
  select mot into v_mot from jsonb_array_elements_text(coalesce(discussion_reglage('mots'), '[]'::jsonb)) as w(mot)
   where position(discussion_simplifier(w.mot) in v_s) > 0 limit 1;
  if v_mot is not null then raise exception 'Ce message contient un mot interdit dans la discussion.'; end if;

  if not v_modo then
    select max(le) into v_der from discussion_messages where auteur = v_uid;
    if v_der is not null and v_der > now() - make_interval(secs => v_d) then
      raise exception 'Doucement : un message toutes les % secondes.', v_d;
    end if;
    if (select count(*) from discussion_messages where auteur = v_uid and le > now() - interval '24 hours')
       >= coalesce((discussion_reglage('par_jour'))::int, 300) then
      raise exception 'Tu as beaucoup écrit aujourd''hui : la discussion te rouvre ses portes demain.';
    end if;
  end if;

  insert into discussion_messages (auteur, texte) values (v_uid, v_t) returning * into m;
  -- ménage : au-delà de 30 jours, les messages disparaissent (leurs signalements avec)
  delete from discussion_messages where le < now() - make_interval(days => coalesce((discussion_reglage('garde_jours'))::int, 30));
  delete from discussion_moderation where le < now() - interval '1 year';
  -- ce qu'on écrit, on l'a lu
  insert into discussion_lecture (joueur_id, dernier_id) values (v_uid, m.id)
  on conflict (joueur_id) do update set dernier_id = greatest(discussion_lecture.dernier_id, excluded.dernier_id), le = now();
  return discussion_json(m, v_uid, v_modo, (select pseudo from joueurs where id = v_uid));
end; $f$;

-- 6. signaler ---------------------------------------------------------------------
create or replace function public.discussion_signaler(p_id bigint)
 returns jsonb language plpgsql volatile security definer set search_path to 'public' as $f$
declare
  v_uid uuid := auth.uid();
  m discussion_messages%rowtype;
  v_cree timestamptz;
  v_n integer;
begin
  /* s2-99 */
  if v_uid is null then raise exception 'Non connecté'; end if;
  select * into m from discussion_messages where id = p_id for update;
  if m.id is null or m.retire then raise exception 'Message introuvable'; end if;
  if m.auteur = v_uid then raise exception 'Tu ne peux pas signaler ton propre message.'; end if;
  select u.created_at into v_cree from auth.users u where u.id = v_uid;
  if v_cree is not null and v_cree > now() - make_interval(hours => coalesce((discussion_reglage('anciennete_h'))::int, 24)) then
    raise exception 'Tu pourras signaler un message 24 h après ton inscription. Écris à contact@terrafront.fr si c''est urgent.';
  end if;
  insert into discussion_signalements (message_id, par, texte) values (p_id, v_uid, m.texte) on conflict do nothing;
  select count(*) into v_n from discussion_signalements where message_id = p_id and not traite;
  if v_n >= coalesce((discussion_reglage('seuil_masque'))::int, 3) and not m.masque then
    update discussion_messages set masque = true where id = p_id;
    return jsonb_build_object('ok', true, 'masque', true);
  end if;
  return jsonb_build_object('ok', true, 'masque', m.masque);
end; $f$;

-- 7. modérer ----------------------------------------------------------------------
-- actions : retirer | muet1h | muet24h | exclure | classer
create or replace function public.discussion_moderer(p_id bigint, p_action text)
 returns jsonb language plpgsql volatile security definer set search_path to 'public' as $f$
declare
  v_uid uuid := auth.uid();
  m discussion_messages%rowtype;
begin
  /* s2-99 */
  if not discussion_est_moderateur(v_uid) then raise exception 'Réservé à la modération'; end if;
  select * into m from discussion_messages where id = p_id for update;
  if m.id is null then raise exception 'Message introuvable'; end if;
  if p_action = 'retirer' then
    insert into discussion_moderation (message_id, auteur, action, texte, par) values (m.id, m.auteur, 'retirer', m.texte, v_uid);
    update discussion_messages set retire = true, masque = false, texte = '' where id = m.id;
    update discussion_signalements set traite = true where message_id = m.id;
  elsif p_action in ('muet1h', 'muet24h', 'exclure') then
    if m.auteur = v_uid then raise exception 'Pas sur toi-même'; end if;
    insert into discussion_moderation (message_id, auteur, action, texte, par) values (m.id, m.auteur, p_action, m.texte, v_uid);
    insert into discussion_sanctions (joueur_id, type, jusqua, par)
    values (m.auteur, case when p_action = 'exclure' then 'exclu' else 'muet' end,
            case p_action when 'muet1h' then now() + interval '1 hour' when 'muet24h' then now() + interval '24 hours' end, v_uid)
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

-- les messages signalés à regarder (modération)
create or replace function public.discussion_signales()
 returns jsonb language plpgsql stable security definer set search_path to 'public' as $f$
declare v_uid uuid := auth.uid();
begin
  /* s2-99 */
  if not discussion_est_moderateur(v_uid) then raise exception 'Réservé à la modération'; end if;
  return coalesce((
    select jsonb_agg(discussion_json(m, v_uid, true, null) order by x.dernier desc)
      from (select s.message_id, max(s.le) as dernier from discussion_signalements s where not s.traite group by s.message_id) x
      join discussion_messages m on m.id = x.message_id), '[]'::jsonb);
end; $f$;

-- 8. lu / non lu ----------------------------------------------------------------------
create or replace function public.discussion_marquer_lu(p_id bigint)
 returns void language plpgsql volatile security definer set search_path to 'public' as $f$
declare v_uid uuid := auth.uid();
begin
  /* s2-99 */
  if v_uid is null or p_id is null then return; end if;
  insert into discussion_lecture (joueur_id, dernier_id) values (v_uid, least(p_id, (select coalesce(max(id), 0) from discussion_messages)))
  on conflict (joueur_id) do update set dernier_id = greatest(discussion_lecture.dernier_id, excluded.dernier_id), le = now();
end; $f$;

-- pour la cloche : non lus, citations, dernier message, signalements (modération)
create or replace function public.discussion_etat()
 returns jsonb language plpgsql stable security definer set search_path to 'public' as $f$
declare
  v_uid uuid := auth.uid();
  v_lu bigint;
  v_pseudo text;
  v_modo boolean;
begin
  /* s2-99 */
  if v_uid is null then raise exception 'Non connecté'; end if;
  v_modo := discussion_est_moderateur(v_uid);
  select pseudo into v_pseudo from joueurs where id = v_uid;
  select dernier_id into v_lu from discussion_lecture where joueur_id = v_uid;
  -- jamais ouvert : seulement les messages des dernières 24 h comptent
  if v_lu is null then
    select coalesce(max(id), 0) into v_lu from discussion_messages where le < now() - interval '24 hours';
  end if;
  return (
    with nl as (
      select m.* from discussion_messages m
       where m.id > v_lu and m.auteur <> v_uid and not m.retire and not m.masque
         and not exists (select 1 from amis a where a.joueur_id = v_uid and a.ami_id = m.auteur and a.etat = 'bloque'))
    select jsonb_build_object(
      'non_lus', least(99, (select count(*) from nl)),
      'dernier', (select jsonb_build_object('pseudo', j.pseudo, 'texte', left(n.texte, 80)) from nl n join joueurs j on j.id = n.auteur order by n.id desc limit 1),
      'citations', coalesce((select jsonb_agg(discussion_json(m, v_uid, v_modo, v_pseudo) order by m.id desc)
                               from discussion_messages m
                              where m.id in (select id from nl order by id desc limit 50)
                                and v_pseudo is not null
                                and m.texte ~* ('@' || regexp_replace(v_pseudo, '([.\-\[\]\\^$*+?(){}|])', '\\\1', 'g') || '($|[^[:alnum:]_À-ÿ])')), '[]'::jsonb),
      'moderateur', v_modo,
      'signalements', case when v_modo then (select count(distinct message_id) from discussion_signalements where not traite) else 0 end));
end; $f$;

revoke all on function public.discussion_lire(bigint), public.discussion_envoyer(text), public.discussion_signaler(bigint),
  public.discussion_moderer(bigint, text), public.discussion_signales(), public.discussion_marquer_lu(bigint),
  public.discussion_etat() from public, anon;
grant execute on function public.discussion_lire(bigint), public.discussion_envoyer(text), public.discussion_signaler(bigint),
  public.discussion_moderer(bigint, text), public.discussion_signales(), public.discussion_marquer_lu(bigint),
  public.discussion_etat() to authenticated;

commit;

-- Contrôle : true | true | true | true | 3 | 0
select has_function_privilege('authenticated', 'public.discussion_envoyer(text)', 'execute')                     as envoyer_ok,
       has_function_privilege('authenticated', 'public.discussion_etat()', 'execute')                            as etat_ok,
       exists (select 1 from pg_policies where tablename = 'discussion_messages' and policyname = 'discussion_messages_lire') as regle_ok,
       exists (select 1 from pg_publication_tables where pubname = 'supabase_realtime' and tablename = 'discussion_messages') as temps_reel_ok,
       (select (c.valeur::jsonb ->> 'seuil_masque')::int from public.config_jeu c where c.cle = 'discussion')     as seuil_masque,
       (select count(*) from public.discussion_moderateurs)                                                      as moderateurs;

-- Lire la discussion en entier (modération, incognito) :
-- select to_char(m.le at time zone 'Europe/Paris', 'DD/MM HH24:MI') as le, j.pseudo, m.texte, m.retire, m.masque, m.id
--   from public.discussion_messages m join public.joueurs j on j.id = m.auteur order by m.id desc limit 200;
-- Lever une sanction :   delete from public.discussion_sanctions where joueur_id = (select id from public.joueurs where pseudo = 'PSEUDO');
-- Fermer la discussion : update public.config_jeu set valeur = (valeur::jsonb || '{"ouvert": 0}'::jsonb) where cle = 'discussion';
-- Ajouter un mot :       update public.config_jeu set valeur = jsonb_set(valeur::jsonb, '{mots}', (valeur::jsonb -> 'mots') || '["mot"]'::jsonb) where cle = 'discussion';
