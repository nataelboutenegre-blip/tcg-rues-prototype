-- s2-114 (7/11/2026) : des bombes plus rapides et plus grosses (décision de Nataël, 19 h 43).
--
-- Constat : 3 bombes lâchées, toutes au niveau 1 (24 à 29 h, 10 km : 5, 11 et
-- 14 communes touchées). Personne n'attend 48 h, l'heure où le Centre apparaît.
--   niveau 1 : 24 h, 15 km (au lieu de 10)
--   niveau 2 : 36 h (au lieu de 48), 20 km (au lieu de 15)
--   niveau 3 : 48 h (au lieu de 72), 25 km (au lieu de 20)
--   le Centre apparaît à 36 h (au lieu de 48) : un niveau 2 part encore caché,
--   un niveau 3 oblige à rester 12 h visible ;
--   pas de 2e bombe à moins de 30 km (au lieu de 20) d'une zone encore active.
-- Le +15 % pour tous pendant 24 h ne change pas. Les bombes déjà lâchées gardent
-- leur rayon (bombes.rayon_km).
--
-- Une préparation avait déjà dépassé 36 h (38,7 h à 19 h 50) : son Centre serait
-- apparu d'un coup. On la recule de 12 h : il apparaît au même moment qu'avec
-- l'ancienne règle, et sa bombe grossit quand même plus vite qu'avant.
-- Les réglages vivent dans config_jeu 'batiments' (lus par batiment_reglage et
-- envoyés au jeu par mes_batiments : bombe_heures, bombe_rayons…).

begin;

update public.bombes_preparations
   set commence_le = commence_le + interval '12 hours'
 where etat = 'en_cours'
   and now() - commence_le >= interval '36 hours'
   and now() - commence_le <  interval '48 hours';

update public.config_jeu
   set valeur = (valeur::jsonb || '{"bombe_rayon1": 15, "bombe_rayon2": 20, "bombe_rayon3": 25,
                                    "bombe_niv2_h": 36, "bombe_niv3_h": 48,
                                    "bombe_devoile_h": 36, "bombe_ecart_km": 30}'::jsonb)::text
 where cle = 'batiments';

commit;

-- Contrôle : t | t | t | 0
select batiment_reglage('bombe_rayon1') = 15 and batiment_reglage('bombe_rayon2') = 20 and batiment_reglage('bombe_rayon3') = 25 as rayons_ok,
       batiment_reglage('bombe_niv1_h') = 24 and batiment_reglage('bombe_niv2_h') = 36 and batiment_reglage('bombe_niv3_h') = 48 as heures_ok,
       batiment_reglage('bombe_devoile_h') = 36 and batiment_reglage('bombe_ecart_km') = 30 as devoile_ecart_ok,
       (select count(*) from public.bombes_preparations
         where etat = 'en_cours' and now() - commence_le >= interval '36 hours') as preparations_visibles;
