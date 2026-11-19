-- s3-37 : la roue du Front garde jusqu'à 5 tours en réserve au lieu de 3 (idée d'ASMFCB, 17/11).
-- À lancer APRÈS le lancement de la saison 3 (pas avant le 23/11), avec patch473 (5 cases dans le jeu).
-- Réglage : config_jeu 'roue_front' -> 'reserve' (5). Seulement avec les jetons propres de la roue :
-- les jetons des paquets gardent leur réserve de 3.
-- Effet le jour du changement : un joueur à 3/3 depuis plus de 40 min passe tout de suite à 5.
-- Retour arrière : update config_jeu set valeur = ((valeur::jsonb) - 'reserve')::text where cle = 'roue_front';

create or replace function public.roue_reserve() returns integer
language sql stable security definer set search_path to 'public' as $$
  select case when roue_cfg_int('jetons_propres') = 1 then greatest(3, coalesce(nullif(roue_cfg_int('reserve'), 0), 3)) else 3 end;
$$;
revoke all on function public.roue_reserve() from public, anon;
grant execute on function public.roue_reserve() to authenticated;

do $$
declare d text; n text;
begin
  -- l'état de la roue
  d := pg_get_functiondef('public.roue_front_etat()'::regprocedure);
  n := replace(d, 'if v_j < 3 then v_j := least(3, v_j', 'if v_j < roue_reserve() then v_j := least(roue_reserve(), v_j');
  n := replace(n, '''propres'',  roue_cfg_int(''jetons_propres'') = 1,', '''propres'',  roue_cfg_int(''jetons_propres'') = 1,
    ''reserve'',  roue_reserve(),   -- s3-37');
  if n = d or position('roue_reserve()' in n) = 0 or position('''reserve''' in n) = 0 then raise exception 's3-37 : roue_front_etat a changé, rien n''est fait'; end if;
  execute n;
  -- le tour de roue
  d := pg_get_functiondef('public.roue_front_tourner()'::regprocedure);
  n := replace(d, 'if v_jet < 3 then v_jet := least(3, v_jet', 'if v_jet < roue_reserve() then v_jet := least(roue_reserve(), v_jet');
  if n = d then raise exception 's3-37 : roue_front_tourner a changé, rien n''est fait'; end if;
  execute n;
  -- le réglage
  update config_jeu set valeur = ((valeur::jsonb) || '{"reserve": 5}'::jsonb)::text where cle = 'roue_front';
end $$;

-- contrôle : 5 · true · true
select roue_reserve() as reserve,
       position('roue_reserve()' in pg_get_functiondef('public.roue_front_etat()'::regprocedure)) > 0 as etat_ok,
       position('roue_reserve()' in pg_get_functiondef('public.roue_front_tourner()'::regprocedure)) > 0 as tourner_ok;
