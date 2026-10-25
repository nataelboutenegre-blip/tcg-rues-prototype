-- ===========================================================================
--  TerraFront — boutique en euros : nouvelle grille de prix (25 octobre 2026)
--  +1 € sur les habillages pour tous, +0,50 € sur les paquets OG, +1 € sur
--  les dos OG. Les articles restent INACTIFS (rien n'est en vente).
--  Les commandes gardent le prix payé (euros_commandes.prix_centimes) :
--  changer le catalogue ne touche à aucun achat passé.
--  Rejouable.
-- ===========================================================================
update public.euros_articles a
   set prix_centimes = n.prix
  from (values
    ('og-paquet-prisme',     299),
    ('og-paquet-or-noir',    299),
    ('og-dos-prisme',        399),
    ('og-dos-constellation', 399),
    ('paquet-kraft',         299),
    ('paquet-neon',          299),
    ('paquet-comete',        349),
    ('paquet-maree',         349),
    ('paquet-lave',          399),
    ('paquet-orage',         399)
  ) as n(id, prix)
 where a.id = n.id;

-- Contrôle : 10 lignes, toutes inactives, aux nouveaux prix
select id, prix_centimes, actif from public.euros_articles order by ordre;
