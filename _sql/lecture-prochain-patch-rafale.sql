-- ===========================================================================
--  LECTURE SEULE — prochain patch : calibrer la quête Rafale de Stonirr
--  (« trouve 5 communes »). Score = nombre de communes trouvées dans une
--  partie classée terminée, sur les 7 derniers jours. Chiffres agrégés,
--  aucun pseudo. Ne modifie rien.
-- ===========================================================================
with r as (
  select score from rafale_parties
   where fini and not amical and fin_le > now() - interval '7 days' and score is not null
)
select count(*)                                                                  as parties,
       percentile_cont(0.25) within group (order by score)::int || ' / '
       || percentile_cont(0.5) within group (order by score)::int || ' / '
       || percentile_cont(0.75) within group (order by score)::int               as score_25_med_75,
       count(*) filter (where score >= 4) || ' / ' || count(*) filter (where score >= 5) || ' / '
       || count(*) filter (where score >= 6) || ' / ' || count(*) filter (where score >= 8) as au_moins_4_5_6_8
  from r;
