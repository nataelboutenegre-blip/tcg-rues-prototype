-- ===========================================================================
--  TerraFront — s3-80 : l'Espagne, l'Andorre et Monaco entrent dans le jeu (JOUR J, après s3-79)
--
--  ⚠️  À LANCER SEULEMENT LE JOUR DE L'OUVERTURE, quand le jeu sait les afficher
--  (interrupteur ESPAGNE_OUVERTE poussé). Dès ce fichier, les 8 140 communes sortent des
--  paquets du Front, comptent dans le pot, les 52 provinces, l'Andorre et Monaco comptent comme
--  des départements, et le paquet Terra « Espagne » s'ouvre. Revenir en arrière est compliqué.
--
--  Prérequis (vérifiés : sinon rien ne se passe) :
--    - s3-79 passé (est_province_es, est_micro_etat, est_etranger, est_zone_front) ;
--    - la réserve complète (photos-espagne.py : 8 140 communes, 54 « départements »).
--
--  En une seule transaction :
--    1. copie les communes de la réserve dans communes (avec leur photo) ;
--    2. numérote les cartes dans leur rareté, par pays : Espagne entre elles (« n° 1 / 71 » pour Madrid),
--       Andorre entre elles, Monaco seul (« n° 1 / 1 »). Les numéros des autres pays ne bougent pas ;
--    3. les coefficients de population (s3-30) ;
--    4. le catalogue de la carte.
--  Rejouable : une commune déjà entrée n'est pas recopiée.
--
--  Contrôle attendu :
--    8140 | ES legendaire 71, epique 237, rare 797, peucommun 3006, commun 4021 | 0 | 0 | true | Madrid : legendaire n° 1 / 71 | Monaco : legendaire n° 1 / 1 | 54
-- ===========================================================================
begin;

do $$
declare
  v_n integer;
  v_c integer;
begin
  if to_regprocedure('public.est_province_es(text)') is null or to_regprocedure('public.est_micro_etat(text)') is null then
    raise exception 's3-79 n''est pas passé : rien n''a changé';
  end if;
  if not public.est_zone_front('E28') or not public.est_zone_front('AND') or public.est_province_es('28') then
    raise exception 'est_zone_front / est_province_es ne reconnaissent pas les provinces : rien n''a changé';
  end if;
  if to_regclass('public.espagne_communes_attente') is null then
    raise exception 'La réserve espagnole n''existe pas : rien n''a changé';
  end if;
  select count(*), count(distinct departement) into v_n, v_c from public.espagne_communes_attente;
  if v_n <> 8140 or v_c <> 54 then
    raise exception 'Réserve incomplète : % communes dans % départements (il en faut 8 140 dans 54). Rien n''a changé', v_n, v_c;
  end if;
  select count(*) into v_n from public.espagne_communes_attente where not (public.est_province_es(departement) or public.est_micro_etat(departement));
  if v_n > 0 then raise exception '% commune(s) de la réserve hors des provinces : rien n''a changé', v_n; end if;
  select count(*) into v_n from public.communes c join public.espagne_communes_attente a using (code) where c.departement is distinct from a.departement;
  if v_n > 0 then raise exception '% code(s) déjà présents avec un autre département : rien n''a changé', v_n; end if;
end $$;

-- 1. les communes entrent (les numéros sont posés juste après)
insert into public.communes (code, nom, departement, tier, population, rang, palier_total, latitude, longitude,
                             photo, photo_auteur, photo_licence, photo_source)
select code, nom, departement, tier, population, 0, 0, latitude, longitude,
       photo, photo_auteur, photo_licence, photo_source
  from public.espagne_communes_attente
on conflict (code) do nothing;

-- 2. les numéros, par pays (ES, AD, MC) et par rareté
with r as (
  select code,
         row_number() over (partition by left(code, 2), tier order by population desc nulls last, code) as rg,
         count(*) over (partition by left(code, 2), tier) as total
    from public.communes
   where public.est_province_es(departement) or public.est_micro_etat(departement))
update public.communes c set rang = r.rg, palier_total = r.total
  from r
 where r.code = c.code
   and (c.rang is distinct from r.rg or c.palier_total is distinct from r.total);

-- 3. s3-30 : coefficients de population
do $$
begin
  if to_regprocedure('public.score_pop_calculer()') is not null then
    perform public.score_pop_calculer();
  end if;
end $$;

-- 4. le catalogue de la carte
select public.carte_catalogue_refaire();

commit;

select (select count(*) from public.communes where public.est_province_es(departement) or public.est_micro_etat(departement))::integer as communes,
       (select 'ES ' || string_agg(tier || ' ' || n, ', ' order by array_position(array['legendaire','epique','rare','peucommun','commun'], tier))
          from (select tier, count(*) as n from public.communes where public.est_province_es(departement) group by tier) t) as raretes,
       (select count(*) from public.communes where (public.est_province_es(departement) or public.est_micro_etat(departement))
           and (rang is null or rang = 0 or palier_total is null or rang > palier_total))::integer as numeros_faux,
       ((select count(*) from public.communes where not public.est_province_es(departement) and code ~ '^ES[0-9]')
      + (select count(*) from public.communes where public.est_province_es(departement) and code !~ '^ES[0-9]'))::integer as melanges,
       (select sum(total) from public.totaux_paliers()) = (select count(*) from public.communes where est_metropole(departement)) as france_a_part,
       (select nom || ' : ' || tier || ' n° ' || rang || ' / ' || palier_total from public.communes where code = 'ES28079') as madrid,
       (select nom || ' : ' || tier || ' n° ' || rang || ' / ' || palier_total from public.communes where code = 'MC00') as monaco,
       (case when to_regclass('public.score_pop') is null then null
             else (select count(*) from public.score_pop where public.est_province_es(departement) or public.est_micro_etat(departement))::integer end) as provinces_score;
