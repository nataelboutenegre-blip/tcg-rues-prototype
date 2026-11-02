-- ===========================================================================
--  TerraFront — s2-82 : la chance affichée compte la garnison (2/11/2026)
--
--  Vérifié le 2/11 (lecture-chances-combat.sql) : l'aperçu et l'attaque font
--  le même calcul (intensité + proximité + bâtiments, entre 10 et 90 %).
--  Mais quand la cible est en garnison, une victoire sur deux est annulée
--  ensuite (garnison_intervient) : une attaque annoncée à 50 % ne passait
--  qu'environ 1 fois sur 4. Les joueurs se plaignaient des séries de
--  défaites ; c'était en partie ça.
--
--  Désormais apercu_attaque (fiche) et apercu_attaques (liste Combat)
--  divisent la chance par deux quand la commune a une garnison active (celle
--  que le jeu montre déjà : énergie > 0, au propriétaire actuel). Le tirage
--  (attaquer) ne change pas : on affiche juste la vraie chance.
--  Ne remplace que la ligne du calcul dans chaque fonction ; si elle n'est
--  pas trouvée telle quelle, rien n'est modifié. Rejouable.
--  Contrôle attendu : true | true
-- ===========================================================================
begin;

do $g$
declare
  d text;
  n integer;
  v_avant text;
  v_apres text;
begin
  -- la fiche d'une commune
  d := pg_get_functiondef('public.apercu_attaque(text,text)'::regprocedure);
  if position('s2-82' in d) = 0 then
    v_avant := 'v_chance := greatest(0.10, least(0.90, v_chance + bonus_proximite(v_proches) + bonus_batiments(v_uid, p_commune_code)));';
    v_apres := v_avant || '
  -- s2-82 : une garnison active annule une victoire sur deux
  if saison2_active() and exists (select 1 from front_garnisons g
       join possessions po on po.commune_code = g.commune_code and po.joueur_id = g.joueur_id
      where g.commune_code = p_commune_code and g.energie > 0) then
    v_chance := v_chance / 2;
  end if;';
    n := (length(d) - length(replace(d, v_avant, ''))) / length(v_avant);
    if n <> 1 then raise exception 'apercu_attaque : calcul attendu une fois, trouvé % fois : rien n''a changé', n; end if;
    execute replace(d, v_avant, v_apres);
  else
    raise notice 'apercu_attaque : déjà à jour';
  end if;

  -- la liste Combat
  d := pg_get_functiondef('public.apercu_attaques(text[],text)'::regprocedure);
  if position('s2-82' in d) = 0 then
    v_avant := 'round(greatest(0.10, least(0.90, v_base + bonus_proximite(p.nb) + bonus_batiments(v_uid, c.code))) * 100)::integer,';
    v_apres := 'round(greatest(0.10, least(0.90, v_base + bonus_proximite(p.nb) + bonus_batiments(v_uid, c.code)))
           * case when saison2_active() and exists (select 1 from front_garnisons g   -- s2-82 : garnison active
                    join possessions po on po.commune_code = g.commune_code and po.joueur_id = g.joueur_id
                   where g.commune_code = c.code and g.energie > 0) then 0.5 else 1 end * 100)::integer,';
    n := (length(d) - length(replace(d, v_avant, ''))) / length(v_avant);
    if n <> 1 then raise exception 'apercu_attaques : calcul attendu une fois, trouvé % fois : rien n''a changé', n; end if;
    execute replace(d, v_avant, v_apres);
  else
    raise notice 'apercu_attaques : déjà à jour';
  end if;
end
$g$;

commit;

-- contrôle
select position('s2-82' in pg_get_functiondef('public.apercu_attaque(text,text)'::regprocedure)) > 0   as fiche_compte_garnison,
       position('s2-82' in pg_get_functiondef('public.apercu_attaques(text[],text)'::regprocedure)) > 0 as liste_compte_garnison;
