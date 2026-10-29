-- ===========================================================================
--  s2-63 (secours) — couper les brillantes et les éclats
--  Plus de nouvelles brillantes au tirage, plus d'éclat possible. Les cartes
--  déjà brillantes ou avec un éclat restent comme elles sont, et restent
--  visibles. Pour rallumer : relancer s2-63-brillantes.sql.
--  Contrôle attendu : 0
-- ===========================================================================
update public.config_jeu
   set valeur = (valeur::jsonb || '{"ouvert": 0}'::jsonb)
 where cle = 'brillantes';

select (public.brillantes_options() ->> 'ouvert')::int as ouvert;
