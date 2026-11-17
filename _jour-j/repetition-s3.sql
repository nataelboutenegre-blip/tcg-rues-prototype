-- ===========================================================================
--  RÉPÉTITION du jour J de la saison 3 — tout s'annule à la fin (raise exception)
--  Clôture réelle (cloture_s2_s3(true)), entrée de la Suisse (s3-5), ouverture
--  (s3-jj-4), contrôle (s3-jj-6), avec la durée de chaque étape. Rien ne reste.
--  Pendant la répétition, les tables touchées sont verrouillées : le jeu peut
--  attendre quelques secondes à quelques minutes. À lancer à une heure creuse.
-- ===========================================================================
do $rep$
declare
  t0 timestamptz := clock_timestamp(); t1 timestamptz; t2 timestamptz; t3 timestamptz;
  v_rap text := ''; x record;
begin
  -- 1. la clôture
  for x in select * from public.cloture_s2_s3(true) loop
    if x.etape in ('récompenses · ATTRIBUÉ', 'clôture · saison', 'clôture · possessions', 'clôture · gardees apres completion',
                   'clôture · soldes remis a', 'clôture · terra : cartes versees', 'clôture · podium archive',
                   'clôture · ecarts avec le classement affiche', 'bâtiments rasés', 'FAIT', 'SIMULATION') then
      v_rap := v_rap || x.etape || ' = ' || left(coalesce(x.valeur, ''), 120) || E'\n';
    end if;
  end loop;
  t1 := clock_timestamp();

  -- 2. la Suisse (corps de _sql/s3-5-suisse-entree.sql, sans begin/commit)
-- 1. les communes entrent, avec leur numéro dans leur rareté, entre communes suisses
insert into public.communes (code, nom, departement, tier, population, rang, palier_total, latitude, longitude,
                             photo, photo_auteur, photo_licence, photo_source)
select code, nom, departement, tier, population,
       row_number() over (partition by tier order by population desc nulls last, code),
       count(*) over (partition by tier),
       latitude, longitude,
       photo, photo_auteur, photo_licence, photo_source      -- s3-16
  from public.suisse_communes_attente
on conflict (code) do nothing;

-- 2. les numéros encore une fois, sur ce qui est en base (utile si le fichier est rejoué)
with r as (
  select code,
         row_number() over (partition by tier order by population desc nulls last, code) as rg,
         count(*) over (partition by tier) as total
    from public.communes
   where est_canton(departement))
update public.communes c set rang = r.rg, palier_total = r.total
  from r
 where r.code = c.code
   and (c.rang is distinct from r.rg or c.palier_total is distinct from r.total);

-- 2b. (ajout du 16/11) les Aurore suisses : 46 communes dont la photo pleine carte est dans
--     aurore/CHxxxx.jpg et le crédit dans data/aurore.json (choix du 16/11). Même tirage que la France
--     (aurore_tirage) : en Terra comme en Front, une carte de ces communes peut sortir en Aurore.
insert into public.aurore_communes (code)
select c.code from public.communes c
 where c.code = any(array['CH1061', 'CH1711', 'CH2196', 'CH230', 'CH261', 'CH2939', 'CH3203', 'CH351', 'CH5002', 'CH5192', 'CH5938', 'CH6266', 'CH942', 'CH4566', 'CH5886', 'CH3427', 'CH4021', 'CH5724', 'CH4001', 'CH6608', 'CH1301', 'CH1372', 'CH2135', 'CH2275', 'CH2964', 'CH3101', 'CH5091', 'CH576', 'CH581', 'CH584', 'CH6300', 'CH6612', 'CH6037', 'CH250', 'CH1507', 'CH5613', 'CH228', 'CH5477', 'CH1069', 'CH1008', 'CH4260', 'CH6641', 'CH5859', 'CH4641', 'CH5260', 'CH562'])
on conflict (code) do nothing;

-- 3. (ajout du 11/11) le catalogue de la carte (jeu et carte en direct) : sans ça, les communes suisses
--    n'apparaissent sur les cartes qu'après le passage de 4 h 17 (cron carte-catalogue)
perform public.carte_catalogue_refaire();


  t2 := clock_timestamp();

  -- 3. l'ouverture (corps de _jour-j/s3-jj-4-ouverture.sql)
  update public.config_jeu set valeur = (valeur::jsonb || '{"actif": 1}'::jsonb)::text  where cle = 'siege';
  update public.config_jeu set valeur = (valeur::jsonb || '{"ouvert": 1}'::jsonb)::text where cle = 'zone_depart';
  update public.config_jeu set valeur = (valeur::jsonb || '{"actif": 1}'::jsonb)::text  where cle = 'mess';
  update public.config_jeu set valeur = (valeur::jsonb || '{"ouvert": 0}'::jsonb)::text where cle = 'reserve_accueil';
  update public.pass_saisons set debut = coalesce(debut, now()) where saison = 'saison-3';
  t3 := clock_timestamp();

  -- 4. le contrôle (s3-jj-6)
  select into x
    (select etat from saisons where id = 'saison-2') s2,
    (select etat || ' fin ' || to_char(fin_prevue at time zone 'Europe/Paris', 'DD/MM HH24:MI') from saisons where id = 'saison-3') s3,
    (select count(*) from classement_saisons where saison = 'saison-2') palmares,
    (select count(*) from joueur_badges where saison = 'saison-2') badges,
    (select count(*) from boutique_inventaire where article_id like 'dos-podium-s2-%') dos,
    (select count(*) from clan_trophees where saison = 'saison-2') trophee,
    (select count(*) from parrainage_recompenses where quoi = 'pionnier') pionniers,
    (select count(*) from possessions) front,
    (select count(*) from batiments) bat,
    (select count(*) from rafale_joueurs) + (select count(*) from pom_joueurs) + (select count(*) from radar_joueurs) elo,
    (select count(*) from communes where code like 'CH%') ch,
    (select count(*) from communes where code like 'CH%' and photo is not null) ch_photos,
    (select count(*) from aurore_communes where code like 'CH%') ch_aurores,
    (select nom || ' ' || tier || ' n° ' || rang || ' / ' || palier_total from communes where code = 'CH261') zurich,
    exists (select 1 from public.pass_en_cours()) pass,
    (select sum(total) from public.totaux_paliers()) = (select count(*) from public.communes where est_metropole(departement)) france_a_part;
  v_rap := v_rap || E'\n--- contrôle ---\n' || row_to_json(x)::text || E'\n';
  v_rap := v_rap || E'\n--- durées ---\nclôture ' || round(extract(epoch from t1 - t0)::numeric, 1) || ' s · Suisse '
          || round(extract(epoch from t2 - t1)::numeric, 1) || ' s · ouverture ' || round(extract(epoch from t3 - t2)::numeric, 1)
          || ' s · total ' || round(extract(epoch from clock_timestamp() - t0)::numeric, 1) || ' s';
  raise exception 'REPETITION (tout est annulé) %', v_rap;
end $rep$;
