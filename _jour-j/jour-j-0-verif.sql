-- ===========================================================================
--  TerraFront — JOUR J, étape 0 : VÉRIFICATION AVANT LE JOUR J (lecture seule)
--  À lancer quand tu veux, autant de fois que tu veux. Ne modifie rien.
--  N'appelle PAS saison_courante() (qui peut armer le compte à rebours).
--  Un seul résultat (JSON) à envoyer à Claude.
-- ===========================================================================
select jsonb_pretty(jsonb_build_object(
  -- les fonctions du jour J sont bien en production
  'cloturer_saison_v2_ok', exists (select 1 from pg_proc p join pg_namespace n on n.oid = p.pronamespace
                                    where n.nspname = 'public' and p.proname = 'cloturer_saison'
                                      and pg_get_function_arguments(p.oid) like '%p_solde_depart%'),
  'rebasculer_paliers_s2_ok', to_regprocedure('public.rebasculer_paliers_s2(integer, integer, integer, integer, boolean)') is not null,
  'saison_courante_duree_fixe_ok', position('date de fin fixee' in pg_get_functiondef('public.saison_courante()'::regprocedure)) > 0,
  'terra_ouverte_doit_etre_false', public.terra_ouverte(),
  -- les derniers fichiers SQL sont passés
  's2_20_vitrine_ok', to_regclass('public.terra_vitrine') is not null,
  'siege_bloque_ok', to_regprocedure('public.commune_assiegee(text)') is not null,
  -- la saison 1 aujourd'hui
  'saison_en_cours', (select jsonb_build_object('id', id, 'etat', etat, 'fin_prevue', fin_prevue,
                         'seuil', seuil_communes, 'jours_rebours', jours_rebours)
                        from public.saisons where etat <> 'terminee' order by debut desc limit 1),
  'communes_total', (select count(*) from public.communes),
  'communes_libres', (select count(*) from public.communes) - (select count(*) from public.possessions),
  'raretes_actuelles', (select jsonb_object_agg(tier, n) from (select tier, count(*) n from public.communes group by tier) x),
  'joueurs_avec_5_favoris', (select count(*) from (select joueur_id from public.possessions where gardee
                               group by joueur_id having count(*) >= 5) f),
  'joueurs_avec_communes', (select count(distinct joueur_id) from public.possessions)
)) as verif_avant_jour_j;
