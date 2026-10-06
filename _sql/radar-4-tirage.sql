-- =====================================================================
--  TerraFront — Radar, 4 : moins de banlieue parisienne (6 octobre)
--
--  Constat de Nataël : « ça tombe beaucoup trop sur Paris ». C'est mesuré :
--  35 % des communes du Radar (212 sur 614) sont en Île-de-France. Avec un
--  tirage au hasard, une partie en contient 1,7 en moyenne, et plus d'une
--  partie sur deux en a au moins deux.
--
--  Nouveau tirage des 5 communes d'une partie neuve :
--  - 5 zones différentes : chaque département est une zone, sauf
--    l'Île-de-France qui compte pour UNE seule zone ;
--  - une zone a d'autant plus de chances de sortir qu'elle a de communes,
--    mais pas proportionnellement (racine carrée) : le Nord ou la Gironde
--    sortent plus souvent que le Cantal, sans écraser le reste ;
--  - puis une commune au hasard dans chaque zone.
--  Résultat simulé : l'Île-de-France apparaît dans un tiers des parties,
--  jamais plus d'une fois ; la commune la plus fréquente (Ajaccio) sort
--  dans 3 % des parties.
--
--  Les parties déjà jouées et celles en attente ne changent pas.
--  radar_lancer est réécrite à l'identique, sauf l'appel au nouveau tirage.
--  À lancer APRÈS corrections-6-octobre.sql. Rejouable.
-- =====================================================================

create or replace function public.radar_tirer_communes()
returns text[]
language sql volatile
set search_path to 'public'
as $$
  with pool as (
    select c.code,
           case when c.departement in ('75','77','78','91','92','93','94','95') then 'IDF'
                else c.departement end as zone
      from communes c
     where c.population >= radar_reglage('population')
       and length(c.departement) = 2
       and c.latitude is not null
       and c.nom not ilike '%arrondissement%'),
  zones as (select zone, count(*) as n from pool group by zone),
  -- tirage pondéré sans remise (méthode d'Efraimidis-Spirakis)
  choisies as (select zone from zones
                order by power(random(), 1.0 / sqrt(n)) desc
                limit radar_reglage('manches')),
  une_par_zone as (select distinct on (p.zone) p.code
                     from pool p join choisies z using (zone)
                    order by p.zone, random())
  select array_agg(code order by random()) from une_par_zone;
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
  -- dernières 24 h, puis le plus proche en Elo, puis la plus ancienne.
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
    v_codes := radar_tirer_communes();   -- 5 zones différentes (6 octobre)
  end if;

  insert into radar_parties(joueur_id, communes, source_id)
  values (v_uid, v_codes, s.id)
  returning id into v_id;
  return radar_vue(v_id);
end;
$$;

revoke all on function public.radar_tirer_communes() from public, anon, authenticated;
revoke all on function public.radar_lancer() from public, anon;
grant execute on function public.radar_lancer() to authenticated;

-- ---------------------------------------------------------------------
-- Vérification : 500 tirages à blanc (rien n'est enregistré).
-- Attendu : environ un tiers avec l'Île-de-France, jamais plus d'une,
-- toujours 5 communes.
-- ---------------------------------------------------------------------
select round(100.0 * count(*) filter (where nb_idf > 0) / count(*)) as pct_parties_avec_idf,
       max(nb_idf) as idf_max_par_partie,
       min(nb) as communes_min, max(nb) as communes_max
  from (select (select count(*) from unnest(t.codes) u join communes c on c.code = u
                 where c.departement in ('75','77','78','91','92','93','94','95')) as nb_idf,
               cardinality(t.codes) as nb
          from (select radar_tirer_communes() as codes from generate_series(1, 500)) t) x;
