-- =====================================================================
--  TerraFront — corrections du 6 octobre (Commune du jour et Radar)
--
--  1. Commune du jour : le nom des habitants passe en dernier indice, il
--     donnait presque le nom de la commune. Nouvel ordre : population,
--     région, anecdote, département, habitants. Les parties en cours
--     voient le nouvel ordre tout de suite.
--
--  2. Radar : plus de limite de duels par jour.
--
--  3. Radar : des parties restaient sans adversaire. Cause : une règle
--     interdisait d'affronter le même joueur deux fois en 24 h ; avec peu
--     de joueurs actifs, chacun avait vite affronté tout le monde, et
--     chaque nouveau duel devenait une partie « en attente ». C'est
--     maintenant une simple préférence. Les parties déjà en attente
--     seront affrontées dès les prochains duels.
--
--  À lancer APRÈS cdj-3-invite.sql et radar-1.sql. Rejouable.
--  Les fichiers cdj-3-invite.sql et radar-1.sql sont mis à jour pareil.
-- =====================================================================

create or replace function public.cdj_indices(p_code text, p_ouverts int)
returns jsonb
language plpgsql stable security definer
set search_path to 'public'
as $$
declare
  c communes;
  v_fait text;
  v_rang int;
begin
  select * into c from communes where code = p_code;

  -- l'anecdote : le meilleur fait qui ne donne pas le nom, sinon le rang
  -- de population dans le département
  if p_ouverts >= 3 then
    select f->>'t' into v_fait
      from jsonb_array_elements(coalesce(c.faits, '[]'::jsonb)) f
     where (f->>'t') !~ '«|lettres|caractères'
     order by (f->>'r')::int
     limit 1;
    if v_fait is null then
      select count(*) + 1 into v_rang from communes
       where departement = c.departement and population > c.population;
      v_fait := case when v_rang = 1 then 'La commune la plus peuplée de son département.'
                     else 'La ' || v_rang || 'e commune la plus peuplée de son département.' end;
    end if;
  end if;

  return jsonb_build_array(
    jsonb_build_object('cle', 'population', 'valeur', case when p_ouverts >= 1 then
      case when c.population < 10000 then 'entre 5 000 et 10 000 habitants'
           when c.population < 20000 then 'entre 10 000 et 20 000 habitants'
           when c.population < 50000 then 'entre 20 000 et 50 000 habitants'
           when c.population < 100000 then 'entre 50 000 et 100 000 habitants'
           else 'plus de 100 000 habitants' end end),
    jsonb_build_object('cle', 'region',      'valeur', case when p_ouverts >= 2 then cdj_region(c.departement) end),
    jsonb_build_object('cle', 'anecdote',    'valeur', case when p_ouverts >= 3 then v_fait end),
    jsonb_build_object('cle', 'departement', 'valeur', case when p_ouverts >= 4 then c.departement end),
    -- le nom des habitants donnait presque le nom de la commune : en dernier (6 octobre)
    jsonb_build_object('cle', 'gentile',     'valeur', case when p_ouverts >= 5 then c.gentile end));
end;
$$;

create or replace function public.radar_reglage(p text)
returns integer language sql immutable
set search_path to 'public'
as $$
  select case p
    when 'manches'    then 5
    when 'secondes'   then 15
    when 'marge'      then 2
    when 'penalite'   then 1000
    when 'par_jour'   then null   -- null : pas de limite (6 octobre)
    when 'k'          then 24
    when 'population' then 15000
  end;
$$;

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

create or replace function public.radar_lancer()
returns jsonb
language plpgsql security definer
set search_path to 'public'
as $$
declare
  v_uid uuid := auth.uid();
  v_jour date := (now() at time zone 'Europe/Paris')::date;
  v_id bigint;
  v_elo int;
  s radar_parties;
  v_codes text[];
begin
  if v_uid is null then raise exception 'Connecte-toi pour jouer à Radar.'; end if;
  perform pg_advisory_xact_lock(hashtextextended('radar' || v_uid::text, 7));

  -- une partie en cours : on la reprend
  select id into v_id from radar_parties where joueur_id = v_uid and not fini order by id desc limit 1;
  if v_id is not null then
    perform radar_rattraper(v_id);
    return radar_vue(v_id);
  end if;

  if (select count(*) from radar_parties where joueur_id = v_uid and jour = v_jour) >= radar_reglage('par_jour') then
    raise exception 'Plus de duel aujourd''hui. Reviens demain.';
  end if;

  insert into radar_joueurs(joueur_id) values (v_uid) on conflict do nothing;
  select elo into v_elo from radar_joueurs where joueur_id = v_uid;

  -- un adversaire : une partie terminée, pas encore affrontée, d'un autre
  -- joueur. De préférence quelqu'un que je n'ai pas affronté dans les
  -- dernières 24 h, puis le plus proche en Elo, puis la plus ancienne
  -- (personne n'attend trop). Ce n'est qu'une préférence : avec peu de
  -- joueurs, une exclusion laissait des parties sans adversaire (6 octobre).
  select p.* into s
    from radar_parties p
    left join radar_joueurs r on r.joueur_id = p.joueur_id
   where p.source_id is null and p.fini and not p.utilisee
     and p.joueur_id <> v_uid
   order by exists (select 1 from radar_parties m
                      join radar_parties ms on ms.id = m.source_id
                     where m.joueur_id = v_uid and ms.joueur_id = p.joueur_id
                       and m.cree_le > now() - interval '24 hours'),
            abs(coalesce(r.elo, 1000) - v_elo), p.fin_le
   limit 1
   for update of p skip locked;

  if s.id is not null then
    update radar_parties set utilisee = true where id = s.id;
    v_codes := s.communes;
  else
    select array_agg(code) into v_codes from (
      select c.code from communes c
       where c.population >= radar_reglage('population')
         and length(c.departement) = 2
         and c.latitude is not null
         and c.nom not ilike '%arrondissement%'
       order by random() limit radar_reglage('manches')) x;
  end if;

  insert into radar_parties(joueur_id, communes, source_id)
  values (v_uid, v_codes, s.id)
  returning id into v_id;
  return radar_vue(v_id);
end;
$$;

-- les droits ne changent pas (create or replace les garde), on les
-- rappelle quand même
revoke all on function public.cdj_indices(text, int) from public, anon, authenticated;
revoke all on function public.radar_etat()   from public, anon;
revoke all on function public.radar_lancer() from public, anon;
grant execute on function public.radar_etat()   to authenticated;
grant execute on function public.radar_lancer() to authenticated;

-- vérification : doit afficher « population, region, anecdote, departement, gentile » et une limite vide
select (select string_agg(x->>'cle', ', ') from jsonb_array_elements(cdj_indices((select commune_code from cdj_jours order by jour desc limit 1), 0)) x) as ordre_indices,
       radar_reglage('par_jour') as limite_par_jour;
