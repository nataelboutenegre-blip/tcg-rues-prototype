-- ===========================================================================
--  TerraFront — Outre-mer v1 : CHARGEMENT des 129 communes DOM
--  (Guadeloupe 971, Martinique 972, Guyane 973, La Réunion 974, Mayotte 976)
--
--  ⚠️  À LANCER SEULEMENT LE JOUR OÙ LE SITE EST PRÊT (vue carte Outre-mer,
--  cartes DOM, collection « /129 »). Dès cet insert, les DOM peuvent sortir
--  des paquets Terra (~1,5 % par carte) : sans le client à jour, les joueurs
--  tireraient des cartes que le site ne sait pas encore bien afficher.
--
--  Prérequis : s2-34-separation-outremer.sql (passé le 27/10, 9 × true).
--
--  Rareté option B, STATIQUE : classement à part dans les 129 (rang 1-129,
--  palier_total = 129), 1 légendaire par territoire. Jamais recalculée avec la
--  métropole (rebasculer_paliers* filtrent désormais la métropole).
--
--  Une seule transaction : tout passe ou rien. Rejouable (on conflict do
--  nothing). Finit par un contrôle.
-- ===========================================================================
begin;

insert into public.communes (code, nom, departement, tier, population, rang, palier_total, latitude, longitude)
values
  ('97101', 'Les Abymes', '971', 'legendaire', 51055, 11, 129, 16.2747, -61.49971),
  ('97102', 'Anse-Bertrand', '971', 'commun', 4412, 98, 129, 16.4672, -61.45898),
  ('97103', 'Baie-Mahault', '971', 'rare', 30924, 21, 129, 16.25262, -61.58985),
  ('97104', 'Baillif', '971', 'commun', 5096, 91, 129, 16.04681, -61.71719),
  ('97105', 'Basse-Terre', '971', 'peucommun', 9417, 64, 129, 16.0013, -61.72923),
  ('97106', 'Bouillante', '971', 'commun', 6127, 86, 129, 16.13961, -61.75926),
  ('97107', 'Capesterre-Belle-Eau', '971', 'peucommun', 17684, 36, 129, 16.05687, -61.6108),
  ('97108', 'Capesterre-de-Marie-Galante', '971', 'commun', 3123, 107, 129, 15.9183, -61.23537),
  ('97109', 'Gourbeyre', '971', 'commun', 7307, 74, 129, 15.99904, -61.68225),
  ('97110', 'La Désirade', '971', 'commun', 1306, 122, 129, 16.32207, -61.04846),
  ('97111', 'Deshaies', '971', 'commun', 3710, 104, 129, 16.30465, -61.77879),
  ('97112', 'Grand-Bourg', '971', 'commun', 4617, 96, 129, 15.90951, -61.28941),
  ('97113', 'Le Gosier', '971', 'rare', 27757, 22, 129, 16.22428, -61.47775),
  ('97114', 'Goyave', '971', 'commun', 7565, 72, 129, 16.12423, -61.61111),
  ('97115', 'Lamentin', '971', 'peucommun', 18628, 32, 129, 16.24634, -61.66647),
  ('97116', 'Morne-à-l''Eau', '971', 'peucommun', 16228, 38, 129, 16.31952, -61.46942),
  ('97117', 'Le Moule', '971', 'peucommun', 23014, 28, 129, 16.32202, -61.37386),
  ('97118', 'Petit-Bourg', '971', 'rare', 24665, 26, 129, 16.17212, -61.64917),
  ('97119', 'Petit-Canal', '971', 'commun', 8212, 70, 129, 16.3972, -61.44816),
  ('97120', 'Pointe-à-Pitre', '971', 'peucommun', 15040, 41, 129, 16.2317, -61.53303),
  ('97121', 'Pointe-Noire', '971', 'commun', 5762, 87, 129, 16.23001, -61.76285),
  ('97122', 'Port-Louis', '971', 'commun', 5607, 88, 129, 16.42257, -61.49808),
  ('97124', 'Saint-Claude', '971', 'peucommun', 10177, 60, 129, 16.03623, -61.69251),
  ('97125', 'Saint-François', '971', 'peucommun', 13942, 45, 129, 16.26956, -61.26339),
  ('97126', 'Saint-Louis', '971', 'commun', 2610, 111, 129, 15.96408, -61.27276),
  ('97128', 'Sainte-Anne', '971', 'peucommun', 23973, 27, 129, 16.25464, -61.39598),
  ('97129', 'Sainte-Rose', '971', 'peucommun', 17700, 35, 129, 16.298, -61.70001),
  ('97130', 'Terre-de-Bas', '971', 'commun', 873, 124, 129, 15.85535, -61.63211),
  ('97131', 'Terre-de-Haut', '971', 'commun', 1463, 121, 129, 15.86718, -61.58412),
  ('97132', 'Trois-Rivières', '971', 'commun', 7415, 73, 129, 15.98489, -61.65121),
  ('97133', 'Vieux-Fort', '971', 'commun', 1674, 116, 129, 15.95962, -61.69342),
  ('97134', 'Vieux-Habitants', '971', 'commun', 7077, 78, 129, 16.08559, -61.72299),
  ('97201', 'L''Ajoupa-Bouillon', '972', 'commun', 1682, 115, 129, 14.81487, -61.12704),
  ('97202', 'Les Anses-d''Arlet', '972', 'commun', 3912, 102, 129, 14.49808, -61.07315),
  ('97203', 'Basse-Pointe', '972', 'commun', 2852, 109, 129, 14.83781, -61.12561),
  ('97204', 'Le Carbet', '972', 'commun', 3721, 103, 129, 14.71139, -61.15703),
  ('97205', 'Case-Pilote', '972', 'commun', 4537, 97, 129, 14.65663, -61.12607),
  ('97206', 'Le Diamant', '972', 'commun', 6161, 85, 129, 14.48773, -61.01945),
  ('97207', 'Ducos', '972', 'peucommun', 18105, 33, 129, 14.57553, -60.96558),
  ('97208', 'Fonds-Saint-Denis', '972', 'commun', 640, 125, 129, 14.72719, -61.11667),
  ('97209', 'Fort-de-France', '972', 'legendaire', 75506, 5, 129, 14.64203, -61.07015),
  ('97210', 'Le François', '972', 'peucommun', 15778, 40, 129, 14.61204, -60.89953),
  ('97211', 'Grand''Rivière', '972', 'commun', 487, 126, 129, 14.8484, -61.17948),
  ('97212', 'Gros-Morne', '972', 'peucommun', 9610, 62, 129, 14.7095, -61.02404),
  ('97213', 'Le Lamentin', '972', 'rare', 39400, 12, 129, 14.62048, -60.99808),
  ('97214', 'Le Lorrain', '972', 'commun', 6566, 80, 129, 14.79971, -61.0752),
  ('97215', 'Macouba', '972', 'commun', 987, 123, 129, 14.85086, -61.1529),
  ('97216', 'Le Marigot', '972', 'commun', 2948, 108, 129, 14.77572, -61.05283),
  ('97217', 'Le Marin', '972', 'commun', 8486, 67, 129, 14.48135, -60.85951),
  ('97218', 'Le Morne-Rouge', '972', 'commun', 4388, 99, 129, 14.76771, -61.12249),
  ('97219', 'Le Prêcheur', '972', 'commun', 1479, 120, 129, 14.82313, -61.20076),
  ('97220', 'Rivière-Pilote', '972', 'peucommun', 11604, 50, 129, 14.50921, -60.89798),
  ('97221', 'Rivière-Salée', '972', 'peucommun', 11829, 49, 129, 14.52736, -60.96537),
  ('97222', 'Le Robert', '972', 'peucommun', 21553, 29, 129, 14.67517, -60.92915),
  ('97223', 'Saint-Esprit', '972', 'peucommun', 10322, 56, 129, 14.56186, -60.92581),
  ('97224', 'Saint-Joseph', '972', 'peucommun', 16258, 37, 129, 14.67807, -61.04433),
  ('97225', 'Saint-Pierre', '972', 'commun', 3961, 101, 129, 14.76782, -61.16739),
  ('97226', 'Sainte-Anne', '972', 'commun', 4306, 100, 129, 14.43666, -60.85364),
  ('97227', 'Sainte-Luce', '972', 'peucommun', 9410, 65, 129, 14.48555, -60.9446),
  ('97228', 'Sainte-Marie', '972', 'peucommun', 14756, 42, 129, 14.76868, -61.01291),
  ('97229', 'Schœlcher', '972', 'peucommun', 19478, 31, 129, 14.65141, -61.10115),
  ('97230', 'La Trinité', '972', 'peucommun', 11454, 52, 129, 14.74198, -60.94008),
  ('97231', 'Les Trois-Îlets', '972', 'commun', 6507, 82, 129, 14.53478, -61.03705),
  ('97232', 'Le Vauclin', '972', 'commun', 8483, 68, 129, 14.54448, -60.85036),
  ('97233', 'Le Morne-Vert', '972', 'commun', 1718, 114, 129, 14.70316, -61.13618),
  ('97234', 'Bellefontaine', '972', 'commun', 1746, 113, 129, 14.67799, -61.147),
  ('97301', 'Régina', '973', 'commun', 1658, 118, 129, 4.07141, -52.41236),
  ('97302', 'Cayenne', '973', 'legendaire', 62675, 7, 129, 4.92491, -52.31187),
  ('97303', 'Iracoubo', '973', 'commun', 1662, 117, 129, 5.23868, -53.32753),
  ('97304', 'Kourou', '973', 'rare', 24824, 25, 129, 4.88805, -52.78356),
  ('97305', 'Macouria', '973', 'peucommun', 19899, 30, 129, 4.96815, -52.50396),
  ('97306', 'Mana', '973', 'peucommun', 10957, 55, 129, 5.01109, -53.68979),
  ('97307', 'Matoury', '973', 'rare', 36512, 17, 129, 4.83142, -52.35357),
  ('97308', 'Saint-Georges', '973', 'commun', 4915, 95, 129, 3.82804, -52.03398),
  ('97309', 'Remire-Montjoly', '973', 'rare', 27723, 23, 129, 4.88521, -52.28525),
  ('97310', 'Roura', '973', 'commun', 3449, 106, 129, 4.47457, -52.50279),
  ('97311', 'Saint-Laurent-du-Maroni', '973', 'epique', 54429, 10, 129, 4.95739, -53.96873),
  ('97312', 'Sinnamary', '973', 'commun', 2756, 110, 129, 5.20504, -53.03021),
  ('97313', 'Montsinéry-Tonnegrande', '973', 'commun', 3626, 105, 129, 4.82243, -52.48851),
  ('97314', 'Ouanary', '973', 'commun', 150, 129, 129, 4.16258, -51.83398),
  ('97352', 'Saül', '973', 'commun', 277, 127, 129, 3.88359, -53.44402),
  ('97353', 'Maripasoula', '973', 'peucommun', 9579, 63, 129, 2.89906, -53.87543),
  ('97356', 'Camopi', '973', 'commun', 2189, 112, 129, 2.82927, -52.70645),
  ('97357', 'Grand-Santi', '973', 'peucommun', 9668, 61, 129, 4.37799, -54.13813),
  ('97358', 'Saint-Élie', '973', 'commun', 159, 128, 129, 4.59061, -53.06725),
  ('97360', 'Apatou', '973', 'peucommun', 10306, 57, 129, 4.83238, -54.22469),
  ('97361', 'Awala-Yalimapo', '973', 'commun', 1577, 119, 129, 5.67339, -53.9278),
  ('97362', 'Papaichton', '973', 'commun', 5006, 94, 129, 4.05634, -54.01848),
  ('97401', 'Les Avirons', '974', 'peucommun', 11536, 51, 129, -21.20729, 55.36088),
  ('97402', 'Bras-Panon', '974', 'peucommun', 13012, 48, 129, -21.0291, 55.61549),
  ('97403', 'Entre-Deux', '974', 'commun', 7176, 77, 129, -21.2085, 55.49272),
  ('97404', 'L''Étang-Salé', '974', 'peucommun', 14464, 43, 129, -21.24067, 55.36675),
  ('97405', 'Petite-Île', '974', 'peucommun', 13067, 47, 129, -21.33476, 55.57235),
  ('97406', 'La Plaine-des-Palmistes', '974', 'commun', 6936, 79, 129, -21.15626, 55.62799),
  ('97407', 'Le Port', '974', 'rare', 33969, 19, 129, -20.93929, 55.29877),
  ('97408', 'La Possession', '974', 'rare', 36568, 16, 129, -21.0074, 55.40595),
  ('97409', 'Saint-André', '974', 'epique', 58885, 8, 129, -20.96378, 55.63237),
  ('97410', 'Saint-Benoît', '974', 'rare', 38604, 14, 129, -21.09223, 55.6361),
  ('97411', 'Saint-Denis', '974', 'legendaire', 155634, 1, 129, -20.944, 55.44969),
  ('97412', 'Saint-Joseph', '974', 'rare', 39207, 13, 129, -21.30903, 55.64019),
  ('97413', 'Saint-Leu', '974', 'rare', 36163, 18, 129, -21.17089, 55.33478),
  ('97414', 'Saint-Louis', '974', 'epique', 54941, 9, 129, -21.22539, 55.41849),
  ('97415', 'Saint-Paul', '974', 'epique', 108088, 2, 129, -21.05686, 55.34843),
  ('97416', 'Saint-Pierre', '974', 'epique', 85038, 3, 129, -21.31005, 55.51885),
  ('97417', 'Saint-Philippe', '974', 'commun', 5082, 92, 129, -21.3256, 55.73877),
  ('97418', 'Sainte-Marie', '974', 'rare', 37093, 15, 129, -20.95423, 55.52526),
  ('97419', 'Sainte-Rose', '974', 'commun', 6557, 81, 129, -21.17214, 55.7581),
  ('97420', 'Sainte-Suzanne', '974', 'rare', 25551, 24, 129, -20.95201, 55.59034),
  ('97421', 'Salazie', '974', 'commun', 7268, 75, 129, -21.04633, 55.51586),
  ('97422', 'Le Tampon', '974', 'epique', 82579, 4, 129, -21.2168, 55.56477),
  ('97423', 'Les Trois-Bassins', '974', 'commun', 7221, 76, 129, -21.11154, 55.33262),
  ('97424', 'Cilaos', '974', 'commun', 5040, 93, 129, -21.13846, 55.45736),
  ('97601', 'Acoua', '976', 'commun', 5192, 90, 129, -12.72359, 45.05015),
  ('97602', 'Bandraboua', '976', 'peucommun', 13989, 44, 129, -12.71216, 45.12457),
  ('97603', 'Bandrele', '976', 'peucommun', 10282, 58, 129, -12.94432, 45.18586),
  ('97604', 'Bouéni', '976', 'commun', 6189, 84, 129, -12.92408, 45.09415),
  ('97605', 'Chiconi', '976', 'commun', 8295, 69, 129, -12.82347, 45.10646),
  ('97606', 'Chirongui', '976', 'peucommun', 8920, 66, 129, -12.9153, 45.14475),
  ('97607', 'Dembeni', '976', 'peucommun', 15848, 39, 129, -12.84743, 45.19368),
  ('97608', 'Dzaoudzi', '976', 'peucommun', 17831, 34, 129, -12.77981, 45.27795),
  ('97609', 'Kani-Kéli', '976', 'commun', 5507, 89, 129, -12.98112, 45.12234),
  ('97610', 'Koungou', '976', 'rare', 32156, 20, 129, -12.73473, 45.19189),
  ('97611', 'Mamoudzou', '976', 'legendaire', 71437, 6, 129, -12.78263, 45.22358),
  ('97612', 'Mtsamboro', '976', 'commun', 7705, 71, 129, -12.67544, 45.08372),
  ('97613', 'M''Tsangamouji', '976', 'commun', 6432, 83, 129, -12.76102, 45.07732),
  ('97614', 'Ouangani', '976', 'peucommun', 10203, 59, 129, -12.84358, 45.13974),
  ('97615', 'Pamandzi', '976', 'peucommun', 11442, 53, 129, -12.79856, 45.28605),
  ('97616', 'Sada', '976', 'peucommun', 11156, 54, 129, -12.86164, 45.11389),
  ('97617', 'Tsingoni', '976', 'peucommun', 13934, 46, 129, -12.78876, 45.10559)
on conflict (code) do nothing;

commit;

-- Contrôle 1 : les DOM par rareté — attendu legendaire 5, epique 6, rare 15, peucommun 40, commun 63 (total 129)
select tier, count(*) as dom
  from public.communes where length(departement) = 3
 group by tier
 order by array_position(array['legendaire','epique','rare','peucommun','commun'], tier);

-- Contrôle 2 : la métropole n'a pas bougé — attendu 34739 communes, 302 légendaires, 1013 épiques
select sum(total) as communes_metropole,
       sum(total) filter (where tier = 'legendaire') as legendaires,
       sum(total) filter (where tier = 'epique') as epiques
  from public.totaux_paliers();
