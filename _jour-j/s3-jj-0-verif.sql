-- ===========================================================================
--  Saison 3, jour J — étape 0 : VÉRIFICATION (lecture seule, la veille et le matin)
--  Tout doit être à true. Rien n'est modifié.
-- ===========================================================================
select
  (select etat from saisons where id = 'saison-2') in ('en_cours', 'compte_a_rebours')        as s2_ouverte,
  not exists (select 1 from saisons where id = 'saison-3')                                     as s3_pas_encore_creee,
  to_regprocedure('public.cloture_s2_s3(boolean)') is not null                                 as cloture_installee,
  position('s3-15b' in pg_get_functiondef('public.cloture_s2_s3(boolean)'::regprocedure)) > 0 as cloture_accepte_rebours,
  position('s3-15' in pg_get_functiondef('public.cloturer_saison(text,text,text,boolean,integer,text[],numeric)'::regprocedure)) > 0 as tp_gardes,
  to_regprocedure('public.recompenses_s2_attribuer(boolean)') is not null                      as recompenses_installees,
  to_regclass('public.clan_trophees') is not null                                              as table_trophees,
  (select count(*) from boutique_articles where id like 'dos-podium-s2-%') = 3                  as dos_podium,
  (select count(*) from joueur_badges where saison = 'saison-2') = 0                            as badges_s2_pas_encore_donnes,
  (select count(*) from suisse_communes_attente) = 2110                                         as reserve_suisse,
  (select count(*) from suisse_communes_attente where photo is not null) >= 1900                as photos_suisses,
  (select count(*) from communes where code like 'CH%') = 0                                     as suisse_pas_encore_entree,
  to_regprocedure('public.est_canton(text)') is not null                                       as s3_1_passe,
  (select coalesce((valeur::jsonb->>'actif')::int, 0) from config_jeu where cle = 'siege') = 0  as siege_eteint,
  (select coalesce((valeur::jsonb->>'ouvert')::int, 0) from config_jeu where cle = 'zone_depart') = 0 as zone_fermee,
  (select coalesce((valeur::jsonb->>'actif')::int, 0) from config_jeu where cle = 'mess') = 0   as mess_eteint,
  (select coalesce((valeur::jsonb->>'ouvert')::int, 0) from config_jeu where cle = 'reserve_accueil') = 1 as reserve_accueil_encore_ouverte,
  (select debut is null from pass_saisons where saison = 'saison-3')                            as pass_s3_ferme,
  exists (select 1 from cron.job where jobname = 'siege-tick')                                 as tache_siege;
