-- ===========================================================================
--  TerraFront — Plus ou moins : l'historique des duels pour le QG (25 octobre 2026)
--  pom_d_etat() renvoie aussi les parties en attente (attente_liste) et,
--  pour chaque duel réglé, son id et s'il est vu (comme le Radar et la
--  Rafale). Remplace seulement pom_d_etat. Rejouable. Contrôle : true.
-- ===========================================================================
create or replace function public.pom_d_etat()
returns jsonb language plpgsql security definer set search_path to 'public'
as $$
declare v_uid uuid := auth.uid(); v_elo int; v_parties int; v_en_cours bigint;
        v_minuit timestamptz := date_trunc('day', now() at time zone 'Europe/Paris') at time zone 'Europe/Paris';
begin
  if v_uid is null then raise exception 'Connecte-toi pour jouer.'; end if;
  select elo, parties into v_elo, v_parties from pom_joueurs where joueur_id = v_uid;
  v_elo := coalesce(v_elo, 1000);
  select id into v_en_cours from pom_duels where joueur_id = v_uid and not fini order by id desc limit 1;
  if v_en_cours is not null then perform pom_d_rattraper(v_en_cours); end if;
  update pom_duels set vu = true where joueur_id = v_uid and not vu;
  return jsonb_build_object(
    'elo', v_elo, 'parties', coalesce(v_parties, 0), 'rang', pom_rang(v_elo),
    'en_cours', (select id from pom_duels where joueur_id = v_uid and not fini order by id desc limit 1),
    'gains_jour', (select count(*) from pom_duels where joueur_id = v_uid and gain > 0 and gain_le >= v_minuit),
    'gains_max', pom_reglage('gains_jour'),
    'en_attente', (select count(*) from pom_duels where joueur_id = v_uid and fini and source_id is null and resultat is null),
    'attente_liste', (select coalesce(jsonb_agg(x order by x.fin desc), '[]'::jsonb) from (
        select p.id, p.justes, p.fin_le as fin from pom_duels p
         where p.joueur_id = v_uid and p.fini and p.source_id is null and p.resultat is null
         order by p.fin_le desc limit 5) x),
    'derniers', (select coalesce(jsonb_agg(x order by x.fin desc), '[]'::jsonb) from (
        select p.id, p.vu, false as amical, p.resultat, p.justes, p.elo_avant, p.elo_apres, coalesce(p2.fin_le, p.fin_le) as fin,
               (select coalesce(pseudo, 'Joueur') from joueurs where id = coalesce(p2.joueur_id, s.joueur_id)) as adversaire,
               coalesce(p2.justes, s.justes) as adversaire_justes
          from pom_duels p
          left join pom_duels s on s.id = p.source_id
          left join pom_duels p2 on p2.source_id = p.id and p2.fini
         where p.joueur_id = v_uid and p.resultat is not null
         order by coalesce(p2.fin_le, p.fin_le) desc limit 5) x),
    'classement', (select coalesce(jsonb_agg(x order by x.elo desc), '[]'::jsonb) from (
        select coalesce(j.pseudo, 'Joueur') as pseudo, r.elo, pom_rang(r.elo) as rang, r.joueur_id = v_uid as moi
          from pom_joueurs r join joueurs j on j.id = r.joueur_id
         where r.parties > 0 order by r.elo desc limit 10) x));
end; $$;

select position('attente_liste' in pg_get_functiondef('public.pom_d_etat()'::regprocedure)) > 0 as historique_ok;
