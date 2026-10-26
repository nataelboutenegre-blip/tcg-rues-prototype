-- ===========================================================================
--  TerraFront — boutique en euros : 9. le PDF des CGV, et tous les objets en
--  test (26 octobre 2026)
--
--  1. cgv_pdf_url : le PDF des CGV v3 (cgv/cgv-2026-10-19-v3.pdf, publié par
--     GitHub Pages) est joint à chaque e-mail de confirmation.
--     À PASSER APRÈS le git push : avant, l'adresse n'existe pas encore.
--  2. Tous les objets sont activés, SAUF le pass de saison (sa progression
--     n'existe pas). La boutique reste FERMÉE à tous sauf aux testeurs
--     (boutique_ouverte = false) : seul le compte Nataël les voit.
--  Rejouable. Contrôle attendu :
--    false | https://terrafront.fr/cgv/cgv-2026-10-19-v3.pdf | 10 (tous les objets) | 0
-- ===========================================================================
begin;

insert into public.euros_reglages(cle, valeur)
values ('cgv_pdf_url', '"https://terrafront.fr/cgv/cgv-2026-10-19-v3.pdf"'::jsonb)
on conflict (cle) do update set valeur = excluded.valeur;

update public.euros_articles set actif = true where type <> 'pass';

commit;

-- contrôle : boutique fermée | adresse du PDF | articles actifs | pass actifs (doit être 0)
select (select valeur from public.euros_reglages where cle = 'boutique_ouverte')              as boutique_ouverte,
       (select valeur #>> '{}' from public.euros_reglages where cle = 'cgv_pdf_url')          as cgv_pdf_url,
       (select count(*) from public.euros_articles where actif)                               as articles_actifs,
       (select count(*) from public.euros_articles where actif and type = 'pass')             as pass_actifs;
