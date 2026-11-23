-- s3-63 (23/11/2026) : la notification « X a défendu » et l'historique de l'attaquant montrent le recul réel,
-- au plus la jauge (signalé par H34VEN : « −188 sur ta jauge (0 / 55) »). Le jeu, lui, était juste.
do $do$
declare d text; n text;
begin
  d := pg_get_functiondef('public.siege_renforcer(text, uuid, integer)'::regprocedure);
  n := replace(d, 'values (s.attaquant, s.id, p_code, ''defendu'', v_uid, round(v_recul),',
                  'values (s.attaquant, s.id, p_code, ''defendu'', v_uid, round(least(v_recul, s.degats)) /* s3-63 : le recul réel */,');
  n := replace(n, '''−'' || round(v_recul) || '' sur ta jauge''', '''−'' || round(least(v_recul, s.degats)) || '' sur ta jauge''');
  if n = d or position('s3-63' in n) = 0 or position('round(least(v_recul, s.degats)) || '' sur ta jauge''' in n) = 0 then raise exception 's3-63 : siege_renforcer introuvable'; end if;
  execute n;
end $do$;
