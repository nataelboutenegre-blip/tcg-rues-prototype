-- ===========================================================================
--  TerraFront — DATE DE FIN DE LA SAISON 1 : dimanche 25 octobre 2026, 10 h
--  (heure de Paris). Rejouable.
--
--  Effet (grâce à s2-14) :
--   - le compte à rebours s'arme tout seul 5 jours avant, le mardi 20 à 10 h ;
--   - la règle des 3 000 communes libres ne joue plus pour la saison 1 ;
--   - l'écran affiche « Fin de saison dans N jours · le 25 octobre ».
--  Attention : passage à l'heure d'hiver la nuit du 24 au 25. La date est
--  écrite en heure de Paris, Postgres fait la conversion tout seul.
--
--  N'appelle PAS saison_courante(). Pour annuler : remettre fin_prevue à null
--  (seulement tant que l'état est encore 'en_cours').
-- ===========================================================================
update public.saisons
   set fin_prevue = timestamptz '2026-10-25 10:00:00 Europe/Paris'
 where id = 'saison-1' and etat = 'en_cours';

-- contrôle attendu : saison-1 | en_cours | 2026-10-25 09:00:00+00 (10 h à Paris, déjà en heure d hiver) | true
select id, etat, fin_prevue,
       position('date de fin fixee' in pg_get_functiondef('public.saison_courante()'::regprocedure)) > 0
         as regle_date_en_place_doit_etre_true
  from public.saisons where id = 'saison-1';
