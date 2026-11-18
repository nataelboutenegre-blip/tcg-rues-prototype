-- Saison 3, jour J, juste après la clôture (étape 4 ter) : bonus de territoire selon la population (s3-30, lancé éteint le 18/11).
-- Département et région × 0,6 à × 1,6 selon la population ; légendaire 45 au lieu de 60 au classement du Front.
-- Pour éteindre : la même ligne avec 0.
update public.config_jeu set valeur = ((valeur::jsonb) || '{"pop_actif": 1}'::jsonb)::text where cle = 'score_s2';
select public.score_pop_calculer() as departements_et_cantons;   -- 122 (96 départements + 26 cantons)
select public.classement_cache_maj();
-- Contrôle : 1 · 0.6 · 1.6 · 45
select score_reglage('pop_actif') as actif, score_coef_dep('48') as lozere, score_coef_dep('59') as nord, points_front('legendaire') as legendaire;
