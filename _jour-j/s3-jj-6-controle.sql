-- ===========================================================================
--  Saison 3, jour J — étape 6 : CONTRÔLE (lecture seule, après tout le reste)
-- ===========================================================================
select
  (select etat from saisons where id = 'saison-2')                                              as s2,
  (select etat || ' · fin ' || to_char(fin_prevue at time zone 'Europe/Paris', 'DD/MM HH24:MI') from saisons where id = 'saison-3') as s3,
  (select count(*) from classement_saisons where saison = 'saison-2')                            as palmares_s2,
  (select count(*) from joueur_badges where saison = 'saison-2')                                as badges_s2,
  (select count(*) from boutique_inventaire where article_id like 'dos-podium-s2-%')            as dos_podium,
  (select count(*) from clan_trophees where saison = 'saison-2')                                as trophee,
  (select count(*) from parrainage_recompenses where quoi = 'pionnier')                         as paquets_pionniers,
  (select count(*) from possessions)                                                            as front_communes,
  (select count(*) from batiments)                                                              as batiments,
  (select count(*) from rafale_joueurs) + (select count(*) from pom_joueurs) + (select count(*) from radar_joueurs) as elo_restants,
  (select count(*) from communes where code like 'CH%')                                         as communes_suisses,
  (select count(*) from communes where code like 'CH%' and photo is not null)                   as photos_suisses,
  (select count(*) from aurore_communes where code like 'CH%')                                  as aurores_suisses,
  (select count(*) from communes where code like 'BE%')                                         as communes_belges,      -- 565 (ajout du 19/11)
  (select count(*) from communes where code like 'BE%' and photo is not null)                   as photos_belges,        -- 562
  (select count(*) from aurore_communes where code like 'BE%')                                  as aurores_belges,       -- 51
  (select (valeur::jsonb->>'actif')::int from config_jeu where cle = 'siege')                   as siege,
  (select (valeur::jsonb->>'ouvert')::int from config_jeu where cle = 'reserve_accueil')        as reserve_accueil,
  (select (valeur::jsonb->>'toujours')::int + (valeur::jsonb->>'jetons_propres')::int from config_jeu where cle = 'roue_front') as roue_s3_2;
