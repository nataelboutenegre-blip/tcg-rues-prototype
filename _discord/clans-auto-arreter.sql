-- ===========================================================================
--  Clans Discord : ARRÊTER le bot (plus aucun passage, ni simulé ni réel).
--  Pour relancer : clans-auto-activer.sql (ou 'simulation' à la place de 'arret').
--  Contrôle attendu : arret
-- ===========================================================================
update public.discord_sync set valeur = 'arret' where cle = 'mode';
select valeur as mode from public.discord_sync where cle = 'mode';
