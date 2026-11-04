-- ===========================================================================
--  TerraFront — s2-95 : la défense se paie selon l'engagement, comme l'attaque
--  (4/11/2026, aperçu validé par Nataël : « parfait ! »).
--
--  Avant : une défense coûtait toujours 1 énergie, et sa chance suivait
--  l'engagement (35 / 50 / 65 %) : 65 % pour 1 énergie en offensif, quand
--  l'attaquant paie 3 énergies pour le même 65 %.
--  Après : prudente 1 énergie (35 %), normale 2 (50 %), offensive 3 (65 %),
--  exactement comme l'attaque. Le joueur choisit à chaque défense (patch338).
--  Les communes voisines ne comptent toujours pas en défense (inchangé).
--
--  1. defendre() : le coût vient de energie_intensite(engagement) ; message
--     d'énergie insuffisante avec le bon chiffre.
--  2. sieges_contre_moi() : nouvelle colonne defenses_faites (pour afficher
--     « 1 sur 2 défenses disponibles »), et defense_revient donnée dès la
--     première défense utilisée (« la 2e revient dans 18 h »). Supprimée puis
--     recréée à partir de sa définition en production, droits remis.
--  Modifiées en place (textes de s2-6 et s2-93 vérifiés : s'il en manque un,
--  rien ne change). Ne touche ni aux chances, ni à la garnison, ni à attaquer().
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
  if position('s2-95' in d) > 0 then raise notice 'defendre : déjà à jour'; return; end if;
  d := pg_temp.remp(d, 'v_cout := 1;',
                       'v_cout := coalesce(energie_intensite(p_intensite), 1);   -- s2-95 : 1, 2 ou 3 selon l''engagement',
                       1, 'defendre (coût)');
  if position('Énergie insuffisante pour défendre (1 requise)' in d) > 0 then
    d := replace(d, '''Énergie insuffisante pour défendre (1 requise)''', '''Énergie insuffisante pour défendre (% requise)'', v_cout');
  else
    raise notice 'defendre : message d''énergie insuffisante non trouvé, laissé tel quel';
  end if;
  execute d;
end $$;

-- 2. sieges_contre_moi ---------------------------------------------------------
do $$
declare d text; n int;
begin
  d := pg_get_functiondef('public.sieges_contre_moi()'::regprocedure);
  if position('s2-95' in d) > 0 then raise notice 'sieges_contre_moi : déjà à jour'; return; end if;
  d := pg_temp.remp(d, 'defense_revient timestamp with time zone)',
                       'defense_revient timestamp with time zone, defenses_faites integer)',
                       1, 'sieges_contre_moi (colonnes)');
  d := pg_temp.remp(d, 'case when s.defense_utilisee and s.derniere_defense is not null then',
                       'case when coalesce(s.defenses_faites, 0) > 0 and s.derniere_defense is not null then',
                       1, 'sieges_contre_moi (revient)');
  n := (select count(*) from regexp_matches(d, 'end   -- s2-93(\s+)from sieges s', 'g'));
  if n <> 1 then
    raise exception 'sieges_contre_moi : texte de s2-93 trouvé % fois au lieu de 1 — rien n''a changé', n;
  end if;
  d := regexp_replace(d, 'end   -- s2-93(\s+)from sieges s',
         E'end,   -- s2-93 / s2-95\n         coalesce(s.defenses_faites, 0)   -- s2-95\\1from sieges s');
  drop function public.sieges_contre_moi();
  execute d;
  revoke all on function public.sieges_contre_moi() from public, anon;
  grant execute on function public.sieges_contre_moi() to authenticated, service_role;
end $$;

commit;

-- Contrôle : true | true | true | true
select position('s2-95' in pg_get_functiondef('public.defendre(text, uuid, text)'::regprocedure)) > 0      as defendre_ok,
       position('s2-95' in pg_get_functiondef('public.sieges_contre_moi()'::regprocedure)) > 0             as liste_ok,
       has_function_privilege('authenticated', 'public.defendre(text, uuid, text)', 'execute')             as droits_defendre,
       has_function_privilege('authenticated', 'public.sieges_contre_moi()', 'execute')                    as droits_liste;
