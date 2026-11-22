-- s3-54 (22/11/2026, décision de Nataël 20 h 24) : plus de prise instantanée en siège éclair.
-- Commune : au moins 5 min ; peu commune : au moins 10 min (rare 20 min, épique 1 h : inchangées).
-- Même mécanique que s3-49 : 10 % partent tout de suite, le reste attend et part tout seul (siege-tick toutes les 5 min,
-- donc en pratique la prise tombe entre 5 et 10 min pour une commune). Le propriétaire a le temps de renforcer.
-- Testé en retour arrière : avant = prise immédiate ; après = 6/55 tout de suite, 29 en attente, pas de prise.
-- Retour arrière : update config_jeu set valeur = jsonb_set(valeur::jsonb, '{eclair_min}', (valeur::jsonb->'eclair_min') - 'commun' - 'peucommun')::text where cle = 'siege';
update config_jeu set valeur = jsonb_set(valeur::jsonb, '{eclair_min}', (valeur::jsonb->'eclair_min') || '{"commun": 5, "peucommun": 10}')::text where cle = 'siege';
select valeur::jsonb->'eclair_min' eclair_min from config_jeu where cle = 'siege';
