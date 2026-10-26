-- ===========================================================================
--  TerraFront — boutique en euros : 15. CGV version 4 (26 octobre 2026)
--  Ajout : les collections (packs dos + skin) sont nommées dans l'article 1,
--  avec leur règle de prix quand on possède déjà une partie du contenu.
--  À PASSER APRÈS le git push (le PDF doit être en ligne).
--  Les commandes passées gardent la version qu'elles ont acceptée (v3) ;
--  le PDF v3 reste en ligne. Rejouable.
--  Contrôle attendu : 2026-10-26-v4 | https://terrafront.fr/cgv/cgv-2026-10-26-v4.pdf
-- ===========================================================================
begin;

insert into public.euros_reglages(cle, valeur) values ('cgv_version', '"2026-10-26-v4"'::jsonb)
on conflict (cle) do update set valeur = excluded.valeur;

insert into public.euros_reglages(cle, valeur) values ('cgv_pdf_url', '"https://terrafront.fr/cgv/cgv-2026-10-26-v4.pdf"'::jsonb)
on conflict (cle) do update set valeur = excluded.valeur;

commit;

select (select valeur #>> '{}' from public.euros_reglages where cle = 'cgv_version') as cgv_version,
       (select valeur #>> '{}' from public.euros_reglages where cle = 'cgv_pdf_url') as cgv_pdf_url;
