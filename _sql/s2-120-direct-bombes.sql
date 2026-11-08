-- s2-120 (8/11/2026) : la carte en direct montre les bombes (patch378, direct/bombe.js).
-- direct_bombes() : les zones encore actives et les impacts des 6 dernières heures, pour le
-- cercle (24 h) et l'animation. Page publique : comme les autres direct_*, ouverte à anon,
-- et seulement si le direct est ouvert. Rien de secret : position, rayon, lanceur et
-- garnisons soufflées sont déjà annoncés à tous à l'impact (sans dire à qui elles étaient).
-- [id, code, nom, dept, lat, lon, rayon_km, garnisons, forteresses, communes, lanceur, le, fin, [codes des garnisons]]

begin;

create or replace function public.direct_bombes()
 returns json language sql stable security definer set search_path to 'public' as $f$
  -- s2-120
  select coalesce(json_agg(json_build_array(b.id, b.cible_code, c.nom, c.departement, b.lat, b.lon, b.rayon_km::integer,
                   coalesce(b.garnisons, 0), coalesce(b.forteresses, 0), coalesce(b.communes, 0), j.pseudo,
                   floor(extract(epoch from b.le))::bigint, floor(extract(epoch from b.fin))::bigint,
                   coalesce((select json_agg(e ->> 'c') from jsonb_array_elements(coalesce(b.touchees, '[]'::jsonb)) e), '[]'::json))
                   order by b.le desc), '[]'::json)
    from bombes b join communes c on c.code = b.cible_code left join joueurs j on j.id = b.lanceur
   where direct_ouvert() and (b.fin > now() or b.le > now() - interval '6 hours');
$f$;
revoke execute on function public.direct_bombes() from public;
grant execute on function public.direct_bombes() to anon, authenticated;

commit;

-- Contrôle : t | t
select has_function_privilege('anon', 'public.direct_bombes()', 'execute') as anon_ok,
       json_typeof(public.direct_bombes()) = 'array' as tableau_ok;
