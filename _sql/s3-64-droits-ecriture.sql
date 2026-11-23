-- s3-64 (23/11/2026) : durcissement après l'audit des droits (demande de Nataël).
-- 19 tables gardaient les droits d'écriture accordés par défaut à anon et authenticated. La sécurité ligne par
-- ligne les bloquait déjà (aucune règle d'écriture, sauf contrat_exclusions : ses propres lignes), mais on retire
-- la deuxième porte. Le jeu n'écrit jamais directement dans une table : tout passe par des fonctions du serveur.
do $do$
declare t text;
begin
  foreach t in array array['bourse_ventes','clan_alliance_membres','clan_alliances','clan_diplomatie','clan_trophees','contrat_exclusions',
    'euros_prix_historique','euros_promos','front_siege_alertes','joueur_motifs','joueur_vus','mess_421_parties','monuments','motif_formes',
    'motif_signalements','mouvements_points','paquet_departement_prix_cache','solde_corrections','terra_roue_tours'] loop
    execute format('revoke insert, update, delete, truncate on public.%I from anon, authenticated', t);
  end loop;
  revoke truncate on public.amis from anon, authenticated;   -- TRUNCATE ignore la sécurité ligne par ligne (inaccessible par l'API, mais on ferme)
end $do$;
-- Contrôle : aucune ligne attendue
-- select grantee, table_name, privilege_type from information_schema.role_table_grants
--  where grantee in ('anon','authenticated') and table_schema = 'public' and privilege_type in ('INSERT','UPDATE','DELETE','TRUNCATE');
