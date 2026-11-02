-- ===========================================================================
--  TerraFront — s2-81 : la garnison retirée dit ce qu'elle rend vraiment
--  (2/11/2026, signalé par H34VEN : deux garnisons pleines retirées, rien reçu)
--
--  Le remboursement ne fait jamais dépasser 60 d'énergie (plafond des bonus,
--  inchangé). Un joueur à 58 qui retire une garnison de 10 ne reçoit que 2,
--  à 60 il ne reçoit rien, mais la fonction annonçait quand même 7. Elle
--  renvoie maintenant le gain réel (patch314 l'affiche, et prévient avant).
--  Ne change que la dernière ligne de garnison_retirer. Si elle n'est pas
--  trouvée telle quelle, rien n'est modifié. Rejouable.
--  Contrôle attendu : true
-- ===========================================================================
do $g$
declare
  d text := pg_get_functiondef('public.garnison_retirer(text)'::regprocedure);
  v_avant text := 'return query select v_rendue, floor(least(60, v + v_rendue))::integer;';
  v_apres text := 'return query select greatest(0, floor(least(60, v + v_rendue)) - floor(v))::integer, floor(least(60, v + v_rendue))::integer;   -- s2-81 : gain réel';
  n integer;
begin
  if position('s2-81' in d) > 0 then raise notice 'garnison_retirer : déjà à jour'; return; end if;
  n := (length(d) - length(replace(d, v_avant, ''))) / length(v_avant);
  if n <> 1 then raise exception 'garnison_retirer : dernière ligne attendue une fois, trouvée % fois : rien n''a changé', n; end if;
  execute replace(d, v_avant, v_apres);
end
$g$;

-- contrôle
select position('s2-81' in pg_get_functiondef('public.garnison_retirer(text)'::regprocedure)) > 0 as gain_reel;
