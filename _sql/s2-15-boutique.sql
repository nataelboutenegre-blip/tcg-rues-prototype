-- ===========================================================================
--  TerraFront — saison 2 : la boutique (points Terra uniquement)
--  (décision de Nataël, 10 octobre 2026 : paquets + dos de cartes au
--  lancement ; cadre, titre et drapeau plus tard ; pas d'argent réel)
--
--  Tables :
--   - boutique_articles   : le catalogue, prix modifiables sans toucher au code
--   - boutique_inventaire : ce que chaque joueur possède (dos de cartes)
--   - boutique_achats     : le registre de tous les achats (sert aussi à la
--                           limite de 3 paquets de boutique par jour)
--   - boutique_reglages   : le dos de carte choisi par chaque joueur
--
--  Fonctions (joueur connecté) :
--   - boutique()                                : le catalogue et l'état du joueur (jsonb)
--   - boutique_ouvrir_paquet(article, dep)      : paie et tire 5 communes, comme
--                                                 terra_ouvrir_paquet (même retour)
--   - boutique_acheter(article)                 : achète un dos de carte
--   - boutique_equiper(article)                 : choisit son dos (null = dos d'origine)
--
--  Paquet garanti : 4 communes au hasard + 1 rare, épique ou légendaire.
--  Paquet du département : 5 communes différentes du département choisi.
--  Les paquets de boutique ne comptent PAS pour les quêtes (sinon les points
--  achèteraient de l'énergie).
--
--  SANS EFFET EN SAISON 1 : tout refuse tant que terra_ouverte() est faux.
--  Ne touche à aucune fonction existante. Rejouable. Finit par un contrôle.
-- ===========================================================================

create table if not exists public.boutique_articles(
  id          text primary key,
  type        text not null check (type in ('paquet', 'dos')),
  nom         text not null,
  description text not null default '',
  prix        integer not null check (prix >= 0),
  actif       boolean not null default true,
  ordre       integer not null default 0
);
alter table public.boutique_articles enable row level security;
revoke all on public.boutique_articles from public, anon, authenticated;

insert into public.boutique_articles(id, type, nom, description, prix, ordre) values
  ('paquet-garanti',     'paquet', 'Paquet garanti',         '5 communes, dont au moins une rare ou mieux', 500, 10),
  ('paquet-departement', 'paquet', 'Paquet du département',  '5 communes du département de ton choix',      800, 20),
  ('dos-bocage',         'dos',    'Bocage',                 'Dos de carte vert sapin, liseré cuivre',     1500, 30),
  ('dos-terre-cuite',    'dos',    'Terre cuite',            'Dos de carte brique, liseré crème',          1500, 40),
  ('dos-ble-or',         'dos',    'Blé d''or',              'Dos de carte or et nuit',                    3000, 50)
on conflict (id) do nothing;   -- rejouable : ne réécrit pas un prix modifié à la main

create table if not exists public.boutique_inventaire(
  joueur_id  uuid not null references public.joueurs(id) on delete cascade,
  article_id text not null references public.boutique_articles(id),
  achete_le  timestamptz not null default now(),
  primary key (joueur_id, article_id)
);
alter table public.boutique_inventaire enable row level security;
revoke all on public.boutique_inventaire from public, anon, authenticated;

create table if not exists public.boutique_achats(
  id          bigint generated always as identity primary key,
  joueur_id   uuid not null references public.joueurs(id) on delete cascade,
  article_id  text not null references public.boutique_articles(id),
  prix        integer not null,
  departement text,
  le          timestamptz not null default now()
);
create index if not exists boutique_achats_joueur_le on public.boutique_achats(joueur_id, le);
alter table public.boutique_achats enable row level security;
revoke all on public.boutique_achats from public, anon, authenticated;

create table if not exists public.boutique_reglages(
  joueur_id uuid primary key references public.joueurs(id) on delete cascade,
  dos       text references public.boutique_articles(id)
);
alter table public.boutique_reglages enable row level security;
revoke all on public.boutique_reglages from public, anon, authenticated;

-- nombre de paquets de boutique achetés aujourd'hui (jour de Paris)
create or replace function public.boutique_paquets_du_jour(p_uid uuid)
 returns integer language sql stable security definer set search_path to 'public'
as $f$
  select count(*)::integer
    from boutique_achats b join boutique_articles a on a.id = b.article_id
   where b.joueur_id = p_uid and a.type = 'paquet'
     and (b.le at time zone 'Europe/Paris')::date = (now() at time zone 'Europe/Paris')::date;
$f$;

create or replace function public.boutique()
 returns jsonb language plpgsql stable security definer set search_path to 'public'
as $f$
declare
  v_uid uuid := auth.uid();
begin
  if v_uid is null then raise exception 'Non connecte'; end if;
  if not terra_ouverte() then raise exception 'La boutique ouvre avec la saison 2'; end if;
  return jsonb_build_object(
    'solde', (select coalesce(solde, 0) from joueurs where id = v_uid),
    'paquets_du_jour', boutique_paquets_du_jour(v_uid),
    'paquets_max', 3,
    'dos', (select dos from boutique_reglages where joueur_id = v_uid),
    'articles', coalesce((
      select jsonb_agg(jsonb_build_object(
               'id', a.id, 'type', a.type, 'nom', a.nom, 'description', a.description, 'prix', a.prix,
               'possede', exists(select 1 from boutique_inventaire i where i.joueur_id = v_uid and i.article_id = a.id))
             order by a.ordre)
        from boutique_articles a where a.actif), '[]'::jsonb));
end;
$f$;

create or replace function public.boutique_ouvrir_paquet(p_article text, p_departement text default null)
 returns table(code text, nom text, departement text, tier text, population integer,
               nouvelle boolean, exemplaires integer, rang integer, palier_total integer,
               latitude double precision, longitude double precision)
 language plpgsql security definer set search_path to 'public'
as $f$
declare
  v_uid uuid := auth.uid();
  a boutique_articles%rowtype;
  j joueurs%rowtype;
begin
  if v_uid is null then raise exception 'Non connecte'; end if;
  if not terra_ouverte() then raise exception 'La boutique ouvre avec la saison 2'; end if;
  select * into a from boutique_articles ba where ba.id = p_article and ba.actif and ba.type = 'paquet';
  if not found then raise exception 'Article introuvable'; end if;
  if a.id = 'paquet-departement' then
    if p_departement is null or not exists(select 1 from communes c where c.departement = p_departement) then
      raise exception 'Choisis un departement';
    end if;
  end if;

  -- verrou : deux achats simultanés ne dépensent pas le même solde
  select * into j from joueurs jj where jj.id = v_uid for update;
  if not found then raise exception 'Joueur inconnu'; end if;
  if boutique_paquets_du_jour(v_uid) >= 3 then
    raise exception 'Tu as deja achete 3 paquets en boutique aujourd''hui';
  end if;
  if coalesce(j.solde, 0) < a.prix then raise exception 'Solde insuffisant'; end if;

  perform set_config('terrafront.motif', 'boutique', true);
  update joueurs jj set solde = jj.solde - a.prix where jj.id = v_uid;
  insert into boutique_achats(joueur_id, article_id, prix, departement)
  values (v_uid, a.id, a.prix, case when a.id = 'paquet-departement' then p_departement end);

  return query
  with tirage as (
    select t.code from (
      -- paquet du département : 5 communes différentes du département
      (select c.code from communes c
        where a.id = 'paquet-departement' and c.departement = p_departement
        order by random() limit 5)
      union all
      -- paquet garanti : 1 rare ou mieux ...
      (select c.code from (select c2.code from communes c2
                            where a.id = 'paquet-garanti' and c2.tier in ('rare', 'epique', 'legendaire')
                            order by random() limit 1) c)
      union all
      -- ... + 4 au hasard
      (select c.code from (select c3.code from communes c3
                            where a.id = 'paquet-garanti'
                            order by random() limit 4) c)
    ) t
  ), compte as (
    select tirage.code, count(*)::integer n from tirage group by tirage.code
  ), avant as (
    select t.commune_code, t.exemplaires from terra_collection t
     where t.joueur_id = v_uid and t.commune_code in (select compte.code from compte)
  ), ajout as (
    insert into terra_collection as tc (joueur_id, commune_code, exemplaires, origine)
    select v_uid, compte.code, compte.n, 'boutique' from compte
    on conflict (joueur_id, commune_code) do update set exemplaires = tc.exemplaires + excluded.exemplaires
    returning tc.commune_code, tc.exemplaires
  )
  select c.code::text, c.nom::text, c.departement::text, c.tier::text, c.population::integer,
         coalesce(av.exemplaires, 0) = 0, a2.exemplaires::integer, c.rang::integer, c.palier_total::integer,
         c.latitude::double precision, c.longitude::double precision
    from ajout a2
    join communes c on c.code = a2.commune_code
    left join avant av on av.commune_code = a2.commune_code;
end;
$f$;

create or replace function public.boutique_acheter(p_article text)
 returns jsonb language plpgsql security definer set search_path to 'public'
as $f$
declare
  v_uid uuid := auth.uid();
  a boutique_articles%rowtype;
  j joueurs%rowtype;
begin
  if v_uid is null then raise exception 'Non connecte'; end if;
  if not terra_ouverte() then raise exception 'La boutique ouvre avec la saison 2'; end if;
  select * into a from boutique_articles ba where ba.id = p_article and ba.actif and ba.type = 'dos';
  if not found then raise exception 'Article introuvable'; end if;
  select * into j from joueurs jj where jj.id = v_uid for update;
  if not found then raise exception 'Joueur inconnu'; end if;
  if exists(select 1 from boutique_inventaire i where i.joueur_id = v_uid and i.article_id = a.id) then
    raise exception 'Tu l''as deja';
  end if;
  if coalesce(j.solde, 0) < a.prix then raise exception 'Solde insuffisant'; end if;

  perform set_config('terrafront.motif', 'boutique', true);
  update joueurs jj set solde = jj.solde - a.prix where jj.id = v_uid;
  insert into boutique_achats(joueur_id, article_id, prix) values (v_uid, a.id, a.prix);
  insert into boutique_inventaire(joueur_id, article_id) values (v_uid, a.id);
  -- un dos acheté est mis tout de suite
  insert into boutique_reglages(joueur_id, dos) values (v_uid, a.id)
  on conflict (joueur_id) do update set dos = excluded.dos;
  return boutique();
end;
$f$;

create or replace function public.boutique_equiper(p_article text)
 returns jsonb language plpgsql security definer set search_path to 'public'
as $f$
declare
  v_uid uuid := auth.uid();
begin
  if v_uid is null then raise exception 'Non connecte'; end if;
  if not terra_ouverte() then raise exception 'La boutique ouvre avec la saison 2'; end if;
  if p_article is not null and not exists(
       select 1 from boutique_inventaire i where i.joueur_id = v_uid and i.article_id = p_article) then
    raise exception 'Tu ne l''as pas encore';
  end if;
  insert into boutique_reglages(joueur_id, dos) values (v_uid, p_article)
  on conflict (joueur_id) do update set dos = excluded.dos;
  return boutique();
end;
$f$;

revoke all on function public.boutique_paquets_du_jour(uuid)           from public, anon, authenticated;
revoke all on function public.boutique()                               from public, anon;
revoke all on function public.boutique_ouvrir_paquet(text, text)       from public, anon;
revoke all on function public.boutique_acheter(text)                   from public, anon;
revoke all on function public.boutique_equiper(text)                   from public, anon;
grant execute on function public.boutique()                            to authenticated;
grant execute on function public.boutique_ouvrir_paquet(text, text)    to authenticated;
grant execute on function public.boutique_acheter(text)                to authenticated;
grant execute on function public.boutique_equiper(text)                to authenticated;

-- Contrôle ------------------------------------------------------------------------------------
select (select count(*) from public.boutique_articles) as articles_doit_etre_5,
       (select count(*) from pg_proc where pronamespace = 'public'::regnamespace and proname like 'boutique%') as fonctions_doit_etre_5,
       has_function_privilege('anon', 'public.boutique_ouvrir_paquet(text,text)', 'execute') as anon_doit_etre_false,
       public.terra_ouverte() as terra_ouverte_doit_etre_false;
