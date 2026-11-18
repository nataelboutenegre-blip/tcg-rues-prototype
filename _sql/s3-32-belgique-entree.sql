-- ===========================================================================
--  TerraFront — s3-32 : la Belgique entre dans le jeu (JOUR DE L'OUVERTURE BELGE)
--
--  ⚠️  À LANCER SEULEMENT LE JOUR DE L'OUVERTURE, quand le jeu sait afficher
--  la Belgique (interrupteur BELGIQUE_OUVERTE poussé). Dès ce fichier, les 565
--  communes belges sortent des paquets du Front, comptent dans le pot et la
--  réserve d'accueil, et les 11 provinces comptent comme des départements
--  (région unique « Belgique »). Une fois que des joueurs en ont tiré, revenir
--  en arrière est compliqué.
--
--  Prérequis (vérifiés : sinon rien ne se passe) :
--    - s3-31 passé (est_province_be, est_etranger, est_zone_front) ;
--    - la réserve complète (s3-32a + photos-belgique.py : 565 communes, 11 provinces).
--
--  Ce que fait le fichier, en une seule transaction (tout passe ou rien) :
--    1. copie les communes de la réserve dans communes (code BE…, nom, province,
--       population, position, rareté, photo) ;
--    2. numérote les cartes belges dans leur rareté, entre elles : « n° 1 / 5 »
--       pour Anvers. Les numéros de France et de Suisse ne bougent pas ;
--    3. les 51 Aurore belges (choix de Nataël du 19/11 : photos aurore/BExxxxx.jpg,
--       crédits dans data/aurore.json) ;
--    4. les coefficients de population des provinces (s3-30), si s3-30 est là ;
--    5. le catalogue de la carte.
--  Rejouable : une commune déjà entrée n'est pas recopiée.
--
--  Contrôle attendu :
--    565 | legendaire 5, epique 16, rare 56, peucommun 209, commun 279 | 0 | 0 | true | Anvers : legendaire n° 1 / 5 | 51 | 11
-- ===========================================================================
begin;

do $$
declare
  v_n integer;
  v_c integer;
begin
  -- s3-31 : la Belgique connue du serveur
  if to_regprocedure('public.est_province_be(text)') is null
     or to_regprocedure('public.est_zone_front(text)') is null
     or to_regprocedure('public.est_etranger(text)') is null then
    raise exception 's3-31 n''est pas passé (est_province_be / est_zone_front / est_etranger) : rien n''a changé';
  end if;
  if not public.est_province_be('VAN') or not public.est_province_be('BRU') or public.est_province_be('75') then
    raise exception 'est_province_be ne reconnaît pas les provinces : rien n''a changé';
  end if;

  -- la réserve doit être complète
  if to_regclass('public.belgique_communes_attente') is null then
    raise exception 'La réserve belge n''existe pas : lance d''abord s3-32a puis photos-belgique.py. Rien n''a changé';
  end if;
  select count(*), count(distinct departement) into v_n, v_c from public.belgique_communes_attente;
  if v_n <> 565 or v_c <> 11 then
    raise exception 'Réserve incomplète : % communes dans % provinces (il en faut 565 dans 11). Rien n''a changé', v_n, v_c;
  end if;
  select count(*) into v_n from public.belgique_communes_attente where not public.est_province_be(departement);
  if v_n > 0 then
    raise exception '% commune(s) de la réserve hors des 11 provinces : rien n''a changé', v_n;
  end if;

  -- aucun code belge déjà pris par autre chose
  select count(*) into v_n
    from public.communes c join public.belgique_communes_attente a using (code)
   where c.departement is distinct from a.departement;
  if v_n > 0 then
    raise exception '% code(s) BE déjà présents avec une autre province : rien n''a changé', v_n;
  end if;
end $$;

-- 1. les communes entrent, avec leur numéro dans leur rareté, entre communes belges
insert into public.communes (code, nom, departement, tier, population, rang, palier_total, latitude, longitude,
                             photo, photo_auteur, photo_licence, photo_source)
select code, nom, departement, tier, population,
       row_number() over (partition by tier order by population desc nulls last, code),
       count(*) over (partition by tier),
       latitude, longitude,
       photo, photo_auteur, photo_licence, photo_source
  from public.belgique_communes_attente
on conflict (code) do nothing;

-- 2. les numéros encore une fois, sur ce qui est en base (utile si le fichier est rejoué)
with r as (
  select code,
         row_number() over (partition by tier order by population desc nulls last, code) as rg,
         count(*) over (partition by tier) as total
    from public.communes
   where public.est_province_be(departement))
update public.communes c set rang = r.rg, palier_total = r.total
  from r
 where r.code = c.code
   and (c.rang is distinct from r.rg or c.palier_total is distinct from r.total);

-- 3. les Aurore belges (choix du 19/11) : même tirage que la France et la Suisse (aurore_tirage)
insert into public.aurore_communes (code)
select c.code from public.communes c
 where c.code = any(array['BE11002', 'BE44021', 'BE52011', 'BE21004', 'BE62063', 'BE21015', 'BE21001', 'BE31005', 'BE92094', 'BE21012', 'BE53053', 'BE41002', 'BE71072', 'BE21009', 'BE12025', 'BE21016', 'BE46021', 'BE58001', 'BE34022', 'BE35013', 'BE36015', 'BE62096', 'BE21018', 'BE57096', 'BE63079', 'BE21010', 'BE21005', 'BE21013', 'BE71004', 'BE23088', 'BE42006', 'BE44083', 'BE21019', 'BE71053', 'BE25014', 'BE73107', 'BE34040', 'BE23025', 'BE12021', 'BE11008', 'BE44019', 'BE24107', 'BE23077', 'BE33011', 'BE25112', 'BE41018', 'BE72020', 'BE34027', 'BE58002', 'BE45035', 'BE31043'])
on conflict (code) do nothing;

-- 4. s3-30 : coefficients de population (les provinces entrent dans score_pop)
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
--   565 | legendaire 5, epique 16, rare 56, peucommun 209, commun 279 | 0 | 0 | true | Anvers : legendaire n° 1 / 5 | 51 | 11
-- (melanges = un code BE rangé ailleurs, ou l'inverse ; france_a_part = le tableau des raretés de France
--  ignore toujours la Belgique ; provinces_score = provinces dans score_pop, 11 si s3-30 est là)
select (select count(*) from public.communes where public.est_province_be(departement))::integer   as communes_belges,
       (select string_agg(tier || ' ' || n, ', '
                          order by array_position(array['legendaire','epique','rare','peucommun','commun'], tier))
          from (select tier, count(*) as n from public.communes
                 where public.est_province_be(departement) group by tier) t)                     as raretes,
       (select count(*) from public.communes
         where public.est_province_be(departement)
           and (rang is null or palier_total is null or rang > palier_total))::integer          as numeros_faux,
       ((select count(*) from public.communes where not public.est_province_be(departement) and code like 'BE%')
      + (select count(*) from public.communes where public.est_province_be(departement) and code not like 'BE%'))::integer
                                                                                                as melanges,
       (select sum(total) from public.totaux_paliers())
         = (select count(*) from public.communes where est_metropole(departement))              as france_a_part,
       (select nom || ' : ' || tier || ' n° ' || rang || ' / ' || palier_total
          from public.communes where code = 'BE11002')                                          as anvers,
       (select count(*) from public.aurore_communes where code like 'BE%')::integer               as aurores_belges,
       (case when to_regclass('public.score_pop') is null then null
             else (select count(*) from public.score_pop where public.est_province_be(departement))::integer end)
                                                                                                as provinces_score;

-- Après vérification du jeu (quelques jours plus tard), la réserve peut partir :
--   drop table public.belgique_communes_attente;
