-- ===========================================================================
--  Clans Discord : lancer UN passage en SIMULATION (rien ne change sur Discord).
--  Attendre ~30 secondes, puis lancer clans-auto-journal.sql pour lire ce que
--  le bot ferait. Renvoie le numéro de l'appel (un nombre = bien parti).
-- ===========================================================================
select public.discord_clans_lancer('simulation') as appel;
