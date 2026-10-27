-- ===========================================================================
--  TerraFront — le skin de la cible pendant l'assaut (27 octobre 2026)
--  (aperçu validé par Nataël : la carte de la cible, en entier, avec son skin)
--
--  skin_front_commune(code) : le skin posé sur cette carte du Front par celui
--  qui la tient aujourd'hui (seulement s'il possède bien ce skin), sinon null.
--  Lecture seule, pour les joueurs connectés. Rejouable.
-- ===========================================================================
create or replace function public.skin_front_commune(p_code text)
 returns text language plpgsql stable security definer set search_path to 'public'
as $f$
declare v_proprio uuid; v_skin text;
begin
  if auth.uid() is null then raise exception 'Non connecte'; end if;
  select p.joueur_id into v_proprio from possessions p where p.commune_code = p_code;
  if v_proprio is null then return null; end if;
  select s.skin into v_skin
    from skin_cartes s
   where s.joueur_id = v_proprio and s.source = 'front' and s.commune_code = p_code
     and garde_robe_possede(v_proprio, 'skin', s.skin);
  return v_skin;
end;
$f$;
revoke all on function public.skin_front_commune(text) from public, anon;
grant execute on function public.skin_front_commune(text) to authenticated;

-- Contrôle : true | true | nombre de cartes du Front habillées aujourd'hui
select has_function_privilege('authenticated', 'public.skin_front_commune(text)', 'execute') as joueurs_ok,
       not has_function_privilege('anon', 'public.skin_front_commune(text)', 'execute')      as anon_ferme,
       (select count(*) from public.skin_cartes s join public.possessions p
          on p.commune_code = s.commune_code and p.joueur_id = s.joueur_id where s.source = 'front') as cartes_front_habillees;
