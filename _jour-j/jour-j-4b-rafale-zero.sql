-- ===========================================================================
--  TerraFront — jour J, étape 4 bis : Rafale repart de zéro (comme le Radar)
--  À lancer juste après jour-j-4-ouverture.sql.
--  Efface les parties Rafale et l'Elo de la saison 1. Les points déjà gagnés
--  ne sont pas touchés (les soldes ont été remis à 100 par la clôture).
--  Rejouable. Irréversible pour l'historique Rafale de la saison 1 (sans
--  enjeu : ni carte ni point n'en dépend).
-- ===========================================================================
delete from public.rafale_parties;
delete from public.rafale_joueurs;

select (select count(*) from public.rafale_parties) as parties_doit_etre_0,
       (select count(*) from public.rafale_joueurs) as joueurs_doit_etre_0;
