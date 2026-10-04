-- =====================================================================
--  TerraFront — Commune du jour, 1/2 : tables et fonctions
--
--  Une commune mystère par jour (heure de Paris), la même pour tout le
--  monde, six essais. La réponse ne quitte jamais le serveur avant la fin
--  de la partie : le navigateur n'envoie qu'un code de commune et reçoit
--  une distance, une direction et les indices déjà gagnés.
--
--  Communes possibles : 5 000 habitants et plus, métropole, avec un
--  gentilé et une silhouette (fichier 2/2). Jamais deux fois la même tant
--  qu'il en reste.
--
--  Aucun gain : rien ne touche aux points, aux paquets ni aux cartes.
--
--  À lancer AVANT le fichier 2/2. Rejouable : rien n'est effacé.
-- =====================================================================

-- ---------------------------------------------------------------------
-- 1. Les tables
-- ---------------------------------------------------------------------
create table if not exists public.cdj_silhouettes(
  code   text primary key,
  points jsonb not null              -- [[ [x,y], ... ], ...] dans un carré 0-100, sans coordonnées
);

create table if not exists public.cdj_jours(
  jour          date primary key,    -- jour de Paris
  numero        integer not null unique,
  commune_code  text not null,
  cree_le       timestamptz not null default now()
);

create table if not exists public.cdj_essais(
  joueur_id     uuid not null,
  jour          date not null,
  n             smallint not null check (n between 1 and 6),
  commune_code  text not null,
  km            integer not null,    -- 0 = trouvée
  cree_le       timestamptz not null default now(),
  primary key (joueur_id, jour, n),
  unique (joueur_id, jour, commune_code)
);
create index if not exists cdj_essais_jour on public.cdj_essais(jour);

-- Personne ne lit ces tables directement : tout passe par les fonctions.
alter table public.cdj_silhouettes enable row level security;
alter table public.cdj_jours       enable row level security;
alter table public.cdj_essais      enable row level security;
revoke all on public.cdj_silhouettes, public.cdj_jours, public.cdj_essais from public, anon, authenticated;

-- ---------------------------------------------------------------------
-- 2. Les régions (les 13 de métropole)
-- ---------------------------------------------------------------------
create or replace function public.cdj_region(p_dep text)
returns text language sql immutable
set search_path to 'public'
as $$
  select case
    when p_dep in ('01','03','07','15','26','38','42','43','63','69','73','74') then 'Auvergne-Rhône-Alpes'
    when p_dep in ('21','25','39','58','70','71','89','90') then 'Bourgogne-Franche-Comté'
    when p_dep in ('22','29','35','56') then 'Bretagne'
    when p_dep in ('18','28','36','37','41','45') then 'Centre-Val de Loire'
    when p_dep in ('2A','2B') then 'Corse'
    when p_dep in ('08','10','51','52','54','55','57','67','68','88') then 'Grand Est'
    when p_dep in ('02','59','60','62','80') then 'Hauts-de-France'
    when p_dep in ('75','77','78','91','92','93','94','95') then 'Île-de-France'
    when p_dep in ('14','27','50','61','76') then 'Normandie'
    when p_dep in ('16','17','19','23','24','33','40','47','64','79','86','87') then 'Nouvelle-Aquitaine'
    when p_dep in ('09','11','12','30','31','32','34','46','48','65','66','81','82') then 'Occitanie'
    when p_dep in ('44','49','53','72','85') then 'Pays de la Loire'
    when p_dep in ('04','05','06','13','83','84') then 'Provence-Alpes-Côte d''Azur'
    else 'Outre-mer'
  end;
$$;

-- ---------------------------------------------------------------------
-- 3. La commune du jour : tirée au premier appel de la journée
-- ---------------------------------------------------------------------
create or replace function public.cdj_jour_courant()
returns public.cdj_jours
language plpgsql security definer
set search_path to 'public'
as $$
declare
  v_jour date := (now() at time zone 'Europe/Paris')::date;
  v_ligne cdj_jours;
  v_code text;
begin
  select * into v_ligne from cdj_jours where jour = v_jour;
  if found then return v_ligne; end if;

  -- une commune jamais tombée ; s'il n'en reste plus, on recommence le cycle
  select c.code into v_code
    from communes c join cdj_silhouettes s on s.code = c.code
   where c.population >= 5000
     and length(c.departement) = 2
     and c.gentile is not null
     and c.latitude is not null and c.longitude is not null
     and c.nom not ilike '%arrondissement%'
     and not exists (select 1 from cdj_jours j where j.commune_code = c.code)
   order by random() limit 1;
  if v_code is null then
    select c.code into v_code
      from communes c join cdj_silhouettes s on s.code = c.code
     where c.population >= 5000 and length(c.departement) = 2
       and c.gentile is not null and c.latitude is not null
       and c.nom not ilike '%arrondissement%'
     order by random() limit 1;
  end if;
  if v_code is null then
    raise exception 'La commune du jour n''est pas encore prête.';
  end if;

  insert into cdj_jours(jour, numero, commune_code)
  values (v_jour, (select coalesce(max(numero), 0) + 1 from cdj_jours), v_code)
  on conflict (jour) do nothing;

  select * into v_ligne from cdj_jours where jour = v_jour;
  return v_ligne;
end;
$$;

-- distance en km entre deux points
create or replace function public.cdj_km(lat1 numeric, lon1 numeric, lat2 numeric, lon2 numeric)
returns numeric language sql immutable
as $$
  select 2 * 6371 * asin(sqrt(
           power(sin(radians((lat2 - lat1) / 2)), 2)
         + cos(radians(lat1)) * cos(radians(lat2)) * power(sin(radians((lon2 - lon1) / 2)), 2)));
$$;

-- direction de a vers b : 0 = nord, 1 = nord-est … 7 = nord-ouest
create or replace function public.cdj_cap(lat1 numeric, lon1 numeric, lat2 numeric, lon2 numeric)
returns integer language sql immutable
as $$
  select (round(((degrees(atan2(
            sin(radians(lon2 - lon1)) * cos(radians(lat2)),
            cos(radians(lat1)) * sin(radians(lat2))
          - sin(radians(lat1)) * cos(radians(lat2)) * cos(radians(lon2 - lon1))
         )) + 360)::numeric % 360) / 45)::int % 8);
$$;

-- ---------------------------------------------------------------------
-- 4. L'état d'une partie, tel que le joueur a le droit de le voir
-- ---------------------------------------------------------------------
create or replace function public.cdj_etat(p_uid uuid, p_jour public.cdj_jours)
returns jsonb
language plpgsql security definer
set search_path to 'public'
as $$
declare
  c communes;
  v_essais jsonb;
  v_nb int;
  v_trouve boolean;
  v_fini boolean;
  v_ouverts int;
  v_fait text;
  v_rang int;
  v_serie int := 0;
  v_d date;
  v_indices jsonb;
begin
  select * into c from communes where code = p_jour.commune_code;

  select coalesce(jsonb_agg(jsonb_build_object(
           'code', e.commune_code, 'nom', x.nom, 'dept', x.departement,
           'lat', x.latitude, 'lon', x.longitude, 'km', e.km,
           'cap', case when e.km = 0 then null
                       else cdj_cap(x.latitude, x.longitude, c.latitude, c.longitude) end)
         order by e.n), '[]'::jsonb),
         count(*), coalesce(bool_or(e.km = 0), false)
    into v_essais, v_nb, v_trouve
    from cdj_essais e join communes x on x.code = e.commune_code
   where e.joueur_id = p_uid and e.jour = p_jour.jour;

  v_fini := v_trouve or v_nb >= 6;
  v_ouverts := case when v_fini then 5 else least(5, v_nb) end;

  -- l'anecdote : le meilleur fait qui ne donne pas le nom, sinon le rang
  -- de population dans le département
  if v_ouverts >= 5 then
    select f->>'t' into v_fait
      from jsonb_array_elements(coalesce(c.faits, '[]'::jsonb)) f
     where (f->>'t') !~ '«|lettres|caractères'
     order by (f->>'r')::int
     limit 1;
    if v_fait is null then
      select count(*) + 1 into v_rang from communes
       where departement = c.departement and population > c.population;
      v_fait := case when v_rang = 1 then 'La commune la plus peuplée de son département.'
                     else 'La ' || v_rang || 'e commune la plus peuplée de son département.' end;
    end if;
  end if;

  v_indices := jsonb_build_array(
    jsonb_build_object('cle', 'population', 'valeur', case when v_ouverts >= 1 then
      case when c.population < 10000 then 'entre 5 000 et 10 000 habitants'
           when c.population < 20000 then 'entre 10 000 et 20 000 habitants'
           when c.population < 50000 then 'entre 20 000 et 50 000 habitants'
           when c.population < 100000 then 'entre 50 000 et 100 000 habitants'
           else 'plus de 100 000 habitants' end end),
    jsonb_build_object('cle', 'region',      'valeur', case when v_ouverts >= 2 then cdj_region(c.departement) end),
    jsonb_build_object('cle', 'gentile',     'valeur', case when v_ouverts >= 3 then c.gentile end),
    jsonb_build_object('cle', 'departement', 'valeur', case when v_ouverts >= 4 then c.departement end),
    jsonb_build_object('cle', 'anecdote',    'valeur', case when v_ouverts >= 5 then v_fait end));

  -- la série : jours trouvés d'affilée, jusqu'à aujourd'hui ou hier
  v_d := p_jour.jour;
  if not v_trouve then v_d := v_d - 1; end if;
  while exists (select 1 from cdj_essais where joueur_id = p_uid and jour = v_d and km = 0) loop
    v_serie := v_serie + 1;
    v_d := v_d - 1;
  end loop;

  return jsonb_build_object(
    'jour', p_jour.jour,
    'numero', p_jour.numero,
    'silhouette', (select points from cdj_silhouettes where code = c.code),
    'essais', v_essais,
    'max', 6,
    'fini', v_fini,
    'trouve', v_trouve,
    'indices', v_indices,
    'serie', v_serie,
    'joueurs', (select count(distinct joueur_id) from cdj_essais where jour = p_jour.jour),
    'trouves', (select count(*) from cdj_essais where jour = p_jour.jour and km = 0),
    'reponse', case when v_fini then jsonb_build_object(
                 'code', c.code, 'nom', c.nom, 'dept', c.departement,
                 'pop', c.population, 'lat', c.latitude, 'lon', c.longitude) end);
end;
$$;

-- ---------------------------------------------------------------------
-- 5. Ce que le jeu appelle
-- ---------------------------------------------------------------------
create or replace function public.cdj_partie()
returns jsonb
language plpgsql security definer
set search_path to 'public'
as $$
declare
  v_uid uuid := auth.uid();
begin
  if v_uid is null then
    raise exception 'Connecte-toi pour jouer à la commune du jour.';
  end if;
  return cdj_etat(v_uid, cdj_jour_courant());
end;
$$;

create or replace function public.cdj_essayer(p_code text)
returns jsonb
language plpgsql security definer
set search_path to 'public'
as $$
declare
  v_uid uuid := auth.uid();
  v_jour cdj_jours;
  v_cible communes;
  v_essai communes;
  v_nb int;
  v_trouve boolean;
  v_km int;
begin
  if v_uid is null then
    raise exception 'Connecte-toi pour jouer à la commune du jour.';
  end if;
  v_jour := cdj_jour_courant();

  -- un essai à la fois par joueur : deux clics rapides ne font pas deux essais
  perform pg_advisory_xact_lock(hashtextextended(v_uid::text || v_jour.jour::text, 42));

  select count(*), coalesce(bool_or(km = 0), false) into v_nb, v_trouve
    from cdj_essais where joueur_id = v_uid and jour = v_jour.jour;
  if v_trouve or v_nb >= 6 then
    raise exception 'La partie du jour est terminée. Reviens demain.';
  end if;

  select * into v_essai from communes where code = p_code;
  if not found or v_essai.latitude is null then
    raise exception 'Commune inconnue.';
  end if;
  if exists (select 1 from cdj_essais
              where joueur_id = v_uid and jour = v_jour.jour and commune_code = p_code) then
    raise exception 'Tu as déjà proposé cette commune.';
  end if;

  select * into v_cible from communes where code = v_jour.commune_code;
  if p_code = v_cible.code then
    v_km := 0;
  else
    v_km := greatest(1, round(cdj_km(v_essai.latitude, v_essai.longitude,
                                     v_cible.latitude, v_cible.longitude))::int);
  end if;

  insert into cdj_essais(joueur_id, jour, n, commune_code, km)
  values (v_uid, v_jour.jour, v_nb + 1, p_code, v_km);

  return cdj_etat(v_uid, v_jour);
end;
$$;

-- ---------------------------------------------------------------------
-- 6. Les droits : seuls les deux points d'entrée, et seulement connecté
-- ---------------------------------------------------------------------
revoke all on function public.cdj_jour_courant()                     from public, anon, authenticated;
revoke all on function public.cdj_etat(uuid, public.cdj_jours)       from public, anon, authenticated;
revoke all on function public.cdj_partie()                           from public, anon;
revoke all on function public.cdj_essayer(text)                      from public, anon;
grant execute on function public.cdj_partie()       to authenticated;
grant execute on function public.cdj_essayer(text)  to authenticated;
