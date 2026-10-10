-- ===========================================================================
--  TerraFront — RÉPÉTITION GÉNÉRALE, étape 0 : sécuriser la BRANCHE
--  À lancer UNIQUEMENT dans la branche de test, JAMAIS en production.
--
--  Pourquoi : une branche créée avec « Include data » peut contenir les
--  abonnements aux notifications des vrais joueurs. Sans ce fichier, une
--  attaque de test ou la tâche « paquet gratuit prêt » enverrait de VRAIES
--  notifications sur leurs téléphones.
--
--  Ce que fait le fichier, dans la branche :
--   1. coupe les déclencheurs de notifications_a_envoyer (plus aucun envoi) ;
--   2. arrête les tâches planifiées (pg_cron), s'il y en a ;
--   3. vide les abonnements aux notifications.
--
--  SÉCURITÉ : il refuse de tourner tant que la ligne marquée ci-dessous dit
--  'PRODUCTION'. Dans la branche, remplace PRODUCTION par BRANCHE (un mot),
--  puis lance.
-- ===========================================================================
do $s$
declare
  v_ou text := 'PRODUCTION';   -- <<< dans la branche, écrire 'BRANCHE' ici
  j record;
begin
  if v_ou <> 'BRANCHE' then
    raise exception 'Refusé : ce fichier ne doit tourner que dans la BRANCHE de test. Remplace PRODUCTION par BRANCHE à la ligne marquée si tu es bien dans la branche.';
  end if;

  if to_regclass('public.notifications_a_envoyer') is not null then
    execute 'alter table public.notifications_a_envoyer disable trigger user';
  end if;

  if to_regclass('cron.job') is not null then
    for j in execute 'select jobid, jobname from cron.job' loop
      execute 'select cron.unschedule($1)' using j.jobid;
      raise notice 'tâche planifiée arrêtée : %', j.jobname;
    end loop;
  end if;

  if to_regclass('public.abonnements_push') is not null then
    execute 'delete from public.abonnements_push';
  end if;
end
$s$;

-- Contrôle ---------------------------------------------------------------------------------
select (select count(*) from pg_trigger t where t.tgrelid = 'public.notifications_a_envoyer'::regclass
          and not t.tgisinternal and t.tgenabled <> 'D') as declencheurs_actifs_doit_etre_0,
       (select count(*) from public.abonnements_push) as abonnements_doit_etre_0;
