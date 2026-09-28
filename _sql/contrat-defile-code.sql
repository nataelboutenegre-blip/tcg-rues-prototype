-- ===========================================================================
--  TerraFront — contrat_defile renvoie aussi le code INSEE
--
--  Le dessin d'une carte est derive de son code INSEE. Le defile du
--  contrat ne recevait que le nom, donc ses cartes de decor portaient un
--  dessin qui n'etait pas celui de la commune. Avec le code, une commune
--  apercue dans le defile a le meme dessin que si elle finit dans la
--  Collection.
--
--  Le type de retour change : « create or replace » ne suffit pas, il
--  faut supprimer la fonction d'abord.
-- ===========================================================================

drop function if exists public.contrat_defile(text, integer);

create function public.contrat_defile(p_tier text, p_combien integer default 40)
returns table(code text, nom text, departement text, population integer)
language sql
stable
security definer
set search_path to 'public'
as $function$
  select c.code::text, c.nom::text, c.departement::text, c.population
    from communes c
    left join possessions p on p.commune_code = c.code
   where c.tier = p_tier
     and p.commune_code is null
     and auth.uid() is not null
   order by random()
   limit least(greatest(coalesce(p_combien, 40), 1), 60);
$function$;

revoke all on function public.contrat_defile(text, integer) from public, anon;
grant execute on function public.contrat_defile(text, integer) to authenticated;


-- ---------------------------------------------------------------------------
--  Verification
-- ---------------------------------------------------------------------------
select 'A. colonnes renvoyees' as controle,
       string_agg(a.attname, ', ' order by a.attnum) as valeur
  from pg_proc p
  join pg_namespace n on n.oid = p.pronamespace
  join unnest(p.proargnames, p.proargmodes) with ordinality
       as a(attname, mode, attnum) on a.mode = 't'
 where n.nspname = 'public' and p.proname = 'contrat_defile'
union all
select 'B. droits (aucun anon)',
       coalesce(array_to_string(p.proacl, ' '), 'defaut')
  from pg_proc p join pg_namespace n on n.oid = p.pronamespace
 where n.nspname = 'public' and p.proname = 'contrat_defile'
order by 1;
