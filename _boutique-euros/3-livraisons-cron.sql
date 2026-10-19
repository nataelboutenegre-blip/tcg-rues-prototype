-- ===========================================================================
--  TerraFront — boutique en euros : 3. livraison automatique après 14 jours
--  À passer APRÈS 2-fonctions.sql.
--  Prérequis : extension pg_cron activée (Database > Extensions > pg_cron).
--  Toutes les 15 minutes, livre les commandes « livraison dans 14 jours »
--  dont le délai de rétractation est passé.
-- ===========================================================================

select cron.unschedule(jobid) from cron.job where jobname = 'euros-livraisons-differees';
select cron.schedule('euros-livraisons-differees', '*/15 * * * *',
                     $$select public.euros_livrer_differees()$$);

select jobname, schedule, active from cron.job where jobname = 'euros-livraisons-differees';
