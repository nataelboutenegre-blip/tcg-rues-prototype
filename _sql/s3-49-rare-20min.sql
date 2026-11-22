-- s3-49 (22/11/2026, décision de Nataël 17 h 52) : une rare demande au moins 20 min, même en siège éclair,
-- pour laisser au propriétaire le temps de renforcer (avant : prise en une seconde sans défense).
-- Même mécanique que l'épique (1 h) : 10 % partent tout de suite, le reste de la vague attend et part toute seule
-- (siege-tick toutes les 5 min). Commune et peu commune : inchangées.
-- Retour arrière : update config_jeu set valeur = jsonb_set(valeur::jsonb, '{eclair_min}', '{"epique": 60}')::text where cle = 'siege';
update config_jeu set valeur = jsonb_set(valeur::jsonb, '{eclair_min}', (valeur::jsonb->'eclair_min') || '{"rare": 20}')::text where cle = 'siege';
select valeur::jsonb->'eclair_min' eclair_min, siege_tier_n('eclair_min', 'rare') rare, siege_tier_n('eclair_min', 'epique') epique from config_jeu where cle = 'siege';
