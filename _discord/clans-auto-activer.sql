-- ===========================================================================
--  Clans Discord : PASSER EN AUTOMATIQUE (le bot agit toutes les 10 minutes)
--  et lancer un premier passage tout de suite.
--  Pour arrêter : clans-auto-arreter.sql. Contrôle attendu : actif | un nombre
-- ===========================================================================
update public.discord_sync set valeur = 'actif' where cle = 'mode';
select (select valeur from public.discord_sync where cle = 'mode') as mode,
       public.discord_clans_lancer() as appel;
