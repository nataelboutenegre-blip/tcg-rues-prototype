-- s3-89 (27/11/2026) : la recherche de communes sur les cartes (idée de Saaslil).
-- Même recherche que communes_publiques_chercher (accueil), avec la position pour centrer la carte.
create or replace function public.carte_chercher(p_texte text)
 returns jsonb language sql stable security definer set search_path to 'public', 'extensions'
as $function$
  with q as (select trim(both '-' from regexp_replace(lower(unaccent(coalesce(p_texte, ''))), '[^a-z0-9]+', '-', 'g')) as m),
  x as (select c.code, c.nom, c.departement as dept, c.population, c.tier, c.latitude as lat, c.longitude as lon,
               case when r.s = q.m then 0 when r.s like q.m || '%' then 1 else 2 end as ordre
          from communes_recherche r join communes c on c.code = r.code, q
         where length(q.m) >= 2 and length(q.m) <= 60 and position(q.m in r.s) > 0
         order by ordre, c.population desc
         limit 8)
  select coalesce(jsonb_agg(to_jsonb(x) - 'ordre' order by x.ordre, x.population desc), '[]'::jsonb) from x;
$function$;
revoke all on function public.carte_chercher(text) from public, anon;
grant execute on function public.carte_chercher(text) to authenticated;
-- retour arrière : drop function public.carte_chercher(text);
