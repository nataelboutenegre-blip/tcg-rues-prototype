-- ===========================================================================
--  TerraFront — D'où viennent les cartes : du paquet ou du combat ?
--
--  LECTURE SEULE. Ne modifie rien.
--  Tout coller, lancer, me coller le résultat. Une seule requête.
--
--  N'APPELLE PAS saison_courante() : cette fonction arme le compte à rebours
--  de fin de saison. Mesurer ne doit jamais déclencher une fin de saison.
--
--  LA QUESTION
--    Le combat ne vide pas le pot : une commune conquise change de main, elle
--    ne sort pas du jeu. Les paquets, eux, la sortent définitivement. Donc la
--    part des paquets dans les acquisitions dit combien de joueurs le jeu peut
--    accueillir avant que la carte ne se vide en quelques jours.
--
--  CE QU'IL FAUT SAVOIR SUR LES CHIFFRES
--    — Les lignes « tirage » du journal ne gardent QUE les rares et les
--      légendaires (trg_journal_tirage filtre dessus). Elles ne peuvent donc
--      pas servir à compter les cartes tirées.
--    — On passe par objectifs_compteurs.total_paquets, multiplié par 5 tirages
--      par paquet. Ce compteur inclut les paquets offerts par les objectifs,
--      ce qui est voulu : ce sont aussi des cartes sorties du pot.
--    — total_paquets ne remonte qu'à la pose du déclencheur trg_suivi_paquet,
--      pas au premier jour du jeu. Le chiffre est donc un PLANCHER.
--    — Les conquêtes viennent du journal, complet depuis le 13 septembre
--      (la purge ne frappe qu'au-delà de 30 jours).
-- ===========================================================================

with pot as (
  select (select count(*) from communes)   as total,
         (select count(*) from possessions) as prises
),
par_type as (
  select type, count(*) as n,
         count(*) filter (where cree_le > now() - interval '3 days')  as j3,
         count(*) filter (where cree_le > now() - interval '7 days')  as j7,
         count(*) filter (where cree_le > now() - interval '14 days') as j14
    from journal group by type
),
paquets as (
  select coalesce(sum(total_paquets), 0) as nb,
         coalesce(sum(total_paquets), 0) * 5 as cartes,
         coalesce(sum(total_conquetes), 0) as conquetes
    from objectifs_compteurs
),
joueurs_actifs as (
  select count(*) as n from objectifs_compteurs
   where jour > current_date - 7
)

select 'A1. communes au total' as mesure, total::text as valeur from pot
union all select 'A2. prises par un joueur', prises::text from pot
union all select 'A3. encore libres', (total - prises)::text from pot
union all select 'A4. part du pot deja prise',
       round(100.0 * prises / nullif(total, 0), 1)::text || ' %' from pot

union all select 'B1. cartes sorties par les paquets (plancher)', cartes::text from paquets
union all select 'B2. paquets ouverts (plancher)', nb::text from paquets
union all select 'B3. conquetes (compteur)', conquetes::text from paquets
union all select 'B4. conquetes (journal)', coalesce((select n from par_type where type = 'conquete'), 0)::text
union all select 'B5. une conquete pour N cartes tirees',
       round((select cartes from paquets)::numeric
             / nullif((select coalesce(n, 0) from par_type where type = 'conquete'), 0), 1)::text

union all select 'C1. achats a la bourse', coalesce((select n from par_type where type = 'achat'), 0)::text
union all select 'C2. echanges', coalesce((select n from par_type where type = 'echange'), 0)::text
union all select 'C3. contrats', coalesce((select n from par_type where type = 'contrat'), 0)::text

union all select 'D1. conquetes sur 3 jours', coalesce((select j3 from par_type where type = 'conquete'), 0)::text
union all select 'D2. conquetes sur 7 jours', coalesce((select j7 from par_type where type = 'conquete'), 0)::text
union all select 'D3. conquetes sur 14 jours', coalesce((select j14 from par_type where type = 'conquete'), 0)::text
union all select 'D4. conquetes par jour (sur 7 j)',
       round(coalesce((select j7 from par_type where type = 'conquete'), 0) / 7.0, 1)::text

union all select 'E1. joueurs actifs sur 7 jours', n::text from joueurs_actifs
union all select 'E2. cartes tirees par joueur (plancher)',
       round((select cartes from paquets)::numeric / nullif((select n from joueurs_actifs), 0), 0)::text
order by 1;
