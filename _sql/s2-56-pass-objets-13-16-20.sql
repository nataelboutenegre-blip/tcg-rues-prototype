-- ===========================================================================
--  s2-56 — Pass « Brumes d'automne » : les trois derniers objets sont prêts
--  (patch257, aperçus validés par Nataël : « C'est parfait ! », 28/10)
--    niveau 13 : Dos Automne            ('pass-s2-dos-automne', gratuit)
--    niveau 16 : Dos Braises d'automne  ('pass-s2-dos-braises')
--    niveau 20 : Skin Vendanges         ('pass-s2-skin-vendanges')
--  Après ce SQL, les 20 récompenses du pass sont réclamables.
--  À lancer APRÈS avoir poussé patch257. Rejouable.
--  Contrôle attendu : 0 (aucune récompense encore « bientôt »)
-- ===========================================================================
update public.pass_recompenses set dispo = true
 where valeur in ('pass-s2-dos-automne', 'pass-s2-dos-braises', 'pass-s2-skin-vendanges');

select count(*) as encore_bientot from public.pass_recompenses where not dispo;
