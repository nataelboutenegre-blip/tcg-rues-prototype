-- ===========================================================================
--  s2-46 — Combat du Front : la série est gardée, 2 défenses par attaque
--  Décision de Nataël, 27 octobre 2026 (retours de Boule2Pain et D.C.A :
--  « perdre au 3e round annule toutes tes attaques »).
--
--  1. attaquer() : un round perdu ne remet plus la série à zéro, elle reste
--     où elle était. Il faut toujours 3 victoires, plus forcément d'affilée.
--     Nouvelle colonne de retour par_garnison (vrai quand la garnison a annulé
--     la victoire) : l'écran d'assaut ne peut plus le deviner tout seul.
--     Comme la liste des colonnes de retour change, la fonction est
--     supprimée puis recréée à partir de sa définition en production, et ses
--     droits sont remis (authenticated, service_role).
--  2. Le défenseur a droit à 2 défenses par attaque (au lieu d'une). Nouvelle
--     colonne sieges.defenses_faites ; defense_utilisee garde son sens pour le
--     jeu (« plus de défense possible »). Les deux se remettent à zéro quand
--     la série de l'attaquant retombe à 0 (par les défenses).
--  Les textes attendus sont vérifiés : s'il en manque un, rien ne change.
--  Ne touche ni aux coûts, ni aux chances, ni aux délais, ni à la garnison.
--  Rejouable. Contrôle attendu : true | true | true | true.
-- ===========================================================================
begin;

alter table public.sieges add column if not exists defenses_faites integer not null default 0;
-- une défense déjà utilisée avant ce changement compte pour une des deux
update public.sieges set defenses_faites = 1 where defense_utilisee and defenses_faites = 0;
update public.sieges set defense_utilisee = false where defense_utilisee and defenses_faites < 2;

create or replace function pg_temp.remp(d text, avant text, apres text, nb int, quoi text)
 returns text language plpgsql as $f$
begin
  if (length(d) - length(replace(d, avant, ''))) / length(avant) <> nb then
    raise exception '% : texte attendu % fois, trouvé % fois — rien n''a changé : %',
      quoi, nb, (length(d) - length(replace(d, avant, ''))) / length(avant), avant;
  end if;
  return replace(d, avant, apres);
end;
$f$;

-- 1. attaquer -----------------------------------------------------------------
do $$
declare d text;
begin
  d := pg_get_functiondef('public.attaquer(text, text)'::regprocedure);
  if position('par_garnison' in d) > 0 then raise notice 'attaquer : déjà à jour'; return; end if;
  d := pg_temp.remp(d, 'a_distance boolean)', 'a_distance boolean, par_garnison boolean)', 1, 'attaquer (retour)');
  d := pg_temp.remp(d, 'v_proches integer;', E'v_proches integer;\n  v_par_garnison boolean := false;   -- s2-46', 1, 'attaquer (variable)');
  -- la garnison : on le note (avant de toucher à la ligne de la défaite, qui deviendra pareille)
  d := pg_temp.remp(d, 'v_nouvelles_victoires := v_siege_actuel;',
                       'v_nouvelles_victoires := v_siege_actuel; v_par_garnison := true;', 1, 'attaquer (garnison)');
  -- la défaite : la série reste où elle était
  d := pg_temp.remp(d, 'v_nouvelles_victoires := 0;',
                       'v_nouvelles_victoires := v_siege_actuel;   -- s2-46 : une défaite ne remet plus à zéro', 1, 'attaquer (défaite)');
  d := pg_temp.remp(d, 'then false else sieges.defense_utilisee end;',
                       'then false else sieges.defense_utilisee end,'
                    || E'\n                defenses_faites = case when v_nouvelles_victoires = 0 then 0 else sieges.defenses_faites end;',
                    1, 'attaquer (défenses)');
  d := pg_temp.remp(d, 'v_proches, v_proches <= 0;', 'v_proches, v_proches <= 0, v_par_garnison;', 2, 'attaquer (renvoi)');
  drop function public.attaquer(text, text);
  execute d;
  revoke all on function public.attaquer(text, text) from public, anon;
  grant execute on function public.attaquer(text, text) to authenticated, service_role;
end $$;

-- 2. defendre -----------------------------------------------------------------
do $$
declare d text;
begin
  d := pg_get_functiondef('public.defendre(text, uuid, text)'::regprocedure);
  if position('defenses_faites' in d) > 0 then raise notice 'defendre : déjà à jour'; return; end if;
  d := pg_temp.remp(d, 'select s.victoires_consecutives, s.defense_utilisee into v_victoires, v_deja',
                       'select s.victoires_consecutives, coalesce(s.defenses_faites, 0) >= 2 into v_victoires, v_deja',
                       1, 'defendre (lecture)');
  d := pg_temp.remp(d, 'Tu as déjà utilisé ta défense contre cette attaque',
                       'Tu as déjà utilisé tes deux défenses contre cette attaque', 1, 'defendre (message)');
  d := pg_temp.remp(d, 'defense_utilisee = (v_restantes > 0)',
                       'defenses_faites = case when v_restantes > 0 then coalesce(defenses_faites, 0) + 1 else 0 end,'
                    || E'\n        defense_utilisee = (v_restantes > 0 and coalesce(defenses_faites, 0) + 1 >= 2)',
                       1, 'defendre (écriture)');
  execute d;
end $$;

commit;

select pg_get_functiondef('public.attaquer(text, text)'::regprocedure) ~ 'ne remet plus à zéro'           as serie_gardee,
       pg_get_functiondef('public.attaquer(text, text)'::regprocedure) ~ 'par_garnison boolean'           as retour_garnison,
       has_function_privilege('authenticated', 'public.attaquer(text, text)', 'execute')                 as joueurs_peuvent_attaquer,
       pg_get_functiondef('public.defendre(text, uuid, text)'::regprocedure) ~ 'defenses_faites, 0\) \+ 1' as deux_defenses;
