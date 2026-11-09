-- s2-130 (9/11/2026, lancé à 16 h 48) : roue du Front, 50 tours par jour au lieu de 30
-- (Nataël : « Ok vas-y et on surveillera ça au fur et à mesure »).
-- Pourquoi : à 16 h 45, les 4 joueurs les plus à court d'énergie (1, 2, 2, 5) avaient déjà fait leurs 30 tours
-- avec 3 tours en réserve inutilisables. Recharge des tours inchangée (1 toutes les 20 min, 3 en réserve),
-- soirée inchangée (15 tours de 21 h à 23 h, hors des 50). Retour arrière : '30'.
update config_jeu set valeur = jsonb_set(valeur::jsonb, '{par_jour}', '50'::jsonb)::text where cle = 'roue_front';
