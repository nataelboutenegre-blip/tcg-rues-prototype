-- ===========================================================================
--  LECTURE SEULE — le rythme des paquets Terra en saison 2, pour caler le
--  taux des cartes brillantes (29 octobre 2026). Ne modifie rien.
--  Source : quetes_compteurs, clé 'terra_paquet' = paquets Terra ouverts
--  (gratuits + achetés à 200 pts). Les paquets de boutique (3 par jour au
--  plus) ne sont pas comptés.
--  Jours pleins seulement : du 26 octobre à hier (heure de Paris).
--  Une seule table, aucun pseudo (peut aller dans le dépôt).
--  Lignes : le joueur médian, le quart le plus actif, le dixième le plus
--  actif et le plus actif (brillantes PAR SEMAINE s'il joue tous les jours),
--  puis tout le jeu (brillantes PAR JOUR).
--  Colonnes « 1_sur_N » : brillantes attendues si 1 carte sur N sort brillante.
-- ===========================================================================
with j as (
  select q.joueur_id, q.jour, q.n
    from quetes_compteurs q
   where q.cle = 'terra_paquet'
     and q.jour >= date '2026-10-26'
     and q.jour < (now() at time zone 'Europe/Paris')::date
     and q.n > 0
), par_joueur as (
  select joueur_id, avg(n)::numeric as paquets_jour
    from j group by joueur_id
), lignes as (
  select 1 as ordre, 'joueur médian, par semaine' as profil, 7 as jours,
         (percentile_cont(0.5) within group (order by paquets_jour))::numeric as paquets_jour
    from par_joueur
  union all
  select 2, 'quart le plus actif, par semaine', 7,
         (percentile_cont(0.75) within group (order by paquets_jour))::numeric
    from par_joueur
  union all
  select 3, 'dixième le plus actif, par semaine', 7,
         (percentile_cont(0.9) within group (order by paquets_jour))::numeric
    from par_joueur
  union all
  select 4, 'le plus actif, par semaine', 7, max(paquets_jour)
    from par_joueur
  union all
  select 5, 'tout le jeu (' || (select count(*) from par_joueur) || ' joueurs), par jour', 1,
         sum(n)::numeric / nullif(count(distinct jour), 0)
    from j
)
select profil,
       round(paquets_jour, 1)                      as paquets_par_jour,
       round(paquets_jour * 5)                     as cartes_par_jour,
       round(paquets_jour * 5 * jours / 100.0, 1) as brillantes_1_sur_100,
       round(paquets_jour * 5 * jours / 200.0, 1) as brillantes_1_sur_200,
       round(paquets_jour * 5 * jours / 300.0, 1) as brillantes_1_sur_300,
       round(paquets_jour * 5 * jours / 500.0, 1) as brillantes_1_sur_500
  from lignes
 order by ordre;
