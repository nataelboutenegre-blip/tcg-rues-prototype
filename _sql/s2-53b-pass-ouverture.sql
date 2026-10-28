-- ===========================================================================
--  s2-53b — OUVRIR le pass « Brumes d'automne » (à lancer le jour J, après
--  s2-53 et après avoir poussé le jeu)
--  - l'XP commence à compter maintenant ;
--  - le pass se vend (article 'pass-s2', 3,99 €).
--  Rejouable (ne change pas la date d'ouverture une fois posée).
--  Contrôle attendu : <date d'ouverture> | <fin> | true | true
-- ===========================================================================
update public.pass_saisons set debut = coalesce(debut, now()) where article_id = 'pass-s2';
update public.euros_articles set actif = true where id = 'pass-s2';

select p.debut at time zone 'Europe/Paris' as ouvert_le, p.fin at time zone 'Europe/Paris' as fin,
       (select actif from public.euros_articles where id = 'pass-s2') as en_vente,
       exists(select 1 from public.pass_en_cours())                  as en_cours
  from public.pass_saisons p where p.article_id = 'pass-s2';
