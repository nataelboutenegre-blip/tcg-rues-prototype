-- s3-38 : la recherche de la mallette (bombe) trouve le nom exact (signalé par D.C.A, 20/11 : « Saint-Sulpice (63) » introuvable).
-- Avant : 15 candidats triés par population, puis 6 ; un petit « Saint-Sulpice » passait après les « Saint-Sulpice-… ».
-- Maintenant : le nom exact d'abord, puis les plus proches de tes communes ; et un numéro de département
-- tapé avec le nom (« saint sulpice 63 ») filtre sur ce département.
-- Retour arrière : la version d'avant est dans s2-118 (même signature).
create or replace function public.bombe_chercher(p_texte text)
 returns table(code text, nom text, dept text, distance_km integer, ok boolean, raison text, lat double precision, lon double precision)
 language plpgsql stable security definer
 set search_path to 'public', 'extensions'
as $function$
#variable_conflict use_column
declare
  v_uid uuid := auth.uid();
  v_d text := upper(substring(coalesce(p_texte, '') from '(?:^|[^0-9A-Za-z])(97[1-6]|[0-9]{2}|2[AaBb])(?:$|[^0-9A-Za-z])'));   -- s3-38
  v_m text := btrim(regexp_replace(unaccent(lower(btrim(regexp_replace(coalesce(p_texte, ''), '(^|[^0-9A-Za-z])(97[1-6]|[0-9]{2}|2[AaBb])($|[^0-9A-Za-z])', ' ', 'g')))), '[^a-z]+', ' ', 'g'));
  v_c text;
  v_p double precision := coalesce(batiment_reglage('bombe_portee_km'), 50);
begin
  if v_uid is null then raise exception 'Non connecte'; end if;
  v_c := replace(v_m, ' ', '');
  if length(v_c) < 2 then return; end if;
  return query
  with bb as (
    select min(m.latitude) - v_p / 111.0 la0, max(m.latitude) + v_p / 111.0 la1,
           min(m.longitude) - v_p / 78.0 lo0, max(m.longitude) + v_p / 78.0 lo1
      from possessions p join communes m on m.code = p.commune_code
     where p.joueur_id = v_uid and m.latitude is not null
  ), t as (
    select c.code, c.nom, c.departement, c.population, c.latitude::double precision lat, c.longitude::double precision lon,
           regexp_replace(unaccent(lower(c.nom)), '[^a-z]+', ' ', 'g') k,
           regexp_replace(unaccent(lower(c.nom)), '[^a-z]+', '', 'g') kc
      from communes c
     where c.latitude is not null
       and (v_d is null or c.departement = v_d)
  ), m as (
    select t.*, (t.kc = v_c) exact, (t.kc like v_c || '%') debut,
           coalesce(t.lat between bb.la0 and bb.la1 and t.lon between bb.lo0 and bb.lo1, false) proche
      from t cross join bb
     where t.kc like v_c || '%'
        or (length(v_m) >= 3 and t.k like '% ' || v_m || '%')
        or (length(v_c) >= 4 and t.kc like '%' || v_c || '%')
     order by exact desc, proche desc, debut desc, t.population desc nulls last
     limit 20
  ), r as (
    select m.*, bombe_refus(v_uid, m.lat, m.lon) refus, dist_mes_communes(v_uid, m.lat, m.lon) dk from m
  )
  select r.code, r.nom, r.departement, round(r.dk)::integer,
         r.refus is null, r.refus, r.lat, r.lon
    from r
   order by r.exact desc, (r.refus is null) desc, r.debut desc, r.dk nulls last, r.population desc nulls last
   limit 6;
end;
$function$;

-- contrôle : 'saint sulpice 63' -> Saint-Sulpice (63) en premier
