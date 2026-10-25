-- ===========================================================================
--  TerraFront — boutique en euros : 7. activer deux articles pour le test
--  (25 octobre 2026, mode test Stripe)
--
--  Active « Paquet Kraft » et « Paquet Néon » (2,99 €). La boutique reste
--  FERMÉE à tous sauf aux testeurs (boutique_ouverte = false) : les joueurs
--  ne voient rien. Rejouable. Finit par un contrôle.
-- ===========================================================================

update public.euros_articles set actif = true
 where id in ('paquet-kraft', 'paquet-neon');

-- contrôle : attendu  false | 1 | paquet-kraft, paquet-neon
select (select valeur from public.euros_reglages where cle = 'boutique_ouverte')            as boutique_ouverte,
       (select jsonb_array_length(valeur) from public.euros_reglages where cle = 'testeurs') as testeurs,
       (select string_agg(id, ', ' order by id) from public.euros_articles where actif)      as articles_actifs;
