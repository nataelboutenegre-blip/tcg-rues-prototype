-- ===========================================================================
--  s2-49 — La proximité en outre-mer (bug signalé par Arkhannou, 28/10)
--  En Guyane, les communes sont immenses : leurs centres sont souvent à plus
--  de 20 km les uns des autres (Kourou–Macouria ≈ 35 km). Un joueur qui tient
--  des communes voisines attaquait donc « à distance » (−12 points).
--  Règle en outre-mer : toutes tes communes du MÊME territoire (971, 972, 973,
--  974, 976) comptent comme proches, quelle que soit la distance. En
--  métropole, rien ne change (20 km). Le bonus reste plafonné comme avant
--  (bonus_proximite), et attaquer / apercu_attaque / apercu_attaques /
--  defendre en profitent sans être modifiées : elles appellent toutes
--  communes_proches.
--  Sécurité : la définition en production doit être celle attendue (proximite-v2) ;
--  sinon rien ne change.
--  Rejouable. Contrôle attendu : true.
-- ===========================================================================
do $do$
declare d text := pg_get_functiondef('public.communes_proches(uuid, text, numeric)'::regprocedure);
begin
  if position('s2-49' in d) > 0 then raise notice 'communes_proches : déjà à jour'; return; end if;
  if position('v_dlat := p_rayon_km / 111.19;' in d) = 0 or position('return coalesce(v_n, 0);' in d) = 0
     or position('p.joueur_id = p_joueur' in d) = 0 then
    raise exception 'communes_proches ne ressemble pas à la version attendue : rien n''a changé';
  end if;
  execute $f$
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
  v_dep  text;
  v_dlat numeric;
  v_dlon numeric;
  v_n    integer;
begin
  select latitude, longitude, departement into v_lat, v_lon, v_dep
    from communes where code = p_commune_code;

  -- s2-49 : en outre-mer, tout le territoire compte
  if length(v_dep) = 3 then
    select count(*)::integer into v_n
      from possessions p join communes c on c.code = p.commune_code
     where p.joueur_id = p_joueur and c.departement = v_dep and c.code <> p_commune_code;
    return coalesce(v_n, 0);
  end if;

  if v_lat is null or v_lon is null then
    return 0;
  end if;

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
$function$
$f$;
end $do$;

select pg_get_functiondef('public.communes_proches(uuid, text, numeric)'::regprocedure) ~ 's2-49' as outremer_territoire;
