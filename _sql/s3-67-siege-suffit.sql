-- s3-67 (24/11/2026, idée d'Arkhannou) : siege_estimer dit quand l'énergie en attente suffit.
-- Avant : « e » valait au moins 1, même quand l'attente couvrait déjà la prise (≈1 ⚡ trompeur).
-- Après : siège en cours → e peut valoir 0 ; nouveaux champs 'suffit' (bool) et 'attente' (⚡ en attente).
do $m$
declare d text; n text;
begin
  d := pg_get_functiondef('public.siege_estimer(text[])'::regprocedure);
  n := replace(d,
    $a$'e', greatest(1, ceil(greatest(0, v_res - coalesce(s.degats, 0) + siege_garnison(c) * siege_n('bouclier_par_energie')) / (v_pts * v_mult))
                       + case when s.id is null then v_pose else 0 end - coalesce(s.attente, 0)),$a$,
    $b$'e', greatest(case when s.id is null then 1 else 0 end, ceil(greatest(0, v_res - coalesce(s.degats, 0) + siege_garnison(c) * siege_n('bouclier_par_energie')) / (v_pts * v_mult))
                       + case when s.id is null then v_pose else 0 end - coalesce(s.attente, 0)),
      'suffit', s.id is not null and ceil(greatest(0, v_res - coalesce(s.degats, 0) + siege_garnison(c) * siege_n('bouclier_par_energie')) / (v_pts * v_mult)) - coalesce(s.attente, 0) <= 0,
      'attente', coalesce(round(s.attente), 0),$b$);
  if n = d then raise exception 's3-67 : texte introuvable dans siege_estimer'; end if;
  execute n;
end $m$;
