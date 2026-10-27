-- ===========================================================================
--  TerraFront — les skins des cartes du Front, d'un coup (27 octobre 2026)
--  (Combat en vraies cartes, version A validée par Nataël)
--
--  front_skins() : chaque carte du Front habillée d'un skin par celui qui la
--  tient (et qui possède bien ce skin). Lecture seule, joueurs connectés.
--  Rejouable.
-- ===========================================================================
create or replace function public.front_skins()
 returns table(commune_code text, skin text) language sql stable security definer set search_path to 'public'
as $f$
  select s.commune_code, s.skin
    from skin_cartes s
    join possessions p on p.commune_code = s.commune_code and p.joueur_id = s.joueur_id
   where s.source = 'front'
     and garde_robe_possede(s.joueur_id, 'skin', s.skin);
$f$;
revoke all on function public.front_skins() from public, anon;
grant execute on function public.front_skins() to authenticated;

-- Contrôle : true | true | nombre de cartes du Front habillées (5 le 27/10 à 18 h)
select has_function_privilege('authenticated', 'public.front_skins()', 'execute') as joueurs_ok,
       not has_function_privilege('anon', 'public.front_skins()', 'execute')      as anon_ferme,
       (select count(*) from public.front_skins())                                as cartes_habillees;
