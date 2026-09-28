-- =====================================================================
--  TerraFront — un fait vrai sur chaque commune
--
--  Tout est calculé depuis la table communes : rien n'est importé, rien
--  n'est inventé, rien n'est à vérifier. Un joueur qui tire sa propre
--  commune ne peut pas y lire une erreur, parce qu'il n'y a rien d'autre
--  que ce que les données disent déjà.
--
--  L'enjeu n'est pas décoratif. 88 % du pot est du commun — 27 680 communes
--  libres que personne n'a envie de tirer. Y (80) et Ô-de-Selle (80) sont
--  des communes au sens du jeu, et uniques en France. Un fait vrai suffit à
--  en faire des trophées sans toucher ni à la rareté, ni au prix, ni aux taux.
--
--  À relancer si la table communes change. Idempotent.
-- =====================================================================

alter table public.communes add column if not exists faits jsonb;

-- On repart de zéro à chaque exécution : sinon les faits s'empilent.
update public.communes set faits = '[]'::jsonb;

-- Un fait porte un rang d'intérêt : 1 = unique en France, 5 = anecdotique.
-- Le navigateur affiche le plus petit en premier.
create or replace function public.ajouter_fait(p_codes text[], p_rang int, p_texte text)
returns integer
language sql
as $$
  with maj as (
    update public.communes
       set faits = coalesce(faits, '[]'::jsonb) || jsonb_build_array(
             jsonb_build_object('r', p_rang, 't', p_texte))
     where code = any(p_codes)
    returning 1)
  select count(*)::integer from maj;
$$;

-- ---------------------------------------------------------------------
-- 1. Les noms extrêmes
-- ---------------------------------------------------------------------
do $$
declare r record;
begin
  for r in (select code, nom, length(nom) as l from communes order by length(nom), nom limit 5) loop
    perform ajouter_fait(array[r.code], case when r.l <= 2 then 1 else 2 end,
      case when r.l = 1 then 'Le nom de commune le plus court de France : une seule lettre.'
           else 'Un des noms de commune les plus courts de France : ' || r.l || ' lettres.' end);
  end loop;
  for r in (select code, nom, length(nom) as l from communes order by length(nom) desc limit 5) loop
    perform ajouter_fait(array[r.code], 2,
      'Un des noms de commune les plus longs de France : ' || r.l || ' caractères.');
  end loop;
end $$;

-- ---------------------------------------------------------------------
-- 2. Les palindromes
-- ---------------------------------------------------------------------
select ajouter_fait(
  array(select code from communes
         where length(replace(lower(nom), '-', '')) >= 4
           and replace(lower(nom), '-', '') = reverse(replace(lower(nom), '-', ''))),
  2, 'Son nom se lit dans les deux sens.');

-- ---------------------------------------------------------------------
-- 3. Les initiales rares
-- ---------------------------------------------------------------------
do $$
declare r record;
begin
  for r in (select upper(left(nom, 1)) as lettre, count(*) as n
              from communes group by 1 having count(*) <= 220) loop
    perform ajouter_fait(
      array(select code from communes where upper(left(nom, 1)) = r.lettre),
      case when r.n = 1 then 1 when r.n <= 40 then 2 else 4 end,
      case when r.n = 1
           then 'La seule commune de France dont le nom commence par « ' || r.lettre || ' ».'
           else 'Une des ' || r.n || ' communes de France dont le nom commence par « '
                || r.lettre || ' ».' end);
  end loop;
end $$;

-- ---------------------------------------------------------------------
-- 4. Les homonymes
-- ---------------------------------------------------------------------
do $$
declare r record;
begin
  for r in (select nom, count(*) as n from communes group by nom having count(*) >= 2) loop
    perform ajouter_fait(
      array(select code from communes where nom = r.nom),
      case when r.n >= 6 then 3 else 5 end,
      case when r.n = 2 then 'Deux communes de France portent ce nom.'
           else r.n || ' communes de France portent ce nom.' end);
  end loop;
end $$;

-- ---------------------------------------------------------------------
-- 5. Les extrêmes de population, en France et dans son département
-- ---------------------------------------------------------------------
do $$
declare r record;
begin
  for r in (select code from communes where population > 0 order by population desc limit 3) loop
    perform ajouter_fait(array[r.code], 1, 'Une des communes les plus peuplées du jeu.');
  end loop;
  for r in (select code from communes where population > 0 order by population limit 3) loop
    perform ajouter_fait(array[r.code], 1, 'Une des communes les moins peuplées de France.');
  end loop;

  -- la plus et la moins peuplée de chaque département
  for r in (
    select distinct on (departement) code, departement
      from communes where population > 0 order by departement, population desc) loop
    perform ajouter_fait(array[r.code], 3,
      'La commune la plus peuplée de son département.');
  end loop;
  for r in (
    select distinct on (departement) code, departement
      from communes where population > 0 order by departement, population) loop
    perform ajouter_fait(array[r.code], 3,
      'La commune la moins peuplée de son département.');
  end loop;
end $$;

-- ---------------------------------------------------------------------
-- 6. Les familles de noms
-- ---------------------------------------------------------------------
do $$
declare r record;
begin
  for r in (
    select split_part(nom, '-', 1) || '-' || split_part(nom, '-', 2) as mot, count(*) as n
      from communes where nom like '%-%' group by 1 having count(*) >= 30) loop
    perform ajouter_fait(
      array(select code from communes
             where nom like '%-%'
               and split_part(nom, '-', 1) || '-' || split_part(nom, '-', 2) = r.mot),
      5, 'Une des ' || r.n || ' communes dont le nom commence par « ' || r.mot || ' ».');
  end loop;
end $$;

-- ---------------------------------------------------------------------
-- 7. Les quatre points cardinaux de chaque département
-- ---------------------------------------------------------------------
-- Gratuit : les coordonnées sont déjà là. Et « la commune la plus au nord
-- de la Charente » est un titre qu'on a envie de garder.
do $$
declare r record;
begin
  for r in (select distinct on (departement) code, departement from communes
             where latitude is not null order by departement, latitude desc) loop
    perform ajouter_fait(array[r.code], 3, 'La commune la plus au nord de son département.');
  end loop;
  for r in (select distinct on (departement) code, departement from communes
             where latitude is not null order by departement, latitude) loop
    perform ajouter_fait(array[r.code], 3, 'La commune la plus au sud de son département.');
  end loop;
  for r in (select distinct on (departement) code, departement from communes
             where longitude is not null order by departement, longitude desc) loop
    perform ajouter_fait(array[r.code], 3, 'La commune la plus à l''est de son département.');
  end loop;
  for r in (select distinct on (departement) code, departement from communes
             where longitude is not null order by departement, longitude) loop
    perform ajouter_fait(array[r.code], 3, 'La commune la plus à l''ouest de son département.');
  end loop;
end $$;

-- Les quatre extrémités de la France, elles, valent le rang 1.
do $$
declare r record;
begin
  for r in (select code, 'nord' as sens from communes
             where latitude is not null and departement !~ '^97'
             order by latitude desc limit 1) loop
    perform ajouter_fait(array[r.code], 1, 'La commune la plus au nord de France métropolitaine.');
  end loop;
  for r in (select code from communes
             where latitude is not null and departement !~ '^97'
             order by latitude limit 1) loop
    perform ajouter_fait(array[r.code], 1, 'La commune la plus au sud de France métropolitaine.');
  end loop;
  for r in (select code from communes
             where longitude is not null and departement !~ '^97'
             order by longitude desc limit 1) loop
    perform ajouter_fait(array[r.code], 1, 'La commune la plus à l''est de France métropolitaine.');
  end loop;
  for r in (select code from communes
             where longitude is not null and departement !~ '^97'
             order by longitude limit 1) loop
    perform ajouter_fait(array[r.code], 1, 'La commune la plus à l''ouest de France métropolitaine.');
  end loop;
end $$;

-- ---------------------------------------------------------------------
-- 8. Le rang de population dans son département, pour toutes les autres
-- ---------------------------------------------------------------------
-- Le rang national ne dit rien à personne : être 28 471e sur 34 739, c'est
-- un nombre. Le rang départemental se compare à ce qu'on connaît.
do $$
begin
  with rangs as (
    select code, departement,
           row_number() over (partition by departement order by population desc nulls last) as rg,
           count(*)      over (partition by departement) as total
      from communes)
  update communes c
     set faits = c.faits || jsonb_build_array(jsonb_build_object(
           'r', 6,
           't', rangs.rg || 'e commune de son département par la population, sur '
                || rangs.total || '.'))
    from rangs
   where rangs.code = c.code
     and jsonb_array_length(c.faits) = 0;
end $$;

-- ---------------------------------------------------------------------
-- 9. Un index pour les succès à venir
-- ---------------------------------------------------------------------
create index if not exists communes_faits_idx on public.communes using gin (faits);

-- ---------------------------------------------------------------------
-- Vérifications
-- ---------------------------------------------------------------------
-- a) combien de communes ont au moins un fait (doit être 34 739)
-- select count(*) filter (where jsonb_array_length(faits) > 0) as avec_fait,
--        count(*) as total from communes;
--
-- b) les deux perles de la Somme
-- select nom, departement, jsonb_pretty(faits) from communes
--  where nom in ('Y', 'Ô-de-Selle');
--
-- c) répartition du nombre de faits par commune
-- select jsonb_array_length(faits) as nb_faits, count(*) from communes group by 1 order by 1;
