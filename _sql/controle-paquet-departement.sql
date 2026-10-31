-- ===========================================================================
--  TerraFront — contrôle du « Paquet du département » (31 octobre 2026)
--  LECTURE SEULE : aucune écriture, rien n'est modifié.
--
--  Le paquet tire 5 communes au hasard dans le département choisi.
--  Paris (75) n'a que 20 communes, presque toutes légendaires : le paquet
--  y donne surtout des légendaires. Revendues au jeu (600 TP pièce une fois
--  la commune possédée), elles rapportent plus que le prix du paquet.
--
--  Deux requêtes : lance-les UNE PAR UNE (sélectionne le bloc, puis Run),
--  l'éditeur n'affiche que le dernier résultat.
-- ===========================================================================

-- 1) Par département : valeur de revente attendue d'un paquet (si les 5
--    cartes sont des doublons) comparée au prix, et paquets déjà achetés.
with prix as (
  select prix from public.boutique_articles where id = 'paquet-departement'
), dep as (
  select c.departement,
         count(*)                                         as communes,
         count(*) filter (where c.tier = 'legendaire')    as legendaires,
         count(*) filter (where c.tier = 'epique')        as epiques,
         avg(coalesce(public.terra_prix_revente(c.tier), 0)) as revente_moy
    from public.communes c
   group by c.departement
), val as (
  select d.*, round(least(5, d.communes) * d.revente_moy)::int as revente_paquet_tp from dep d
)
select v.departement,
       v.communes,
       v.legendaires,
       v.epiques,
       v.revente_paquet_tp,
       (select prix from prix)                                             as prix_paquet_tp,
       count(a.id)                                                         as paquets_achetes,
       count(distinct a.joueur_id)                                         as joueurs,
       count(a.id) filter (where a.le > now() - interval '7 days')         as paquets_7j
  from val v
  left join public.boutique_achats a
         on a.article_id = 'paquet-departement' and a.departement = v.departement
 group by v.departement, v.communes, v.legendaires, v.epiques, v.revente_paquet_tp
having v.revente_paquet_tp >= 0.5 * (select prix from prix) or count(a.id) > 0
 order by v.revente_paquet_tp desc, paquets_achetes desc
 limit 40;

-- 2) Par joueur : paquets du département achetés, dont ceux où la revente
--    attendue dépasse le prix, et points gagnés en revente depuis le 1er achat.
with prix as (
  select prix from public.boutique_articles where id = 'paquet-departement'
), val as (
  select c.departement,
         least(5, count(*)) * avg(coalesce(public.terra_prix_revente(c.tier), 0)) as revente_paquet_tp
    from public.communes c
   group by c.departement
), rentables as (
  select departement from val where revente_paquet_tp >= (select prix from prix)
)
select j.pseudo,
       count(*)                                                                         as paquets_dep,
       count(*) filter (where a.departement in (select departement from rentables))     as paquets_rentables,
       string_agg(distinct a.departement, ', ')                                         as departements,
       sum(a.prix)                                                                      as tp_depenses,
       (select coalesce(sum(m.montant), 0) from public.mouvements_points m
         where m.joueur_id = a.joueur_id and m.motif = 'terra_revente'
           and m.cree_le >= min(a.le))                                                  as tp_revente_depuis,
       to_char(min(a.le) at time zone 'Europe/Paris', 'DD/MM HH24:MI')                  as premier,
       to_char(max(a.le) at time zone 'Europe/Paris', 'DD/MM HH24:MI')                  as dernier
  from public.boutique_achats a
  join public.joueurs j on j.id = a.joueur_id
 where a.article_id = 'paquet-departement'
 group by a.joueur_id, j.pseudo
 order by paquets_rentables desc, paquets_dep desc
 limit 30;
