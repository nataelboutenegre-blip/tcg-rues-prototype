-- s2-140 (12/11/2026) : échanges entre clans, un par joueur par jour au lieu d'un par semaine (demande de Nataël).
-- 24 h après son dernier échange entre clans accepté (glissant, comme avant avec 7 jours). Les définitions en base
-- sont reprises telles quelles : seuls l'intervalle et les messages changent. Les 2 propositions en attente au plus restent.
do $m$
declare f text; d text; n int;
begin
  foreach f in array array['clan_ech_inter_dispo', 'clan_ech_inter_proposer', 'clan_ech_repondre'] loop
    select pg_get_functiondef(p.oid) into d from pg_proc p join pg_namespace s on s.oid = p.pronamespace where s.nspname = 'public' and p.proname = f;
    if d is null then raise exception 'fonction % introuvable', f; end if;
    n := length(d);
    d := replace(d, $x$interval '7 days'$x$, $x$interval '1 day'$x$);
    d := replace(d, 'Un échange entre clans par semaine', 'Un échange entre clans par jour');
    d := replace(d, 'son échange entre clans de la semaine', 'son échange entre clans du jour');
    d := replace(d, 'un échange par semaine chacun', 'un échange par jour chacun');
    if d ~ 'semaine|7 days' then raise exception 'reste une mention de la semaine dans %', f; end if;
    execute d;
  end loop;
end $m$;
