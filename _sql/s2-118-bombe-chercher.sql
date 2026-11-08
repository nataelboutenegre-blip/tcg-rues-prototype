-- s2-118 (8/11/2026) : la recherche de la cible dans la mallette (signalé par Oshannir).
--   - tirets, espaces et apostrophes ne comptent plus : « SAINTJEAN » trouve
--     Saint-Jean-de-Luz, « BOURGENBRESSE » trouve Bourg-en-Bresse ;
--   - le mot du milieu marche toujours (« BRESSE ») ;
--   - les communes proches des siennes passent devant (boîte autour de ses
--     communes, élargie de la portée), puis la portée exacte est vérifiée sur
--     15 candidates (même temps de réponse qu'avant, ~0,5 s pour un joueur à 1 900 communes), et celles qu'on peut viser sont en tête des 6 proposées.

begin;

create or replace function public.bombe_chercher(p_texte text)
 returns table(code text, nom text, dept text, distance_km integer, ok boolean, raison text, lat double precision, lon double precision)
 language plpgsql stable security definer set search_path to 'public', 'extensions' as $f$
-- s2-118 : sans tirets ni espaces ; les communes à portée d'abord
#variable_conflict use_column
declare
  v_uid uuid := auth.uid();
  v_m text := btrim(regexp_replace(unaccent(lower(btrim(coalesce(p_texte, '')))), '[^a-z]+', ' ', 'g'));
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
  ), m as (
    select t.*, (t.kc like v_c || '%') debut,
           coalesce(t.lat between bb.la0 and bb.la1 and t.lon between bb.lo0 and bb.lo1, false) proche
      from t cross join bb
     where t.kc like v_c || '%'
        or (length(v_m) >= 3 and t.k like '% ' || v_m || '%')
        or (length(v_c) >= 4 and t.kc like '%' || v_c || '%')
     order by proche desc, debut desc, t.population desc nulls last
     limit 15
  ), r as (
    select m.*, bombe_refus(v_uid, m.lat, m.lon) refus from m
  )
  select r.code, r.nom, r.departement, round(dist_mes_communes(v_uid, r.lat, r.lon))::integer,
         r.refus is null, r.refus, r.lat, r.lon
    from r
   order by (r.refus is null) desc, r.debut desc, r.population desc nulls last
   limit 6;
end;
$f$;

commit;

-- Contrôle : t
select position('s2-118' in pg_get_functiondef('public.bombe_chercher(text)'::regprocedure)) > 0 as chercher_ok;
