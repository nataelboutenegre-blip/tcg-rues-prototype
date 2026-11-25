-- s3-72 (25/11/2026, Saaslil et H34VEN) : la quête « Réussis une défense » était presque impossible en S3 :
-- un siège n'« échoue » qu'au bout de 24 h sans vague. Elle devient « Repousse un siège » : ramener à zéro
-- la jauge d'un siège contre toi (renfort, le tien ou celui d'un allié ; alerte « defendu », degats_apres = 0).
do $m$
declare d text; n text;
begin
  d := pg_get_functiondef('public.quetes_liste(uuid)'::regprocedure);
  n := replace(d, $a$v_nouv_rare int; v_achat_bourse int; v_eclat int; v_dep3 int;$a$, $b$v_nouv_rare int; v_achat_bourse int; v_eclat int; v_dep3 int; v_repousse int;   -- s3-72$b$);
  n := replace(n, $a$  return query
  with reserve$a$, $b$  select count(*) into v_repousse from front_siege_alertes a   -- s3-72
   where a.defenseur = p_uid and a.type = 'defendu' and a.degats_apres = 0 and a.le >= v_minuit;

  return query
  with reserve$b$);
  n := replace(n, $a$('f_defense',     'combat', 'Réussis une défense',              case when b_siege then 'Un siège contre toi qui échoue' else 'Défends toi-même une commune attaquée' end, c_defense, 1, 0, 10, true),$a$,
    $b$('f_defense',     'combat', case when b_siege then 'Repousse un siège' else 'Réussis une défense' end, case when b_siege then 'Ramène à zéro la jauge d''un siège contre toi' else 'Défends toi-même une commune attaquée' end, c_defense + case when b_siege then v_repousse else 0 end, 1, 0, 10, true),   -- s3-72$b$);
  if (length(n) - length(replace(n, 's3-72', ''))) / 5 < 3 then raise exception 's3-72 : remplacements incomplets'; end if;
  execute n;
end $m$;
