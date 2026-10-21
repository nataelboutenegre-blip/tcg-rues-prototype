-- ===========================================================================
--  TerraFront — JOUR J, étape 1 : SIMULATION (ne modifie rien)
--  La clôture de la saison 1 et la nouvelle échelle des raretés, en mode
--  blanc. Envoyer les deux résultats à Claude avant l'étape 2.
-- ===========================================================================
select * from cloturer_saison('saison-1', 'saison-2', 'Saison 2', p_solde_depart => 100,
                               -- 45 % pile compte (décision du 21 octobre) : la fonction compare
                               -- en « strictement plus que » ; aucun département de moins de
                               -- 1 000 communes ne tombe entre 44,9999 et 45 %
                               p_seuil_terra => 44.9999);
