-- ===========================================================================
--  s2-62 (secours) — couper les screamers d'Halloween sans toucher au code
--
--  Par défaut : les screamers s'arrêtent, le décor reste. Les joueurs déjà
--  connectés sont concernés au plus tard 10 min après, les autres à
--  l'ouverture du jeu.
--  Pour TOUT éteindre (décor compris), lancer plutôt la ligne commentée.
--  Contrôle attendu : la ligne 'halloween' avec "screamers": 0 (ou "ouvert": 0).
-- ===========================================================================
update public.config_jeu set valeur = (valeur::jsonb || '{"screamers": 0}'::jsonb) where cle = 'halloween';

-- tout éteindre :
-- update public.config_jeu set valeur = (valeur::jsonb || '{"ouvert": 0}'::jsonb) where cle = 'halloween';

select cle, valeur from public.config_jeu where cle = 'halloween';
