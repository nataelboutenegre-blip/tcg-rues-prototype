-- ===========================================================================
--  TerraFront — boutique en euros : 10. les neuf dos premium
--  26 octobre 2026. À passer AVANT de pousser patch199. Rejouable.
--
--  Les 9 dos dessinés par la carte graphique (patch199). Ils sont actifs,
--  donc visibles des seuls comptes testeurs tant que « boutique_ouverte »
--  est faux (6-garde-robe.sql) : personne d'autre ne les voit.
--
--  Prix : grille du 12 octobre (dos-premium-collections.md), INDICATIFS.
--  Un prix changé à la main n'est pas réécrit si on rejoue ce fichier.
--  L'identifiant « dos-xxx » donne la clé « xxx » lue par le jeu (dosCle).
-- ===========================================================================
begin;

insert into public.euros_articles(id, type, nom, description, prix_centimes, reserve_og, actif, ordre) values
  ('dos-comete',  'dos', 'Dos Comète',     'Une nébuleuse, des étoiles en relief et une comète qui passe', 299, false, true, 110),
  ('dos-juillet', 'dos', 'Dos 14 Juillet', 'Un feu d''artifice bleu, blanc, rouge au-dessus du relief',  399, false, true, 120),
  ('dos-maree',   'dos', 'Dos Marée',      'La lumière danse sous l''eau, les courbes ondulent',          299, false, true, 130),
  ('dos-feu',     'dos', 'Dos Puy de feu', 'La lave coule dans les courbes, la roche se fissure',         399, false, true, 140),
  ('dos-prisme',  'dos', 'Dos Prisme',     'Une feuille holographique : la couleur change avec l''angle', 399, false, true, 150),
  ('dos-orfondu', 'dos', 'Dos Or fondu',   'De l''or martelé : la lumière glisse sur chaque courbe',     399, false, true, 160),
  ('dos-neon',    'dos', 'Dos Néon',       'Chaque courbe devient un tube néon qui grésille',             299, false, true, 170),
  ('dos-gravure', 'dos', 'Dos Gravure',    'Une planche d''atlas gravée à l''encre, sur papier ancien',  249, false, true, 180),
  ('dos-orage',   'dos', 'Dos Orage',      'Nuages, pluie en biais et foudre, jamais deux fois pareille',  399, false, true, 190)
on conflict (id) do nothing;

commit;

-- ---------- contrôle : attendu  9 | 9 | 0 | false ----------
-- dos_premium : les 9 articles ; actifs : les 9 ; doublons : aucun dos en
-- points ne porte le même identifiant ; boutique_ouverte : toujours fermée
select (select count(*) from public.euros_articles
         where id in ('dos-comete','dos-juillet','dos-maree','dos-feu','dos-prisme','dos-orfondu','dos-neon','dos-gravure','dos-orage')
           and type = 'dos')                                                        as dos_premium,
       (select count(*) from public.euros_articles
         where id in ('dos-comete','dos-juillet','dos-maree','dos-feu','dos-prisme','dos-orfondu','dos-neon','dos-gravure','dos-orage')
           and actif)                                                               as actifs,
       (select count(*) from public.boutique_articles
         where id in ('dos-comete','dos-juillet','dos-maree','dos-feu','dos-prisme','dos-orfondu','dos-neon','dos-gravure','dos-orage')) as doublons,
       (select valeur from public.euros_reglages where cle = 'boutique_ouverte')    as boutique_ouverte;
