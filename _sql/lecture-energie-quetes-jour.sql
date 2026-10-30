-- ===========================================================================
--  Lecture seule — l'énergie des quêtes Front réclamées AUJOURD'HUI (30/10)
--  Remarque de Stonirr / Oshannir : « je n'ai pas reçu l'énergie des défis ».
--  Une ligne par joueur qui a réclamé une quête Front aujourd'hui.
--  energie_recue = ce que reclamer_quete a vraiment donné (colonne energie).
--  Les 2 dernières colonnes disent ce que contient reclamer_quete en base :
--  le plafond du jour et le plafond du réservoir.
--  Ne modifie rien.
-- ===========================================================================
with def as (
  select pg_get_functiondef('public.reclamer_quete(text)'::regprocedure) as d
), jour as (
  select r.joueur_id,
         count(*)                                         as quetes_front,
         count(*) filter (where r.energie = 0)            as quetes_a_zero,
         coalesce(sum(r.energie), 0)                      as energie_recue,
         string_agg(r.quete || '=' || r.energie, ', ' order by r.le) as detail,
         max(r.le) at time zone 'Europe/Paris'            as derniere
    from public.quetes_reclamees r
   where r.jour = (now() at time zone 'Europe/Paris')::date
     and r.quete like 'f\_%'
   group by r.joueur_id
)
select j.pseudo,
       q.quetes_front, q.quetes_a_zero, q.energie_recue,
       round(public.front_energie_lire(j.front_energie, j.front_energie_maj))  as energie_maintenant,
       to_char(q.derniere, 'HH24:MI')                                         as derniere_reclamee,
       q.detail,
       (regexp_match((select d from def), 'greatest\(0, (\d+) - v_deja\)'))[1] as plafond_jour,
       (regexp_match((select d from def), 'least\((\d+), v \+ v_e\)'))[1]     as plafond_reservoir
  from jour q
  join public.joueurs j on j.id = q.joueur_id
 order by q.quetes_a_zero desc, q.energie_recue;
