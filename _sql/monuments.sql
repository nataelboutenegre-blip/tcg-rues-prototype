-- ===========================================================================
--  TerraFront — Les emblemes : un lieu connu par commune
--
--  L'IDEE
--    Une commune qui abrite un lieu connu porte son embleme. Celui qui possede
--    la commune possede l'embleme ; celui qui la lui prend le prend avec.
--
--    Ca donne enfin une raison de vouloir une commune PRECISE. Aujourd'hui une
--    commune vaut par sa population ; avec ca, Millau vaut parce qu'il y a le
--    viaduc. Et ca ne sort aucune carte du pot : c'est une couche posee sur ce
--    qui existe deja, pas une economie de plus.
--
--  D'OU VIENT LA LISTE
--    Wikidata, filtree par le nombre de versions linguistiques de la page
--    Wikipedia — a peu pres la definition de « tout le monde connait ». Seuil
--    retenu : 20 langues. Un seul embleme par commune, le plus connu.
--
--    248 emblemes, 78 departements. Paris n'en represente que 8 %, parce que
--    la regle d'un par commune ramene ses 631 lieux a 20 arrondissements.
--
--  CE QUI A ETE ECARTE A LA MAIN
--    Dix entrees etaient des attentats, des tueries et un crime de guerre —
--    Wikidata les classe comme des lieux puisqu'elles ont des coordonnees.
--    Un drame n'est pas une carte a collectionner. Egalement ecartes : gares,
--    aeroports, universites, hopitaux, stations de metro, entreprises.
--
--  CE FICHIER NE TOUCHE A RIEN D'EXISTANT
--    Il cree une table et une fonction. Aucune table du jeu n'est modifiee.
-- ===========================================================================


create table if not exists public.monuments (
  commune_code text primary key references public.communes(code),
  nom          text not null,
  type         text,
  langues      integer,          -- versions linguistiques : la mesure de notoriete
  image        text,             -- nom du fichier sur Wikimedia Commons
  wikidata     text,
  photo        text              -- rempli plus tard, comme communes.photo
);

comment on table public.monuments is
  'Un lieu connu par commune. Le proprietaire de la commune possede l''embleme.';

-- Lecture pour tous les joueurs : le catalogue doit etre visible, y compris
-- ce qu'on ne possede pas. C'est meme tout l'interet.
alter table public.monuments enable row level security;
drop policy if exists monuments_lecture on public.monuments;
create policy monuments_lecture on public.monuments for select using (true);
grant select on public.monuments to anon, authenticated;


-- ---------------------------------------------------------------------------
--  Les 248 emblemes
--
--  On passe par une table temporaire : certains codes INSEE peuvent ne pas
--  exister dans communes (communes fusionnees, outre-mer). Plutot que de faire
--  echouer tout le fichier sur une cle etrangere, on insere ce qui correspond
--  et on compte le reste.
-- ---------------------------------------------------------------------------
-- Pas de « on commit drop » : l'editeur SQL execute chaque instruction dans sa
-- propre transaction, la table disparaitrait avant qu'on s'en serve. Elle est
-- temporaire, donc elle s'efface toute seule a la fin de la session.
create temporary table if not exists lot_monuments (
  commune_code text, nom text, type text, langues integer, image text, wikidata text
);
truncate lot_monuments;

insert into lot_monuments (commune_code, nom, type, langues, image, wikidata) values
  ('75107', 'tour Eiffel', 'tour d''observation', 191, 'Tour Eiffel Wikimedia Commons.jpg', 'Q243'),
  ('74236', 'mont Blanc', 'montagne', 127, 'Panorama of Mont Blanc du Tacul, Mont Maudit and Mont Blanc from Aiguille du Midi, Chamonix, Haute-Savoie.jpg', 'Q583'),
  ('75104', 'cathédrale Notre-Dame de Paris', 'basilique mineure', 125, 'Notre-Dame de Paris 2013-07-24.jpg', 'Q2981'),
  ('78646', 'château de Versailles', 'palais', 109, 'Vue aérienne du domaine de Versailles par ToucanWings - Creative Commons By Sa 3.0 - 083.jpg', 'Q2946'),
  ('49219', 'château de Montsoreau', 'palais', 100, 'Chateau de Montsoreau Museum of contemporary art Loire Valley France.jpg', 'Q1143049'),
  ('75113', 'Bibliothèque nationale de France', 'bibliothèque nationale', 91, 'Bibliothèque Mitterrand Mai 2022.jpg', 'Q193563'),
  ('75117', 'arc de triomphe de l''Étoile', 'arc de triomphe', 85, 'Arc de Triomphe - Août 2026.jpg', 'Q64436'),
  ('12145', 'viaduc de Millau', 'pont à haubans', 74, '00 0237 Millau - Département Aveyron.jpg', 'Q99236'),
  ('28085', 'cathédrale Notre-Dame de Chartres', 'basilique mineure', 73, 'Westfassade Chartres.jpg', 'Q180274'),
  ('93066', 'stade de France', 'stade', 72, 'StadeFranceNationsLeague2018.jpg', 'Q13205'),
  ('75120', 'cimetière du Père-Lachaise', 'cimetière', 71, 'Main gate of the Père-Lachaise Cemetery, Paris 13 June 2014.jpg', 'Q311'),
  ('75116', 'Parc des Princes', 'stade multifonction', 70, 'Paris Parc des Princes 1.jpg', 'Q193431'),
  ('24291', 'grotte de Lascaux', 'grotte ornée', 69, 'Lascaux painting.jpg', 'Q172125'),
  ('75108', 'palais de l''Élysée', 'résidence officielle', 66, 'Secretary Pompeo Arrives to Meet with French Foreign Minister Le Drian in Paris (50610423656) (cropped).jpg', 'Q188190'),
  ('75118', 'Montmartre', 'colline', 65, 'View from Notre-Dame de Paris, 24 June 2014 004.jpg', 'Q186115'),
  ('14047', 'Tapisserie de Bayeux', 'broderie', 64, 'Bayeux Tapestry scene1 EDWARD REX.jpg', 'Q187483'),
  ('51454', 'cathédrale Notre-Dame de Reims', 'cathédrale catholique', 60, 'Reims Cathedral 016 8341.jpg', 'Q206823'),
  ('75105', 'Panthéon', 'église', 60, 'Panthéon, Paris 25 March 2012.jpg', 'Q188856'),
  ('07330', 'grotte Chauvet', 'grotte ornée', 59, 'Rhinocéros grotte Chauvet.jpg', 'Q374096'),
  ('30346', 'pont du Gard', 'pont en arc', 59, 'Pont du Gard BLS.jpg', 'Q189764'),
  ('77449', 'Disneyland Paris', 'parc d''attractions', 58, 'Disneyland Park 05, Paris 22 August 2013.jpg', 'Q206521'),
  ('75101', 'Sainte-Chapelle', 'chapelle', 57, 'Paris Sainte Chapelle East View 02.JPG', 'Q193193'),
  ('80021', 'cathédrale Notre-Dame d''Amiens', 'personnalité juridique', 57, '0 Amiens - Cathédrale Notre-Dame (1).JPG', 'Q106934'),
  ('13099', 'ITER', 'tokamak', 56, 'ITER site 2018 aerial view (41809720041).jpg', 'Q191788'),
  ('13208', 'stade Vélodrome', 'stade', 56, 'Stade Vélodrome closeup.jpg', 'Q202150'),
  ('77186', 'château de Fontainebleau', 'musée', 56, 'Le Grand Escalier à Fer de Cheval.jpg', 'Q201428'),
  ('41034', 'château de Chambord', 'château', 55, 'France Loir-et-Cher Chambord Chateau 03.jpg', 'Q205367'),
  ('75103', 'musée des Arts et Métiers', 'musée scientifique', 53, 'Musée des Arts et Métiers 337.jpg', 'Q1538826'),
  ('76540', 'musée maritime fluvial et portuaire de Rouen', 'musée maritime', 53, 'Eingang zum Musee-maritime-de-rouen.jpg', 'Q104314'),
  ('97304', 'centre spatial guyanais', 'base de lancement', 52, 'Ariane 5ECA on its launch platform on its way to lauch pad ELA-3.jpg', 'Q308987'),
  ('18033', 'cathédrale Saint-Étienne de Bourges', 'cathédrale catholique', 51, 'Bourges-Kathedrale-110-2008-gje.jpg', 'Q207985'),
  ('67482', 'cathédrale Notre-Dame de Strasbourg', 'cathédrale catholique', 51, 'Strasbourg Cathedral Exterior - Diliff.jpg', 'Q745460'),
  ('71137', 'abbaye de Cluny', 'abbaye', 51, 'Cluny-Abtei-Ostfluegel-mtob.jpg', 'Q220301'),
  ('75106', 'jardin du Luxembourg', 'jardin public', 51, 'Jardin du Luxembourg.JPG', 'Q309458'),
  ('42218', 'stade Geoffroy-Guichard', 'stade multifonction', 49, 'AS Saint-Étienne v Olympique Lyonnais, 10 November 2013.jpg', 'Q861000'),
  ('69275', 'Parc Olympique lyonnais', 'stade de football', 49, 'Stade Lumière.jpg', 'Q8507'),
  ('75115', 'Tour Montparnasse', 'gratte-ciel', 48, 'Remote view of the Tour Montparnasse & Eiffel Tower in 2005.jpg', 'Q323767'),
  ('59009', 'stade Pierre-Mauroy', 'stade multifonction', 47, 'Finale Coupe Davis 2017 Pouille Goffin.jpg', 'Q1410402'),
  ('75112', 'bois de Vincennes', 'forêt', 47, 'Bois de Vincennes DSC03761.JPG', 'Q271639'),
  ('75114', 'cimetière du Montparnasse', 'cimetière', 47, 'Cimetière du Montparnasse, 3 boulevard Edgar-Quinet, Paris 14e.jpg', 'Q272208'),
  ('37110', 'château de Chenonceau', 'château', 46, 'Chenonceau-20050320.jpg', 'Q193215'),
  ('84007', 'palais des papes', 'palais', 46, '00 0711 Avignon (Frankreich) - Kathetrale und Papstpalast.jpg', 'Q143463'),
  ('33063', 'Stade Atlantique', 'stade multifonction', 45, '500px photo (165733217).jpeg', 'Q252481'),
  ('62498', 'stade Bollaert-Delelis', 'stade', 45, 'Stade Bollaert Delelis.JPG', 'Q854122'),
  ('06088', 'Allianz Riviera', 'installation sportive', 44, 'Allianzcoupdenvoi.jpg', 'Q127372'),
  ('97302', 'île du Diable', 'île', 44, 'Île du Diable depuis l''île Royale.jpg', 'Q220385'),
  ('17093', 'île d''Oléron', 'île', 43, 'Île d''Oléron aerial view.jpg', 'Q292568'),
  ('31555', 'Stadium municipal de Toulouse', 'stade de football', 43, 'StadiumToulouse3.JPG', 'Q738044'),
  ('75111', 'Bataclan', 'théâtre', 43, 'Bataclan - Paris (3448973995).jpg', 'Q810700'),
  ('16102', 'Hennessy', 'distillerie', 42, 'Hennesy XO close.jpg', 'Q1229287'),
  ('30189', 'maison carrée', 'site archéologique', 42, 'Maison Carree in Nimes (16).jpg', 'Q677659'),
  ('63263', 'puy de Dôme', 'dôme de lave', 42, 'Aerial image of Puy de Dôme (view from the west).jpg', 'Q607372'),
  ('64260', 'île des Faisans', 'île fluviale', 42, 'Irun - Isla de los Faisanes sobre el río Bisasoa 01.jpg', 'Q373767'),
  ('74056', 'aiguille du Midi', 'montagne', 42, 'Aiguille-du-Midi-summer.jpg', 'Q404728'),
  ('91534', 'Paris-Saclay', 'entité territoriale administrative', 42, 'Campus Ecole polytechnique de palaiseau.jpg', 'Q251665'),
  ('17019', 'île de Ré', 'île', 41, 'Ré SPOT 1156.jpg', 'Q292384'),
  ('41018', 'château de Blois', 'château', 41, 'Loire Cher Blois1 tango7174.jpg', 'Q4055'),
  ('77269', 'château de Vaux-le-Vicomte', 'château', 41, '0 Maincy - Château de Vaux-le-Vicomte (2).JPG', 'Q739976'),
  ('78172', 'assassinat de Samuel Paty', 'homicide', 41, '2020-10-21 12-05-53 rassemblement-Belfort.jpg', 'Q100437698'),
  ('94080', 'château de Vincennes', 'château fort', 41, 'Château de Vincennes Paris FRA 002.jpg', 'Q663673'),
  ('89446', 'basilique Sainte-Marie-Madeleine', 'monastère', 40, 'Vezelay-7776-Bearbeitet.jpg', 'Q217452'),
  ('21389', 'abbaye de Fontenay', 'monastère', 39, 'Abbaye de Fontenay R01.jpg', 'Q464918'),
  ('44109', 'stade de la Beaujoire', 'stade', 39, 'Stade de la Beaujoire.jpg', 'Q1053455'),
  ('69387', 'stade de Gerland', 'stade multifonction', 39, 'Matmut stadium de gerland.jpg', 'Q1980'),
  ('70451', 'chapelle Notre-Dame-du-Haut de Ronchamp', 'église', 39, 'RonchampsBruxelles.jpg', 'Q638250'),
  ('75056', 'Celine', 'maison de haute couture', 39, 'Madrid - Celine (Calle de José Ortega y Gasset 16).jpg', 'Q948531'),
  ('75109', 'Folies Bergère', 'théâtre', 39, 'Folies Bergère, Paris 6 February 2016.jpg', 'Q330375'),
  ('84087', 'théâtre antique d''Orange', 'théâtre romain', 39, 'Le Théâtre Antique d''Orange, 2007.jpg', 'Q958961'),
  ('97110', 'La Désirade', 'île', 39, 'Pano Désirade.jpg', 'Q1024682'),
  ('11069', 'cité de Carcassonne', 'forteresse', 38, 'Cité de Carcassonne.jpg', 'Q389269'),
  ('37003', 'château d''Amboise', 'château', 38, '00 1292 Château d''Amboise.jpg', 'Q389908'),
  ('83035', 'circuit Paul-Ricard', 'circuit de sport mécanique', 38, 'Circuit Paul Ricard CPR.jpg', 'Q171424'),
  ('97417', 'Piton de la Fournaise', 'sommet', 38, 'Piton de La Fournaise - Paysage de l''île de La Réunion.jpg', 'Q1049644'),
  ('34172', 'stade de la Mosson', 'stade', 37, 'Australie-Fidji.4.JPG', 'Q815833'),
  ('56258', 'alignements de Carnac', 'site archéologique', 37, 'France-Carnac-Alignement de Kermario.jpg', 'Q833850'),
  ('60057', 'cathédrale Saint-Pierre de Beauvais', 'cathédrale catholique', 37, 'Beauvais Cathedral Exterior 1, Picardy, France - Diliff.jpg', 'Q513300'),
  ('93013', 'Salon du Bourget', 'foire commerciale dans l''aérien', 37, 'Paris Air Show 2007 01.jpg', 'Q174352'),
  ('14333', 'pont de Normandie', 'pont', 36, 'Sandouville - 76430 - 2024.07.04 - Johnsons - Yutong TC9 © Anthony Levrot.jpg', 'Q504710'),
  ('38191', 'Alpe d''Huez', 'station de sports d''hiver', 36, 'View of central Alpe d''Huez from Côtes Souveraines, Huez, 2026.jpg', 'Q214364'),
  ('76351', 'pont de Normandie', 'pont', 36, 'Sandouville - 76430 - 2024.07.04 - Johnsons - Yutong TC9 © Anthony Levrot.jpg', 'Q504710'),
  ('33529', 'Dune du Pilat', 'dune', 35, 'Sommet de la Dune du Pilat.jpg', 'Q501726'),
  ('78551', 'château de Saint-Germain-en-Laye', 'château', 35, 'Château de Saint-Germain-en-Laye01.jpg', 'Q1520841'),
  ('86246', 'abbaye de Saint-Savin-sur-Gartempe', 'église abbatiale', 35, 'Saint-Savin abbaye (3).jpg', 'Q1774129'),
  ('06152', 'Sophia Antipolis', 'établissement humain', 34, 'Sophia Antipolis.jpg', 'Q1359930'),
  ('25021', 'saline royale d''Arc-et-Senans', 'saline', 34, 'Koenigliche Saline in Arc-et-Senans Bild1 800px.jpg', 'Q649055'),
  ('50509', 'Utah Beach', 'plage', 34, 'Landings on Omaha beach.jpg', 'Q757273'),
  ('56152', 'Belle-Île-en-Mer', 'île', 34, 'ArGerveur.jpg', 'Q815838'),
  ('58152', 'circuit de Nevers Magny-Cours', 'circuit de sport mécanique', 34, 'Magnycourt1new.jpg', 'Q172876'),
  ('63236', 'puy de Sancy', 'volcan éteint', 34, 'Puy de Sancy 2016-08-23 n18.jpg', 'Q778597'),
  ('74299', 'lac d''Annecy', 'lac glaciaire', 34, 'Aerial image of Lake Annecy (view from the south).jpg', 'Q576704'),
  ('02408', 'cathédrale Notre-Dame de Laon', 'cathédrale catholique', 33, 'Laon, Cathédrale Notre-Dame PM 14294.jpg', 'Q585947'),
  ('05152', 'parc national des Écrins', 'parc national', 33, 'Villar-d''Arêne (Rif de la Planche 1975 m.).JPG', 'Q476446'),
  ('17004', 'fort Boyard', 'fortification maritime', 33, 'Fort Boyard (51269094270).jpg', 'Q92089'),
  ('21008', 'site archéologique d''Alésia', 'oppidum', 33, 'Vue aérienne vestiges Alésia.jpg', 'Q835966'),
  ('35238', 'Roazhon Park', 'installation sportive', 33, 'Staderennais-routelorient.JPG', 'Q1121760'),
  ('38237', 'parc national des Écrins', 'parc national', 33, 'Villar-d''Arêne (Rif de la Planche 1975 m.).JPG', 'Q476446'),
  ('49140', 'abbaye de Fontevraud', 'monastère double', 33, 'Fontevraud3.jpg', 'Q283254'),
  ('54395', 'place Stanislas', 'place', 33, 'Vue de nuit de la Place Stanislas à Nancy.jpg', 'Q426064'),
  ('83069', 'îles d''Hyères', 'archipel', 33, 'Porquerolles, Îles d''Hyères.JPG', 'Q292728'),
  ('85113', 'île d''Yeu', 'île', 33, 'Île d''Yeu.png', 'Q1970151'),
  ('33544', 'phare de Cordouan', 'phare', 32, 'Phare de Cordouan 32.jpg', 'Q199234'),
  ('37014', 'château d''Azay-le-Rideau', 'château', 32, '0 1157 Château d´Azay-le-Rideau.jpg', 'Q113389'),
  ('85083', 'île de Noirmoutier', 'île', 32, 'Noirmoutier Island SPOT 1275.jpg', 'Q292346'),
  ('01071', 'Compact Muon Solenoid', 'équipe de recherche', 31, 'CMS Under Construction Apr 05.jpg', 'Q659478'),
  ('37272', 'château de Villandry', 'château', 31, 'Château de Villandry aile droite.JPG', 'Q477613'),
  ('73227', 'Courchevel', 'station de sports d''hiver', 31, 'Courchevel dent du Villard.jpg', 'Q290817'),
  ('92026', 'tour First', 'gratte-ciel', 31, 'Tours First et Saint-Gobain (42975144462).jpg', 'Q1509747'),
  ('97124', 'Soufrière', 'montagne', 31, 'Guadeloupe 114 - Sommet de la Soufrière 1467m - Guadeloupe.jpg', 'Q1149310'),
  ('97421', 'piton des Neiges', 'montagne', 31, 'Piton des Neiges1.JPG', 'Q1545452'),
  ('14204', 'Pointe du Hoc', 'rempart montagneux', 30, 'Geological Pointe du Hoc Calvados, France.jpg', 'Q284649'),
  ('25056', 'synagogue de Besançon', 'synagogue', 30, 'Besançon Synagogue 62.JPG', 'Q1141086'),
  ('37072', 'forteresse royale de Chinon', 'château fort', 30, 'Château de Chinon vu de la Vienne.jpg', 'Q912447'),
  ('58128', 'Bibracte', 'musée', 30, 'Bibracte (Mont Beuvray) 17.jpg', 'Q650053'),
  ('60141', 'château de Chantilly', 'château', 30, 'Chateau de Chantilly FRA 003.JPG', 'Q766938'),
  ('71440', 'Bibracte', 'musée', 30, 'Bibracte (Mont Beuvray) 17.jpg', 'Q650053'),
  ('72181', 'circuit des 24 Heures', 'circuit de sport mécanique', 30, 'Circuit de la Sarthe Ford Chicanes.jpg', 'Q174090'),
  ('73285', 'col du Petit-Saint-Bernard', 'col routier', 30, 'Route et hospice du col du Petit-Saint-Bernard en été (août 2019).JPG', 'Q1345705'),
  ('81004', 'cathédrale Sainte-Cécile d''Albi', 'basilique mineure', 30, 'Albi Sainte-Cécile.JPG', 'Q94744'),
  ('92050', 'Plenitude Arena', 'stade', 30, 'France 98 v FIFA 98, 12 June 2018 (1).jpg', 'Q2860806'),
  ('10426', 'abbaye de Clairvaux', 'abbaye', 29, 'Abbaye de Clairvaux (6).JPG', 'Q647070'),
  ('13206', 'basilique Notre-Dame-de-la-Garde', 'église', 29, 'Notre Dame de la Garde 守護聖母院 - panoramio (1).jpg', 'Q975925'),
  ('21564', 'abbaye de Cîteaux', 'abbaye', 29, 'Abbaye de Cîteaux La Bibliothèque.JPG', 'Q843261'),
  ('49007', 'Château d''Angers', 'château', 29, '00 2521Angers - Schloss (Frankreich).jpg', 'Q1048155'),
  ('67314', 'camp de concentration de Natzweiler-Struthof', 'camp de concentration', 29, 'Natzweiler-Struthof.jpg', 'Q639319'),
  ('69123', 'musée des Beaux-Arts de Lyon', 'musée d''art', 29, 'Facade Musee des Beaux-Arts de Lyon n02.jpg', 'Q511'),
  ('78498', 'villa Savoye', 'villa', 29, '', 'Q940746'),
  ('04106', 'voie Domitienne', 'voie romaine', 28, 'Ambrussum voies marquées 10-04-2006.jpg', 'Q1146645'),
  ('06029', 'îles de Lérins', 'archipel', 28, 'Aerial view of Îles de Lérins (cropped).jpg', 'Q292642'),
  ('30123', 'voie Domitienne', 'voie romaine', 28, 'Ambrussum voies marquées 10-04-2006.jpg', 'Q1146645'),
  ('34057', 'voie Domitienne', 'voie romaine', 28, 'Ambrussum voies marquées 10-04-2006.jpg', 'Q1146645'),
  ('62487', 'V3', 'Armes V', 28, 'Bundesarchiv Bild 146-1981-147-30A, Hochdruckpumpe V-3.jpg', 'Q640665'),
  ('65138', 'Vignemale', 'montagne', 28, 'Vignemale Sommer.jpg', 'Q1348903'),
  ('65286', 'sanctuaire de Lourdes', 'sanctuaire marial', 28, 'Lourdes basilique vue depuis château (3).JPG', 'Q7709620'),
  ('66222', 'pic du Canigou', 'montagne', 28, 'Vinça, la retenue d''eau et le Canigou.jpg', 'Q6650'),
  ('73257', 'Val Thorens', 'station de sports d''hiver', 28, 'Val Thorens @ Lac de la Portette 01.jpg', 'Q1026835'),
  ('92063', 'château de Malmaison', 'musée d''art', 28, '2011 Chateau de Malmaison recto-verso.jpg', 'Q684846'),
  ('21508', 'Circuit de Dijon-Prenois', 'installation sportive', 27, 'Dijon-Prenois1.jpg', 'Q172888'),
  ('29083', 'île de Sein', 'île', 27, 'Port de l''île de Sein 01.JPG', 'Q228472'),
  ('49328', 'château de Saumur', 'musée', 27, '0 1106 Saumur - Château de Saumur.jpg', 'Q1150222'),
  ('51282', 'circuit de Reims-Gueux', 'circuit', 27, 'Dodge-challenger-srt8-at-reims-track.jpg', 'Q171574'),
  ('67362', 'château du Haut-Koenigsbourg', 'château fort', 27, 'France Haut-Koenigsbourg aerial view (cropped).jpg', 'Q1552366'),
  ('69385', 'primatiale Saint-Jean de Lyon', 'siège de diocèse', 27, '007. Photo prise depuis les toits de la Basilique Notre-Dame de Fourvière.JPG', 'Q1521'),
  ('75102', 'place des Victoires', 'place', 27, 'Place des Victoires, Paris 26 May 2017.jpg', 'Q1362670'),
  ('06150', 'trophée des Alpes', 'ruine', 26, 'La Turbie BW 1.JPG', 'Q747588'),
  ('13202', 'cathédrale Sainte-Marie-Majeure', 'basilique mineure', 26, 'Cathédrale Sainte-Marie-Majeure de Marseille. Vue générale..JPG', 'Q1419757'),
  ('14118', 'stade Michel-d''Ornano', 'installation sportive', 26, 'Vue densemble dornano.JPG', 'Q1417171'),
  ('2B023', 'Monte Cinto', 'montagne', 26, 'Monte Cinto - Asco (FR2B) - 2021-09-09 - 4.jpg', 'Q1415428'),
  ('50218', 'îles Chausey', 'archipel', 26, 'Chausey le fort.JPG', 'Q292600'),
  ('60491', 'château de Pierrefonds', 'château fort', 26, 'Le Château de Pierrefonds.jpg', 'Q376699'),
  ('60494', 'parc Astérix', 'parc d''attractions', 26, 'Goudurix.JPG', 'Q377592'),
  ('75119', 'parc des Buttes-Chaumont', 'jardin public', 26, '070922 Parce des Buttes Chaumont 005.jpg', 'Q532113'),
  ('78356', 'abbaye de Port-Royal-des-Champs à Magny-les-Hameaux', 'monastère', 26, 'Port Royal des Champs - Oratoire.jpg', 'Q652981'),
  ('90010', 'Lion de Belfort', 'sculpture monumentale', 26, 'LionBelfort.jpg', 'Q926536'),
  ('92012', 'La Seine musicale', 'centre des arts de la scène', 26, 'La Seine musicale at night.jpg', 'Q19944990'),
  ('97356', 'parc amazonien de Guyane', 'parc national', 26, 'Parc naturel regional de guyane vue du dessus.JPG', 'Q665459'),
  ('27016', 'Château-Gaillard', 'château fort', 25, 'Château Gaillard (Les Andelys), vu du ciel.JPG', 'Q1090492'),
  ('31069', 'Aeroscopia', 'musée aéronautique', 25, 'Aeroscopia Blagnac.jpg', 'Q15714017'),
  ('37132', 'château de Loches', 'château fort', 25, 'PixAile17.jpg', 'Q1061061'),
  ('37197', 'château d''Ussé', 'château', 25, 'Aerial image of Château d''Ussé (view from the east).jpg', 'Q185479'),
  ('57412', 'stade Saint-Symphorien', 'installation sportive', 25, 'Tribune Ouest Saint Symphorien.jpg', 'Q1483409'),
  ('57463', 'cathédrale Saint-Étienne de Metz', 'cathédrale catholique', 25, 'Cathedrale-saint-etienne-metz-de-place-prefecture.jpg', 'Q671066'),
  ('63345', 'Circuit de Charade', 'circuit de sport mécanique', 25, 'Circuit de Charade 2017-1.jpg', 'Q172879'),
  ('77111', 'Parc Disneyland', 'parc à thèmes', 25, 'Disneyland Park 05, Paris 22 August 2013.jpg', 'Q2313567'),
  ('01210', 'crêt de la Neige', 'montagne', 24, 'Crêt Neige Thoiry Ain 3.jpg', 'Q1142554'),
  ('02217', 'château de Coucy', 'ruine de château', 24, 'Coucy comparaison.jpg', 'Q576534'),
  ('15108', 'viaduc de Garabit', 'viaduc', 24, '00 0526 Viaduc de Garabit - Département Cantal, Frankreich.jpg', 'Q1333442'),
  ('24172', 'abri de Cro-Magnon', 'abri sous roche', 24, 'Eyzies-Cro-Magnon-3.jpg', 'Q331409'),
  ('37123', 'château de Langeais', 'château', 24, 'Langeais-Chateau.JPG', 'Q1143558'),
  ('38442', 'Grande Chartreuse', 'monastère', 24, 'La Grande Chartreuse.JPG', 'Q180709'),
  ('41045', 'château de Chaumont-sur-Loire', 'château', 24, '00 2417 Château de Chaumont-sur-Loire.jpg', 'Q522779'),
  ('65059', 'pic du Midi de Bigorre', 'montagne', 24, 'Pic du Midi du Bigorre.jpg', 'Q1139060'),
  ('01160', 'LHCb', 'expérience', 23, '', 'Q665728'),
  ('10387', 'stade de l''Aube', 'installation sportive', 23, 'Stade de l''Aube.jpg', 'Q2001732'),
  ('13055', 'musée des civilisations de l''Europe et de la Méditerranée', 'musée', 23, 'Mucem et Cathédrale Sainte-Marie-Majeure de Marseille.jpg', 'Q2808698'),
  ('24520', 'cathédrale Saint-Sacerdos de Sarlat', 'cathédrale', 23, 'Sarlat-Saint Sardos.JPG', 'Q2942447'),
  ('34003', 'Le Cap d''Agde', 'établissement humain', 23, 'Cap d''Agde été 2007 201.jpg', 'Q996129'),
  ('37261', 'cathédrale Saint-Gatien de Tours', 'cathédrale catholique', 23, 'Cathédrale de Tours.JPG', 'Q547013'),
  ('38185', 'stade des Alpes', 'stade', 23, 'Grenoble-Clermont.jpg', 'Q2299298'),
  ('41050', 'château de Cheverny', 'château', 23, 'ChevernySchloss.jpg', 'Q1141846'),
  ('45234', 'cathédrale Sainte-Croix d''Orléans', 'cathédrale catholique', 23, 'Orléans Cathedral, West view 20170609 1.jpg', 'Q1366553'),
  ('63113', 'cathédrale Notre-Dame-de-l''Assomption de Clermont-Ferrand', 'cathédrale catholique', 23, 'Cathedrale vue de montjuzet detail.jpg', 'Q1032205'),
  ('73015', 'Méribel', 'station de sports d''hiver', 23, '131-3116 IMG.JPG', 'Q914361'),
  ('73157', 'tunnel ferroviaire du Fréjus', 'tunnel ferroviaire', 23, 'Bardonecchia (TO) - portale sud del traforo ferroviario del Frejus.jpg', 'Q537800'),
  ('89024', 'Stade de l''Abbé-Deschamps', 'installation sportive', 23, 'Auxerre - Stade Abbé-Deschamps (31).JPG', 'Q1347183'),
  ('89387', 'cathédrale Saint-Étienne de Sens', 'cathédrale catholique', 23, 'Cathédrale Saint-Étienne, Sens-6998.jpg', 'Q489014'),
  ('92062', 'Tour Hekla', 'gratte-ciel', 23, 'Photo tour Hekla janvier 2022.jpg', 'Q17640070'),
  ('92064', 'château de Saint-Cloud', 'palais', 23, 'Saint-Cloud, general view, painting by Allegrain – Château de Versailles (adjusted).jpg', 'Q662491'),
  ('92072', 'manufacture nationale de Sèvres', 'musée', 23, 'Manufacture nationale de Sèvres, vue 002.jpg', 'Q653307'),
  ('09030', 'pique d''Estats', 'montagne', 22, 'Pica Estats.jpg', 'Q1537733'),
  ('09211', 'château de Montségur', 'château fort', 22, 'Montsegur (1).jpg', 'Q1013191'),
  ('13209', 'grotte Cosquer', 'grotte ornée', 22, 'Calanques de Marseille 20120922 36.jpg', 'Q747992'),
  ('24322', 'cathédrale Saint-Front', 'église', 22, 'Périgueux (Fr), cathédrale St.Front, extérieur.jpg', 'Q1736213'),
  ('25388', 'stade Auguste-Bonal', 'installation sportive', 22, 'Stade Sochaux Bonale 2.jpg', 'Q1341629'),
  ('36228', 'château de Valençay', 'château', 22, 'Chateau Valencay 20050726.jpg', 'Q1142363'),
  ('38469', 'Notre-Dame de La Salette', 'titre de Marie', 22, 'Chapelle de la Salette St-Exupére Toulouse.jpg', 'Q1074596'),
  ('45270', 'abbaye de Saint-Benoît-sur-Loire', 'abbaye', 22, 'Saint-Benoît -France.JPG', 'Q956741'),
  ('60471', 'cathédrale Notre-Dame de Noyon', 'cathédrale', 22, 'Cathédrale de Noyon.JPG', 'Q932828'),
  ('73273', 'abbaye royale d’Hautecombe', 'abbaye de l''Ordre de Cîteaux', 22, 'Abbaye d''Hautecombe (Savoie) - Lac du Bourget - Vue depuis le belvédère du mont de la Charvaz - 51619987352.jpg', 'Q63524'),
  ('73290', 'col du Mont-Cenis', 'col routier', 22, 'RD 1006 au col du Mont-Cenis côté Maurienne (septembre 2024).JPG', 'Q13411496'),
  ('74143', 'dôme du Goûter', 'sommet', 22, 'Dôme du Goûter depuis l''Arveyon.jpg', 'Q30434'),
  ('87085', 'cathédrale Saint-Étienne de Limoges', 'cathédrale catholique', 22, 'Abbaye de la Règle à Limoges.png', 'Q2189282'),
  ('09122', 'château de Foix', 'château fort', 21, 'Castle of Foix 05.jpg', 'Q1011806'),
  ('11297', 'Montagne Noire', 'chaîne de montagnes', 21, 'Montagne Noire.JPG', 'Q1509963'),
  ('14060', 'Pegasus Bridge', 'pont basculant', 21, 'Pegasus bridge new.jpg', 'Q594779'),
  ('21231', 'stade Gaston-Gérard', 'stade', 21, 'Dijon FCO 3.JPG', 'Q1848312'),
  ('22070', 'stade de Roudourou', 'stade', 21, 'Roudourou-ensemble.JPG', 'Q1817621'),
  ('2A004', 'musée de la Maison Bonaparte', 'musée national', 21, 'Ajaccio MN1JPG.jpg', 'Q3124818'),
  ('2B120', 'stade Armand-Cesari', 'installation sportive', 21, 'Stade Armand Cesari 2012.png', 'Q1434942'),
  ('30084', 'site nucléaire de Marcoule', 'installation nucléaire', 21, 'CEA Marcoule Site.jpg', 'Q580142'),
  ('45315', 'château de Sully-sur-Loire', 'château', 21, 'Sully-sur-Loire-Chateau-03-gje.jpg', 'Q1470842'),
  ('50353', 'abbaye du Mont-Saint-Michel', 'monastère', 21, 'Le Mont-Saint-Michel Abbaye de Mont-Saint-Michel Südseite 03.jpg', 'Q651388'),
  ('56121', 'stade du Moustoir', 'installation sportive', 21, 'Stade du Moustoir.jpg', 'Q39189'),
  ('59606', 'stade du Hainaut', 'installation sportive', 21, 'Intérieur Stade du Hainaut (2013).JPG', 'Q2299919'),
  ('62193', 'Jungle de Calais', 'camp de réfugiés', 21, 'Overview of Calais Jungle.jpg', 'Q20711958'),
  ('64545', 'La Rhune', 'montagne', 21, 'Urrugne, France - panoramio (3).jpg', 'Q2737839'),
  ('65077', 'Hautacam', 'station de sports d''hiver', 21, 'La station de ski Hautacam (dep.65).jpg', 'Q645628'),
  ('68307', 'Ballon d''Alsace', 'montagne', 21, 'Ballon d''Alsace @ Sud 01.jpg', 'Q1334057'),
  ('71014', 'cathédrale Saint-Lazare d''Autun', 'basilique mineure', 21, 'Cathédrale Autun 02.JPG', 'Q611944'),
  ('74191', 'Avoriaz', 'station de sports d''hiver', 21, 'Avoriaz (6).jpg', 'Q127037'),
  ('78297', 'Golf national', 'terrain de golf', 21, 'Golf national 2011 06.jpg', 'Q3058615'),
  ('78423', 'vélodrome de Saint-Quentin-en-Yvelines', 'vélodrome', 21, 'Journée portes ouvertes au vélodrome de Saint-Quentin-en-Yvelines le 1er février 2014 - 78.jpg', 'Q3564108'),
  ('84050', 'abbaye Notre-Dame de Sénanque', 'abbaye', 21, 'Abbaye-senanque-gordes-iso.jpg', 'Q1245463'),
  ('88426', 'Ballon d''Alsace', 'montagne', 21, 'Ballon d''Alsace @ Sud 01.jpg', 'Q1334057'),
  ('89420', 'château de Guédelon', 'château fort', 21, 'Guedelon 107.jpg', 'Q1557685'),
  ('90065', 'Ballon d''Alsace', 'montagne', 21, 'Ballon d''Alsace @ Sud 01.jpg', 'Q1334057'),
  ('06004', 'Juan-les-Pins', 'petite ville', 20, 'JuanLesPinsDepuisLeCap.jpg', 'Q1026520'),
  ('11262', 'cathédrale Saint-Just-et-Saint-Pasteur de Narbonne', 'cathédrale', 20, 'Narbonne Cathedrale Saint Just et Saint Pasteur.jpg', 'Q473121'),
  ('13004', 'arènes d''Arles', 'site archéologique', 20, 'Arles - 2017-05-24 - Roman Amphitheatre - 3804.jpg', 'Q181189'),
  ('13103', 'Office national d''études et de recherches aérospatiales', 'organisme public de recherche', 20, 'ONERA MEUDON soufflerie S1b.jpg', 'Q2007769'),
  ('16015', 'cathédrale Saint-Pierre d''Angoulême', 'cathédrale catholique', 20, 'Angouleme cathedral StPierre a.jpg', 'Q1736169'),
  ('29232', 'cathédrale Saint-Corentin de Quimper', 'cathédrale catholique', 20, 'Quimper (29) Cathédrale 01.jpg', 'Q2419151'),
  ('31334', 'Office national d''études et de recherches aérospatiales', 'organisme public de recherche', 20, 'ONERA MEUDON soufflerie S1b.jpg', 'Q2007769'),
  ('33314', 'château Lafite Rothschild', 'domaine viticole', 20, 'Chateau Lafite.jpg', 'Q1090558'),
  ('49050', 'château de Brissac', 'château fort', 20, 'Mosaïque participative.jpg', 'Q786075'),
  ('59350', 'Office national d''études et de recherches aérospatiales', 'organisme public de recherche', 20, 'ONERA MEUDON soufflerie S1b.jpg', 'Q2007769'),
  ('63302', 'Gergovie', 'village', 20, 'Toits de Gergovie (63).jpg', 'Q3189964'),
  ('64253', 'camp de Gurs', 'camp de concentration nazi', 20, 'Gurs tombes-3.JPG', 'Q708638'),
  ('64542', 'col du Somport', 'col routier', 20, 'Puerto del Somport.jpg', 'Q389859'),
  ('66067', 'Puigmal', 'montagne', 20, 'Puigmal Fontalba.jpg', 'Q17477'),
  ('68224', 'Cité du train', 'musée national', 20, 'Cite du train.JPG', 'Q728562'),
  ('73047', 'col de l''Iseran', 'col routier', 20, 'Col de l''Iseran 2.jpg', 'Q547474'),
  ('76378', 'abbaye Royale Saint-Pierre de Jumièges', 'monastère en ruines', 20, 'Abbaye de Jumièges.jpg', 'Q333980'),
  ('78517', 'château de Rambouillet', 'palais', 20, 'Chateau-de-Rambouillet-DSC0044.jpg', 'Q648534'),
  ('86115', 'Futuroscope', 'parc à thèmes', 20, 'Le parc du futuroscope.JPG', 'Q1475660'),
  ('91477', 'Office national d''études et de recherches aérospatiales', 'organisme public de recherche', 20, 'ONERA MEUDON soufflerie S1b.jpg', 'Q2007769'),
  ('92020', 'Office national d''études et de recherches aérospatiales', 'organisme public de recherche', 20, 'ONERA MEUDON soufflerie S1b.jpg', 'Q2007769'),
  ('93006', 'Tours Mercuriales', 'gratte-ciel', 20, 'Foire du Trône 2023 - vue vers le nord et les tours Mercuriales.jpg', 'Q3535524'),
  ('93029', 'camp de Drancy', 'camp de concentration', 20, 'Bundesarchiv Bild 183-B10919, Frankreich, Internierungslager Drancy.jpg', 'Q247958');

insert into public.monuments (commune_code, nom, type, langues, image, wikidata)
select l.commune_code, l.nom, l.type, l.langues, l.image, l.wikidata
  from lot_monuments l
 where exists (select 1 from communes c where c.code = l.commune_code)
on conflict (commune_code) do update set
  nom = excluded.nom, type = excluded.type, langues = excluded.langues,
  image = excluded.image, wikidata = excluded.wikidata;


-- ---------------------------------------------------------------------------
--  Le catalogue : tout le monde voit tout, y compris ce qu'il n'a pas
--
--  C'est ce qui donne envie. Voir « viaduc de Millau — appartient a Maroli »,
--  c'est savoir quoi viser et a qui le prendre : la boucle de jeu entiere dans
--  une ligne.
-- ---------------------------------------------------------------------------
create or replace function public.monuments_catalogue()
returns table(
  commune_code text, nom text, embleme text, departement text, tier text,
  langues integer, image text, photo text,
  a_moi boolean, proprietaire text, libre boolean)
language sql
stable security definer
set search_path to 'public'
as $function$
  select m.commune_code,
         c.nom,
         m.nom,
         c.departement,
         c.tier,
         m.langues,
         m.image,
         m.photo,
         (p.joueur_id = auth.uid())            as a_moi,
         j.pseudo                              as proprietaire,
         (p.joueur_id is null)                 as libre
    from monuments m
    join communes c on c.code = m.commune_code
    left join possessions p on p.commune_code = m.commune_code
    left join joueurs j on j.id = p.joueur_id
   order by m.langues desc nulls last, c.nom;
$function$;

revoke all on function public.monuments_catalogue() from public;
grant execute on function public.monuments_catalogue() to anon, authenticated;


-- ---------------------------------------------------------------------------
--  Verification
-- ---------------------------------------------------------------------------
select 'A. emblemes poses' as controle, count(*)::text as valeur from monuments
union all
select 'B. communes introuvables',
       (select count(*)::text from lot_monuments l
         where not exists (select 1 from communes c where c.code = l.commune_code))
union all
select 'C. departements couverts',
       (select count(distinct c.departement)::text
          from monuments m join communes c on c.code = m.commune_code)
union all
select 'D. deja detenus par un joueur',
       (select count(*)::text from monuments m
          join possessions p on p.commune_code = m.commune_code)
union all
select 'E. les trois plus connus',
       (select string_agg(nom, ' · ' order by langues desc)
          from (select nom, langues from monuments order by langues desc limit 3) t)
union all
select 'F. droits sur la fonction',
       coalesce((select array_to_string(p.proacl, ' ') from pg_proc p
                  join pg_namespace n on n.oid = p.pronamespace
                 where n.nspname = 'public' and p.proname = 'monuments_catalogue'), 'aucun')
order by 1;
