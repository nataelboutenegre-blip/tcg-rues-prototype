-- s3-52 (22/11/2026, idée de Maroli, « let's go » de Nataël 19 h 44) : une égalité en duel classé (Plus ou moins,
-- Rafale, Radar) ne change plus l'Elo. Avant : règle des échecs, le moins bien classé gagnait des points sur une égalité.
-- Retour arrière : enlever « case when … = 0.5 then 0 else … end » dans les trois fonctions (pg_get_functiondef + replace).
do $$
declare d text; n text; f record;
begin
  for f in select * from (values ('public.pom_d_clore'::text, 'v_res'), ('public.rafale_clore', 'v_res'), ('public.radar_clore_si_fini', 'v_score')) x(fn, v) loop
    select pg_get_functiondef(p.oid) into d from pg_proc p where p.oid = f.fn::regproc;
    n := replace(d, format('va := ea + round(v_k * (%s - v_att));', f.v),
                    format('va := ea + case when %s = 0.5 then 0 else round(v_k * (%s - v_att)) end;   -- s3-52 : égalité, Elo inchangé', f.v, f.v));
    n := replace(n, format('vb := eb + round(v_k * ((1 - %s) - (1 - v_att)));', f.v),
                    format('vb := eb + case when %s = 0.5 then 0 else round(v_k * ((1 - %s) - (1 - v_att))) end;', f.v, f.v));
    if n = d or position('s3-52' in n) = 0 or position('vb := eb + case' in n) = 0 then raise exception 's3-52 : % inchangée', f.fn; end if;
    execute n;
  end loop;
end $$;
select p.proname, position('s3-52' in prosrc) > 0 ok from pg_proc p where p.proname in ('pom_d_clore', 'rafale_clore', 'radar_clore_si_fini');
