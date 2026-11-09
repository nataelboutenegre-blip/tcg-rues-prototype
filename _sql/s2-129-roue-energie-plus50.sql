-- s2-129 (9/11/2026, lancé à 16 h 24) : énergie des cases de la roue du Front +50 %
-- (décision de Nataël, « ok let's go », 16 h 21). Petit éclair 3 -> 4, Éclair 5 -> 7, Gros éclair 10 -> 15,
-- Jackpot 12 -> 18 (lingots inchangés), Mixte 3 -> 4 (lingots inchangés). Poids inchangés.
-- Moyenne par tour : 2,0 -> 2,8 énergie. Le jeu lit les cases du serveur (rien à changer côté jeu).
-- Pour revenir en arrière : mêmes lignes avec 3, 5, 10, 12, 3.
update config_jeu c
   set valeur = jsonb_set(c.valeur::jsonb, '{cases}',
     (select jsonb_agg(case e->>'id'
                         when 'petit'   then e || '{"energie": 4}'::jsonb
                         when 'eclair'  then e || '{"energie": 7}'::jsonb
                         when 'gros'    then e || '{"energie": 15}'::jsonb
                         when 'jackpot' then e || '{"energie": 18}'::jsonb
                         when 'mixte'   then e || '{"energie": 4}'::jsonb
                         else e end order by n)
        from jsonb_array_elements(c.valeur::jsonb->'cases') with ordinality x(e, n)))::text
 where c.cle = 'roue_front';
