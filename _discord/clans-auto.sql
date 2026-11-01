-- ===========================================================================
--  TerraFront — les clans sur le Discord, tout seuls (2 novembre 2026)
--  Va avec la fonction Edge « discord-clans » (_discord/fonction-discord-clans).
--  Mode d'emploi complet : _discord/LISEZMOI-clans-auto.md
--
--  1. discord_sync : réglages (mode, adresse de la fonction) et un secret tiré
--     au hasard ici, que personne n'a besoin de connaître : pg_cron l'envoie,
--     la fonction le compare à la base. Fermé aux joueurs.
--  2. discord_correspondances : pseudo du jeu → nom sur le Discord, pour ceux
--     qui ne s'appellent pas pareil (remplace _discord/correspondances.json).
--  3. discord_sync_journal : une ligne par passage (ce qui a été fait ou serait
--     fait, les joueurs pas trouvés, les refus de Discord). Gardé 14 jours.
--  4. discord_clans_donnees() : les clans pour la fonction (comme clans-discord.sql).
--  5. discord_clans_lancer(mode) : appelle la fonction (pg_net). Sans argument,
--     prend le mode réglé : 'simulation' (rien ne change), 'actif', ou 'arret'.
--  6. pg_cron : toutes les 10 minutes.
--
--  DÉPART EN SIMULATION : rien ne change sur le Discord tant que tu n'as pas
--  passé le mode à 'actif' (voir le mode d'emploi).
--  Prérequis : extensions pg_cron (déjà là) et pg_net (Database > Extensions).
--  Rejouable. Contrôle attendu : simulation | true | true | true | true
-- ===========================================================================
create extension if not exists pg_net;

begin;

-- 1. Réglages et secret -------------------------------------------------------
create table if not exists public.discord_sync(cle text primary key, valeur text not null);
alter table public.discord_sync enable row level security;
revoke all on public.discord_sync from public, anon, authenticated;
insert into public.discord_sync values
  ('mode', 'simulation'),
  ('url', 'https://yzcgroprydxhbwaufkdu.supabase.co/functions/v1/discord-clans'),
  ('secret', replace(gen_random_uuid()::text, '-', '') || replace(gen_random_uuid()::text, '-', ''))
on conflict (cle) do nothing;

-- 2. Correspondances pseudo du jeu → Discord ----------------------------------
create table if not exists public.discord_correspondances(pseudo text primary key, discord text not null);
alter table public.discord_correspondances enable row level security;
revoke all on public.discord_correspondances from public, anon, authenticated;

-- 3. Journal ---------------------------------------------------------------------
create table if not exists public.discord_sync_journal(
  id      bigserial primary key,
  le      timestamptz not null default now(),
  mode    text,
  ok      boolean,
  resume  text,
  details jsonb
);
alter table public.discord_sync_journal enable row level security;
revoke all on public.discord_sync_journal from public, anon, authenticated;
revoke all on sequence public.discord_sync_journal_id_seq from public, anon, authenticated;

-- 4. Ce que la fonction lit --------------------------------------------------------
create or replace function public.discord_sync_verifier(p_secret text)
 returns boolean language sql stable security definer set search_path to 'public'
as $f$
  select coalesce(p_secret <> '' and p_secret = (select valeur from discord_sync where cle = 'secret'), false);
$f$;

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
    'correspondances', coalesce((select jsonb_object_agg(pseudo, discord) from discord_correspondances), '{}'::jsonb));
$f$;

-- 5. Lancer un passage --------------------------------------------------------------
create or replace function public.discord_clans_lancer(p_mode text default null)
 returns bigint language plpgsql security definer set search_path to 'public'
as $f$
declare v_mode text := coalesce(p_mode, (select valeur from discord_sync where cle = 'mode'), 'simulation');
begin
  delete from discord_sync_journal where le < now() - interval '14 days';
  if v_mode not in ('simulation', 'actif') then return null; end if;   -- 'arret' : rien
  return net.http_post(
    url     := (select valeur from discord_sync where cle = 'url'),
    body    := jsonb_build_object('mode', v_mode),
    headers := jsonb_build_object('Content-Type', 'application/json',
                                  'x-clans-secret', (select valeur from discord_sync where cle = 'secret')),
    timeout_milliseconds := 60000);
end;
$f$;

revoke all on function public.discord_sync_verifier(text), public.discord_clans_donnees(),
  public.discord_clans_lancer(text) from public, anon, authenticated;
grant execute on function public.discord_sync_verifier(text), public.discord_clans_donnees() to service_role;

commit;

-- 6. Toutes les 10 minutes ------------------------------------------------------------
select cron.unschedule(jobid) from cron.job where jobname = 'discord-clans';
select cron.schedule('discord-clans', '*/10 * * * *', $$select public.discord_clans_lancer()$$);

-- Contrôle : simulation | true | true | true | true
select (select valeur from public.discord_sync where cle = 'mode')                         as mode,
       (select length(valeur) = 64 from public.discord_sync where cle = 'secret')          as secret_tire,
       exists (select 1 from pg_extension where extname = 'pg_net')                        as pg_net,
       exists (select 1 from cron.job where jobname = 'discord-clans' and active)          as cron_actif,
       not has_function_privilege('anon', 'public.discord_clans_donnees()', 'execute')     as ferme_aux_joueurs;
