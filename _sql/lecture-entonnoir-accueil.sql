-- ===========================================================================
--  LECTURE SEULE — l'entonnoir de l'accueil (s2-86 + patch324, 3/11/2026)
--  Pour les nouveaux comptes (moins de 14 jours) entrés dans le jeu depuis
--  patch324 : combien passent chaque étape, sur téléphone et sur ordinateur,
--  et en combien de minutes après leur arrivée (médiane).
--  « arrivés » = étape « arrive » (le jeu a commencé à se charger).
--  Les étapes viennent du jeu (une fois par joueur), sauf les lignes BASE,
--  lues dans la base. Lignes SOURCE (patch325) : d'où venaient les joueurs
--  (?src=reddit dans le lien, sinon le site d'origine, sinon « direct ») et
--  combien d'entre eux sont revenus un autre jour.
--  Aucun pseudo ni e-mail. Ne modifie rien. Un seul tableau.
-- ===========================================================================
with base as (
  select a.joueur_id, a.le as arrive_le, coalesce(a.detail, 'inconnue') as source,
         case when j.detail like 'mobile%' then 'mobile' when j.detail like 'ordi%' then 'ordi' else '?' end as appareil
    from public.accueil_etapes a
    left join public.accueil_etapes j on j.joueur_id = a.joueur_id and j.etape = 'jeu'
   where a.etape = 'arrive'
),
ordre(etape, ord, libelle) as (values
  ('arrive',          1, 'arrivés (le jeu se charge)'),
  ('jeu',             2, 'jeu affiché'),
  ('accueil_vu',      3, 'écran d''accueil vu'),
  ('accueil_ouvrir',  4, '  « Ouvrir mon premier paquet »'),
  ('accueil_passer',  5, '  « Passer »'),
  ('accueil_regles',  6, '  « Voir les règles »'),
  ('guide_1',         7, 'guide : étape 1 (deux modes)'),
  ('guide_2',         8, 'guide : étape 2 (paquets Terra)'),
  ('guide_3',         9, 'guide : étape 3 (collection)'),
  ('guide_4',        10, 'guide : étape 4 (le Front)'),
  ('guide_5',        11, 'guide : étape 5 (attaque)'),
  ('guide_6',        12, 'guide : étape 6 (chaque jour)'),
  ('guide_fini',     13, 'guide fini'),
  ('guide_passe',    14, 'guide passé avant la fin'),
  ('paquet_terra',   15, '1er paquet Terra payé'),
  ('cartes_terra',   16, '1res cartes Terra révélées'),
  ('mode_front',     17, 'passé en mode Front'),
  ('mode_terra',     18, 'passé en mode Terra'),
  ('paquet_front',   19, '1er paquet du Front payé'),
  ('cartes_front',   20, '1res communes du Front révélées'),
  ('pp_vu',          21, 'carte « Premiers pas » vue'),
  ('pp_paquet',      22, '  bouton « Ouvrir » (paquet du Front)'),
  ('pp_attaque',     23, '  bouton « Attaquer »'),
  ('pp_clan',        24, '  bouton « Voir les clans »'),
  ('pp_fonderie',    25, '  bouton « Comment ? » (Fonderie)'),
  ('pp_reclamer',    26, '  récompense récupérée')
),
etapes as (
  select coalesce(o.ord, 50) as ord, coalesce(o.libelle, e.etape) as libelle, b.joueur_id, b.appareil,
         extract(epoch from (e.le - b.arrive_le)) / 60 as minutes
    from public.accueil_etapes e
    join base b on b.joueur_id = e.joueur_id
    left join ordre o on o.etape = e.etape
  union all
  select 91, 'BASE : a une commune au Front aujourd''hui', b.joueur_id, b.appareil, null
    from base b where exists (select 1 from public.possessions p where p.joueur_id = b.joueur_id)
  union all
  select 92, 'BASE : a gagné un round ou conquis (Premiers pas 2)', b.joueur_id, b.appareil, null
    from base b where exists (select 1 from public.premiers_pas pp where pp.joueur_id = b.joueur_id and pp.attaque)
  union all
  select 93, 'BASE : revenu un autre jour', b.joueur_id, b.appareil, null
    from base b where exists (select 1 from public.jours_joues jj where jj.joueur_id = b.joueur_id
                               and jj.jour > (b.arrive_le at time zone 'Europe/Paris')::date)
  union all
  select 95, 'SOURCE : ' || b.source, b.joueur_id, b.appareil, null from base b
  union all
  select 96, 'SOURCE : ' || b.source || ' · revenus un autre jour', b.joueur_id, b.appareil, null
    from base b where exists (select 1 from public.jours_joues jj where jj.joueur_id = b.joueur_id
                               and jj.jour > (b.arrive_le at time zone 'Europe/Paris')::date)
),
total as (select count(*) as n, count(*) filter (where appareil = 'mobile') as nm, count(*) filter (where appareil = 'ordi') as no from base)
select e.libelle                                                                              as etape,
       count(distinct e.joueur_id)                                                            as joueurs,
       round(100.0 * count(distinct e.joueur_id) / nullif(t.n, 0)) || ' %'                    as part_des_arrives,
       count(distinct e.joueur_id) filter (where e.appareil = 'mobile') || ' / ' || t.nm      as telephone,
       count(distinct e.joueur_id) filter (where e.appareil = 'ordi')   || ' / ' || t.no      as ordinateur,
       round(percentile_cont(0.5) within group (order by e.minutes)::numeric, 1)              as minutes_mediane
  from etapes e cross join total t
 group by e.ord, e.libelle, t.n, t.nm, t.no
 order by e.ord, e.libelle;
