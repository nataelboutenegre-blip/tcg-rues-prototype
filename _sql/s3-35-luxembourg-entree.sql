-- ===========================================================================
--  TerraFront — s3-35 : le Luxembourg entre dans le jeu (JOUR J DE LA SAISON 3, après s3-32)
--
--  ⚠️  À LANCER SEULEMENT LE JOUR DE L'OUVERTURE (22/11/2026, étape 3 ter), quand le jeu
--  sait afficher le Luxembourg (interrupteur LUXEMBOURG_OUVERT poussé à l'étape 5). Dès ce
--  fichier, les 100 communes luxembourgeoises sortent des paquets du Front, comptent dans
--  le pot, et les 12 cantons comptent comme des départements (région unique « Luxembourg »).
--  Une fois que des joueurs en ont tiré, revenir en arrière est compliqué.
--
--  Prérequis (vérifiés : sinon rien ne se passe) :
--    - s3-34 passé (est_canton_lu, est_etranger, est_zone_front) ;
--    - la réserve complète (photos-luxembourg.py : 100 communes, 12 cantons).
--
--  Ce que fait le fichier, en une seule transaction (tout passe ou rien) :
--    1. copie les communes de la réserve dans communes (code LU…, nom, canton,
--       population, position, rareté, photo) ;
--    2. numérote les cartes luxembourgeoises dans leur rareté, entre elles : « n° 1 / 1 »
--       pour Luxembourg-Ville. Les numéros de France, de Suisse et de Belgique ne bougent pas ;
--    3. pas d'Aurore luxembourgeoises pour l'instant (décision du 19/11) ;
--    4. les coefficients de population des cantons (s3-30) ;
--    5. le catalogue de la carte.
--  Rejouable : une commune déjà entrée n'est pas recopiée.
--
--  Contrôle attendu :
--    100 | legendaire 1, epique 3, rare 10, peucommun 37, commun 49 | 0 | 0 | true | Luxembourg : legendaire n° 1 / 1 | 12
-- ===========================================================================
begin;

do $$
declare
  v_n integer;
  v_c integer;
begin
  -- s3-34 : le Luxembourg connu du serveur
  if to_regprocedure('public.est_canton_lu(text)') is null
     or to_regprocedure('public.est_zone_front(text)') is null
     or to_regprocedure('public.est_etranger(text)') is null then
    raise exception 's3-34 n''est pas passé (est_canton_lu / est_zone_front / est_etranger) : rien n''a changé';
  end if;
  if not public.est_canton_lu('LLU') or not public.est_canton_lu('LWI') or public.est_canton_lu('LU') or public.est_canton_lu('75') then
    raise exception 'est_canton_lu ne reconnaît pas les cantons : rien n''a changé';
  end if;

  -- la réserve doit être complète
  if to_regclass('public.luxembourg_communes_attente') is null then
    raise exception 'La réserve luxembourgeoise n''existe pas : lance d''abord s3-34 puis photos-luxembourg.py. Rien n''a changé';
  end if;
  select count(*), count(distinct departement) into v_n, v_c from public.luxembourg_communes_attente;
  if v_n <> 100 or v_c <> 12 then
    raise exception 'Réserve incomplète : % communes dans % cantons (il en faut 100 dans 12). Rien n''a changé', v_n, v_c;
  end if;
  select count(*) into v_n from public.luxembourg_communes_attente where not public.est_canton_lu(departement);
  if v_n > 0 then
    raise exception '% commune(s) de la réserve hors des 12 cantons : rien n''a changé', v_n;
  end if;

  -- aucun code luxembourgeois déjà pris par autre chose
  select count(*) into v_n
    from public.communes c join public.luxembourg_communes_attente a using (code)
   where c.departement is distinct from a.departement;
  if v_n > 0 then
    raise exception '% code(s) LU déjà présents avec un autre canton : rien n''a changé', v_n;
  end if;
end $$;

-- 1. les communes entrent, avec leur numéro dans leur rareté, entre communes luxembourgeoises
insert into public.communes (code, nom, departement, tier, population, rang, palier_total, latitude, longitude,
                             photo, photo_auteur, photo_licence, photo_source)
select code, nom, departement, tier, population,
       row_number() over (partition by tier order by population desc nulls last, code),
       count(*) over (partition by tier),
       latitude, longitude,
       photo, photo_auteur, photo_licence, photo_source
  from public.luxembourg_communes_attente
on conflict (code) do nothing;

-- 2. les numéros encore une fois, sur ce qui est en base (utile si le fichier est rejoué)
with r as (
  select code,
         row_number() over (partition by tier order by population desc nulls last, code) as rg,
         count(*) over (partition by tier) as total
    from public.communes
   where public.est_canton_lu(departement))
update public.communes c set rang = r.rg, palier_total = r.total
  from r
 where r.code = c.code
   and (c.rang is distinct from r.rg or c.palier_total is distinct from r.total);

-- 4. s3-30 : coefficients de population (les cantons entrent dans score_pop)
do $$
begin
  if to_regprocedure('public.score_pop_calculer()') is not null then
    perform public.score_pop_calculer();
  end if;
end $$;

-- 5. le catalogue de la carte (jeu et carte en direct), sans attendre le cron de 4 h 17
select public.carte_catalogue_refaire();

commit;

-- Contrôle :
--   100 | legendaire 1, epique 3, rare 10, peucommun 37, commun 49 | 0 | 0 | true | Luxembourg : legendaire n° 1 / 1 | 12
-- (melanges = un code LU rangé ailleurs, ou l'inverse ; france_a_part = le tableau des raretés de France
--  ignore toujours le Luxembourg ; cantons_score = cantons dans score_pop, 12)
select (select count(*) from public.communes where public.est_canton_lu(departement))::integer   as communes_lux,
       (select string_agg(tier || ' ' || n, ', '
                          order by array_position(array['legendaire','epique','rare','peucommun','commun'], tier))
          from (select tier, count(*) as n from public.communes
                 where public.est_canton_lu(departement) group by tier) t)                       as raretes,
       (select count(*) from public.communes
         where public.est_canton_lu(departement)
           and (rang is null or palier_total is null or rang > palier_total))::integer          as numeros_faux,
       ((select count(*) from public.communes where not public.est_canton_lu(departement) and code ~ '^LU[0-9]')
      + (select count(*) from public.communes where public.est_canton_lu(departement) and code !~ '^LU[0-9]'))::integer
                                                                                                as melanges,
       (select sum(total) from public.totaux_paliers())
         = (select count(*) from public.communes where est_metropole(departement))              as france_a_part,
       (select nom || ' : ' || tier || ' n° ' || rang || ' / ' || palier_total
          from public.communes where code = 'LU0304')                                           as luxembourg,
       (case when to_regclass('public.score_pop') is null then null
             else (select count(*) from public.score_pop where public.est_canton_lu(departement))::integer end)
                                                                                                as cantons_score;

-- Après vérification du jeu (quelques jours plus tard), la réserve peut partir :
--   drop table public.luxembourg_communes_attente;
