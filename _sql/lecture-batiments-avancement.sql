-- ===========================================================================
--  LECTURE SEULE — Front : où en sont les joueurs sur le chemin
--  Fonderie → 2e Fonderie → Centre de recherche → bombe (saison 2).
--  Pour décider s'il faut baisser les prix (fonderie2_prix, centre_prix).
--  « Actif » = a ouvert le jeu dans les 2 derniers jours ET tient au moins
--  une commune au Front. Les autres lignes comptent TOUS les joueurs.
--  « Réserve pleine » = la réserve est au plafond (30 ou 45) : le joueur ne
--  gagne plus rien, signe qu'il n'a rien à acheter ou qu'il n'est pas venu.
--  Aucun pseudo. Ne modifie rien.
--  Un seul tableau (l'éditeur Supabase n'affiche que le dernier résultat).
-- ===========================================================================
with auj as (select (now() at time zone 'Europe/Paris')::date as d),
actifs as (
  select j.id
    from joueurs j
   where exists (select 1 from possessions p where p.joueur_id = j.id)
     and (select max(jj.jour) from jours_joues jj where jj.joueur_id = j.id) >= (select d from auj) - 2
),
b as (
  select j.id,
         count(*) filter (where x.type = 'fonderie')                              as fonderies,
         count(*) filter (where x.type = 'fonderie' and x.pret_le <= now())       as fonderies_pretes,
         count(*) filter (where x.type = 'forteresse')                            as forteresses,
         count(*) filter (where x.type = 'centre')                                as centre,
         count(*) filter (where x.type = 'centre' and x.pret_le <= now())         as centre_pret,
         min(x.cree_le) filter (where x.type = 'fonderie')                        as fonderie1_le
    from joueurs j join batiments x on x.joueur_id = j.id
   group by j.id
),
r as (
  select b.*, coalesce(lingots_lire(b.id), 0) as lingots, lingots_max(b.id) as mx,
         exists (select 1 from bombes_preparations p where p.joueur_id = b.id and p.etat = 'en_cours') as prepare,
         (select count(*) from bombes bo where bo.lanceur = b.id)                                     as bombes
    from b
)
select '01. joueurs actifs au Front' as etape,
       (select count(*) from actifs) as joueurs,
       null::text as detail
union all
select '02. ont posé une Fonderie',
       count(*),
       'dont actifs : ' || count(*) filter (where id in (select id from actifs))
       || ' · 1re Fonderie posée, médiane : ' || to_char(percentile_disc(0.5) within group (order by fonderie1_le) at time zone 'Europe/Paris', 'DD/MM HH24"h"')
  from r where fonderies >= 1
union all
select '03. ont 2 Fonderies',
       count(*),
       'dont actifs : ' || count(*) filter (where id in (select id from actifs))
  from r where fonderies >= 2
union all
select '04. ont au moins une Forteresse',
       count(*),
       'Forteresses au total : ' || coalesce(sum(forteresses), 0)
  from r where forteresses >= 1
union all
select '05. ont un Centre de recherche',
       count(*),
       'prêts : ' || count(*) filter (where centre_pret >= 1)
  from r where centre >= 1
union all
select '06. 2 Fonderies, pas de Centre, déjà 40 lingots ou plus',
       count(*),
       'pourraient construire le Centre tout de suite'
  from r where fonderies >= 2 and centre = 0 and lingots >= 40
union all
select '07. préparent une bombe',
       count(*) filter (where prepare),
       null
  from r
union all
select '08. ont déjà lâché une bombe',
       count(*) filter (where bombes > 0),
       'bombes lâchées au total : ' || coalesce(sum(bombes), 0)
  from r
union all
select '09. réserve pleine (ne gagnent plus rien)',
       count(*) filter (where lingots >= mx),
       'avec 1 Fonderie : ' || count(*) filter (where lingots >= mx and fonderies = 1)
       || ' · avec 2 : ' || count(*) filter (where lingots >= mx and fonderies >= 2)
  from r where fonderies_pretes >= 1
union all
select '10. lingots en réserve (joueurs avec une Fonderie prête)',
       count(*),
       'moyenne : ' || round(avg(lingots)) || ' · médiane : ' || round((percentile_cont(0.5) within group (order by lingots))::numeric)
       || ' · max : ' || floor(max(lingots))
  from r where fonderies_pretes >= 1
order by 1;
