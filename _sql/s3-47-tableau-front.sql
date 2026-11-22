-- s3-47 (22/11/2026) : le tableau de bord, onglet « Front » (demande de Nataël, 22/11 14 h 28) :
-- les sièges en cours, ce que coûte un siège selon la rareté, et l'énergie (dépensée, gagnée, en réserve).
-- Lecture seule, réservée à la modération, comme tableau_de_bord() (s2-139).
-- Sources : front_sieges (S3), quetes_compteurs ('energie', 'siege_vague', 'conquete' : par joueur et par jour,
-- heure de Paris), les tables de gains d'énergie, joueurs.front_energie.
-- La recharge naturelle (1 toutes les 7 min) n'est écrite nulle part : elle n'est pas dans les gains.

create or replace function public.tableau_front() returns jsonb
language plpgsql stable security definer set search_path to 'public' as $$
declare
  v_jour date := (now() at time zone 'Europe/Paris')::date;
  v_minuit timestamptz := (now() at time zone 'Europe/Paris')::date::timestamp at time zone 'Europe/Paris';
  v_max numeric := front_energie_reglage('max');
  v_depart numeric := coalesce(siege_n('depart_long'), 0);
begin
  if auth.uid() is null or not discussion_est_moderateur(auth.uid()) then raise exception 'Réservé à l''administration'; end if;
  return (
  with actifs as (select joueur_id from jours_joues where jour = v_jour),
  stock as (select j.id, j.pseudo, front_energie_lire(j.front_energie, j.front_energie_maj) e from joueurs j where j.id in (select joueur_id from actifs)),
  qc as (select joueur_id, cle, n from quetes_compteurs where jour = v_jour and cle in ('energie', 'siege_vague', 'conquete', 'garnison', 'renfort')),
  encours as (select s.*, siege_resistance(s.commune_code, s.attaquant) res, case when s.long_depuis is not null then s.long_depuis + make_interval(mins => ((1 - v_depart) * siege_tier_n('duree_long_min', s.tier))::int)
                     when siege_tier_n('eclair_min', s.tier) is not null then s.cree_le + make_interval(mins => ((1 - v_depart) * siege_tier_n('eclair_min', s.tier))::int) end tot
                from front_sieges s where s.fini_le is null)
  select jsonb_build_object(
    'le', now(),
    'reglages', jsonb_build_object('max', v_max, 'plafond', front_energie_reglage('plafond'), 'recharge_s', front_energie_reglage('recharge_s'),
                                   'expiration_h', siege_n('expiration_h'), 'resistance', siege_cfg()->'resistance'),
    -- [id, code, nom, tier, attaquant, défenseur, dégâts, résistance, long, défendu, énergie mise, énergie défense, créé, dernière vague, tombe le, au plus tôt, garnison touchée]
    'en_cours', (select coalesce(jsonb_agg(jsonb_build_array(e.id, e.commune_code, c.nom, e.tier, ja.pseudo, jd.pseudo, round(e.degats), round(coalesce(e.res, 0)),
                    e.long_depuis is not null, e.defendu, e.energie_mise, e.energie_defense, e.cree_le, e.derniere_vague,
                    e.derniere_vague + make_interval(hours => siege_n('expiration_h')::int), e.tot, e.garnison_touchee)
                    order by e.degats / nullif(e.res, 0) desc nulls last), '[]'::jsonb)
                   from encours e left join communes c on c.code = e.commune_code left join joueurs ja on ja.id = e.attaquant left join joueurs jd on jd.id = e.defenseur),
    -- [rareté, sièges, conquises, en cours, autres fins, énergie moyenne par conquête, médiane, min, max, minutes médianes, défense moyenne]
    'par_rarete', (select coalesce(jsonb_agg(jsonb_build_array(x.tier, x.n, x.c, x.ec, x.autres, x.moy, x.med, x.mn, x.mx, x.duree, x.def)
                    order by array_position(array['commun', 'peucommun', 'rare', 'epique', 'legendaire'], x.tier)), '[]'::jsonb) from (
                    select tier, count(*) n, count(*) filter (where resultat = 'conquise') c, count(*) filter (where fini_le is null) ec,
                           count(*) filter (where fini_le is not null and resultat is distinct from 'conquise') autres,
                           round(avg(energie_mise) filter (where resultat = 'conquise'), 1) moy,
                           percentile_cont(0.5) within group (order by energie_mise) filter (where resultat = 'conquise') med,
                           min(energie_mise) filter (where resultat = 'conquise') mn, max(energie_mise) filter (where resultat = 'conquise') mx,
                           round((percentile_cont(0.5) within group (order by extract(epoch from fini_le - cree_le) / 60) filter (where resultat = 'conquise'))::numeric, 1) duree,
                           round(avg(energie_defense) filter (where energie_defense > 0), 1) def
                      from front_sieges group by tier) x),
    'fins', (select coalesce(jsonb_object_agg(coalesce(resultat, 'en_cours'), n), '{}'::jsonb) from (select resultat, count(*) n from front_sieges group by 1) x),
    'debut', (select min(cree_le) from front_sieges),
    -- [jour, énergie dépensée, joueurs, moyenne, médiane, vagues de siège, conquêtes]
    'jours', (select jsonb_agg(jsonb_build_array(s.d, coalesce(e.t, 0), coalesce(e.j, 0), coalesce(e.moy, 0), coalesce(e.med, 0), coalesce(v.n, 0), coalesce(k.n, 0)) order by s.d)
                from (select (v_jour - g) d from generate_series(0, 13) g) s
                left join (select jour, sum(n) t, count(*) j, round(avg(n)) moy, percentile_cont(0.5) within group (order by n) med from quetes_compteurs where cle = 'energie' and jour > v_jour - 14 group by jour) e on e.jour = s.d
                left join (select jour, sum(n) n from quetes_compteurs where cle = 'siege_vague' and jour > v_jour - 14 group by jour) v on v.jour = s.d
                left join (select jour, sum(n) n from quetes_compteurs where cle = 'conquete' and jour > v_jour - 14 group by jour) k on k.jour = s.d),
    'gains', jsonb_build_object(
      'quetes', (select coalesce(sum(energie), 0) from quetes_reclamees where jour = v_jour),
      'roue', (select coalesce(sum(energie), 0) from roue_front_tours where jour = v_jour),
      'recolte', (select coalesce(sum(energie), 0) from front_recoltes where jour = v_jour),
      'centrale', (select coalesce(sum(energie), 0) from centrale_ramassages where jour = v_jour),
      'objectif', (select coalesce(sum(energie), 0) from clan_objectif_gains where le >= v_minuit),
      'mess', (select coalesce(sum(energie), 0) from mess_rations where jour = v_jour),
      'parrainage', (select coalesce(sum(energie_versee), 0) from parrainages where valide_le >= v_minuit),
      'sieges_rendue', (select coalesce(sum(energie_rendue), 0) from front_siege_alertes where le >= v_minuit),
      'remboursements', (select coalesce(sum(energie), 0) from remboursements where le >= v_minuit)),
    'stock', (select jsonb_build_object('actifs', count(*), 'moyenne', round(avg(e)), 'mediane', round((percentile_cont(0.5) within group (order by e))::numeric),
                     'pleins', count(*) filter (where e >= v_max), 'bas', count(*) filter (where e < 20)) from stock),
    -- [pseudo, dépensée aujourd'hui, vagues, conquêtes, réserve maintenant, sièges en cours (attaquant), garnisons posées]
    'joueurs', (select coalesce(jsonb_agg(jsonb_build_array(x.pseudo, x.dep, x.vag, x.conq, x.e, x.sg, x.gar) order by x.dep desc, x.e desc), '[]'::jsonb) from (
                  select s.pseudo, round(s.e) e,
                         coalesce((select n from qc where qc.joueur_id = s.id and cle = 'energie'), 0) dep,
                         coalesce((select n from qc where qc.joueur_id = s.id and cle = 'siege_vague'), 0) vag,
                         coalesce((select n from qc where qc.joueur_id = s.id and cle = 'conquete'), 0) conq,
                         coalesce((select n from qc where qc.joueur_id = s.id and cle = 'garnison'), 0) gar,
                         (select count(*) from encours where encours.attaquant = s.id) sg
                    from stock s order by 3 desc, 2 desc limit 40) x)
  ));
end; $$;

revoke all on function public.tableau_front() from public, anon;
grant execute on function public.tableau_front() to authenticated;
