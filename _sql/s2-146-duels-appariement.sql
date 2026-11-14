-- s2-146 (15/11/2026) : corrige s2-145 (trop strict : ~74 % des duels Rafale auraient attendu) et l'étend à Radar.
-- Plus de refus des revanches (le jeu préfère toujours un nouvel adversaire, comme avant) ;
-- refus seulement au-delà de 300 d'écart d'Elo ; une partie qui attend depuis plus de 12 h va à n'importe qui.
-- Plus ou moins : rien (Elo de 856 à 1 096, 0 duel à plus de 200 d'écart sur 7 jours).

update config_jeu set valeur = '{"ecart_max": 300, "attente_h": 12}' where cle = 'rafale_appariement';
insert into config_jeu(cle, valeur) values ('radar_appariement', '{"ecart_max": 300, "attente_h": 12}')
on conflict (cle) do nothing;

CREATE OR REPLACE FUNCTION public.rafale_lancer()
 RETURNS jsonb
 LANGUAGE plpgsql
 SECURITY DEFINER
 SET search_path TO 'public'
AS $function$
declare
  v_uid uuid := auth.uid();
  v_id bigint;
  v_elo int;
  s rafale_parties;
  v_lettre text;
  v_cfg jsonb := coalesce((select valeur::jsonb from config_jeu where cle = 'rafale_appariement'), '{}'::jsonb);   -- s2-145/146
  v_ecart int := coalesce((v_cfg ->> 'ecart_max')::int, 300);
  v_attente int := coalesce((v_cfg ->> 'attente_h')::int, 12);
begin
  if v_uid is null then raise exception 'Connecte-toi pour jouer à Rafale.'; end if;
  perform pg_advisory_xact_lock(hashtextextended('rafale' || v_uid::text, 7));

  select id into v_id from rafale_parties where joueur_id = v_uid and not fini order by id desc limit 1;
  if v_id is not null then
    perform rafale_rattraper(v_id);
    if not (select fini from rafale_parties where id = v_id) then return rafale_vue(v_id); end if;
  end if;

  insert into rafale_joueurs(joueur_id) values (v_uid) on conflict do nothing;
  select elo into v_elo from rafale_joueurs where joueur_id = v_uid;

  -- un adversaire : partie classée finie, pas encore affrontée, d'un autre
  -- joueur ; de préférence pas affronté depuis 24 h, puis Elo proche, puis
  -- la plus ancienne
  -- s2-146 : pas au-delà de ecart_max d'Elo, sauf partie en attente depuis plus de attente_h
  select p.* into s
    from rafale_parties p
    left join rafale_joueurs r on r.joueur_id = p.joueur_id
   where p.source_id is null and p.fini and not p.utilisee
     and p.joueur_id <> v_uid and p.cible_id is null and not p.amical
     and (abs(coalesce(r.elo, 1000) - v_elo) <= v_ecart or p.fin_le < now() - make_interval(hours => v_attente))
   order by exists (select 1 from rafale_parties m
                      join rafale_parties ms on ms.id = m.source_id
                     where m.joueur_id = v_uid and ms.joueur_id = p.joueur_id
                       and m.cree_le > now() - interval '24 hours'),
            abs(coalesce(r.elo, 1000) - v_elo), p.fin_le
   limit 1
   for update of p skip locked;

  if s.id is not null then
    update rafale_parties set utilisee = true where id = s.id;
    v_lettre := s.lettre;
  else
    v_lettre := substr(rafale_lettres(), 1 + floor(random() * length(rafale_lettres()))::int, 1);
  end if;

  insert into rafale_parties(joueur_id, lettre, source_id) values (v_uid, v_lettre, s.id)
  returning id into v_id;
  return rafale_vue(v_id);
end;
$function$;

CREATE OR REPLACE FUNCTION public.radar_lancer()
 RETURNS jsonb
 LANGUAGE plpgsql
 SECURITY DEFINER
 SET search_path TO 'public'
AS $function$
declare
  v_uid uuid := auth.uid();
  v_jour date := (now() at time zone 'Europe/Paris')::date;
  v_id bigint;
  v_elo int;
  s radar_parties;
  v_codes text[];
  v_cfg jsonb := coalesce((select valeur::jsonb from config_jeu where cle = 'radar_appariement'), '{}'::jsonb);   -- s2-146
  v_ecart int := coalesce((v_cfg ->> 'ecart_max')::int, 300);
  v_attente int := coalesce((v_cfg ->> 'attente_h')::int, 12);
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
     and (abs(coalesce(r.elo, 1000) - v_elo) <= v_ecart or p.fin_le < now() - make_interval(hours => v_attente))   -- s2-146
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
$function$;
