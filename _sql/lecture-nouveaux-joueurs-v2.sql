-- ===========================================================================
--  LECTURE SEULE — les nouveaux joueurs restent-ils ? (version 2, 3/11/2026)
--  Corrige le biais de la version 1 : chaque taux ne compte que les joueurs
--  qui ont tous eu le même temps pour revenir.
--
--  Groupe : comptes créés ces 14 derniers jours, avant aujourd'hui.
--  Colonnes (« x / n (p %) » : n = joueurs qui ont eu le temps) :
--   revenus_le_lendemain : a ouvert le jeu le jour qui suit son inscription
--                          (seulement les inscrits d'avant-hier ou plus tôt,
--                          dont le lendemain est terminé) ;
--   encore_la_a_j3       : a ouvert le jeu 3 jours ou plus après son
--                          inscription (inscrits il y a 4 jours ou plus) ;
--   actifs_hier_ou_auj   : a ouvert le jeu hier ou aujourd'hui.
--
--  A. Par jour d'inscription.
--  B. Paires à comparer (B01/B02, B03/B04…), toutes sur les 24 premières
--     heures : ce qu'a fait le joueur avant de décider de revenir ou non.
--     Ça reste une corrélation, pas une preuve.
--  C. Les nouveaux qui n'ont aucune commune au Front aujourd'hui : prises par
--     d'autres, libérées, ou aucune trace (jamais eu de commune au Front, ou
--     vendues au jeu : la vente ne laisse pas de trace lisible ici).
--     Les lignes C peuvent se chevaucher.
--
--  Aucun pseudo ni e-mail. Ne modifie rien. Un seul tableau.
-- ===========================================================================
with auj as (select (now() at time zone 'Europe/Paris')::date as d),
n as (
  select u.id,
         (u.created_at at time zone 'Europe/Paris')::date as inscrit,
         u.created_at
    from auth.users u join public.joueurs j on j.id = u.id
   where u.created_at >= now() - interval '14 days'
     and (u.created_at at time zone 'Europe/Paris')::date < (select d from auj)
),
f as (
  select n.id, n.inscrit,
         -- retour, à temps égal
         n.inscrit <= (select d from auj) - 2                                                                   as e1,
         exists (select 1 from public.jours_joues jj where jj.joueur_id = n.id and jj.jour = n.inscrit + 1)    as r1,
         n.inscrit <= (select d from auj) - 4                                                                   as e3,
         exists (select 1 from public.jours_joues jj where jj.joueur_id = n.id and jj.jour >= n.inscrit + 3)   as r3,
         exists (select 1 from public.jours_joues jj where jj.joueur_id = n.id and jj.jour >= (select d from auj) - 1) as actif,
         -- les 24 premières heures
         coalesce((select sum(q.n) from public.quetes_compteurs q
                    where q.joueur_id = n.id and q.cle = 'energie' and q.jour = n.inscrit), 0) > 0               as combat_j1,
         exists (select 1 from public.front_victoires v where v.joueur_id = n.id and v.type = 'conquete'
                  and v.le < n.created_at + interval '24 hours')                                                 as conquete_24h,
         exists (select 1 from public.front_prises p where p.victime = n.id
                  and p.le < n.created_at + interval '24 hours')                                                 as pris_24h,
         exists (select 1 from public.clan_membres m where m.joueur_id = n.id
                  and m.depuis < n.created_at + interval '24 hours')                                             as clan_24h,
         exists (select 1 from public.batiments b where b.joueur_id = n.id and b.type = 'fonderie'
                  and b.cree_le < n.created_at + interval '24 hours')                                            as fonderie_24h,
         -- aujourd'hui
         exists (select 1 from public.possessions p where p.joueur_id = n.id)                                   as communes_front,
         exists (select 1 from public.terra_collection t where t.joueur_id = n.id and t.exemplaires > 0)         as cartes_terra,
         exists (select 1 from public.front_prises p where p.victime = n.id)                                    as s_est_fait_prendre,
         exists (select 1 from public.front_liberations x where x.joueur_id = n.id)                             as a_libere
    from n
),
l as (
            select 'A' || to_char(inscrit, 'YYYYMMDD') as ord,
                   'A. inscrits le ' || to_char(inscrit, 'DD/MM')        as groupe, f.* from f
  union all select 'A99', 'A. TOTAL 14 jours',                                  f.* from f
  union all select 'B01', 'B01. ont attaqué/défendu le 1er jour',               f.* from f where combat_j1
  union all select 'B02', 'B02. n''ont PAS combattu le 1er jour',               f.* from f where not combat_j1
  union all select 'B03', 'B03. ont conquis une commune en 24 h',               f.* from f where conquete_24h
  union all select 'B04', 'B04. aucune conquête en 24 h',                       f.* from f where not conquete_24h
  union all select 'B05', 'B05. se sont fait PRENDRE une commune en 24 h',      f.* from f where pris_24h
  union all select 'B06', 'B06. rien perdu en 24 h',                            f.* from f where not pris_24h
  union all select 'B07', 'B07. dans un clan en 24 h',                          f.* from f where clan_24h
  union all select 'B08', 'B08. pas de clan en 24 h',                           f.* from f where not clan_24h
  union all select 'B09', 'B09. Fonderie commencée en 24 h',                    f.* from f where fonderie_24h
  union all select 'B10', 'B10. pas de Fonderie en 24 h',                       f.* from f where not fonderie_24h
  union all select 'C1',  'C1. AUCUNE commune au Front aujourd''hui',           f.* from f where not communes_front
  union all select 'C2',  'C2.   dont s''en sont fait prendre au moins une',    f.* from f where not communes_front and s_est_fait_prendre
  union all select 'C3',  'C3.   dont en ont libéré au moins une',              f.* from f where not communes_front and a_libere
  union all select 'C4',  'C4.   dont ni prise ni libération',                  f.* from f where not communes_front and not s_est_fait_prendre and not a_libere
  union all select 'C5',  'C5.   dont ont des cartes Terra',                    f.* from f where not communes_front and cartes_terra
  union all select 'C6',  'C6.   dont n''ont RIEN (ni Front ni Terra)',         f.* from f where not communes_front and not cartes_terra
)
select groupe,
       count(*) as joueurs,
       case when count(*) filter (where e1) = 0 then '—' else
         (count(*) filter (where e1 and r1)) || ' / ' || (count(*) filter (where e1)) || '  ('
         || round(100.0 * count(*) filter (where e1 and r1) / count(*) filter (where e1)) || ' %)' end as revenus_le_lendemain,
       case when count(*) filter (where e3) = 0 then '—' else
         (count(*) filter (where e3 and r3)) || ' / ' || (count(*) filter (where e3)) || '  ('
         || round(100.0 * count(*) filter (where e3 and r3) / count(*) filter (where e3)) || ' %)' end as encore_la_a_j3,
       count(*) filter (where actif) as actifs_hier_ou_auj
  from l
 group by ord, groupe
 order by ord;
