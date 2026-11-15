-- ===========================================================================
--  s3-13b — OUVRIR le pass de la saison 3 (jour J, après la clôture de la
--  saison 2 et l'ouverture de la saison 3). L'XP commence à compter.
--  La VENTE est à part (2e bloc) : seulement après un achat test réussi.
--  Rejouable. Contrôle attendu : <date d'ouverture> | 13/12 10 h | <en vente> | true
-- ===========================================================================
update public.pass_saisons set debut = coalesce(debut, now()) where saison = 'saison-3';

-- À lancer à part, quand l'achat test est passé :
-- update public.euros_articles set actif = true where id = 'pass-s3';

select p.debut at time zone 'Europe/Paris' as ouvert_le, p.fin at time zone 'Europe/Paris' as fin,
       (select actif from public.euros_articles where id = 'pass-s3') as en_vente,
       exists(select 1 from public.pass_en_cours())                  as en_cours
  from public.pass_saisons p where p.saison = 'saison-3';
