-- ===========================================================================
--  LECTURE SEULE — Pourquoi personne ne prépare de bombe ? (3/11/2026)
--  Le 3/11 à 23 h : 8 Centres de recherche, 0 préparation depuis le début.
--  Cette lecture sépare les causes possibles :
--    - les bombes fermées ou la fonction interdite aux joueurs (réglages) ;
--    - pas assez de lingots (prix de la bombe face à la réserve) ;
--    - une réserve qui ne peut plus atteindre le prix (une Fonderie perdue :
--      la réserve plafonne alors en dessous du prix, la bombe est impossible) ;
--    - des lingots dépensés ailleurs (Forteresses posées après le Centre).
--  Seuls les joueurs qui ont un Centre sont comptés. Aucun pseudo.
--  Ne modifie rien. Un seul tableau (l'éditeur Supabase n'affiche que le
--  dernier résultat).
-- ===========================================================================
with reg as (
  select batiment_reglage('bombe_prix') as prix
),
c as (
  select x.joueur_id as id, x.pret_le, x.pret_le <= now() as pret
    from batiments x where x.type = 'centre'
),
r as (
  select c.*,
         coalesce(lingots_lire(c.id), 0)                                                   as lingots,
         lingots_max(c.id)                                                                 as mx,
         (select count(*) from batiments f where f.joueur_id = c.id and f.type = 'fonderie' and f.pret_le <= now()) as fonderies,
         (select count(*) from batiments f where f.joueur_id = c.id and f.type = 'forteresse' and f.cree_le > c.pret_le) as fort_apres,
         extract(epoch from now() - c.pret_le) / 3600                                      as pret_depuis_h
    from c
)
select '01. réglages des bombes' as ligne,
       null::bigint as nombre,
       'ouvertes : ' || case when batiment_reglage('bombes_ouvertes') = 1 then 'oui' else 'NON' end
       || ' · Centre ' || batiment_reglage('centre_prix')::integer || ' lingots'
       || ' · bombe ' || batiment_reglage('bombe_prix')::integer || ' lingots'
       || ' · portée ' || batiment_reglage('bombe_portee_km')::integer || ' km'
       || ' · rayon ' || batiment_reglage('bombe_rayon1')::integer || ' / ' || batiment_reglage('bombe_rayon2')::integer
       || ' / ' || batiment_reglage('bombe_rayon3')::integer || ' km'
       || ' à ' || batiment_reglage('bombe_niv1_h')::integer || ' / ' || batiment_reglage('bombe_niv2_h')::integer
       || ' / ' || batiment_reglage('bombe_niv3_h')::integer || ' h'
       || ' · dévoilé à ' || batiment_reglage('bombe_devoile_h')::integer || ' h' as detail
union all
select '02. les joueurs ont le droit de préparer une bombe',
       null,
       case when has_function_privilege('authenticated', 'public.bombe_preparer()', 'execute') then 'oui' else 'NON' end
union all
select '03. joueurs avec un Centre',
       count(*),
       'prêts : ' || count(*) filter (where pret) || ' · en construction : ' || count(*) filter (where not pret)
  from r
union all
select '04. Centre prêt depuis (heures)',
       count(*) filter (where pret),
       coalesce('le plus récent : ' || floor(min(pret_depuis_h) filter (where pret))
       || ' h · médiane : ' || floor((percentile_cont(0.5) within group (order by pret_depuis_h) filter (where pret))::numeric)
       || ' h · le plus ancien : ' || floor(max(pret_depuis_h) filter (where pret)) || ' h', 'aucun')
  from r
union all
select '05. Centre prêt ET assez de lingots pour une bombe',
       count(*) filter (where pret and lingots >= (select prix from reg)),
       'ils pourraient préparer une bombe tout de suite'
  from r
union all
select '06. lingots des joueurs avec un Centre prêt',
       count(*) filter (where pret),
       coalesce('min : ' || floor(min(lingots) filter (where pret))
       || ' · médiane : ' || floor((percentile_cont(0.5) within group (order by lingots) filter (where pret))::numeric)
       || ' · max : ' || floor(max(lingots) filter (where pret)), 'aucun')
  from r
union all
select '07. réserve plafonnée SOUS le prix de la bombe (bombe impossible)',
       count(*) filter (where mx < (select prix from reg)),
       'avec moins de 2 Fonderies prêtes : ' || count(*) filter (where fonderies < 2)
  from r
union all
select '08. ont posé une Forteresse après leur Centre',
       count(*) filter (where fort_apres > 0),
       'Forteresses posées après le Centre : ' || coalesce(sum(fort_apres), 0)
  from r
order by 1;
