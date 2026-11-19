-- Saison 3, jour J — étape 4 bis : les collections de la saison 3 (à lancer après s3-jj-4-ouverture.sql, avant le patch du jeu).
-- Sans risque pour le reste : si ce fichier échoue, la saison est ouverte quand même, seules les collections manquent.
--  1. cinq collections en boutique (skin + dos : Topo, Givre, Kintsugi, Vitrail, Aquarelle). Décision de Nataël du 19/11 :
--     le recto et le verso se vendent ensemble, ces cinq thèmes ne se vendent pas à l'unité (dessins : patch454 et patch468) ;
--  2. nouvelles descriptions des neuf skins repris (leur dessin change le 22/11 à 10 h 01 avec l'habillage Topo) ;
--  3. les neuf anciens thèmes ne se vendent plus qu'en collection (plus de skin ni de dos à l'unité).
-- On peut le relancer : il ne crée pas de doublon. (Les articles existent depuis _sql/s3-36, non visibles ; ce fichier les recrée au besoin.)
begin;

insert into public.euros_articles (id, type, nom, description, prix_centimes, reserve_og, saison, actif, ordre, contenu) values
  -- les skins (dessins dans le jeu depuis patch454) : vendus seulement dans leur collection
  ('skin-givre',     'skin', 'Skin Givre',     'Le gel prend sur les bords, la photo se voit à travers une vitre givrée',           399, false, null, false, 291, null),
  ('skin-aquarelle', 'skin', 'Skin Aquarelle', 'La photo repeinte à l''aquarelle sur papier à grain, avec sa palette',              399, false, null, false, 292, null),
  ('skin-topo',      'skin', 'Skin Topo',      'La photo en carte d''état-major : deux encres et des courbes de niveau dorées',     499, false, null, false, 293, null),
  ('skin-vitrail',   'skin', 'Skin Vitrail',   'La photo devient un vitrail, sa lumière colorée tombe sur la carte',                499, false, null, false, 294, null),
  ('skin-kintsugi',  'skin', 'Skin Kintsugi',  'La carte brisée puis réparée à l''or, à la japonaise',                              599, false, null, false, 295, null),
  -- les dos assortis (dessins dans le jeu depuis patch468) : vendus seulement dans leur collection
  ('dos-givre',      'dos',  'Dos Givre',      'La glace prend par les bords, une étoile de givre derrière l''épingle, la neige tombe', 299, false, null, false, 191, null),
  ('dos-aquarelle',  'dos',  'Dos Aquarelle',  'Des lavis de couleur sur papier à grain, les courbes au crayon',                    299, false, null, false, 192, null),
  ('dos-topo',       'dos',  'Dos Topo',       'Une carte de nuit : courbes dorées, carroyage et rose des vents',                   299, false, null, false, 193, null),
  ('dos-vitrail',    'dos',  'Dos Vitrail',    'Une rosace de verres de couleur, la lumière suit ta carte',                         299, false, null, false, 194, null),
  ('dos-kintsugi',   'dos',  'Dos Kintsugi',   'Des éclats de laque noire et rouge, recollés à l''or',                              299, false, null, false, 195, null),
  -- les collections (prix validés par Nataël le 19/11 : Kintsugi 6,99 € au plus) ; en tête de la section Collections
  ('pack-topo',      'collection', 'Collection Topo',      'Le dos et le skin Topo',      649, false, null, true, 281, array['dos-topo', 'skin-topo']),
  ('pack-givre',     'collection', 'Collection Givre',     'Le dos et le skin Givre',     599, false, null, true, 282, array['dos-givre', 'skin-givre']),
  ('pack-kintsugi',  'collection', 'Collection Kintsugi',  'Le dos et le skin Kintsugi',  699, false, null, true, 283, array['dos-kintsugi', 'skin-kintsugi']),
  ('pack-vitrail',   'collection', 'Collection Vitrail',   'Le dos et le skin Vitrail',   649, false, null, true, 284, array['dos-vitrail', 'skin-vitrail']),
  ('pack-aquarelle', 'collection', 'Collection Aquarelle', 'Le dos et le skin Aquarelle', 599, false, null, true, 285, array['dos-aquarelle', 'skin-aquarelle'])
on conflict (id) do update set type = excluded.type, nom = excluded.nom, description = excluded.description,
  prix_centimes = excluded.prix_centimes, actif = excluded.actif, ordre = excluded.ordre, contenu = excluded.contenu;

update public.euros_articles a set description = v.d
from (values
  ('skin-comete',  'La nuit tombe sur la photo, une comète traverse son ciel et l''éclaire'),
  ('skin-juillet', 'Le feu d''artifice éclate dans le ciel de la photo et colore les façades'),
  ('skin-maree',   'L''eau monte sur la photo : la commune se devine sous la surface'),
  ('skin-feu',     'Les flammes montent au pied de la photo et l''éclairent, la braise couve dessous'),
  ('skin-prisme',  'Une feuille holographique qui suit les formes de la photo et change avec l''angle'),
  ('skin-orfondu', 'La photo coulée dans l''or, qui goutte sur la carte'),
  ('skin-neon',    'Les contours de la photo s''allument en néons'),
  ('skin-gravure', 'La photo gravée à la plume : hachures, papier ancien et cachet'),
  ('skin-orage',   'La pluie ruisselle sur la vitre, l''éclair éclaire le ciel de la photo')
) as v(id, d) where a.id = v.id;

-- 3. (décision de Nataël, 19/11, 13 h 30) le recto et le verso ne se vendent plus séparément : les neuf anciens thèmes
--    ne gardent que leur collection. Les skins et les dos déjà achetés restent à leurs propriétaires ; qui a déjà une
--    moitié ne paie que l'autre dans la collection (euros_catalogue.prix_moi, euros_preparer_commande). Les dos OG restent.
update public.euros_articles set actif = false
 where id in ('skin-comete', 'skin-juillet', 'skin-maree', 'skin-feu', 'skin-prisme', 'skin-orfondu', 'skin-neon', 'skin-gravure', 'skin-orage',
              'dos-comete',  'dos-juillet',  'dos-maree',  'dos-feu',  'dos-prisme',  'dos-orfondu',  'dos-neon',  'dos-gravure',  'dos-orage');

commit;

-- Contrôle : 14 collections en vente, les cinq nouvelles en tête · 0 skin à l'unité · 0 dos à l'unité (hors OG) · 14 collections complètes
select id, nom, prix_centimes, actif, ordre, contenu from public.euros_articles where type = 'collection' and actif order by ordre;
select (select count(*) from public.euros_articles where type = 'collection' and actif) as collections_en_vente,
       (select count(*) from public.euros_articles where type = 'skin' and actif) as skins_a_l_unite,
       (select count(*) from public.euros_articles where type = 'dos' and actif and not reserve_og) as dos_a_l_unite,
       (select count(*) from public.euros_articles a where a.type = 'collection' and a.actif
           and (select count(*) from public.euros_articles b where b.id = any(a.contenu)) = 2) as collections_completes;
-- Retour en arrière (vente à l'unité des neuf anciens thèmes) : la même liste avec actif = true.
