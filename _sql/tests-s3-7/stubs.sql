-- Base locale minimale pour tester s3-7-siege.sql (tables et fonctions de production simplifiées)
do $$ begin create role anon; exception when others then null; end $$; do $$ begin create role authenticated; exception when others then null; end $$;
create schema auth;
create function auth.uid() returns uuid language sql stable as $$
  select nullif(coalesce(current_setting('request.jwt.claims', true), '{}')::jsonb->>'sub', '')::uuid $$;
create schema cron;
create table cron.job(jobid serial primary key, jobname text, schedule text, command text);
create function cron.schedule(n text, s text, c text) returns int language sql as $$ insert into cron.job(jobname, schedule, command) values (n, s, c) returning jobid $$;
create function cron.unschedule(id int) returns boolean language sql as $$ delete from cron.job where jobid = id returning true $$;

create table communes(code text primary key, nom text, tier text, departement text, latitude float8, longitude float8);
create table joueurs(id uuid primary key, pseudo text, front_energie numeric default 100, front_energie_maj timestamptz default now(), clan text);
create table possessions(commune_code text primary key references communes(code), joueur_id uuid, acquired_at timestamptz default now() - interval '1 day',
  bouclier_jusqua timestamptz, conquise_le timestamptz, saison text);
create table config_jeu(cle text primary key, valeur text);
create table front_garnisons(commune_code text primary key, joueur_id uuid, energie int, posee_le timestamptz default now());
create table batiments(id bigserial primary key, joueur_id uuid, commune_code text, type text, pret_le timestamptz default now() - interval '1 day');
create table bombes(id bigserial, lat float8, lon float8, rayon_km float8, fin timestamptz);
create table rebellions(id bigserial, financeur uuid, commune_code text, victime uuid, fonds numeric, fin timestamptz, etouffee_le timestamptz);
create table historique(commune_code text, joueur_id uuid, saison text, acquired_at timestamptz, released_at timestamptz);
create table front_prises(attaquant uuid, victime uuid, commune_code text, saison text, le timestamptz default now());
create table journal(type text, acteur uuid, cible uuid, commune_code text, tier text, le timestamptz default clock_timestamp());
create table notifs(joueur uuid, titre text, texte text);
create table compteurs(joueur uuid, champ text, n int);
create table quetes(joueur uuid, cle text, n int);
create table gains(joueur uuid, pts int, motif text);

create function dist_km(a float8, b float8, c float8, d float8) returns float8 language sql immutable as $$
  select 111.19 * sqrt(power(a - c, 2) + power((b - d) * cos(radians(a)), 2)) $$;
create function communes_proches(p_joueur uuid, p_code text, p_km numeric) returns int language sql stable as $$
  select count(*)::int from possessions p join communes c on c.code = p.commune_code join communes t on t.code = p_code
   where p.joueur_id = p_joueur and p.commune_code <> p_code and dist_km(c.latitude, c.longitude, t.latitude, t.longitude) <= p_km $$;
create function batiment_reglage(k text) returns numeric language sql as $$ select 20::numeric $$;
create function debutant_actif(u uuid) returns boolean language sql as $$ select false $$;
create function garnison_active(p_code text) returns boolean language sql stable as $$
  select exists (select 1 from front_garnisons g join possessions po on po.commune_code = g.commune_code and po.joueur_id = g.joueur_id
                  where g.commune_code = p_code and g.energie > 0) $$;
create function rebellion_pct(f numeric) returns numeric language sql as $$ select least(15, f / 3) $$;
create function meme_clan(a uuid, b uuid) returns boolean language sql stable as $$
  select coalesce((select x.clan from joueurs x where x.id = a) = (select y.clan from joueurs y where y.id = b), false) $$;
create function notif_alerte_dep(u uuid, c text) returns boolean language sql as $$ select true $$;
create function notifier_joueur(u uuid, t text, x text, url text, tag text) returns int language sql as $$ insert into notifs values (u, t, x) returning 1 $$;
create function front_energie_reglage(k text) returns numeric language sql as $$ select case k when 'max' then 120 when 'plafond' then 130 else 420 end::numeric $$;
create function front_energie_lire(v numeric, m timestamptz) returns numeric language sql stable as $$
  select case when v >= 120 then v else least(120, v + extract(epoch from now() - m) / 420) end $$;
create function quete_noter(u uuid, k text, n int) returns void language sql as $$ insert into quetes values (u, k, n) $$;
create function front_energie_depenser(p_uid uuid, p_n int) returns boolean language plpgsql as $$
declare v numeric; begin
  select front_energie_lire(front_energie, front_energie_maj) into v from joueurs where id = p_uid for update;
  if v is null or v < p_n then return false; end if;
  update joueurs set front_energie = v - p_n, front_energie_maj = now() where id = p_uid;
  perform quete_noter(p_uid, 'energie', p_n); return true; end $$;
create function saison_en_cours_id() returns text language sql as $$ select 'saison-3' $$;
create function front_gain_conquete(a uuid, d uuid, c text, t text) returns int language sql as $$ insert into front_prises(attaquant, victime, commune_code, saison) values (a, d, c, 'saison-3') returning 5 $$;
create function ajouter_compteur(u uuid, c text, n int) returns void language sql as $$ insert into compteurs values (u, c, n) $$;
create function noter_journal(t text, a uuid, c uuid, code text, tier text) returns void language sql as $$ insert into journal(type, acteur, cible, commune_code, tier) values (t, a, c, code, tier) $$;
create function front_gagner(u uuid, p int, m text) returns int language sql as $$ insert into gains values (u, p, m) returning p $$;
create function attaquer(p_commune_code text, p_intensite text default 'normale') returns int language plpgsql as $$
declare v_attaquant_id uuid := auth.uid(); begin
  if v_attaquant_id is null then raise exception 'Non connecte'; end if;
  return 1; end $$;
create function defendre(p_commune_code text, p_attaquant uuid, p_intensite text) returns int language plpgsql as $$
declare v_uid uuid := auth.uid(); begin
  if v_uid is null then raise exception 'Non connecté'; end if;
  return 1; end $$;

-- données : A attaque, D défend, E coéquipier de D
insert into joueurs(id, pseudo, clan) values
 ('00000000-0000-0000-0000-00000000000a', 'Attaquant', 'X'),
 ('00000000-0000-0000-0000-00000000000d', 'Defenseur', 'Y'),
 ('00000000-0000-0000-0000-00000000000e', 'Coequipier', 'Y'),
 ('00000000-0000-0000-0000-00000000000b', 'Autre', 'Z');
insert into communes values
 ('C1', 'Commune1', 'commun', '16', 45.60, 0.10), ('C2', 'Garnie', 'commun', '16', 45.62, 0.12),
 ('C3', 'Defendue', 'commun', '16', 45.64, 0.14), ('C4', 'Legende', 'legendaire', '16', 45.66, 0.16),
 ('C5', 'Fort', 'rare', '16', 45.68, 0.18), ('C6', 'Epique', 'epique', '16', 45.70, 0.20),
 ('A1', 'ChezA1', 'commun', '16', 45.61, 0.11), ('A2', 'ChezA2', 'commun', '16', 45.63, 0.13),
 ('L1', 'Loin', 'commun', '67', 48.6, 7.7);
insert into possessions(commune_code, joueur_id) values
 ('C1', '00000000-0000-0000-0000-00000000000d'), ('C2', '00000000-0000-0000-0000-00000000000d'),
 ('C3', '00000000-0000-0000-0000-00000000000d'), ('C4', '00000000-0000-0000-0000-00000000000d'),
 ('C5', '00000000-0000-0000-0000-00000000000d'), ('C6', '00000000-0000-0000-0000-00000000000d'),
 ('A1', '00000000-0000-0000-0000-00000000000a'), ('A2', '00000000-0000-0000-0000-00000000000a'),
 ('L1', '00000000-0000-0000-0000-00000000000d');
insert into front_garnisons(commune_code, joueur_id, energie) values ('C2', '00000000-0000-0000-0000-00000000000d', 5);
insert into batiments(joueur_id, commune_code, type) values ('00000000-0000-0000-0000-00000000000d', 'C5', 'forteresse');
