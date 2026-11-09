-- s2-127 (9/11/2026, lancé à 1 h 40) : quand le plafond de 80 énergie de quêtes par jour coupe une partie
-- du gain, le message de la quête le dit : « +7 énergie (plafond du jour atteint : 80 / 80) ».
-- Avant, seul un gain de 0 était expliqué. Signalé par Oshannir (quête Radar : 7 au lieu de 10, le 8/11).
do $$
declare d text; avant text; apres text;
begin
  d := pg_get_functiondef('public.reclamer_quete'::regproc);
  avant := $a$           case when v_e > 0 then '+' || v_e || ' énergie' end,$a$;
  apres := $a$           case when v_e > 0 then '+' || v_e || ' énergie'
                                || case when v_e < q.energie then ' (plafond du jour atteint : 80 / 80)' else '' end end,   -- s2-127$a$;
  if (length(d) - length(replace(d, avant, ''))) / length(avant) <> 1 then raise exception 'texte attendu une fois'; end if;
  execute replace(d, avant, apres);
end $$;
-- Contrôle : t
select position('s2-127' in pg_get_functiondef('public.reclamer_quete'::regproc)) > 0 as ok;
