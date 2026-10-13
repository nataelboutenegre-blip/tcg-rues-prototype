-- ===========================================================================
--  TerraFront — Rafale, correctif (13 octobre 2026, signalé par Maroli et
--  Nataël : « Lyon », « Paris » refusés)
--  Dans le jeu, Paris, Lyon et Marseille sont découpées en arrondissements
--  (« Paris 1er Arrondissement »...) que rafale-1 avait écartés : les trois
--  villes n'étaient donc pas reconnues. On les ajoute à la liste des noms.
--  Rejouable.
-- ===========================================================================
insert into public.rafale_noms(cle, code, nom, dept, pop) values
  ('PARIS',     '75056', 'Paris',     '75', 2100000),
  ('MARSEILLE', '13055', 'Marseille', '13', 870000),
  ('LYON',      '69123', 'Lyon',      '69', 520000)
on conflict (cle) do nothing;

select string_agg(nom, ', ' order by nom) as reconnues_doit_etre_lyon_marseille_paris
  from public.rafale_noms where cle in ('PARIS', 'MARSEILLE', 'LYON');
