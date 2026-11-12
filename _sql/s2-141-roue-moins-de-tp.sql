-- s2-141 (12/11/2026, lancé 18 h 24 UTC) : roue du Front, moins de « 10 TerraPoints » (demande de Stonirr, 7 votes sur Discord).
-- 10 TP : 22 -> 12 ; Lingots (2) : 10 -> 15 ; Paquet Terra : 10 (au lieu de 5). Total toujours 100.
-- L'énergie donnée par la roue ne change pas (décision du 11/11 : on ne touche pas à l'énergie avant la clôture).
-- La roue dessine ses parts à partir de ces poids : rien à changer dans le jeu.
update config_jeu c set valeur = (
  select jsonb_set(c.valeur::jsonb, '{cases}', jsonb_agg(
    case e->>'id' when 'tp' then jsonb_set(e, '{poids}', '12') when 'lingots' then jsonb_set(e, '{poids}', '15') when 'terra' then jsonb_set(e, '{poids}', '10') else e end order by n))::text
  from jsonb_array_elements(c.valeur::jsonb -> 'cases') with ordinality x(e, n))
where c.cle = 'roue_front';
