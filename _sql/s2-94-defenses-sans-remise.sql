-- ===========================================================================
--  TerraFront — s2-94 : les défenses ne reviennent plus quand la série retombe
--  (4/11/2026, signalé par H34VEN, décision de Nataël : « on fait la correction vite »).
--
--  Avant : deux défenses par attaque, mais quand une défense faisait retomber
--  la série de l'attaquant à zéro, le défenseur récupérait ses deux défenses
--  (s2-46). Résultat : face à un attaquant à 1 victoire, un défenseur présent
--  pouvait défendre sans limite (9 défenses réussies sur une même commune le
--  4/11), et la limite de deux ne jouait qu'à partir de 2 victoires.
--  Après : deux défenses par attaque, point. Une défense utilisée revient
--  seulement 24 h après la dernière défense (s2-93), jusqu'à deux. La série qui
--  retombe à zéro ne rend plus rien.
--
--  1. defendre() : le compteur monte à chaque défense réussie, même quand la
--     série retombe à zéro ; l'heure de la défense est toujours notée.
--  2. attaquer() : ne remet plus le compteur à zéro ; « deux défenses
--     utilisées » se lit directement sur le compteur (écran Défense et note
--     côté attaquant).
--  Les deux fonctions sont modifiées en place à partir de leur définition en
--  production (textes de s2-46 et s2-93 vérifiés : s'il en manque un, rien ne
--  change). Ne touche ni aux chances, ni aux coûts, ni à la garnison.
--  Rejouable. Contrôle attendu : true | true | true | true
-- ===========================================================================
begin;

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

-- 1. defendre ------------------------------------------------------------------
do $$
declare d text;
begin
  d := pg_get_functiondef('public.defendre(text, uuid, text)'::regprocedure);
  if position('s2-94' in d) > 0 then raise notice 'defendre : déjà à jour'; return; end if;
  d := pg_temp.remp(d, 'defenses_faites = case when v_restantes > 0 then coalesce(defenses_faites, 0) + 1 else 0 end,',
                       'defenses_faites = coalesce(defenses_faites, 0) + 1,   -- s2-94 : plus de remise à zéro quand la série retombe',
                       1, 'defendre (compteur)');
  d := pg_temp.remp(d, 'derniere_defense = case when v_restantes > 0 then now() end,   -- s2-93',
                       'derniere_defense = now(),   -- s2-93 / s2-94',
                       1, 'defendre (heure)');
  d := pg_temp.remp(d, 'defense_utilisee = (v_restantes > 0 and coalesce(defenses_faites, 0) + 1 >= 2)',
                       'defense_utilisee = (coalesce(defenses_faites, 0) + 1 >= 2)',
                       1, 'defendre (deux utilisées)');
  execute d;
end $$;

-- 2. attaquer ------------------------------------------------------------------
do $$
declare d text; n int;
begin
  d := pg_get_functiondef('public.attaquer(text, text)'::regprocedure);
  if position('s2-94' in d) > 0 then raise notice 'attaquer : déjà à jour'; return; end if;
  n := (select count(*) from regexp_matches(d,
         'defense_utilisee = case when [^\n]*? then false else sieges\.defense_utilisee end,\s*defenses_faites = case when v_nouvelles_victoires = 0 then 0 else sieges\.defenses_faites end;', 'g'));
  if n <> 1 then
    raise exception 'attaquer : texte de s2-46 (défenses) trouvé % fois au lieu de 1 — rien n''a changé', n;
  end if;
  d := regexp_replace(d,
         'defense_utilisee = case when [^\n]*? then false else sieges\.defense_utilisee end,\s*defenses_faites = case when v_nouvelles_victoires = 0 then 0 else sieges\.defenses_faites end;',
         E'defense_utilisee = coalesce(sieges.defenses_faites, 0) >= 2,   -- s2-94\n                defenses_faites = sieges.defenses_faites;   -- s2-94 : plus de remise à zéro');
  execute d;
end $$;

commit;

-- Contrôle : true | true | true | true
select position('s2-94' in pg_get_functiondef('public.defendre(text, uuid, text)'::regprocedure)) > 0        as defendre_ok,
       position('s2-94' in pg_get_functiondef('public.attaquer(text, text)'::regprocedure)) > 0              as attaquer_ok,
       has_function_privilege('authenticated', 'public.defendre(text, uuid, text)', 'execute')               as droits_defendre,
       has_function_privilege('authenticated', 'public.attaquer(text, text)', 'execute')                     as droits_attaquer;
