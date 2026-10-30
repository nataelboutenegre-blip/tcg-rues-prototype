-- ===========================================================================
--  s2-68 — SECOURS : couper les communes hantées
--  Plus de commune hantée dans les paquets (Terra et Front), la quête
--  disparaît du jeu (relu à l'ouverture et toutes les 10 min).
--  Ce qui a été gagné est gardé : cartes hantées, titres, récompenses.
--  Pour rallumer : relancer s2-68-halloween-hantees.sql.
--  Contrôle attendu : 0
-- ===========================================================================
update public.config_jeu
   set valeur = (valeur::jsonb || '{"ouvert": 0}'::jsonb)
 where cle = 'halloween_hantees';

select (select c.valeur::jsonb ->> 'ouvert' from public.config_jeu c where c.cle = 'halloween_hantees')::int as ouvert;
