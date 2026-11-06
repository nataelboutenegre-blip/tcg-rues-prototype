-- s2-107 (6/11/2026) : échange Terra, « lui manque » (idée de H34VEN).
-- Parmi les communes que je pourrais donner (p_codes, mes doublons), celles
-- que l'autre joueur n'a pas dans sa collection Terra. Le jeu les met en
-- premier, avec l'étiquette « lui manque », dès qu'on a choisi sa carte.
-- Lecture seule ; ne répond que sur 400 codes au plus, et seulement sur des
-- codes que l'appelant possède en Terra (on ne sonde pas la collection d'un
-- autre avec n'importe quelle commune).

create or replace function public.terra_lui_manque(p_autre uuid, p_codes text[])
 returns text[]
 language sql
 stable security definer
 set search_path to 'public'
as $f$
  select coalesce(array_agg(m.commune_code order by m.commune_code), array[]::text[])
    from terra_collection m
   where auth.uid() is not null
     and p_autre is not null and p_autre <> auth.uid()
     and m.joueur_id = auth.uid()
     and m.exemplaires > 0
     and m.commune_code = any(p_codes[1:400])
     and not exists (select 1 from terra_collection t
                      where t.joueur_id = p_autre and t.commune_code = m.commune_code and t.exemplaires > 0);
$f$;
revoke all on function public.terra_lui_manque(uuid, text[]) from public, anon;
grant execute on function public.terra_lui_manque(uuid, text[]) to authenticated, service_role;

-- Contrôle attendu : t | t
select has_function_privilege('authenticated', 'public.terra_lui_manque(uuid, text[])', 'execute') as jeu_ok,
       not has_function_privilege('anon', 'public.terra_lui_manque(uuid, text[])', 'execute')      as prive_ok;
