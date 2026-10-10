-- ===========================================================================
--  TerraFront — JOUR J, étape 3 : NOUVELLE ÉCHELLE DES RARETÉS (IRRÉVERSIBLE)
--  APRÈS la clôture (le palmarès de la saison 1 est compté avec l'ancienne
--  échelle). Ajoute les épiques, recalcule les numéros des cartes.
-- ===========================================================================
select * from rebasculer_paliers_s2(p_confirmer => true);
