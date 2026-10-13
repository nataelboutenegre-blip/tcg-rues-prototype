-- ===========================================================================
--  TerraFront — taux de retour des joueurs (12 octobre 2026)
--  LECTURE SEULE : rien n'est créé ni modifié. Un seul résultat (JSON) à
--  envoyer à Claude.
--
--  Un joueur est « actif » un jour (heure de Paris) s'il a fait au moins une
--  chose qui laisse une trace : une commune obtenue (historique, depuis le
--  début), un évènement du journal (30 derniers jours), un mouvement de points
--  (depuis le 3 octobre). Ouvrir le jeu sans rien faire ne laisse AUCUNE
--  trace : les taux sont donc des minimums.
--   - J1  : actif le lendemain de l'inscription ;
--   - J7  : actif le 7e jour ;  J30 : actif le 30e jour ;
--   - « revenu après J7 » : actif au moins une fois à partir du 7e jour.
--  Seuls comptent les joueurs inscrits depuis assez longtemps pour chaque taux.
--  Le compte de Nataël (exclus_classement) est retiré.
-- ===========================================================================
with joueurs_ok as (
  select j.id, (j.created_at at time zone 'Europe/Paris')::date as inscrit
    from public.joueurs j
   where j.created_at is not null and not public.est_exclu_classement(j.pseudo)
), traces as (
  select h.joueur_id as id, (h.acquired_at at time zone 'Europe/Paris')::date as jour from public.historique h
  union
  select jl.acteur, (jl.cree_le at time zone 'Europe/Paris')::date from public.journal jl where jl.acteur is not null
  union
  select mp.joueur_id, (mp.cree_le at time zone 'Europe/Paris')::date from public.mouvements_points mp
), aujourdhui as (
  select (now() at time zone 'Europe/Paris')::date as d
), par_joueur as (
  select jo.id, jo.inscrit,
         (select d from aujourdhui) - jo.inscrit as anciennete,
         bool_or(t.jour = jo.inscrit + 1)  as j1,
         bool_or(t.jour = jo.inscrit + 7)  as j7,
         bool_or(t.jour = jo.inscrit + 30) as j30,
         bool_or(t.jour >= jo.inscrit + 7) as apres_j7,
         bool_or(t.jour >= (select d from aujourdhui) - 6) as actif_7_derniers_jours,
         count(distinct t.jour) as jours_actifs,
         max(t.jour) as dernier_jour
    from joueurs_ok jo left join traces t on t.id = jo.id
   group by jo.id, jo.inscrit
), taux as (
  select 'J1' as quoi, 1 as delai, count(*) filter (where anciennete >= 2) as base,
         count(*) filter (where anciennete >= 2 and j1) as revenus from par_joueur
  union all
  select 'J7', 7, count(*) filter (where anciennete >= 8), count(*) filter (where anciennete >= 8 and j7) from par_joueur
  union all
  select 'J30', 30, count(*) filter (where anciennete >= 31), count(*) filter (where anciennete >= 31 and j30) from par_joueur
  union all
  select 'revenu apres J7', 7, count(*) filter (where anciennete >= 8), count(*) filter (where anciennete >= 8 and apres_j7) from par_joueur
)
select jsonb_pretty(jsonb_build_object(
  'comptes', (select count(*) from par_joueur),
  'comptes_sans_aucune_trace', (select count(*) from par_joueur where jours_actifs = 0),
  'premiere_inscription', (select min(inscrit) from par_joueur),
  'actifs_7_derniers_jours', (select count(*) from par_joueur where actif_7_derniers_jours),
  'taux', (select jsonb_agg(jsonb_build_object('quoi', quoi, 'joueurs_eligibles', base, 'revenus', revenus,
                    'pourcent', case when base > 0 then round(100.0 * revenus / base) end) order by delai, quoi) from taux),
  'inscriptions_par_semaine', (select jsonb_agg(jsonb_build_object('semaine_du', s, 'inscrits', n, 'actifs_7_derniers_jours', a) order by s)
                    from (select date_trunc('week', inscrit)::date s, count(*) n, count(*) filter (where actif_7_derniers_jours) a
                            from par_joueur group by 1) w),
  'actifs_par_jour_14_derniers_jours', (select jsonb_object_agg(jour, n) from
                    (select t.jour, count(distinct t.id) n from traces t join joueurs_ok jo on jo.id = t.id
                      where t.jour >= (select d from aujourdhui) - 13 group by t.jour) x),
  'jours_actifs_repartition', (select jsonb_object_agg(tranche, n) from
                    (select case when jours_actifs = 0 then '0' when jours_actifs = 1 then '1' when jours_actifs <= 3 then '2-3'
                                 when jours_actifs <= 7 then '4-7' when jours_actifs <= 14 then '8-14' else '15+' end tranche, count(*) n
                       from par_joueur group by 1) r)
)) as retours;
