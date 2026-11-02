-- ===========================================================================
--  TerraFront — s2-85 : l'éclat coûte 2 doublons au lieu de 3 (3/11/2026)
--  Décidé par Nataël le 3/11 à 0 h 52 : avec « ×3 » sur la carte (ta carte +
--  2 doublons), on doit pouvoir faire l'éclat. Le prix en TP ne change pas
--  (500 TP).
--
--  Le prix est un réglage (config_jeu 'brillantes', clé eclat_doublons, lu
--  par brillantes_options() et par l'éclat côté serveur) : rien d'autre à
--  modifier, la fiche du jeu affiche le nouveau prix toute seule.
--  Rejouable. Contrôle attendu : 2 | 500
-- ===========================================================================

update public.config_jeu
   set valeur = (valeur::jsonb || '{"eclat_doublons": 2}'::jsonb)::text
 where cle = 'brillantes';

-- Contrôle : 2 | 500
select (public.brillantes_options() ->> 'eclat_doublons')::int as eclat_doublons,
       (public.brillantes_options() ->> 'eclat_tp')::int       as eclat_tp;
