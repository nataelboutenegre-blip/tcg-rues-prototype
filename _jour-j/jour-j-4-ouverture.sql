-- ===========================================================================
--  TerraFront — JOUR J, étape 4 : OUVERTURE DE TERRA ET DU FRONT
--  Active côté serveur tout ce qui était caché (Terra, énergie, garnisons,
--  quêtes, Bourse / Échange / Contrat en doublons). Pousser le patch du jour J
--  (SAISON2 = true, EPIQUE_VISIBLE = true) JUSTE APRÈS.
--  Pour revenir en arrière en urgence : remplacer 'true' par 'false' et relancer.
-- ===========================================================================
insert into public.config_jeu (cle, valeur) values ('terra_ouverte', 'true'::jsonb)
on conflict (cle) do update set valeur = excluded.valeur;

-- la saison 2 dure 4 semaines (compte a rebours automatique 5 jours avant ;
-- demande s2-14-saison-4-semaines.sql). Doit rester aligne avec
-- DUREE_SAISON_JOURS = 28 dans app.js.
update public.saisons set fin_prevue = now() + interval '28 days'
 where id = 'saison-2' and etat = 'en_cours' and fin_prevue is null;

select public.terra_ouverte() as terra_ouverte_doit_etre_true,
       public.saison2_active() as saison2_active_doit_etre_true,
       (select fin_prevue from public.saisons where id = 'saison-2') as fin_de_la_saison_2;
