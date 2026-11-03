-- ===========================================================================
--  TerraFront — s2-89 : l'état compact de la carte (3/11/2026, avec patch329)
--  Saison 3, étape 1 (« chargement compact de la carte », claude/saison-3.md).
--  Prérequis de la carte en direct et de l'Europe, utile tout de suite.
--
--  Avant : à chaque ouverture, le jeu lisait toutes les possessions des
--  autres joueurs AVEC la fiche complète de chaque commune et le pseudo
--  (≈ 25 000 lignes, ≈ 25 à 30 requêtes, plusieurs Mo), puis tout relisait
--  après une conquête ou un échange. Entre deux, la carte ne bougeait pas.
--
--  Maintenant :
--   1. carte_catalogue() : la fiche fixe de chaque commune (code, nom,
--      département, population, latitude, longitude, rareté), préparée une
--      fois (carte_catalogue_cache) et refaite chaque nuit à 4 h 17 ; le jeu
--      la garde dans le navigateur tant que sa version ne change pas.
--   2. carte_etat() : qui possède quoi, en tableaux compacts
--      (commune, n° du joueur, acquise le, bouclier jusqu'à) + la liste des
--      joueurs (id, pseudo), + le n° du dernier changement.
--   3. carte_changements : un déclencheur note chaque changement de
--      propriétaire (ou d'acquisition, de bouclier) ; carte_depuis(n) rend
--      ce qui a changé depuis le n° n (avec un recouvrement de 100 numéros,
--      pour ne rien rater d'une transaction validée en retard). Gardé 3 jours.
--      Le jeu le demande toutes les 60 s et après chaque action.
--  Rien ne change pour les joueurs à l'écran, sauf que la carte se met à
--  jour toute seule. Tant que patch329 n'est pas en ligne, rien n'utilise
--  ces fonctions.
--
--  Rejouable. Contrôle (une ligne) :
--  true | true | true | true | (communes au catalogue, ≈ 34 900) | (possessions) | true
-- ===========================================================================
begin;

-- ---------- 1. le catalogue des communes ----------
create table if not exists public.carte_catalogue_cache(
  id       integer primary key default 1 check (id = 1),
  version  text not null,
  donnees  json not null,
  maj      timestamptz not null default now()
);
alter table public.carte_catalogue_cache enable row level security;
revoke all on public.carte_catalogue_cache from public, anon, authenticated;

-- [code, nom, département, population, latitude, longitude, rareté (0 commun … 4 légendaire, null si autre)]
create or replace function public.carte_catalogue_refaire()
 returns text language plpgsql security definer set search_path to 'public' as $f$
declare d json; v text;
begin
  select json_agg(json_build_array(
           c.code, c.nom, c.departement, c.population,
           round(c.latitude::numeric, 4), round(c.longitude::numeric, 4),
           array_position(array['commun','peucommun','rare','epique','legendaire'], c.tier::text) - 1)
         order by c.code)
    into d from communes c;
  v := left(md5(coalesce(d::text, '')), 12);
  insert into carte_catalogue_cache(id, version, donnees, maj) values (1, v, coalesce(d, '[]'::json), now())
  on conflict (id) do update set version = excluded.version, donnees = excluded.donnees, maj = now()
  where carte_catalogue_cache.version is distinct from excluded.version;
  return v;
end; $f$;
revoke all on function public.carte_catalogue_refaire() from public, anon, authenticated;

create or replace function public.carte_catalogue()
 returns json language sql stable security definer set search_path to 'public' as $f$
  select json_build_object('version', k.version, 'c', k.donnees)
    from carte_catalogue_cache k where auth.uid() is not null;
$f$;
revoke all on function public.carte_catalogue() from public, anon;
grant execute on function public.carte_catalogue() to authenticated;

select public.carte_catalogue_refaire();

-- ---------- 2. le journal des changements ----------
create table if not exists public.carte_changements(
  id              bigserial primary key,
  commune_code    text not null,
  joueur_id       uuid,
  acquired_at     timestamptz,
  bouclier_jusqua timestamptz,
  le              timestamptz not null default now()
);
create index if not exists carte_changements_le on public.carte_changements(le);
alter table public.carte_changements enable row level security;
revoke all on public.carte_changements from public, anon, authenticated;

create or replace function public.carte_noter()
 returns trigger language plpgsql security definer set search_path to 'public' as $f$
begin
  if tg_op = 'DELETE' then
    insert into carte_changements(commune_code) values (old.commune_code);
    return null;
  end if;
  if tg_op = 'UPDATE'
     and new.joueur_id is not distinct from old.joueur_id
     and new.acquired_at is not distinct from old.acquired_at
     and new.bouclier_jusqua is not distinct from old.bouclier_jusqua
     and new.commune_code = old.commune_code then
    return null;
  end if;
  if tg_op = 'UPDATE' and new.commune_code <> old.commune_code then
    insert into carte_changements(commune_code) values (old.commune_code);
  end if;
  insert into carte_changements(commune_code, joueur_id, acquired_at, bouclier_jusqua)
  values (new.commune_code, new.joueur_id, new.acquired_at, new.bouclier_jusqua);
  if random() < 0.001 then delete from carte_changements where le < now() - interval '3 days'; end if;
  return null;
end; $f$;
revoke all on function public.carte_noter() from public, anon, authenticated;
drop trigger if exists carte_noter on public.possessions;
create trigger carte_noter after insert or update or delete on public.possessions
  for each row execute function public.carte_noter();

-- ---------- 3. l'état complet, compact ----------
create or replace function public.carte_etat()
 returns json language sql stable security definer set search_path to 'public' as $f$
  with p as (select commune_code, joueur_id, acquired_at, bouclier_jusqua from possessions),
       ji as (select joueur_id, (row_number() over (order by joueur_id) - 1)::int as i
                from (select distinct joueur_id from p where joueur_id is not null) d)
  select json_build_object(
    'id', coalesce((select max(id) from carte_changements),
                   (select case when is_called then last_value else 0 end from carte_changements_id_seq)),
    'catalogue', (select version from carte_catalogue_cache where id = 1),
    'joueurs', coalesce((select json_agg(json_build_array(ji.joueur_id, j.pseudo) order by ji.i)
                           from ji left join joueurs j on j.id = ji.joueur_id), '[]'::json),
    'p', coalesce((select json_agg(json_build_array(p.commune_code, ji.i,
                                   coalesce(floor(extract(epoch from p.acquired_at))::bigint, 0),
                                   coalesce(floor(extract(epoch from p.bouclier_jusqua))::bigint, 0)))
                     from p join ji using (joueur_id)), '[]'::json))
  where auth.uid() is not null;
$f$;
revoke all on function public.carte_etat() from public, anon;
grant execute on function public.carte_etat() to authenticated;

-- ---------- 4. ce qui a changé depuis ----------
-- complet = true : trop ancien ou trop de changements, recharger carte_etat().
create or replace function public.carte_depuis(p_id bigint)
 returns json language plpgsql stable security definer set search_path to 'public' as $f$
declare
  v_min bigint; v_max bigint; v_n int;
begin
  if auth.uid() is null then return null; end if;
  select min(id), max(id) into v_min, v_max from carte_changements;
  if v_max is null then
    -- table vide : complet si la séquence est allée plus loin que le joueur
    if (select last_value from carte_changements_id_seq) > coalesce(p_id, 0)
       and (select is_called from carte_changements_id_seq) then
      return json_build_object('complet', true);
    end if;
    return json_build_object('id', coalesce(p_id, 0), 'ch', '[]'::json, 'joueurs', '[]'::json);
  end if;
  if p_id is null or v_min > p_id + 1 then return json_build_object('complet', true); end if;
  select count(*) into v_n from carte_changements where id > p_id - 100;
  if v_n > 5000 then return json_build_object('complet', true); end if;
  return json_build_object(
    'id', greatest(v_max, p_id),
    'ch', coalesce((select json_agg(json_build_array(x.id, x.commune_code, x.joueur_id,
                                    coalesce(floor(extract(epoch from x.acquired_at))::bigint, 0),
                                    coalesce(floor(extract(epoch from x.bouclier_jusqua))::bigint, 0)) order by x.id)
                      from carte_changements x where x.id > p_id - 100), '[]'::json),
    'joueurs', coalesce((select json_agg(json_build_array(j.id, j.pseudo))
                           from joueurs j
                          where j.id in (select x.joueur_id from carte_changements x where x.id > p_id - 100)), '[]'::json));
end; $f$;
revoke all on function public.carte_depuis(bigint) from public, anon;
grant execute on function public.carte_depuis(bigint) to authenticated;

commit;

-- ---------- 5. le catalogue refait chaque nuit (4 h 17, heure du serveur) ----------
do $do$
begin
  if exists (select 1 from pg_extension where extname = 'pg_cron') then
    perform cron.unschedule(jobid) from cron.job where jobname = 'carte-catalogue';
    perform cron.schedule('carte-catalogue', '17 4 * * *', 'select public.carte_catalogue_refaire()');
  else
    raise notice 's2-89 : pg_cron absent, le catalogue ne se refera pas tout seul';
  end if;
end $do$;

-- Contrôle : true | true | true | true | (communes au catalogue) | (possessions) | true
select has_function_privilege('authenticated', 'public.carte_etat()', 'execute')               as etat_ok,
       has_function_privilege('authenticated', 'public.carte_depuis(bigint)', 'execute')       as depuis_ok,
       has_function_privilege('authenticated', 'public.carte_catalogue()', 'execute')          as catalogue_ok,
       exists (select 1 from pg_trigger where tgname = 'carte_noter' and not tgisinternal)     as declencheur_ok,
       (select json_array_length(donnees) from public.carte_catalogue_cache where id = 1)       as communes_catalogue,
       (select count(*) from public.possessions)                                                as possessions,
       exists (select 1 from cron.job where jobname = 'carte-catalogue')                        as nuit_ok;
