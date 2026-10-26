-- ===========================================================================
--  TerraFront — Besançon : la citadelle remplace la synagogue (signalé par
--  Arkhannou). Le choix automatique prenait le lieu le plus traduit sur
--  Wikipédia (30 langues contre 13), pas le plus emblématique.
--  La photo est vidée : relancer ensuite monuments-2-images.py, qui ne
--  traitera que Besançon (retiré de monuments-faits.txt). Rejouable.
--  Contrôle attendu : citadelle de Besançon | château fort | Q1329976 | (vide)
-- ===========================================================================
update public.monuments
   set nom = 'citadelle de Besançon', type = 'château fort', langues = 13,
       image = 'Aerial image of the Citadel of Besançon (view from the southwest).jpg',
       wikidata = 'Q1329976', photo = null, photo_auteur = null, photo_licence = null, photo_source = null
 where commune_code = '25056';

select nom, type, wikidata, photo from public.monuments where commune_code = '25056';
