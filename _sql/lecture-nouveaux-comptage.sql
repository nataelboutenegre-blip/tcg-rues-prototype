-- ===========================================================================
--  LECTURE SEULE — d'où vient la hausse du nombre de joueurs ?
--  Sépare les vrais nouveaux comptes (créés récemment) des anciens comptes
--  revenus jouer, et compte ceux d'aujourd'hui (absents de
--  lecture-nouveaux-joueurs.sql). Aucun pseudo ni e-mail. Un seul tableau.
-- ===========================================================================
with auj as (select (now() at time zone 'Europe/Paris')::date as d),
u as (
  select u.id, (u.created_at at time zone 'Europe/Paris')::date as inscrit,
         exists (select 1 from joueurs j where j.id = u.id)                          as a_pseudo,
         (select max(jj.jour) from jours_joues jj where jj.joueur_id = u.id)         as dernier_jour,
         exists (select 1 from possessions p where p.joueur_id = u.id)               as communes_front
    from auth.users u
)
select ligne, nombre from (
            select '01. comptes au total'                                          as ligne, count(*)::text as nombre from u
  union all select '02. comptes créés AUJOURD''HUI',                               count(*)::text from u where inscrit = (select d from auj)
  union all select '03. comptes créés HIER',                                       count(*)::text from u where inscrit = (select d from auj) - 1
  union all select '04. comptes créés ces 7 derniers jours (aujourd''hui compris)', count(*)::text from u where inscrit > (select d from auj) - 7
  union all select '05. comptes créés ces 14 derniers jours (aujourd''hui compris)', count(*)::text from u where inscrit > (select d from auj) - 14
  union all select '06.   dont sans pseudo (inscription pas terminée)',            count(*)::text from u where inscrit > (select d from auj) - 14 and not a_pseudo
  union all select '07. joueurs venus AUJOURD''HUI',                               count(*)::text from u where dernier_jour = (select d from auj)
  union all select '08. joueurs venus depuis 7 jours',                             count(*)::text from u where dernier_jour > (select d from auj) - 7
  union all select '09.   dont comptes créés il y a plus de 14 jours (anciens revenus)', count(*)::text from u where dernier_jour > (select d from auj) - 7 and inscrit <= (select d from auj) - 14
  union all select '10. joueurs avec au moins une commune au Front',               count(*)::text from u where communes_front
  union all select '11. inscriptions par jour (14 j)',
         string_agg(to_char(j, 'DD/MM') || ' : ' || n, ' · ' order by j)
    from (select inscrit as j, count(*) as n from u where inscrit > (select d from auj) - 14 group by inscrit) x
) t
order by ligne;
