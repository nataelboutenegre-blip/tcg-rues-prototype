-- ===========================================================================
--  TerraFront — compteur des parties payées dans le QG (18 octobre 2026)
--  Idée d'un joueur : savoir où on en est des 5 victoires payées par jour.
--
--  gains_du_jour() -> { radar, rafale, max_radar, max_rafale, cdj }
--    radar / rafale : victoires payées depuis minuit (heure de Paris),
--                     compteés exactement comme radar_gagner / rafale_gagner ;
--    cdj            : points gagnés à la Commune du jour aujourd'hui (null sinon).
--  Lecture seule. Rejouable. Finit par un contrôle.
-- ===========================================================================

create or replace function public.gains_du_jour()
returns jsonb
language sql
stable security definer
set search_path to 'public'
as $function$
  with m as (
    select date_trunc('day', now() at time zone 'Europe/Paris') at time zone 'Europe/Paris' as minuit,
           (now() at time zone 'Europe/Paris')::date as jour
  )
  select jsonb_build_object(
    'radar',      (select count(*) from radar_parties r, m
                    where r.joueur_id = auth.uid() and r.gain > 0 and r.gain_le >= m.minuit),
    'rafale',     (select count(*) from rafale_parties r, m
                    where r.joueur_id = auth.uid() and r.gain > 0 and r.gain_le >= m.minuit),
    'max_radar',  5,
    'max_rafale', rafale_reglage('gains_jour'),
    'cdj',        (select g.gain from cdj_gains g, m where g.joueur_id = auth.uid() and g.jour = m.jour)
  )
  from m;
$function$;

revoke all on function public.gains_du_jour() from public, anon;
grant execute on function public.gains_du_jour() to authenticated;

-- contrôle (dans l'éditeur, auth.uid() est vide : 0 / 0 / 5 / 5 / null attendu)
select public.gains_du_jour() as controle;
