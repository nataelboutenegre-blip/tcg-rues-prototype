-- =====================================================================
--  TerraFront — communes_proches, version 2 : partir du rectangle
--
--  Le plan a parlé : pour chacune des 2 561 communes du joueur, Postgres
--  lit la ligne complète dans communes, puis en jette 2 560 sur le
--  rectangle. Une seule était à moins de 20 km.
--
--  Le rectangle ne peut pas servir d'index tant que ses bornes viennent
--  de l'autre côté de la jointure. On calcule donc les coordonnées de la
--  cible d'abord, dans des variables : elles deviennent des constantes,
--  et l'index des coordonnées devient utilisable. Le rectangle contient
--  une centaine de communes sur 34 739 — le reste n'est jamais lu.
--
--  LA FORMULE EST RECOPIÉE À L'IDENTIQUE. Même rayon, même conversion
--  degrés-kilomètres, même exclusion de la cible, même distance
--  euclidienne corrigée par le cosinus de la latitude.
--
--  Mais « recopiée à l'identique » est une intention, pas une preuve :
--  ce fichier crée la nouvelle fonction SOUS UN AUTRE NOM et la compare
--  à l'ancienne sur des cas réels. On ne remplace rien aujourd'hui.
--
--  Idempotent.
-- =====================================================================

-- ---------------------------------------------------------------------
--  1. L'index qui rend le rectangle utilisable
-- ---------------------------------------------------------------------
create index if not exists communes_coord_idx
  on public.communes (latitude, longitude);

analyze public.communes;

-- ---------------------------------------------------------------------
--  2. La nouvelle version, sous un nom provisoire
-- ---------------------------------------------------------------------
create or replace function public.communes_proches_v2(p_joueur uuid,
                                                      p_commune_code text,
                                                      p_rayon_km numeric default 20)
returns integer
language plpgsql
stable
security definer
set search_path to 'public'
as $function$
declare
  v_lat  numeric;
  v_lon  numeric;
  v_dlat numeric;
  v_dlon numeric;
  v_n    integer;
begin
  select latitude, longitude into v_lat, v_lon
    from communes where code = p_commune_code;

  -- une commune sans coordonnées n'a aucun voisin mesurable
  if v_lat is null or v_lon is null then
    return 0;
  end if;

  -- les demi-côtés du rectangle, calculés UNE fois : c'est tout l'objet
  -- de cette version. Dans l'ancienne, ils étaient recalculés pour chaque
  -- commune du joueur, et donc inutilisables par un index.
  v_dlat := p_rayon_km / 111.19;
  v_dlon := p_rayon_km / (111.19 * cos(radians(v_lat)));

  select count(*)::integer into v_n
    from communes c
    join possessions p on p.commune_code = c.code
   where c.latitude  between v_lat - v_dlat and v_lat + v_dlat
     and c.longitude between v_lon - v_dlon and v_lon + v_dlon
     and c.code <> p_commune_code
     and p.joueur_id = p_joueur
     and 111.19 * sqrt(
           power(c.latitude - v_lat, 2)
         + power((c.longitude - v_lon) * cos(radians(v_lat)), 2)
         ) <= p_rayon_km;

  return coalesce(v_n, 0);
end;
$function$;

grant execute on function public.communes_proches_v2(uuid, text, numeric) to authenticated;

-- ---------------------------------------------------------------------
--  3. LA PREUVE — les deux versions doivent répondre la même chose
-- ---------------------------------------------------------------------
--  30 communes au hasard, pour les deux joueurs qui ont le plus de
--  territoire. L'ancienne version met environ 0,7 s par appel, donc
--  compte à peu près une minute. C'est le prix de la certitude.
--
--  « differences » doit valoir 0. S'il ne vaut pas 0, on ne remplace
--  rien et je regarde les cas qui divergent.

with cibles as (
  select code from communes
   where latitude is not null
   order by random()
   limit 30
),
joueurs_test as (
  select p.joueur_id as id
    from possessions p
   group by p.joueur_id
   order by count(*) desc
   limit 2
),
comparaison as (
  select j.id, c.code,
         communes_proches(j.id, c.code, 20)    as ancien,
         communes_proches_v2(j.id, c.code, 20) as nouveau
    from cibles c cross join joueurs_test j
)
select count(*)                                       as comparaisons,
       count(*) filter (where ancien <> nouveau)      as differences,
       sum(ancien)                                    as total_ancien,
       sum(nouveau)                                   as total_nouveau,
       count(*) filter (where ancien > 0)             as cas_non_nuls
  from comparaison;

-- ---------------------------------------------------------------------
--  4. Le gain, une fois la preuve faite
-- ---------------------------------------------------------------------
--  À lancer séparément. Avant : 712 ms, 7 743 blocs.

explain (analyze, buffers)
select public.communes_proches_v2(
         (select id from joueurs where pseudo = 'Maroli'),
         '69204', 20);
-- =====================================================================
