-- ===========================================================================
--  TerraFront — boutique en euros : 19. CGV version 5 (23 novembre 2026)
--  Audit du 23/11 (patch507) : encadré des garanties légales (art. D. 211-4 du Code de la consommation),
--  compatibilité, phrase sur les promotions (date de fin annoncée, prix barré = plus bas des 30 jours).
--  À PASSER APRÈS le git push (le PDF doit être en ligne).
--  Les commandes passées gardent la version qu'elles ont acceptée ; les PDF v3 et v4 restent en ligne. Rejouable.
--  Retour arrière : repasser 15-cgv-v4.sql (et remettre cgv.html v4).
--  Contrôle attendu : 2026-11-23-v5 | https://terrafront.fr/cgv/cgv-2026-11-23-v5.pdf
-- ===========================================================================
begin;
insert into public.euros_reglages(cle, valeur) values ('cgv_version', '"2026-11-23-v5"'::jsonb)
on conflict (cle) do update set valeur = excluded.valeur;
insert into public.euros_reglages(cle, valeur) values ('cgv_pdf_url', '"https://terrafront.fr/cgv/cgv-2026-11-23-v5.pdf"'::jsonb)
on conflict (cle) do update set valeur = excluded.valeur;
commit;
select (select valeur #>> '{}' from public.euros_reglages where cle = 'cgv_version') as cgv_version,
       (select valeur #>> '{}' from public.euros_reglages where cle = 'cgv_pdf_url') as cgv_pdf_url;
