-- =====================================================================
--  TerraFront — Radar, 5 : défier un joueur (7 octobre)
--
--  Un joueur en défie un autre : il joue 5 communes neuves tout de suite,
--  et la partie attend SON adversaire, pas le premier venu. L'adversaire
--  voit le défi au QG, le relève (mêmes 5 communes) ou le décline.
--
--  RÈGLES
--  - Un défi est AMICAL : il ne compte pas dans l'Elo ni dans le
--    classement Radar. Sinon deux amis pourraient se faire monter.
--  - Un seul défi en attente par adversaire, 5 défis envoyés en attente
--    au maximum.
--  - Un défi non relevé expire au bout de 7 jours.
--  - On ne peut pas défier un joueur qui nous a bloqué (message neutre).
--  - Les parties de défi ne servent jamais au matchmaking des duels
--    classés.
--
--  CE QUI CHANGE
--  - radar_parties : colonnes cible_id (le joueur défié) et amical ;
--  - nouvelles fonctions radar_defier, radar_relever, radar_refuser ;
--  - réécrites à l'identique sauf ce qui concerne les défis :
--    radar_clore_si_fini (pas d'Elo si amical), radar_lancer (n'affronte
--    jamais une partie de défi), radar_vue et radar_resume (disent si
--    c'est un défi), radar_etat (défis reçus, défis envoyés).
--
--  À lancer APRÈS radar-4-tirage.sql. Rejouable. Aucune donnée existante
--  n'est modifiée (les colonnes ajoutées valent null / false).
-- =====================================================================

alter table public.radar_parties add column if not exists cible_id uuid;
alter table public.radar_parties add column if not exists amical boolean not null default false;
create index if not exists radar_parties_cible on public.radar_parties(cible_id) where cible_id is not null;

-- ---------------------------------------------------------------------
-- Fin de partie : un défi se règle sans toucher à l'Elo
-- ---------------------------------------------------------------------
create or replace function public.radar_clore_si_fini(p_id bigint)
returns void
language plpgsql security definer
set search_path to 'public'
as $$
declare
  p radar_parties;
  s radar_parties;
  v_total int;
  ea int; eb int;
  v_att numeric;
  v_score numeric;
  v_k int := radar_reglage('k');
  va int; vb int;
begin
  select * into p from radar_parties where id = p_id for update;
  if p.fini or p.manche < radar_reglage('manches') then return; end if;

  select coalesce(sum((c->>'km')::int), 0) into v_total from jsonb_array_elements(p.coups) c;
  update radar_parties set fini = true, total_km = v_total, fin_le = now() where id = p_id;

  if p.source_id is null then return; end if;   -- partie neuve ou défi lancé : elle attend

  select * into s from radar_parties where id = p.source_id for update;
  v_score := case when v_total < s.total_km then 1 when v_total > s.total_km then 0 else 0.5 end;

  -- défi amical : un vainqueur, pas d'Elo
  if p.amical or s.amical then
    update radar_parties set vu = true,
           resultat = case v_score when 1 then 'victoire' when 0 then 'defaite' else 'egalite' end
     where id = p.id;
    update radar_parties set vu = false,
           resultat = case v_score when 0 then 'victoire' when 1 then 'defaite' else 'egalite' end
     where id = s.id;
    return;
  end if;

  -- duel classé : inchangé
  insert into radar_joueurs(joueur_id) values (p.joueur_id), (s.joueur_id) on conflict do nothing;
  select elo into ea from radar_joueurs where joueur_id = p.joueur_id for update;
  select elo into eb from radar_joueurs where joueur_id = s.joueur_id for update;

  v_att := 1 / (1 + power(10, (eb - ea) / 400.0));
  va := ea + round(v_k * (v_score - v_att));
  vb := eb + round(v_k * ((1 - v_score) - (1 - v_att)));

  update radar_joueurs set elo = va, parties = parties + 1,
         victoires = victoires + (v_score = 1)::int, maj = now() where joueur_id = p.joueur_id;
  update radar_joueurs set elo = vb, parties = parties + 1,
         victoires = victoires + (v_score = 0)::int, maj = now() where joueur_id = s.joueur_id;

  update radar_parties set elo_avant = ea, elo_apres = va, vu = true,
         resultat = case v_score when 1 then 'victoire' when 0 then 'defaite' else 'egalite' end
   where id = p.id;
  update radar_parties set elo_avant = eb, elo_apres = vb, vu = false,
         resultat = case v_score when 0 then 'victoire' when 1 then 'defaite' else 'egalite' end
   where id = s.id;
end;
$$;

-- ---------------------------------------------------------------------
-- Ce que le joueur voit d'une partie : + amical, + le joueur défié
-- ---------------------------------------------------------------------
create or replace function public.radar_vue(p_id bigint)
returns jsonb
language plpgsql security definer
set search_path to 'public'
as $$
declare
  p radar_parties;
  s radar_parties;
  v_manches jsonb := '[]'::jsonb;
  i int;
  c communes;
  v_adv jsonb := null;
begin
  select * into p from radar_parties where id = p_id;
  if p.source_id is not null then select * into s from radar_parties where id = p.source_id; end if;

  for i in 1 .. jsonb_array_length(p.coups) loop
    select * into c from communes where code = p.communes[i];
    v_manches := v_manches || jsonb_build_object(
      'nom', c.nom, 'dept', c.departement, 'lat', c.latitude, 'lon', c.longitude,
      'moi', p.coups->(i - 1),
      'lui', case when s.id is not null then s.coups->(i - 1) end);
  end loop;

  if s.id is not null then
    v_adv := jsonb_build_object(
      'pseudo', (select coalesce(pseudo, 'Joueur') from joueurs where id = s.joueur_id),
      'elo', (select elo from radar_joueurs where joueur_id = s.joueur_id),
      'joue_le', s.fin_le,
      'total_km', case when p.fini then s.total_km end);
  end if;

  return jsonb_build_object(
    'id', p.id,
    'manche', p.manche,
    'manches', radar_reglage('manches'),
    'secondes', radar_reglage('secondes'),
    'en_cours', case when not p.fini and p.manche_debut is not null then jsonb_build_object(
        'nom', (select nom from communes where code = p.communes[p.manche + 1]),
        'reste_ms', greatest(0, round(extract(epoch from (p.manche_debut
                      + make_interval(secs => radar_reglage('secondes')) - now())) * 1000)))
      end,
    'jouees', v_manches,
    'fini', p.fini,
    'total_km', p.total_km,
    'adversaire', v_adv,
    'en_attente', p.fini and p.source_id is null and p.resultat is null,
    'resultat', p.resultat,
    'elo_avant', p.elo_avant,
    'elo_apres', p.elo_apres,
    'amical', p.amical,
    'cible', case when p.cible_id is not null
                  then (select coalesce(pseudo, 'un joueur') from joueurs where id = p.cible_id) end);
end;
$$;

-- ---------------------------------------------------------------------
-- Résumé d'une partie finie : + amical, + défi décliné ou expiré
-- ---------------------------------------------------------------------
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

  if p.source_id is not null then
    return radar_vue(p_id) || jsonb_build_object('regle_le', p.fin_le);
  end if;

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
    'amical', p.amical,
    'regle_le', m.fin_le);
end;
$$;

-- ---------------------------------------------------------------------
-- Lancer un duel classé : jamais contre une partie de défi
-- (radar-4-tirage.sql, une seule condition ajoutée)
-- ---------------------------------------------------------------------
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

  select p.* into s
    from radar_parties p
    left join radar_joueurs r on r.joueur_id = p.joueur_id
   where p.source_id is null and p.fini and not p.utilisee
     and p.joueur_id <> v_uid
     and p.cible_id is null and not p.amical          -- 7 octobre : pas les défis
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
    v_codes := radar_tirer_communes();
  end if;

  insert into radar_parties(joueur_id, communes, source_id)
  values (v_uid, v_codes, s.id)
  returning id into v_id;
  return radar_vue(v_id);
end;
$$;

-- ---------------------------------------------------------------------
-- Défier un joueur
-- ---------------------------------------------------------------------
create or replace function public.radar_defier(p_cible uuid)
returns jsonb
language plpgsql security definer
set search_path to 'public'
as $$
declare
  v_uid uuid := auth.uid();
  v_id bigint;
  v_pseudo text;
  v_bloque boolean := false;
begin
  if v_uid is null then raise exception 'Connecte-toi pour jouer à Radar.'; end if;
  if p_cible is null or p_cible = v_uid then raise exception 'Choisis un autre joueur à défier.'; end if;
  select pseudo into v_pseudo from joueurs where id = p_cible;
  if not found then raise exception 'Ce joueur n''existe plus.'; end if;

  if to_regclass('public.amis') is not null then
    execute 'select exists (select 1 from amis where joueur_id = $1 and ami_id = $2 and etat = ''bloque'')'
       into v_bloque using p_cible, v_uid;
    if v_bloque then raise exception 'Ce joueur ne peut pas être défié pour le moment.'; end if;
  end if;

  perform pg_advisory_xact_lock(hashtextextended('radar' || v_uid::text, 7));

  if exists (select 1 from radar_parties where joueur_id = v_uid and not fini) then
    raise exception 'Termine d''abord ta partie en cours.';
  end if;
  if exists (select 1 from radar_parties
              where joueur_id = v_uid and cible_id = p_cible
                and resultat is null and not utilisee
                and cree_le > now() - interval '7 days') then
    raise exception 'Tu as déjà un défi en attente avec %.', coalesce(v_pseudo, 'ce joueur');
  end if;
  if (select count(*) from radar_parties
       where joueur_id = v_uid and cible_id is not null
         and resultat is null and not utilisee
         and cree_le > now() - interval '7 days') >= 5 then
    raise exception 'Tu as déjà 5 défis en attente. Attends qu''ils soient relevés.';
  end if;

  insert into radar_parties(joueur_id, communes, cible_id, amical)
  values (v_uid, radar_tirer_communes(), p_cible, true)
  returning id into v_id;
  return radar_vue(v_id);
end;
$$;

-- Relever un défi reçu : on joue les mêmes 5 communes
create or replace function public.radar_relever(p_id bigint)
returns jsonb
language plpgsql security definer
set search_path to 'public'
as $$
declare
  v_uid uuid := auth.uid();
  d radar_parties;
  v_id bigint;
begin
  if v_uid is null then raise exception 'Connecte-toi pour jouer à Radar.'; end if;
  perform pg_advisory_xact_lock(hashtextextended('radar' || v_uid::text, 7));

  select * into d from radar_parties
   where id = p_id and cible_id = v_uid and fini and not utilisee and resultat is null
     and cree_le > now() - interval '7 days'
   for update;
  if not found then raise exception 'Ce défi n''est plus disponible.'; end if;

  if exists (select 1 from radar_parties where joueur_id = v_uid and not fini) then
    raise exception 'Termine d''abord ta partie en cours.';
  end if;

  update radar_parties set utilisee = true where id = d.id;
  insert into radar_parties(joueur_id, communes, source_id, amical)
  values (v_uid, d.communes, d.id, true)
  returning id into v_id;
  return radar_vue(v_id);
end;
$$;

-- Décliner un défi reçu : celui qui a défié le voit au QG
create or replace function public.radar_refuser(p_id bigint)
returns void
language plpgsql security definer
set search_path to 'public'
as $$
declare
  v_uid uuid := auth.uid();
begin
  if v_uid is null then raise exception 'Connecte-toi pour jouer à Radar.'; end if;
  update radar_parties set utilisee = true, resultat = 'refuse', vu = false
   where id = p_id and cible_id = v_uid and fini and not utilisee and resultat is null;
  if not found then raise exception 'Ce défi n''est plus disponible.'; end if;
end;
$$;

-- ---------------------------------------------------------------------
-- L'état du QG : + défis reçus, + défis envoyés
-- (radar-3-resume.sql, les défis en plus ; les parties de défi ne
-- comptent plus comme « en attente d'un adversaire »)
-- ---------------------------------------------------------------------
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

  select joueur_id into v_premier from radar_joueurs
   where parties >= 5 and elo > 1000 order by elo desc, maj limit 1;

  select id into v_en_cours from radar_parties where joueur_id = v_uid and not fini order by id desc limit 1;
  if v_en_cours is not null then perform radar_rattraper(v_en_cours); end if;

  -- les défis de plus de 7 jours qui me concernent expirent
  update radar_parties set utilisee = true, resultat = 'expire', vu = false
   where cible_id is not null and fini and not utilisee and resultat is null
     and cree_le <= now() - interval '7 days'
     and (joueur_id = v_uid or cible_id = v_uid);

  return jsonb_build_object(
    'elo', v_elo,
    'parties', coalesce(v_parties, 0),
    'rang', case when v_premier = v_uid then 'Lapérouse' else radar_rang(v_elo) end,
    'restants', case when radar_reglage('par_jour') is null then null
                     else greatest(0, radar_reglage('par_jour')
                       - (select count(*) from radar_parties where joueur_id = v_uid and jour = v_jour)) end,
    'en_cours', (select id from radar_parties where joueur_id = v_uid and not fini order by id desc limit 1),
    'non_vus', (select count(*) from radar_parties where joueur_id = v_uid and not vu),
    'en_attente', (select count(*) from radar_parties
                    where joueur_id = v_uid and fini and source_id is null and resultat is null
                      and cible_id is null),
    'attente_liste', (select coalesce(jsonb_agg(x order by x.fin desc), '[]'::jsonb) from (
        select p.id, p.total_km, p.fin_le as fin
          from radar_parties p
         where p.joueur_id = v_uid and p.fini and p.source_id is null and p.resultat is null
           and p.cible_id is null
         order by p.fin_le desc limit 5) x),
    -- les défis qu'on m'a lancés, à relever ou décliner
    'defis_recus', (select coalesce(jsonb_agg(x order by x.fin desc), '[]'::jsonb) from (
        select p.id, coalesce(j.pseudo, 'un joueur') as pseudo, p.joueur_id, p.fin_le as fin,
               p.cree_le + interval '7 days' as expire_le
          from radar_parties p left join joueurs j on j.id = p.joueur_id
         where p.cible_id = v_uid and p.fini and not p.utilisee and p.resultat is null
         order by p.fin_le desc limit 10) x),
    -- mes défis joués, qui attendent la réponse de l'autre
    'defis_envoyes', (select coalesce(jsonb_agg(x order by x.fin desc), '[]'::jsonb) from (
        select p.id, coalesce(j.pseudo, 'un joueur') as pseudo, p.total_km, p.fin_le as fin
          from radar_parties p left join joueurs j on j.id = p.cible_id
         where p.joueur_id = v_uid and p.cible_id is not null and p.fini and p.resultat is null
         order by p.fin_le desc limit 5) x),
    'derniers', (select coalesce(jsonb_agg(x order by x.fin desc), '[]'::jsonb) from (
        select p.id, p.resultat, p.total_km, p.elo_avant, p.elo_apres, p.vu, p.amical,
               coalesce(p2.fin_le, p.fin_le) as fin,
               (select coalesce(pseudo, 'Joueur') from joueurs
                 where id = coalesce(p2.joueur_id, s.joueur_id, p.cible_id)) as adversaire,
               coalesce(p2.total_km, s.total_km) as adversaire_km
          from radar_parties p
          left join radar_parties s  on s.id = p.source_id
          left join radar_parties p2 on p2.source_id = p.id and p2.fini
         where p.joueur_id = v_uid and p.resultat is not null
         order by coalesce(p2.fin_le, p.fin_le) desc limit 8) x),
    'classement', (select coalesce(jsonb_agg(x order by x.elo desc), '[]'::jsonb) from (
        select r.joueur_id as id, coalesce(j.pseudo, 'Joueur') as pseudo, r.elo, r.parties,
               case when r.joueur_id = v_premier then 'Lapérouse' else radar_rang(r.elo) end as rang,
               r.joueur_id = v_uid as moi
          from radar_joueurs r join joueurs j on j.id = r.joueur_id
         where r.parties > 0
         order by r.elo desc limit 20) x));
end;
$$;

-- ---------------------------------------------------------------------
-- Droits
-- ---------------------------------------------------------------------
revoke all on function public.radar_clore_si_fini(bigint) from public, anon, authenticated;
revoke all on function public.radar_vue(bigint)           from public, anon, authenticated;
revoke all on function public.radar_lancer()              from public, anon;
revoke all on function public.radar_resume(bigint)        from public, anon;
revoke all on function public.radar_etat()                from public, anon;
revoke all on function public.radar_defier(uuid)          from public, anon;
revoke all on function public.radar_relever(bigint)       from public, anon;
revoke all on function public.radar_refuser(bigint)       from public, anon;
grant execute on function public.radar_lancer()        to authenticated;
grant execute on function public.radar_resume(bigint)  to authenticated;
grant execute on function public.radar_etat()          to authenticated;
grant execute on function public.radar_defier(uuid)    to authenticated;
grant execute on function public.radar_relever(bigint) to authenticated;
grant execute on function public.radar_refuser(bigint) to authenticated;

-- Vérification : trois « oui » attendus
select case when has_function_privilege('authenticated', 'public.radar_defier(uuid)', 'execute')
             and not has_function_privilege('anon', 'public.radar_defier(uuid)', 'execute')
            then 'oui' else 'NON' end as defier_reserve_aux_joueurs,
       case when pg_get_functiondef('public.radar_lancer()'::regprocedure) like '%cible_id is null%'
            then 'oui' else 'NON' end as duels_classes_sans_defis,
       case when exists (select 1 from information_schema.columns
                          where table_name = 'radar_parties' and column_name = 'amical')
            then 'oui' else 'NON' end as colonnes_ajoutees;
