-- ===========================================================================
--  TerraFront — JOUR J, étape 4 : OUVERTURE DE TERRA ET DU FRONT
--  Active côté serveur tout ce qui était caché (Terra, énergie, garnisons,
--  quêtes, Bourse / Échange / Contrat en doublons). Pousser le patch du jour J
--  (SAISON2 = true, EPIQUE_VISIBLE = true) JUSTE APRÈS.
--  Pour revenir en arrière en urgence : remplacer 'true' par 'false' et relancer.
-- ===========================================================================
insert into public.config_jeu (cle, valeur) values ('terra_ouverte', 'true'::jsonb)
on conflict (cle) do update set valeur = excluded.valeur;

select public.terra_ouverte() as terra_ouverte_doit_etre_true,
       public.saison2_active() as saison2_active_doit_etre_true;
