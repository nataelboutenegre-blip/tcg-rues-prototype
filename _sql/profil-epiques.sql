-- ===========================================================================
--  TerraFront — le profil compte aussi les épiques (25 octobre 2026)
--  profil_joueur() renvoyait légendaires et rares, pas épiques (la rareté
--  est arrivée avec la saison 2). Ajoute la clé 'epiques' (communes épiques
--  possédées en Front), à partir de la définition en base : si la ligne
--  attendue n'y est pas exactement une fois, rien ne change.
--  Rejouable. Contrôle attendu : true.
-- ===========================================================================
do $$
declare
  d text := pg_get_functiondef('public.profil_joueur(uuid)'::regprocedure);
  avant text := $a$'rares',         coalesce(m.rares, 0),$a$;
  apres text := $a$'rares',         coalesce(m.rares, 0),
    'epiques',       (select count(*)::integer from possessions pe join communes ce on ce.code = pe.commune_code
                       where pe.joueur_id = p_joueur and ce.tier = 'epique'),$a$;
begin
  if position('''epiques''' in d) > 0 then raise notice 'profil_joueur : déjà fait'; return; end if;
  if (length(d) - length(replace(d, avant, ''))) / length(avant) <> 1 then
    raise exception 'profil_joueur : ligne attendue introuvable, rien n''a changé';
  end if;
  execute replace(d, avant, apres);
  raise notice 'profil_joueur : épiques ajoutées';
end $$;

select position('''epiques''' in pg_get_functiondef('public.profil_joueur(uuid)'::regprocedure)) > 0 as epiques_ok;
