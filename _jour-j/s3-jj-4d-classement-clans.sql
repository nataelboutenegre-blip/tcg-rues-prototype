-- ===========================================================================
--  Saison 3, jour J — étape 4 quater : classement des clans aux POINTS des
--  5 meilleurs membres actifs (s3-28 + s3-33, idée d'Oshannir). APRÈS la clôture.
--  Réversible : la même ligne avec 0 (retour à la moyenne de communes).
--  Contrôle attendu : 1 | top5
-- ===========================================================================
update public.config_jeu set valeur = ((valeur::jsonb) || '{"classement_top5": 1}'::jsonb)::text where cle = 'clans_s3';
select (select (valeur::jsonb->>'classement_top5')::int from config_jeu where cle = 'clans_s3') as top5,
       (select count(*) from config_jeu where cle = 'clans_s3') as ok;
