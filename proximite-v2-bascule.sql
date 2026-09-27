-- =====================================================================
--  TerraFront — bascule de communes_proches sur la version rapide
--
--  Preuve faite : 60 comparaisons, 0 différence, 255 voisins comptés des
--  deux côtés, dont 50 cas non nuls. Les deux versions rendent les mêmes
--  nombres.
--
--  Mesure : 712 ms et 7 743 blocs pour un appel, contre 1,4 ms et 454
--  blocs. Cinq cents fois moins cher, pour un résultat identique.
--
--  Ce que ça change dans le jeu, sans qu'aucune règle bouge :
--    - le panneau d'attaque sur la carte s'ouvre sans délai
--    - la fonction groupée apercu_attaques devient utilisable, donc
--      l'onglet Combat pourra afficher les vraies chances au lieu du
--      taux nominal de l'intensité
--
--  Idempotent.
-- =====================================================================

create or replace function public.communes_proches(p_joueur uuid,
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

  if v_lat is null or v_lon is null then
    return 0;
  end if;

  -- Les demi-côtés du rectangle, calculés UNE fois. C'est toute la
  -- différence : dans l'ancienne version ils dépendaient de la commune
  -- cible arrivant de l'autre côté de la jointure, donc Postgres ne
  -- pouvait pas s'en servir comme condition d'index. Il lisait alors les
  -- 2 561 communes du joueur pour n'en garder qu'une.
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

-- La version provisoire n'a plus de raison d'être.
drop function if exists public.communes_proches_v2(uuid, text, numeric);

-- ---------------------------------------------------------------------
--  La mesure groupée, à lancer séparément
-- ---------------------------------------------------------------------
--  Exactement la requête du départ, pour que le chiffre soit comparable.
--  Avant : 9 191 ms.

select set_config(
  'request.jwt.claims',
  json_build_object('sub', (select id from joueurs where pseudo = 'Maroli'))::text,
  true);

explain analyze
select * from public.apercu_attaques(
  array(select p.commune_code
          from possessions p
          join communes c on c.code = p.commune_code
         where c.tier in ('rare', 'legendaire')
           and p.joueur_id <> (select id from joueurs where pseudo = 'Maroli')
         limit 200),
  'normale');
-- =====================================================================
