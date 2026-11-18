-- ===========================================================================
--  s3-25 (18/11/2026) — le Mess donne deux fois plus d'énergie (421 et Recensement)
--  Mesure du 15-17/11 : 13 à 20 joueurs font des duels classés par jour, médiane
--  ~15 tickets, 2 à 4 au plafond de 30. Avec les lots du 17/11, un ticket rapporte
--  ~0,37 ⚡ (421) : ~5 ⚡/jour pour un joueur médian, 11 au plus — la ration de
--  25 ⚡/jour n'était jamais atteinte. Décision de Nataël (18/11, 16 h 02, « option 2
--  et on avisera ») : un joueur actif gagne de l'énergie en jouant → énergie des lots
--  ×2. Attendu : ~10 ⚡/jour médiane, ~22 au plus (ration 25 ⚡ et 6 lingots inchangée).
--
--  421 : 421 du premier coup 1 paquet Terra + 5 → 10 ⚡ ; 421 en relançant 3 → 6 ;
--        trois as 6 → 12 ; autre brelan 3 → 6 ; suite 15 TP (inchangée).
--  Recensement : gagné 3 → 6 ⚡ (+30 TP +1 lingot inchangés) ; parfait 6 → 12 ⚡
--        (+1 paquet Terra +2 lingots inchangés).
--  Machine à chiffrer : inchangée.
--  Retour arrière : remettre 5 / 3 / 6 / 3 et 3 / 6.
--  Contrôle attendu (dernière ligne) : 10 | 6 | 12 | 6 | 6 | 12
-- ===========================================================================

update public.config_jeu
   set valeur = (
     jsonb_set(jsonb_set(jsonb_set(jsonb_set(jsonb_set(jsonb_set(valeur::jsonb,
       '{des,lots,421sec,energie}', '10'),
       '{des,lots,421,energie}', '6'),
       '{des,lots,as,energie}', '12'),
       '{des,lots,brelan,energie}', '6'),
       '{recensement,lots,gagne,energie}', '6'),
       '{recensement,lots,parfait,energie}', '12')
   )::text
 where cle = 'mess';

-- Contrôle
select (v #>> '{des,lots,421sec,energie}')::int as d421sec, (v #>> '{des,lots,421,energie}')::int as d421,
       (v #>> '{des,lots,as,energie}')::int as das, (v #>> '{des,lots,brelan,energie}')::int as dbrelan,
       (v #>> '{recensement,lots,gagne,energie}')::int as rgagne, (v #>> '{recensement,lots,parfait,energie}')::int as rparfait
  from (select valeur::jsonb v from config_jeu where cle = 'mess') x;
