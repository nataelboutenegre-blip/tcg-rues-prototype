-- s2-138 (11/11/2026) : les dos de carte du podium de la saison 2 (patch420)
-- Trois dos offerts, jamais en vente (actif = false, comme le dos OG ; boutique_acheter exige actif) :
-- « Lauriers d'or » au 1er, « Lauriers d'argent » au 2e, « Lauriers de bronze » au 3e.
-- Invisibles tant que personne ne les a : boutique() et garde_robe() ne montrent un dos inactif qu'à son propriétaire.
-- L'attribution se fait à la clôture (script des récompenses de la saison 2), dans boutique_inventaire.
begin;

insert into public.boutique_articles(id, type, nom, description, prix, actif, ordre) values
  ('dos-podium-s2-or',     'dos', 'Lauriers d''or · S2',       'Réservé au champion de la saison 2',      0, false, 0),
  ('dos-podium-s2-argent', 'dos', 'Lauriers d''argent · S2',   'Réservé au vice-champion de la saison 2', 0, false, 0),
  ('dos-podium-s2-bronze', 'dos', 'Lauriers de bronze · S2',   'Réservé au 3e de la saison 2',            0, false, 0)
on conflict (id) do update set type = excluded.type, nom = excluded.nom, description = excluded.description,
                               prix = 0, actif = false, ordre = excluded.ordre;

commit;
