-- ===========================================================================
--  TerraFront — boutique en euros : 12. prix des dos premium (26 octobre 2026)
--  +1 € sur les neuf dos, comme les habillages et les dos OG le 25 octobre.
--  Standard 2,99 · Épique 3,99 · Légendaire 4,99. Rejouable.
--  Les commandes gardent le prix payé : rien ne change pour un achat passé.
-- ===========================================================================
update public.euros_articles a
   set prix_centimes = n.prix
  from (values
    ('dos-gravure', 299),
    ('dos-comete',  399),
    ('dos-juillet', 399),
    ('dos-maree',   399),
    ('dos-orfondu', 399),
    ('dos-neon',    399),
    ('dos-feu',     499),
    ('dos-orage',   499),
    ('dos-prisme',  499)
  ) as n(id, prix)
 where a.id = n.id;

-- Contrôle : attendu  9 | 1 | 5 | 3
select count(*)                                   as dos_premium,
       count(*) filter (where prix_centimes = 299) as a_2_99,
       count(*) filter (where prix_centimes = 399) as a_3_99,
       count(*) filter (where prix_centimes = 499) as a_4_99
  from public.euros_articles
 where id in ('dos-comete','dos-juillet','dos-maree','dos-feu','dos-prisme','dos-orfondu','dos-neon','dos-gravure','dos-orage');
