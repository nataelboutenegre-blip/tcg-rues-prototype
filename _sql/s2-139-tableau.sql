-- s2-139 (12/11/2026, complété le même jour : « les nouveaux restent-ils ? ») : le tableau de bord de Nataël (direct/tableau.html), demande du 12/11.
-- Chiffres du jeu en une lecture : joueurs (total, nouveaux, actifs), activité par jour sur 14 jours, activité du jour,
-- derniers inscrits, les plus actifs du jour ; jours = [jour, inscrits, actifs, rounds, conquêtes, défenses, messages], et la liste id -> pseudo pour nommer les joueurs en ligne (présence du jeu).
-- Réservé à la modération (même règle que la régie du direct : discussion_est_moderateur). Lecture seule.
create or replace function public.tableau_de_bord()
returns jsonb language plpgsql stable security definer set search_path to 'public'
as $f$
declare
  v_jour date := (now() at time zone 'Europe/Paris')::date;
  v_minuit timestamptz := (now() at time zone 'Europe/Paris')::date::timestamp at time zone 'Europe/Paris';
  v_debut timestamptz;
begin
  if auth.uid() is null or not discussion_est_moderateur(auth.uid()) then raise exception 'Réservé à l''administration'; end if;
  v_debut := v_minuit - interval '13 days';
  return (
  with series as (select (v_jour - k) as d from generate_series(0, 13) k),
  pj  as (select (le at time zone 'Europe/Paris')::date d, count(*) n from front_rounds where le >= v_debut group by 1),
  pp  as (select (le at time zone 'Europe/Paris')::date d, count(*) n from front_prises where le >= v_debut group by 1),
  pd  as (select (le at time zone 'Europe/Paris')::date d, count(*) n from front_defenses where le >= v_debut group by 1),
  pm  as (select (le at time zone 'Europe/Paris')::date d, count(*) n from discussion_messages where le >= v_debut group by 1),
  pi  as (select (created_at at time zone 'Europe/Paris')::date d, count(*) n from joueurs where created_at >= v_debut group by 1),
  pa  as (select jour d, count(*) n from jours_joues where jour >= v_jour - 13 group by 1)
  select jsonb_build_object(
    'le', now(),
    'joueurs', jsonb_build_object(
      'total', (select count(*) from joueurs),
      'nouveaux_jour', (select count(*) from joueurs where created_at >= v_minuit),
      'nouveaux_7j', (select count(*) from joueurs where created_at >= v_minuit - interval '6 days'),
      'actifs_jour', (select count(*) from jours_joues where jour = v_jour),
      'actifs_7j', (select count(distinct joueur_id) from jours_joues where jour > v_jour - 7),
      'actifs_30j', (select count(distinct joueur_id) from jours_joues where jour > v_jour - 30),
      'avec_communes', (select count(distinct joueur_id) from possessions),
      'en_clan', (select count(*) from clan_membres)),
    'jours', (select jsonb_agg(jsonb_build_array(s.d, coalesce(pi.n, 0), coalesce(pa.n, 0), coalesce(pj.n, 0), coalesce(pp.n, 0),
                                                 coalesce(pd.n, 0), coalesce(pm.n, 0)) order by s.d)
                from series s left join pi on pi.d = s.d left join pa on pa.d = s.d left join pj on pj.d = s.d
                left join pp on pp.d = s.d left join pd on pd.d = s.d left join pm on pm.d = s.d),
    'aujourdhui', jsonb_build_object(
      'rounds', (select count(*) from front_rounds where le >= v_minuit),
      'conquetes', (select count(*) from front_prises where le >= v_minuit),
      'defenses', (select count(*) from front_defenses where le >= v_minuit),
      'defenses_reussies', (select count(*) from front_defenses where le >= v_minuit and reussie),
      'messages', (select count(*) from discussion_messages where le >= v_minuit and not retire),
      'messages_clans', (select count(*) from clan_messages where le >= v_minuit and not supprime),
      'radar', (select count(*) from radar_parties where cree_le >= v_minuit),
      'rafale', (select count(*) from rafale_parties where cree_le >= v_minuit),
      'pom', (select count(*) from pom_parties where le >= v_minuit),
      'echanges', (select count(*) from terra_echanges where cree_le >= v_minuit) + (select count(*) from clan_echanges where cree_le >= v_minuit),
      'achats', (select count(*) from boutique_achats where le >= v_minuit),
      'batiments', (select count(*) from batiments_historique where cree_le >= v_minuit)),
    'derniers', (select coalesce(jsonb_agg(jsonb_build_array(x.id, x.pseudo, x.created_at, x.jours, x.communes) order by x.created_at desc), '[]'::jsonb)
                   from (select j.id, j.pseudo, j.created_at,
                                (select count(*) from jours_joues d where d.joueur_id = j.id) jours,
                                (select count(*) from possessions p where p.joueur_id = j.id) communes
                           from joueurs j order by j.created_at desc limit 12) x),
    'top_jour', (select coalesce(jsonb_agg(jsonb_build_array(x.id, x.pseudo, x.rounds, x.prises) order by x.rounds desc), '[]'::jsonb)
                   from (select j.id, j.pseudo, count(r.*) rounds,
                                (select count(*) from front_prises p where p.attaquant = j.id and p.le >= v_minuit) prises
                           from front_rounds r join joueurs j on j.id = r.attaquant_id
                          where r.le >= v_minuit group by j.id, j.pseudo order by count(r.*) desc limit 8) x),
    -- cohortes par semaine d'inscription (lundi, heure de Paris), depuis le début du suivi des jours joués (23/10) :
    -- [lundi, inscrits, éligibles J1, revenus J1, éligibles J7, encore là après 7 j, joué ces 7 derniers jours]
    'cohortes', (select coalesce(jsonb_agg(jsonb_build_array(c.lundi, c.n, c.e1, c.r1, c.e7, c.r7, c.a7) order by c.lundi), '[]'::jsonb) from (
        select date_trunc('week', z.d0)::date lundi, count(*) n,
               count(*) filter (where z.d0 + 1 <= v_jour) e1, count(*) filter (where z.d0 + 1 <= v_jour and z.j1) r1,
               count(*) filter (where z.d0 + 7 <= v_jour) e7, count(*) filter (where z.d0 + 7 <= v_jour and z.j7) r7,
               count(*) filter (where z.a7) a7
          from (select (jo.created_at at time zone 'Europe/Paris')::date d0,
                       exists(select 1 from jours_joues x where x.joueur_id = jo.id and x.jour = (jo.created_at at time zone 'Europe/Paris')::date + 1) j1,
                       exists(select 1 from jours_joues x where x.joueur_id = jo.id and x.jour >= (jo.created_at at time zone 'Europe/Paris')::date + 7) j7,
                       exists(select 1 from jours_joues x where x.joueur_id = jo.id and x.jour > v_jour - 7) a7
                  from joueurs jo
                 where jo.created_at >= greatest(date '2026-10-19', date_trunc('week', (v_jour - 49)::timestamp)::date)::timestamp at time zone 'Europe/Paris') z
         group by 1) c),
    'pseudos', (select jsonb_object_agg(id, pseudo) from joueurs))
  );
end; $f$;
revoke all on function public.tableau_de_bord() from public, anon;
grant execute on function public.tableau_de_bord() to authenticated;
