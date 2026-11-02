-- ===========================================================================
--  TerraFront — s2-79 : retirer une garnison rend 75 % de son énergie
--  (au lieu de la moitié), arrondi en dessous. Décidé par Nataël le 2/11
--  après la remarque de H34VEN (« y a déjà pas beaucoup d'énergie »).
--  10 en garnison -> 7 rendus ; 4 -> 3 ; 1 -> 0. Le plafond de 60 ne change pas.
--  Modifie seulement la ligne du calcul dans garnison_retirer. Si elle n'est
--  pas trouvée telle quelle, rien n'est modifié. Rejouable.
--  Contrôle attendu : true | true
-- ===========================================================================
do $g$
declare
  d text := pg_get_functiondef('public.garnison_retirer(text)'::regprocedure);
  v_avant text := 'v_rendue := v_e / 2;';
  v_apres text := 'v_rendue := (v_e * 3) / 4;   -- s2-79 : 75 %';
  n integer;
begin
  if position(v_apres in d) > 0 then raise notice 'garnison_retirer : déjà à 75 %%'; return; end if;
  n := (length(d) - length(replace(d, v_avant, ''))) / length(v_avant);
  if n <> 1 then raise exception 'garnison_retirer : calcul attendu une fois, trouvé % fois : rien n''a changé', n; end if;
  execute replace(d, v_avant, v_apres);
end
$g$;

-- contrôle
select position('(v_e * 3) / 4' in pg_get_functiondef('public.garnison_retirer(text)'::regprocedure)) > 0 as rend_75_pourcent,
       position('v_e / 2' in pg_get_functiondef('public.garnison_retirer(text)'::regprocedure)) = 0 as plus_la_moitie;
