-- ===========================================================================
--  TerraFront — saison 2 : recharge de garnison offerte (10 octobre 2026)
--
--  Une défense active RÉUSSIE sur une commune en garnison remet 3 énergie
--  dans sa garnison (plafond 10). Récompense le joueur qui défend lui-même.
--  SANS EFFET EN SAISON 1 (saison2_active() faux). À lancer APRÈS
--  s2-7-garnison.sql. Rejouable. Finit par un contrôle.
-- ===========================================================================
do $g$
declare
  v_def text;
  v_avant text := $a$    if saison2_active() then perform front_gagner(v_uid, 10, 'front_defense'); end if;$a$;
  v_apres text := $a$    if saison2_active() then perform front_gagner(v_uid, 10, 'front_defense'); end if;
    -- recharge de garnison offerte : +3 (plafond 10)
    if saison2_active() then
      update front_garnisons set energie = least(10, energie + 3)
       where commune_code = p_commune_code and joueur_id = v_uid;
    end if;$a$;
  n integer;
begin
  v_def := pg_get_functiondef('public.defendre(text,uuid,text)'::regprocedure);
  if position(v_apres in v_def) > 0 then
    raise notice 'defendre : deja en place';
    return;
  end if;
  n := (length(v_def) - length(replace(v_def, v_avant, ''))) / length(v_avant);
  if n <> 1 then
    raise exception 'defendre : texte a remplacer present % fois au lieu de 1. Rien n''a ete modifie.', n;
  end if;
  execute replace(v_def, v_avant, v_apres);
end
$g$;

-- Contrôle ---------------------------------------------------------------------------------
select saison2_active() as saison2_active_doit_etre_false,
       position('least(10, energie + 3)' in pg_get_functiondef('public.defendre(text,uuid,text)'::regprocedure)) > 0 as recharge_en_place;
