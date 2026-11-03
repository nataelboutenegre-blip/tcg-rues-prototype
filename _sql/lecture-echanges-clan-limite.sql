-- ===========================================================================
--  LECTURE SEULE — échanges de clan : la limite de 3 par jour gêne-t-elle ?
--  (3/11/2026, proposition d'Oshannir : « 3 échanges par membre »)
--  Depuis le 28/10 (s2-50 : 3 échanges conclus par jour et par joueur).
--  Un échange accepté compte pour les deux joueurs.
--   JOUR   : échanges acceptés, joueurs qui en ont conclu, et combien ont
--            atteint 1, 2 ou 3 (la limite) ce jour-là ; propositions refusées
--            ou expirées.
--   PAIRE  : jours où un joueur a fait 2 échanges ou plus avec le MÊME membre
--            (ce que changerait une limite « par membre »).
--   CLAN   : échanges acceptés depuis le 28/10 par clan, avec sa taille.
--  Aucun pseudo (les sigles de clan seulement). Ne modifie rien. Un seul tableau.
-- ===========================================================================
with e as (
  select x.*, (x.repondu_le at time zone 'Europe/Paris')::date as jour_rep,
              (x.cree_le    at time zone 'Europe/Paris')::date as jour_prop
    from public.clan_echanges x
   where x.cree_le >= timestamptz '2026-10-28 00:00 Europe/Paris'
),
acc as (
  select jour_rep as jour, proposant as joueur, destinataire as autre, clan_id from e where etat = 'accepte'
  union all
  select jour_rep, destinataire, proposant, clan_id from e where etat = 'accepte'
),
pj as (select jour, joueur, count(*) as n from acc group by 1, 2),
paire as (select jour, joueur, autre, count(*) as n from acc group by 1, 2, 3),
jours as (select distinct jour_prop as jour from e union select distinct jour from acc)
select 1 as ordre, 'JOUR' as quoi, to_char(j.jour, 'DD/MM') as ligne,
       'acceptés ' || (select count(*) from e where etat = 'accepte' and jour_rep = j.jour)
       || ' · joueurs ' || (select count(*) from pj where pj.jour = j.jour)
       || ' (à 1 : ' || (select count(*) from pj where pj.jour = j.jour and n = 1)
       || ', à 2 : ' || (select count(*) from pj where pj.jour = j.jour and n = 2)
       || ', à 3 : '  || (select count(*) from pj where pj.jour = j.jour and n >= 3) || ')'
       || ' · refusés ' || (select count(*) from e where etat = 'refuse' and jour_rep = j.jour)
       || ' · expirés ' || (select count(*) from e where etat = 'expire' and jour_prop = j.jour) as valeur
  from jours j where j.jour is not null
union all
select 2, 'TOTAL', 'jours-joueurs',
       (select count(*) from pj) || ' jours-joueurs avec au moins 1 échange, dont '
       || (select count(*) from pj where n >= 3) || ' à la limite de 3 ('
       || coalesce(round(100.0 * (select count(*) from pj where n >= 3) / nullif((select count(*) from pj), 0)), 0) || ' %)'
       || ' · ' || (select count(distinct joueur) from pj where n >= 3) || ' joueurs différents ont touché la limite'
union all
select 3, 'PAIRE', 'même membre',
       (select count(*) from paire where n >= 2) || ' fois un joueur a fait 2 échanges ou plus avec le même membre le même jour'
       || ' · paires différentes par jour en moyenne : '
       || coalesce((select round(avg(k), 1) from (select count(*) as k from paire group by jour, joueur) z), 0)
union all
select 4, 'CLAN', '[' || c.tag || ']',
       count(e.id) || ' échanges acceptés · ' || (select count(*) from public.clan_membres m where m.clan_id = c.id) || ' membres aujourd''hui'
  from public.clans c left join e on e.clan_id = c.id and e.etat = 'accepte'
 group by c.id, c.tag
order by 1, 3;
