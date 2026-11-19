-- s3-36 : les cinq thèmes de la saison 3 (Givre, Aquarelle, Topo, Vitrail, Kintsugi) en collections, PAS ENCORE EN VENTE.
-- Décisions de Nataël (19/11/2026) : le recto et le verso se vendent ensemble ; ces cinq thèmes ne se vendent
-- qu'en collection (le skin et le dos existent en base pour être livrés, mais ne sont pas en vente seuls) ;
-- prix : Givre 5,99 · Aquarelle 5,99 · Topo 6,49 · Vitrail 6,49 · Kintsugi 6,99.
-- Tout est créé avec actif = false : rien n'apparaît en boutique. La mise en vente : _jour-j/s3-jj-4b-skins.sql, le 22/11.
-- Et, pour le test sur téléphone avant le 22 : les cinq dos et les cinq skins dans la garde-robe de Nataël.
-- Rejouable.
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
  ('pack-topo',      'collection', 'Collection Topo',      'Le dos et le skin Topo',      649, false, null, false, 281, array['dos-topo', 'skin-topo']),
  ('pack-givre',     'collection', 'Collection Givre',     'Le dos et le skin Givre',     599, false, null, false, 282, array['dos-givre', 'skin-givre']),
  ('pack-kintsugi',  'collection', 'Collection Kintsugi',  'Le dos et le skin Kintsugi',  699, false, null, false, 283, array['dos-kintsugi', 'skin-kintsugi']),
  ('pack-vitrail',   'collection', 'Collection Vitrail',   'Le dos et le skin Vitrail',   649, false, null, false, 284, array['dos-vitrail', 'skin-vitrail']),
  ('pack-aquarelle', 'collection', 'Collection Aquarelle', 'Le dos et le skin Aquarelle', 599, false, null, false, 285, array['dos-aquarelle', 'skin-aquarelle'])
on conflict (id) do update set type = excluded.type, nom = excluded.nom, description = excluded.description,
  prix_centimes = excluded.prix_centimes, actif = excluded.actif, ordre = excluded.ordre, contenu = excluded.contenu;

insert into public.euros_inventaire (joueur_id, article_id)
select 'be0515d7-31de-40a3-9834-f0fb97ef0d89'::uuid, a.id from public.euros_articles a
 where a.id ~ '^(dos|skin)-(givre|aquarelle|topo|vitrail|kintsugi)$'
on conflict (joueur_id, article_id) do nothing;

commit;

-- Contrôle : 15 articles, aucun en vente · 10 objets chez Nataël · le reste de la boutique inchangé (9 skins, 9 collections en vente)
select (select count(*) from public.euros_articles where id ~ '-(givre|aquarelle|topo|vitrail|kintsugi)$') as articles,
       (select count(*) from public.euros_articles where id ~ '-(givre|aquarelle|topo|vitrail|kintsugi)$' and actif) as en_vente,
       (select count(*) from public.euros_inventaire where joueur_id = 'be0515d7-31de-40a3-9834-f0fb97ef0d89'
           and article_id ~ '-(givre|aquarelle|topo|vitrail|kintsugi)$') as chez_natael,
       (select count(*) from public.euros_articles where type = 'skin' and actif) as skins_en_vente,
       (select count(*) from public.euros_articles where type = 'collection' and actif) as collections_en_vente;
