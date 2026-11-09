-- s2-132 (10/11/2026) : le fil de la roue du Front (idée d'Oshannir, 9/11 : « un historique de la roue
-- pour partager notre malchance ou notre chance »). Lecture seule.
-- lots : les 6 derniers gros lots (jackpot, gros éclair, coffre, cagnotte, paquet Terra) des 48 dernières heures ;
-- jackpot : le dernier jackpot des 7 derniers jours et le nombre de jackpots sur 24 h ;
-- moi : ma journée (tous les tours, offerts et soirée compris).
create or replace function public.roue_front_journal()
returns jsonb
language sql
stable security definer
set search_path to 'public'
as $f$
  select jsonb_build_object(
    'lots', coalesce((select jsonb_agg(to_jsonb(x) order by x.le desc) from (
        select j.pseudo, t.case_id, t.energie, t.lingots, t.tp, t.terra, t.le
          from roue_front_tours t join joueurs j on j.id = t.joueur_id
         where t.case_id in ('jackpot', 'gros', 'coffre', 'cagnotte', 'terra')
           and t.le > now() - interval '48 hours'
         order by t.le desc
         limit 6) x), '[]'::jsonb),
    'jackpot', (select jsonb_build_object('pseudo', j.pseudo, 'le', t.le,
                       'jour', (select count(*) from roue_front_tours z where z.case_id = 'jackpot' and z.le > now() - interval '24 hours'))
                  from roue_front_tours t join joueurs j on j.id = t.joueur_id
                 where t.case_id = 'jackpot' and t.le > now() - interval '7 days'
                 order by t.le desc limit 1),
    'moi', (select jsonb_build_object('tours', count(*), 'energie', coalesce(sum(t.energie), 0), 'lingots', coalesce(sum(t.lingots), 0),
                                      'tp', coalesce(sum(t.tp), 0), 'terra', coalesce(sum(t.terra), 0),
                                      'gros', count(*) filter (where t.case_id in ('jackpot', 'gros', 'coffre', 'cagnotte', 'terra')),
                                      'jackpots', count(*) filter (where t.case_id = 'jackpot'))
              from roue_front_tours t
             where t.joueur_id = auth.uid() and t.jour = (now() at time zone 'Europe/Paris')::date)
  );
$f$;
revoke execute on function public.roue_front_journal() from public, anon;
grant execute on function public.roue_front_journal() to authenticated;
notify pgrst, 'reload schema';
