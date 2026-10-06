-- =====================================================================
--  TerraFront — Radar, 3 : le résumé d'un duel (6 octobre)
--
--  radar_resume(id) : une partie FINIE du joueur connecté, vue de son côté,
--  avec ses coups et ceux de l'adversaire manche par manche.
--  - s'il a joué en second : l'adversaire est la partie source ;
--  - s'il a joué en premier : l'adversaire est celui qui a rejoué sa partie ;
--  - personne encore : ses coups seulement ('en_attente' vrai).
--  On ne peut ouvrir que ses propres parties, et seulement finies : rien ne
--  sort sur une partie en cours.
--
--  radar_etat() gagne 'attente_liste' : les parties qui attendent un
--  adversaire (5 au plus), pour pouvoir les ouvrir depuis le QG.
--
--  À lancer APRÈS corrections-6-octobre.sql. Rejouable. Ne touche à aucune
--  donnée.
-- =====================================================================

create or replace function public.radar_resume(p_id bigint)
returns jsonb
language plpgsql security definer
set search_path to 'public'
as $$
declare
  v_uid uuid := auth.uid();
  p radar_parties;
  m radar_parties;
  c communes;
  i int;
  v_manches jsonb := '[]'::jsonb;
begin
  if v_uid is null then raise exception 'Connecte-toi pour jouer à Radar.'; end if;
  select * into p from radar_parties where id = p_id and joueur_id = v_uid;
  if not found or not p.fini then raise exception 'Partie introuvable.'; end if;

  -- joué en second : radar_vue sait déjà tout montrer
  if p.source_id is not null then
    return radar_vue(p_id) || jsonb_build_object('regle_le', p.fin_le);
  end if;

  -- joué en premier : qui a rejoué cette partie ?
  select * into m from radar_parties where source_id = p.id and fini limit 1;
  if m.id is null then
    return radar_vue(p_id) || jsonb_build_object('regle_le', null);
  end if;

  for i in 1 .. jsonb_array_length(p.coups) loop
    select * into c from communes where code = p.communes[i];
    v_manches := v_manches || jsonb_build_object(
      'nom', c.nom, 'dept', c.departement, 'lat', c.latitude, 'lon', c.longitude,
      'moi', p.coups->(i - 1),
      'lui', m.coups->(i - 1));
  end loop;

  return jsonb_build_object(
    'id', p.id,
    'fini', true,
    'jouees', v_manches,
    'total_km', p.total_km,
    'adversaire', jsonb_build_object(
      'pseudo', (select coalesce(pseudo, 'Joueur') from joueurs where id = m.joueur_id),
      'elo', (select elo from radar_joueurs where joueur_id = m.joueur_id),
      'total_km', m.total_km),
    'en_attente', false,
    'resultat', p.resultat,
    'elo_avant', p.elo_avant,
    'elo_apres', p.elo_apres,
    'regle_le', m.fin_le);
end;
$$;

-- L'état du QG, avec les parties en attente
create or replace function public.radar_etat()
returns jsonb
language plpgsql security definer
set search_path to 'public'
as $$
declare
  v_uid uuid := auth.uid();
  v_jour date := (now() at time zone 'Europe/Paris')::date;
  v_elo int;
  v_parties int;
  v_premier uuid;
  v_en_cours bigint;
begin
  if v_uid is null then raise exception 'Connecte-toi pour jouer à Radar.'; end if;

  select elo, parties into v_elo, v_parties from radar_joueurs where joueur_id = v_uid;
  v_elo := coalesce(v_elo, 1000);

  -- le n°1 porte le titre Lapérouse (au moins 5 duels, au-dessus de 1 000)
  select joueur_id into v_premier from radar_joueurs
   where parties >= 5 and elo > 1000 order by elo desc, maj limit 1;

  select id into v_en_cours from radar_parties where joueur_id = v_uid and not fini order by id desc limit 1;
  if v_en_cours is not null then perform radar_rattraper(v_en_cours); end if;

  return jsonb_build_object(
    'elo', v_elo,
    'parties', coalesce(v_parties, 0),
    'rang', case when v_premier = v_uid then 'Lapérouse' else radar_rang(v_elo) end,
    -- null : pas de limite
    'restants', case when radar_reglage('par_jour') is null then null
                     else greatest(0, radar_reglage('par_jour')
                       - (select count(*) from radar_parties where joueur_id = v_uid and jour = v_jour)) end,
    'en_cours', (select id from radar_parties where joueur_id = v_uid and not fini order by id desc limit 1),
    'non_vus', (select count(*) from radar_parties where joueur_id = v_uid and not vu),
    'en_attente', (select count(*) from radar_parties
                    where joueur_id = v_uid and fini and source_id is null and resultat is null),
    -- mes parties finies qui attendent encore un adversaire (cliquables aussi)
    'attente_liste', (select coalesce(jsonb_agg(x order by x.fin desc), '[]'::jsonb) from (
        select p.id, p.total_km, p.fin_le as fin
          from radar_parties p
         where p.joueur_id = v_uid and p.fini and p.source_id is null and p.resultat is null
         order by p.fin_le desc limit 5) x),
    'derniers', (select coalesce(jsonb_agg(x order by x.fin desc), '[]'::jsonb) from (
        -- mes duels réglés, que j'aie joué en premier ou en second
        select p.id, p.resultat, p.total_km, p.elo_avant, p.elo_apres, p.vu,
               coalesce(p2.fin_le, p.fin_le) as fin,
               (select coalesce(pseudo, 'Joueur') from joueurs where id = coalesce(p2.joueur_id, s.joueur_id)) as adversaire,
               coalesce(p2.total_km, s.total_km) as adversaire_km
          from radar_parties p
          left join radar_parties s  on s.id = p.source_id
          left join radar_parties p2 on p2.source_id = p.id and p2.fini
         where p.joueur_id = v_uid and p.resultat is not null
         order by coalesce(p2.fin_le, p.fin_le) desc limit 8) x),
    'classement', (select coalesce(jsonb_agg(x order by x.elo desc), '[]'::jsonb) from (
        select coalesce(j.pseudo, 'Joueur') as pseudo, r.elo, r.parties,
               case when r.joueur_id = v_premier then 'Lapérouse' else radar_rang(r.elo) end as rang,
               r.joueur_id = v_uid as moi
          from radar_joueurs r join joueurs j on j.id = r.joueur_id
         where r.parties > 0
         order by r.elo desc limit 20) x));
end;
$$;

revoke all on function public.radar_resume(bigint) from public, anon;
grant execute on function public.radar_resume(bigint) to authenticated;
revoke all on function public.radar_etat() from public, anon;
grant execute on function public.radar_etat() to authenticated;

-- Vérification : doit répondre « oui » deux fois
select case when has_function_privilege('authenticated', 'public.radar_resume(bigint)', 'execute')
             and not has_function_privilege('anon', 'public.radar_resume(bigint)', 'execute')
            then 'oui' else 'NON' end as resume_reserve_aux_joueurs,
       case when pg_get_functiondef('public.radar_etat()'::regprocedure) like '%attente_liste%'
            then 'oui' else 'NON' end as etat_a_jour;
