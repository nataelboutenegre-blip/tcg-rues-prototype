-- ===========================================================================
--  s2-54 — Pass « Brumes d'automne » : les deux premiers objets sont prêts
--  (patch255, aperçu validé par Nataël : « Parfait », 28/10)
--    niveau 4 : Paquet Vendanges   (habillage 'pass-s2-paquet-vendanges')
--    niveau 6 : Dos Feuilles d'or  (dos 'pass-s2-dos-feuilles-or')
--  Ils deviennent réclamables. À lancer APRÈS avoir poussé patch255.
--  Rejouable. Contrôle attendu : 4 | true ; 6 | true
-- ===========================================================================
update public.pass_recompenses set dispo = true
 where valeur in ('pass-s2-paquet-vendanges', 'pass-s2-dos-feuilles-or');

select niveau, dispo from public.pass_recompenses
 where valeur in ('pass-s2-paquet-vendanges', 'pass-s2-dos-feuilles-or') order by niveau;
