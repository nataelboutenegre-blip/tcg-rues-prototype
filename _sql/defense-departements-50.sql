-- ===========================================================================
--  TerraFront — « Mes départements » : 50 au maximum au lieu de 5
--  (10 octobre 2026). À lancer APRÈS defense-departements.sql.
--  Modifie basculer_departement_defense à partir de sa définition en base.
--  Rejouable. Finit par un contrôle.
-- ===========================================================================
do $g$
declare
  v_def text;
  v_avant text := $a$    if (select count(*) from defense_departements d where d.joueur_id = v_uid) >= 5 then
      raise exception '5 départements au maximum : retires-en un avant';$a$;
  v_apres text := $a$    if (select count(*) from defense_departements d where d.joueur_id = v_uid) >= 50 then
      raise exception '50 départements au maximum : retires-en un avant';$a$;
  n integer;
begin
  v_def := pg_get_functiondef('public.basculer_departement_defense(text)'::regprocedure);
  if position(v_apres in v_def) > 0 then raise notice 'deja en place'; return; end if;
  n := (length(v_def) - length(replace(v_def, v_avant, ''))) / length(v_avant);
  if n <> 1 then
    raise exception 'texte a remplacer present % fois au lieu de 1. Rien n''a ete modifie.', n;
  end if;
  execute replace(v_def, v_avant, v_apres);
end
$g$;

-- Contrôle ---------------------------------------------------------------------------------
select position('>= 50' in pg_get_functiondef('public.basculer_departement_defense(text)'::regprocedure)) > 0 as limite_50;
