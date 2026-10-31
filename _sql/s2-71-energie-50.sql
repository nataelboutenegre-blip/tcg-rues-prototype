-- ===========================================================================
--  s2-71 — Énergie du Front : réserve 50 au lieu de 40 (31 octobre 2026)
--  Décision de Nataël : « On va rajouter 10 d'énergie max, voir ce que ça donne. »
--
--  Change :
--   1. front_energie_lire : la recharge monte jusqu'à 50 (toujours +1 toutes
--      les 10 minutes) ;
--   2. front_energie() : renvoie 50 comme maximum (le jeu l'affiche).
--  Ne change pas : le plafond des bonus (quêtes, récolte, garnison, parrainage,
--  pass, Halloween) reste 60.
--  Les deux fonctions sont modifiées à partir de leur définition EN PRODUCTION :
--  si un texte attendu manque, rien ne change (erreur, transaction annulée).
--  Effet de bord : un joueur resté au plein (40) remonte tout seul jusqu'à 50.
--  Pour revenir en arrière : remplacer 50 par 40 dans ce fichier et le relancer
--  (les tests « déjà à jour » se font sur le nombre visé).
--  Rejouable. Contrôle attendu : true | true | true.
-- ===========================================================================
begin;

do $$
declare d text; n int; ancien text := '40'; nouveau text := '50';
begin
  -- 1. la recharge
  d := pg_get_functiondef('public.front_energie_lire(numeric, timestamptz)'::regprocedure);
  if position('least(' || nouveau || ',' in d) > 0 then
    raise notice 'front_energie_lire : déjà à %', nouveau;
  else
    n := (length(d) - length(replace(d, 'p_val >= ' || ancien || ' then', ''))) / length('p_val >= ' || ancien || ' then');
    if n <> 1 then raise exception 'front_energie_lire : « p_val >= % then » attendu une fois, trouvé % fois : rien n''a changé', ancien, n; end if;
    n := (length(d) - length(replace(d, 'least(' || ancien || ',', ''))) / length('least(' || ancien || ',');
    if n <> 1 then raise exception 'front_energie_lire : « least(%, » attendu une fois, trouvé % fois : rien n''a changé', ancien, n; end if;
    d := replace(d, 'p_val >= ' || ancien || ' then', 'p_val >= ' || nouveau || ' then');
    d := replace(d, 'least(' || ancien || ',', 'least(' || nouveau || ',');
    execute d;
  end if;

  -- 2. le maximum affiché et la réserve pleine
  d := pg_get_functiondef('public.front_energie()'::regprocedure);
  if position('floor(v)::integer, ' || nouveau || ',' in d) > 0 then
    raise notice 'front_energie : déjà à %', nouveau;
  else
    n := (length(d) - length(replace(d, 'floor(v)::integer, ' || ancien || ',', ''))) / length('floor(v)::integer, ' || ancien || ',');
    if n <> 1 then raise exception 'front_energie : maximum % attendu une fois, trouvé % fois : rien n''a changé', ancien, n; end if;
    n := (length(d) - length(replace(d, 'when v >= ' || ancien || ' then null', ''))) / length('when v >= ' || ancien || ' then null');
    if n <> 1 then raise exception 'front_energie : réserve pleine % attendue une fois, trouvée % fois : rien n''a changé', ancien, n; end if;
    d := replace(d, 'floor(v)::integer, ' || ancien || ',', 'floor(v)::integer, ' || nouveau || ',');
    d := replace(d, 'when v >= ' || ancien || ' then null', 'when v >= ' || nouveau || ' then null');
    execute d;
  end if;
end $$;

commit;

-- Contrôle : true | true | true
select pg_get_functiondef('public.front_energie_lire(numeric, timestamptz)'::regprocedure) ~ 'least\(50,' as recharge_jusqua_50,
       pg_get_functiondef('public.front_energie()'::regprocedure) ~ 'integer, 50,' as maximum_50,
       public.front_energie_lire(0, now() - interval '30 days') = 50 as plein_a_50;
