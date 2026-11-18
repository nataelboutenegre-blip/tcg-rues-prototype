-- Saison 3, jour J — étape 4 bis : les skins (à lancer après s3-jj-4-ouverture.sql, avant le patch du jeu).
-- Sans risque pour le reste : si ce fichier échoue, la saison est ouverte quand même, seuls les skins manquent.
--  1. cinq nouveaux skins en boutique (dessins déjà dans le jeu depuis patch454) ;
--  2. nouvelles descriptions des neuf skins repris (leur dessin change le 22/11 à 10 h 01 avec l'habillage Topo).
-- On peut le relancer : il ne crée pas de doublon.
begin;

insert into public.euros_articles (id, type, nom, description, prix_centimes, reserve_og, saison, actif, ordre, contenu) values
  ('skin-givre',     'skin', 'Skin Givre',     'Le gel prend sur les bords, la photo se voit à travers une vitre givrée',           399, false, null, true, 291, null),
  ('skin-aquarelle', 'skin', 'Skin Aquarelle', 'La photo repeinte à l''aquarelle sur papier à grain, avec sa palette',              399, false, null, true, 292, null),
  ('skin-topo',      'skin', 'Skin Topo',      'La photo en carte d''état-major : deux encres et des courbes de niveau dorées',     499, false, null, true, 293, null),
  ('skin-vitrail',   'skin', 'Skin Vitrail',   'La photo devient un vitrail, sa lumière colorée tombe sur la carte',                499, false, null, true, 294, null),
  ('skin-kintsugi',  'skin', 'Skin Kintsugi',  'La carte brisée puis réparée à l''or, à la japonaise',                              599, false, null, true, 295, null)
on conflict (id) do update set nom = excluded.nom, description = excluded.description, prix_centimes = excluded.prix_centimes,
  actif = excluded.actif, ordre = excluded.ordre;

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

commit;

-- Contrôle : 14 skins en vente, les cinq nouveaux en dernier.
select id, nom, prix_centimes, actif, ordre, description from public.euros_articles where type = 'skin' and actif order by ordre;
