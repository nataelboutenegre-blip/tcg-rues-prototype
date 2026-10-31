-- ===========================================================================
--  Secours s2-72 — couper les lingots gagnés en combattant.
--  Les combats ne rapportent plus de lingots ; ce qui a déjà été gagné reste.
--  Pour rallumer : remplacer 0 par 1 et relancer.
--  Contrôle attendu : false
-- ===========================================================================
update public.config_jeu
   set valeur = (valeur::jsonb || '{"lingots_combat_ouvert": 0}'::jsonb)::text
 where cle = 'batiments';

select coalesce(batiment_reglage('lingots_combat_ouvert'), 0) = 1 as ouvert;
