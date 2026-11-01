-- ===========================================================================
--  Clans Discord : les 10 derniers passages (lecture seule).
--  ok = false : quelque chose a bloqué (le résumé dit quoi).
--  actions : ce qui a été fait (FAIT) ou serait fait (SIMULÉ).
--  introuvables : joueurs de clan pas reconnus sur le Discord → les ajouter
--  dans discord_correspondances (pseudo du jeu, nom Discord).
--  Affiche des pseudos : ne pas copier ailleurs. Un seul tableau.
-- ===========================================================================
select to_char(le at time zone 'Europe/Paris', 'DD/MM HH24:MI') as quand, mode, ok, resume,
       details -> 'actions'        as actions,
       details -> 'introuvables'   as introuvables,
       details -> 'avertissements' as avertissements,
       details -> 'erreurs'        as erreurs
  from public.discord_sync_journal
 order by id desc
 limit 10;
