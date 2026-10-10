-- ===========================================================================
--  TerraFront — JOUR J, étape 2 : CLÔTURE DE LA SAISON 1 (IRRÉVERSIBLE)
--  À lancer seulement après la simulation validée (étape 1).
--  Palmarès figé (sans le compte Nataël), départements à plus de 45 % et
--  5 communes gardées versés en Terra, communes rendues au pot, soldes remis
--  à 0, Radar remis à zéro, garnisons et sièges vidés, saison 2 ouverte.
-- ===========================================================================
select * from cloturer_saison('saison-1', 'saison-2', 'Saison 2', p_confirmer => true);
