-- ===========================================================================
--  s2-63 — Cartes brillantes et éclats : l'interrupteur de patch269
--  (aperçus validés le 29/10 : canevas « TerraFront Brillantes et Éclats »,
--  puis la lumière de coupe arc-en-ciel : « parfait ! »)
--
--  À LANCER AU MOMENT DE L'ANNONCE : le code est déjà en ligne mais reste
--  caché tant que brillantes_options() n'existe pas.
--
--  Ce que ça allume (Terra seulement, jamais le Front) :
--    - BRILLANTE : chaque carte tirée dans un paquet Terra (gratuit, acheté
--      200 pts, ou paquet de la Boutique) a 1 chance sur 800 de sortir
--      brillante. Pas les achats directs (« Ta boutique », collections).
--      Chaque brillante reçoit un numéro, compté sur tout le jeu (la 1re
--      tirée est n° 1). Elle ne part jamais : ni échange, ni Bourse, ni
--      contrat, ni vente des doublons.
--    - ÉCLAT : sur la fiche d'une carte, 3 doublons + 500 TP font briller la
--      carte (une fois par carte). L'exemplaire qui porte l'éclat ne part
--      jamais ; les autres doublons restent libres.
--
--  Comment : on ne touche pas aux fonctions de tirage. Deux enveloppes,
--  terra_ouvrir_paquet_b et boutique_ouvrir_paquet_b, appellent les vraies
--  fonctions puis tirent la brillante carte par carte. Le jeu passe par
--  elles seulement quand le réglage est ouvert.
--
--  Réglages (config_jeu 'brillantes') : ouvert (1/0), taux (800 = 1 chance
--  sur 800), eclat_doublons (3), eclat_tp (500).
--  Pour couper (plus de nouvelles brillantes ni d'éclats ; celles qui
--  existent restent) : s2-63-brillantes-couper.sql
--  Rejouable. Contrôle attendu : true | true | true | true | true
-- ===========================================================================
begin;

-- 1. Les réglages ---------------------------------------------------------------
insert into public.config_jeu (cle, valeur)
values ('brillantes', '{"ouvert": 1, "taux": 800, "eclat_doublons": 3, "eclat_tp": 500}')
on conflict (cle) do update set valeur = excluded.valeur;

create or replace function public.brillantes_reglages()
 returns jsonb language sql stable security definer set search_path to 'public'
as $f$
  select coalesce((select c.valeur::jsonb from config_jeu c where c.cle = 'brillantes'), '{}'::jsonb)
$f$;
revoke all on function public.brillantes_reglages() from public, anon, authenticated;

create or replace function public.brillantes_options()
 returns jsonb language sql stable security definer set search_path to 'public'
as $f$
  select jsonb_build_object('ouvert', coalesce((r ->> 'ouvert')::int, 0),
                            'taux', coalesce((r ->> 'taux')::int, 800),
                            'eclat_doublons', coalesce((r ->> 'eclat_doublons')::int, 3),
                            'eclat_tp', coalesce((r ->> 'eclat_tp')::int, 500))
    from (select brillantes_reglages() as r) x
$f$;
revoke all on function public.brillantes_options() from public, anon;
grant execute on function public.brillantes_options() to authenticated;

-- 2. Les colonnes et le registre des brillantes ---------------------------------
alter table public.terra_collection add column if not exists brillantes integer not null default 0;
alter table public.terra_collection add column if not exists eclat boolean not null default false;
alter table public.terra_collection add column if not exists eclat_le timestamptz;
do $$ begin
  alter table public.terra_collection add constraint terra_collection_brillantes_ok
    check (brillantes >= 0 and brillantes <= exemplaires);
exception when duplicate_object then null; end $$;

create table if not exists public.terra_brillantes(
  numero       bigint generated always as identity primary key,   -- compté sur tout le jeu
  joueur_id    uuid not null references public.joueurs(id) on delete cascade,
  commune_code text not null,
  origine      text not null,                                     -- 'paquet' ou 'boutique'
  tiree_le     timestamptz not null default now()
);
create index if not exists terra_brillantes_joueur on public.terra_brillantes(joueur_id, commune_code);
alter table public.terra_brillantes enable row level security;
revoke all on public.terra_brillantes from public, anon, authenticated;

-- 3. Le tirage : une chance sur « taux » pour CETTE carte -----------------------
create or replace function public.brillante_tirer(p_uid uuid, p_code text, p_origine text)
 returns bigint language plpgsql security definer set search_path to 'public'
as $f$
declare
  r jsonb := brillantes_reglages();
  n bigint;
begin
  if coalesce((r ->> 'ouvert')::int, 0) <> 1 or p_uid is null or p_code is null then return null; end if;
  if random() >= 1.0 / greatest(1, coalesce((r ->> 'taux')::int, 800)) then return null; end if;
  update terra_collection set brillantes = brillantes + 1
   where joueur_id = p_uid and commune_code = p_code and brillantes < exemplaires;
  if not found then return null; end if;
  insert into terra_brillantes(joueur_id, commune_code, origine) values (p_uid, p_code, p_origine)
  returning numero into n;
  return n;
end $f$;
revoke all on function public.brillante_tirer(uuid, text, text) from public, anon, authenticated;

-- 4. Les enveloppes des paquets : mêmes lignes, plus « brillante » (le numéro, ou null)
create or replace function public.terra_ouvrir_paquet_b(p_paye boolean default false)
 returns jsonb language plpgsql security definer set search_path to 'public'
as $f$
declare
  v_uid uuid := auth.uid();
  r record;
  res jsonb := '[]'::jsonb;
begin
  for r in select * from terra_ouvrir_paquet(p_paye) loop
    res := res || jsonb_build_array(to_jsonb(r) || jsonb_build_object('brillante', brillante_tirer(v_uid, r.code::text, 'paquet')));
  end loop;
  return res;
end $f$;
revoke all on function public.terra_ouvrir_paquet_b(boolean) from public, anon;
grant execute on function public.terra_ouvrir_paquet_b(boolean) to authenticated;

create or replace function public.boutique_ouvrir_paquet_b(p_article text, p_departement text default null)
 returns jsonb language plpgsql security definer set search_path to 'public'
as $f$
declare
  v_uid uuid := auth.uid();
  r record;
  res jsonb := '[]'::jsonb;
begin
  for r in select * from boutique_ouvrir_paquet(p_article, p_departement) loop
    res := res || jsonb_build_array(to_jsonb(r) || jsonb_build_object('brillante', brillante_tirer(v_uid, r.code::text, 'boutique')));
  end loop;
  return res;
end $f$;
revoke all on function public.boutique_ouvrir_paquet_b(text, text) from public, anon;
grant execute on function public.boutique_ouvrir_paquet_b(text, text) to authenticated;

-- 5. Lire les brillantes et éclats d'un joueur (le sien, ou celui d'une vitrine)
create or replace function public.terra_brillantes_joueur(p_joueur uuid default null)
 returns table(code text, numeros bigint[], eclat boolean)
 language sql stable security definer set search_path to 'public'
as $f$
  select t.commune_code::text,
         coalesce((select array_agg(b.numero order by b.numero) from terra_brillantes b
                    where b.joueur_id = t.joueur_id and b.commune_code = t.commune_code::text), '{}'::bigint[]),
         t.eclat
    from terra_collection t
   where t.joueur_id = coalesce(p_joueur, auth.uid())
     and (t.brillantes > 0 or t.eclat)
$f$;
revoke all on function public.terra_brillantes_joueur(uuid) from public, anon;
grant execute on function public.terra_brillantes_joueur(uuid) to authenticated;

-- 6. L'éclat : 3 doublons libres + 500 TP, d'un seul bloc --------------------------
create or replace function public.terra_faire_eclat(p_code text)
 returns jsonb language plpgsql security definer set search_path to 'public'
as $f$
declare
  v_uid  uuid := auth.uid();
  r      jsonb := brillantes_reglages();
  v_n    integer := coalesce((r ->> 'eclat_doublons')::int, 3);
  v_prix integer := coalesce((r ->> 'eclat_tp')::int, 500);
  j record;
  t record;
begin
  if v_uid is null then raise exception 'Non connecte'; end if;
  if coalesce((r ->> 'ouvert')::int, 0) <> 1 then raise exception 'Les eclats ne sont pas encore ouverts'; end if;
  if not terra_ouverte() then raise exception 'Terra n''est pas encore ouvert'; end if;
  -- verrous dans le même ordre que les paquets : le joueur, puis sa carte
  select * into j from joueurs where id = v_uid for update;
  if not found then raise exception 'Joueur inconnu'; end if;
  select * into t from terra_collection where joueur_id = v_uid and commune_code = p_code for update;
  if not found then raise exception 'Tu n''as pas cette carte'; end if;
  if t.eclat then raise exception 'Cette carte a deja son eclat'; end if;
  if t.exemplaires - greatest(1, coalesce(t.aurore, 0) + t.brillantes) < v_n then
    raise exception 'Il faut % doublons libres de cette carte pour un eclat', v_n;
  end if;
  if coalesce(j.solde, 0) < v_prix then raise exception 'Solde insuffisant'; end if;
  perform set_config('terrafront.motif', 'eclat', true);
  update joueurs set solde = solde - v_prix where id = v_uid;
  update terra_collection set exemplaires = exemplaires - v_n, eclat = true, eclat_le = now()
   where joueur_id = v_uid and commune_code = p_code;
  return jsonb_build_object('exemplaires', t.exemplaires - v_n, 'solde', coalesce(j.solde, 0) - v_prix);
end $f$;
revoke all on function public.terra_faire_eclat(text) from public, anon;
grant execute on function public.terra_faire_eclat(text) to authenticated;

commit;

-- Contrôle : une ligne, tout à true
select (public.brillantes_options() ->> 'ouvert')::int = 1                                        as ouvert,
       (select count(*) from information_schema.columns
         where table_schema = 'public' and table_name = 'terra_collection'
           and column_name in ('brillantes', 'eclat', 'eclat_le')) = 3                              as colonnes,
       to_regclass('public.terra_brillantes') is not null                                           as registre,
       has_function_privilege('authenticated', 'public.terra_ouvrir_paquet_b(boolean)', 'execute')
         and has_function_privilege('authenticated', 'public.boutique_ouvrir_paquet_b(text, text)', 'execute')
         and has_function_privilege('authenticated', 'public.terra_faire_eclat(text)', 'execute')
         and not has_function_privilege('anon', 'public.terra_faire_eclat(text)', 'execute')
         and not has_function_privilege('authenticated', 'public.brillante_tirer(uuid, text, text)', 'execute') as droits,
       (select count(*) from public.terra_brillantes) >= 0                                          as lisible;
