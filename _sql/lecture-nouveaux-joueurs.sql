-- ===========================================================================
--  LECTURE SEULE — les nouveaux joueurs restent-ils, et qu'est-ce qui les retient ?
--  Groupe : comptes créés ces 14 derniers jours, avant aujourd'hui (ceux
--  d'aujourd'hui n'ont pas encore pu « revenir »).
--  « Revenu » = a ouvert le jeu un autre jour que celui de son inscription
--  (jours_joues, jour de Paris).
--  « Actif » = a ouvert le jeu hier ou aujourd'hui.
--  Chaque ligne est un sous-groupe, avec son propre taux de retour : comparer
--  les lignes qui vont par paire (03/04, 05/06, 07/08, 09/10).
--  Attention : c'est une corrélation. Un joueur qui revient a plus de temps
--  pour rejoindre un clan ou se faire attaquer : regarder surtout les
--  critères des premières heures (03/04, 05/06, 09/10).
--  Aucun pseudo ni e-mail. Ne modifie rien. Un seul tableau.
-- ===========================================================================
with auj as (select (now() at time zone 'Europe/Paris')::date as d),
n as (
  select u.id,
         (u.created_at at time zone 'Europe/Paris')::date                         as inscrit,
         u.created_at
    from auth.users u join joueurs j on j.id = u.id
   where u.created_at >= now() - interval '14 days'
     and (u.created_at at time zone 'Europe/Paris')::date < (select d from auj)
),
f as (
  select n.id,
         -- retour
         exists (select 1 from jours_joues jj where jj.joueur_id = n.id and jj.jour > n.inscrit)               as revenu,
         exists (select 1 from jours_joues jj where jj.joueur_id = n.id and jj.jour >= (select d from auj) - 1) as actif,
         -- 1er jour
         coalesce((select sum(q.n) from quetes_compteurs q where q.joueur_id = n.id and q.cle = 'energie'
                    and q.jour = n.inscrit), 0) > 0                                                          as combat_j1,
         exists (select 1 from front_victoires v where v.joueur_id = n.id and v.type = 'conquete'
                  and v.le < n.created_at + interval '24 hours')                                             as conquete_24h,
         exists (select 1 from front_victoires v where v.adversaire = n.id and v.type = 'conquete'
                  and v.le < n.created_at + interval '48 hours')                                             as pris_48h,
         -- depuis
         coalesce((select sum(q.n) from quetes_compteurs q where q.joueur_id = n.id and q.cle = 'energie'), 0) > 0 as a_combattu,
         exists (select 1 from front_victoires v where v.joueur_id = n.id and v.type = 'conquete')            as a_conquis,
         exists (select 1 from clan_membres m where m.joueur_id = n.id)
           or exists (select 1 from clan_departs d where d.joueur_id = n.id)                                  as clan,
         exists (select 1 from batiments b where b.joueur_id = n.id and b.type = 'fonderie')                  as fonderie,
         exists (select 1 from possessions p where p.joueur_id = n.id)                                        as communes_front
    from n
),
l as (
            select '01. TOUS les nouveaux (14 j)'                         as groupe, * from f
  union all select '02. inscrits il y a 3 jours ou plus',                f.* from f join n using (id) where n.inscrit <= (select d from auj) - 3
  union all select '03. ont attaqué/défendu le 1er jour',                * from f where combat_j1
  union all select '04. n''ont PAS combattu le 1er jour',                * from f where not combat_j1
  union all select '05. ont conquis une commune en 24 h',                * from f where conquete_24h
  union all select '06. aucune conquête en 24 h',                        * from f where not conquete_24h
  union all select '07. dans un clan (ou l''ont été)',                   * from f where clan
  union all select '08. jamais de clan',                                 * from f where not clan
  union all select '09. se sont fait PRENDRE une commune en 48 h',       * from f where pris_48h
  union all select '10. rien perdu en 48 h',                             * from f where not pris_48h
  union all select '11. ont une Fonderie',                               * from f where fonderie
  union all select '12. n''ont jamais combattu du tout',                 * from f where not a_combattu
  union all select '13. n''ont plus AUCUNE commune au Front',            * from f where not communes_front
)
select groupe,
       count(*)                                                            as joueurs,
       count(*) filter (where revenu)                                      as revenus,
       case when count(*) > 0 then round(100.0 * count(*) filter (where revenu) / count(*)) || ' %' end as taux_retour,
       count(*) filter (where actif)                                       as actifs_hier_ou_auj
  from l
 group by groupe
 order by groupe;
