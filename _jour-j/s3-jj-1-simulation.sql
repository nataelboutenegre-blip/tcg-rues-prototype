-- ===========================================================================
--  Saison 3, jour J — étape 1 : SIMULATION de la clôture (rien n'est modifié)
--  À lancer juste avant l'étape 2. Attendu : podium, 0 doublon, max 1 distinction
--  par joueur, « soldes remis a (gardes) », « terra : cartes versees 0 »,
--  « ecarts avec le classement affiche 0 », dernière ligne SIMULATION.
-- ===========================================================================
select * from public.cloture_s2_s3(false);
