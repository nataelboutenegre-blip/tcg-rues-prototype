-- ===========================================================================
--  s2-69 — Quêtes du Front : jouer aux duels du QG suffit (idée d'Arkhannou,
--  30/10 : « plutôt que d'obliger la win, demander 1 ou 2 participations,
--  comme ça ceux qui ont du mal peuvent aussi gagner de l'énergie »).
--
--    f_radar  : « Gagne un duel Radar »  → « Joue 2 duels Radar »
--    f_rafale : « Gagne un duel Rafale » → « Joue 2 duels Rafale »
--  Duels classés, gagnés ou perdus (même compte que la quête Terra « Joue un
--  duel Radar »). Récompense inchangée : +5 énergie chacune.
--  Prend effet tout de suite, pour la journée en cours aussi. Rien à pousser.
--
--  quetes_liste est modifiée à partir de son texte en base : si une des deux
--  lignes n'est pas trouvée exactement une fois, rien ne change.
--  Rejouable. Contrôle attendu : true | true | false
-- ===========================================================================
begin;

do $do$
declare
  d  text := pg_get_functiondef('public.quetes_liste(uuid)'::regprocedure);
  r  record;
  n  int;
begin
  if position('Joue 2 duels Radar' in d) > 0 then raise notice 'quetes_liste : déjà fait'; return; end if;
  for r in select * from (values
    ($p$\('f_radar',[^\n]*\)$p$,
     $n$('f_radar',     'front', 'jour',   'Joue 2 duels Radar',             'Classés, gagnés ou perdus, dans le QG',  v_radar,    2,    0, 5)$n$),
    ($p$\('f_rafale',[^\n]*\)$p$,
     $n$('f_rafale',    'front', 'jour',   'Joue 2 duels Rafale',            'Classés, gagnés ou perdus, dans le QG',  v_rafale,   2,    0, 5)$n$)
  ) as x(motif, ligne) loop
    select count(*) into n from regexp_matches(d, r.motif, 'g');
    if n <> 1 then raise exception 'quetes_liste : ligne % trouvée % fois au lieu d''une, rien n''a changé', left(r.motif, 14), n; end if;
    d := regexp_replace(d, r.motif, replace(r.ligne, '\', '\\'));
  end loop;
  execute d;
end $do$;

commit;

-- Contrôle : true | true | false
select position('Joue 2 duels Radar' in pg_get_functiondef('public.quetes_liste(uuid)'::regprocedure)) > 0  as radar,
       position('Joue 2 duels Rafale' in pg_get_functiondef('public.quetes_liste(uuid)'::regprocedure)) > 0 as rafale,
       position('Gagne un duel R' in pg_get_functiondef('public.quetes_liste(uuid)'::regprocedure)) > 0     as reste_gagne;
