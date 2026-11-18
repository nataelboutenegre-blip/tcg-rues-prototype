-- ===========================================================================
--  s3-26 (18/11/2026) — pass de la saison 3 : 1 200 XP par niveau (au lieu de 1 000)
--  Simulation sur l'activité du 4 au 17/11 (quêtes plafonnées à 14 par jour, actions
--  à 500) : régulier médian ≈ 1 280 XP par jour → avec 1 000, pass fini vers le jour 16
--  sur 21 (quart haut jour 12) ; avec 1 200, vers le jour 19 (quart haut jour 14,
--  quart bas niveau 9 au lieu de 11). Décision de Nataël (18/11, 16 h 12).
--  Le jeu lit xp_niveau (aucun texte en dur). Pass encore fermé (debut null).
--  Baisser plus tard ne fait perdre de niveau à personne ; le relever, si.
--  Contrôle attendu : 1200 | null
-- ===========================================================================

update public.pass_saisons set xp_niveau = 1200 where saison = 'saison-3' and debut is null;

select xp_niveau, debut from public.pass_saisons where saison = 'saison-3';
