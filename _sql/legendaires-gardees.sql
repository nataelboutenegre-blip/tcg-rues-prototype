-- ===========================================================================
--  TerraFront — La complétion automatique respecte-t-elle « une seule
--  légendaire parmi les cinq » ?
--
--  LECTURE SEULE. Ne modifie rien. Une seule requête.
--
--  LE DOUTE
--    cloturer_saison() complète les favoris à cinq en prenant les meilleures
--    communes, triées par rareté d'abord. Un joueur avec trois légendaires et
--    aucun favori en garderait donc trois — alors que la règle du 28 septembre
--    en autorise une seule, pour que le palier du haut continue de circuler
--    d'une saison à l'autre.
--
--    Aucun déclencheur de possessions ne pose cette limite. Elle est peut-être
--    dans marquer_gardee(), la fonction appelée quand on clique sur l'étoile —
--    auquel cas la complétion la contourne, ou la fait échouer.
--
--    Cette partie du code n'a jamais tourné : la simulation s'arrête avant.
--
--  CE QUE ÇA SORT
--    A — où la limite est posée, s'il y a une limite
--    B — combien de joueurs seraient complétés avec plus d'une légendaire,
--        et combien de légendaires sortiraient du jeu au lieu d'y revenir
-- ===========================================================================

with limite as (
  select case when pg_get_functiondef(p.oid) ilike '%legendaire%' then 'oui'
              else 'NON' end as posee
    from pg_proc p join pg_namespace n on n.oid = p.pronamespace
   where n.nspname = 'public' and p.proname = 'marquer_gardee'
),
contrainte as (
  select count(*) as n from pg_constraint c
   where c.conrelid = 'public.possessions'::regclass
     and pg_get_constraintdef(c.oid) ilike '%gardee%'
),
-- ce que la complétion garderait, joueur par joueur, en reproduisant son tri
simulation as (
  select p.joueur_id, c.tier,
         row_number() over (
           partition by p.joueur_id
           order by case when p.gardee then 0 else 1 end,
                    case c.tier when 'legendaire' then 1 when 'rare' then 2
                                when 'peucommun' then 3 else 4 end,
                    c.population desc nulls last,
                    p.commune_code) as rang
    from possessions p join communes c on c.code = p.commune_code
),
gardees as (
  select joueur_id,
         count(*) filter (where tier = 'legendaire') as leg_gardees
    from simulation where rang <= 5
   group by joueur_id
)

select 'A1. limite dans marquer_gardee' as controle, posee as valeur from limite
union all
select 'A2. contrainte sur la table possessions',
       case when n > 0 then 'oui, ' || n::text else 'aucune' end from contrainte
union all
select 'B1. joueurs gardant plus d''une legendaire',
       count(*)::text from gardees where leg_gardees > 1
union all
select 'B2. legendaires gardees en trop',
       coalesce(sum(leg_gardees - 1), 0)::text from gardees where leg_gardees > 1
union all
select 'B3. legendaires gardees au total',
       coalesce(sum(leg_gardees), 0)::text from gardees
union all
select 'B4. legendaires existantes dans le jeu',
       (select count(*)::text from communes where tier = 'legendaire')
union all
select 'B5. part du palier qui ne reviendrait pas au pot',
       round(100.0 * coalesce((select sum(leg_gardees) from gardees), 0)
             / nullif((select count(*) from communes where tier = 'legendaire'), 0), 1)::text || ' %'
order by 1;
