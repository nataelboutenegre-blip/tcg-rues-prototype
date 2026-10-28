-- ===========================================================================
--  s2-55 — Pass « Brumes d'automne » : Skin Brume et Paquet Sous-bois prêts
--  (patch256, aperçus validés par Nataël, 28/10)
--    niveau 10 : Skin Brume       ('pass-s2-skin-brume')
--    niveau 12 : Paquet Sous-bois ('pass-s2-paquet-sous-bois')
--  À lancer APRÈS avoir poussé patch256. Rejouable.
--  Contrôle attendu : 10 | true ; 12 | true
-- ===========================================================================
update public.pass_recompenses set dispo = true
 where valeur in ('pass-s2-skin-brume', 'pass-s2-paquet-sous-bois');

select niveau, dispo from public.pass_recompenses
 where valeur in ('pass-s2-skin-brume', 'pass-s2-paquet-sous-bois') order by niveau;
