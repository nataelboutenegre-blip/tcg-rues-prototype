-- ===========================================================================
--  s2-47 — le message d'une quête réclamée dit « TP » au lieu de « pts »
--  (les points de Terra s'appellent TerraPoints, décision du 28 octobre 2026 ;
--  le jeu l'affiche depuis patch242). Ne touche qu'au texte du message de
--  reclamer_quete, à partir de sa définition en production.
--  Rejouable. Contrôle attendu : true.
-- ===========================================================================
do $$
declare d text; avant text := $a$q.points || ' pts'$a$; apres text := $a$q.points || ' TP'$a$;
begin
  d := pg_get_functiondef('public.reclamer_quete(text)'::regprocedure);
  if position(apres in d) > 0 then raise notice 'reclamer_quete : déjà à jour'; return; end if;
  if (length(d) - length(replace(d, avant, ''))) / length(avant) <> 1 then
    raise exception 'reclamer_quete : texte attendu introuvable, rien n''a changé';
  end if;
  execute replace(d, avant, apres);
end $$;

select position($a$q.points || ' TP'$a$ in pg_get_functiondef('public.reclamer_quete(text)'::regprocedure)) > 0 as message_en_tp;
