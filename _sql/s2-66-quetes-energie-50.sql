-- ===========================================================================
--  s2-66 — Énergie des quêtes : plafond 35 → 50 par jour (30/10, décision
--  de Nataël après la remarque de Stonirr et Oshannir : les plus actifs
--  touchaient 35 dès le matin ; les quêtes Front peuvent donner 53 / jour).
--  Le réservoir reste plafonné à 60. Ne touche qu'à reclamer_quete, à partir
--  de sa définition en base : si le texte attendu manque, rien ne change.
--  Effet immédiat : les quêtes déjà réclamées aujourd'hui ne sont pas
--  rejouées (celles restées à 0 le restent), les suivantes vont jusqu'à 50.
--  À lancer tout de suite, avec patch272 (qui affiche « / 50 »).
--  Rejouable. Contrôle attendu : true | false
-- ===========================================================================
do $$
declare d text := pg_get_functiondef('public.reclamer_quete(text)'::regprocedure);
begin
  if position('50 - v_deja' in d) > 0 then raise notice 'reclamer_quete : déjà fait'; return; end if;
  if (length(d) - length(replace(d, 'greatest(0, 35 - v_deja)', ''))) / length('greatest(0, 35 - v_deja)') <> 1
     or (length(d) - length(replace(d, '(35 / 35)', ''))) / length('(35 / 35)') <> 1 then
    raise exception 'reclamer_quete : texte attendu introuvable, rien n''a changé';
  end if;
  execute replace(replace(d, 'greatest(0, 35 - v_deja)', 'greatest(0, 50 - v_deja)'), '(35 / 35)', '(50 / 50)');
end $$;

-- contrôle : plafond 50 | plus de trace du plafond 35
select position('50 - v_deja' in pg_get_functiondef('public.reclamer_quete(text)'::regprocedure)) > 0 as plafond_50,
       position('35 - v_deja' in pg_get_functiondef('public.reclamer_quete(text)'::regprocedure)) > 0 as reste_35;
