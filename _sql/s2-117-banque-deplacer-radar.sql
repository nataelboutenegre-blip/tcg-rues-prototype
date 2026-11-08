-- s2-117 (8/11/2026) : déplacer la Banque, et les Radars voient les Banques.
-- Demande de Nataël (8/11, 13 h 32) ; cela remplace sa décision du 7/11 (« le
-- Radar ne voit pas les Banques ») : maintenant qu'une Banque peut fuir, elle
-- peut aussi être trouvée.
--
-- Déplacer la Banque (comme une forteresse, s2-116) :
--   - banque_deplacer_prix lingots (10) ; 6 h de chantier ; refusé pendant un
--     assaut sur sa commune ; ne s'annule pas ;
--   - c'est la même ligne : son contenu la suit, elle reste comptée une fois au score ;
--   - pendant le chantier : pas de dépôt ni d'intérêts (déjà le cas pour une Banque
--     pas prête), le retrait reste possible ;
--   - les Radars qui la voyaient à l'ancienne adresse l'oublient ; s'ils la voient
--     encore à la nouvelle, son propriétaire est prévenu à nouveau.
-- Le Radar voit les Banques (hors clan, à moins de 50 km, même en chantier) :
--   sur la carte (batiments_visibles), dans « Les autres » (batiments_autres),
--   dans Défendre (radar_infos.voit_banques) ; le propriétaire est prévenu
--   (radar_reperer, radar_infos.banque_reperee_par). Le contenu n'est pas montré.

create or replace function pg_temp.remp(d text, avant text, apres text, nb int, quoi text)
 returns text language plpgsql as $f$
begin
  if (length(d) - length(replace(d, avant, ''))) / length(avant) <> nb then
    raise exception '% : texte attendu % fois, trouvé % fois — rien n''a changé : %',
      quoi, nb, (length(d) - length(replace(d, avant, ''))) / length(avant), avant;
  end if;
  return replace(d, avant, apres);
end;
$f$;

begin;

-- 1. Réglage
update public.config_jeu
   set valeur = (valeur::jsonb || '{"banque_deplacer_prix": 10}'::jsonb)::text
 where cle = 'batiments';

-- 2. Déplacer la Banque
create or replace function public.banque_deplacer(p_vers text)
 returns jsonb language plpgsql security definer set search_path to 'public' as $f$
-- s2-117 : la Banque va sur une autre de ses communes ; 10 lingots, 6 h ; son contenu la suit
declare
  v_uid uuid := auth.uid();
  b record;
  v numeric;
  v_prix numeric := coalesce(batiment_reglage('banque_deplacer_prix'), 10);
begin
  if v_uid is null then raise exception 'Non connecte'; end if;
  if coalesce(batiment_reglage('banques_ouvertes'), 0) < 1 then raise exception 'La Banque n''est pas encore ouverte'; end if;
  perform 1 from joueurs where id = v_uid for update;   -- deux clics ne paient pas deux fois
  select * into b from batiments where joueur_id = v_uid and type = 'banque' for update;
  if b.id is null then raise exception 'Tu n''as pas de Banque'; end if;
  if b.pret_le > now() then raise exception 'Ta Banque est encore en chantier : attends qu''elle soit prête pour la déplacer'; end if;
  if b.commune_code = p_vers then raise exception 'Ta Banque est déjà ici'; end if;
  if not exists (select 1 from possessions p where p.commune_code = p_vers and p.joueur_id = v_uid) then
    raise exception 'Cette commune ne t''appartient pas';
  end if;
  if exists (select 1 from batiments x where x.commune_code = p_vers and x.type = 'banque') then
    raise exception 'Il y a déjà une Banque ici';
  end if;
  if exists (select 1 from sieges s where s.commune_code = b.commune_code and coalesce(s.victoires_consecutives, 0) > 0) then
    raise exception 'Ta Banque est attaquée : impossible de la déplacer pendant l''assaut';
  end if;
  v := lingots_figer(v_uid);
  if v < v_prix then raise exception 'Il te faut % lingots (tu en as %)', v_prix::integer, floor(v)::integer; end if;
  update batiments
     set commune_code = p_vers,
         pret_le = now() + make_interval(hours => batiment_reglage('construction_h')::integer),
         deplacee_le = now()
   where id = b.id;
  delete from radar_reperages where centre_id = b.id;   -- les Radars de l'ancienne adresse l'oublient
  if v_prix > 0 then update joueurs set lingots = lingots - v_prix where id = v_uid; end if;
  return mes_batiments();
end;
$f$;
revoke execute on function public.banque_deplacer(text) from public, anon;
grant execute on function public.banque_deplacer(text) to authenticated;

-- 3. Le Radar : ce qu'il voit, ce qu'on sait de lui
create or replace function public.radar_infos(p_uid uuid)
 returns jsonb language sql stable security definer set search_path to 'public' as $f$
  -- s2-115 ; s2-117 : les Banques aussi (voit_banques, banque_reperee_par)
  select jsonb_build_object(
    'radars_ouverts', coalesce(batiment_reglage('radars_ouverts'), 0) >= 1,
    'radar', (select jsonb_build_object('code', r.commune_code, 'nom', a.nom, 'dept', a.departement,
                       'pret_le', r.pret_le, 'pret', r.pret_le <= now(),
                       'style', coalesce(r.style, batiment_styles() -> 'radar' ->> 0),
                       'voit', coalesce((
                         select jsonb_agg(jsonb_build_object('code', c.commune_code, 'nom', k.nom, 'dept', k.departement, 'pseudo', j.pseudo,
                                  'km', round(dist_km(a.latitude, a.longitude, k.latitude, k.longitude)::numeric, 1),
                                  'pret', c.pret_le <= now(),
                                  'bombe', exists (select 1 from bombes_preparations p where p.joueur_id = c.joueur_id and p.etat = 'en_cours'),
                                  'devoile', centre_devoile(c.joueur_id, c.commune_code))
                                  order by dist_km(a.latitude, a.longitude, k.latitude, k.longitude))
                           from batiments c join communes k on k.code = c.commune_code left join joueurs j on j.id = c.joueur_id
                          where r.pret_le <= now() and c.type = 'centre' and c.joueur_id <> p_uid and not meme_clan(p_uid, c.joueur_id)
                            and dist_km(a.latitude, a.longitude, k.latitude, k.longitude) <= coalesce(batiment_reglage('radar_portee_km'), 50)),
                         '[]'::jsonb),
                       'voit_banques', coalesce((
                         select jsonb_agg(jsonb_build_object('code', c.commune_code, 'nom', k.nom, 'dept', k.departement, 'pseudo', j.pseudo,
                                  'km', round(dist_km(a.latitude, a.longitude, k.latitude, k.longitude)::numeric, 1),
                                  'pret', c.pret_le <= now())
                                  order by dist_km(a.latitude, a.longitude, k.latitude, k.longitude))
                           from batiments c join communes k on k.code = c.commune_code left join joueurs j on j.id = c.joueur_id
                          where r.pret_le <= now() and c.type = 'banque' and c.joueur_id <> p_uid and not meme_clan(p_uid, c.joueur_id)
                            and dist_km(a.latitude, a.longitude, k.latitude, k.longitude) <= coalesce(batiment_reglage('radar_portee_km'), 50)),
                         '[]'::jsonb))
                from batiments r join communes a on a.code = r.commune_code
               where r.joueur_id = p_uid and r.type = 'radar'),
    'repere_par', coalesce((
        select jsonb_agg(jsonb_build_object('id', x.radar_id, 'pseudo', j.pseudo, 'code', r.commune_code, 'nom', a.nom,
                           'dept', a.departement, 'km', x.km, 'le', x.vu_le) order by x.vu_le desc)
          from radar_reperages x
          join batiments r on r.id = x.radar_id
          join batiments c on c.id = x.centre_id and c.joueur_id = p_uid and c.type = 'centre'
          join communes a on a.code = r.commune_code
          left join joueurs j on j.id = x.radar_joueur
         where x.centre_joueur = p_uid and not meme_clan(p_uid, x.radar_joueur)), '[]'::jsonb),
    'banque_reperee_par', coalesce((
        select jsonb_agg(jsonb_build_object('id', x.radar_id, 'pseudo', j.pseudo, 'code', r.commune_code, 'nom', a.nom,
                           'dept', a.departement, 'km', x.km, 'le', x.vu_le) order by x.vu_le desc)
          from radar_reperages x
          join batiments r on r.id = x.radar_id
          join batiments c on c.id = x.centre_id and c.joueur_id = p_uid and c.type = 'banque'
          join communes a on a.code = r.commune_code
          left join joueurs j on j.id = x.radar_joueur
         where x.centre_joueur = p_uid and not meme_clan(p_uid, x.radar_joueur)), '[]'::jsonb),
    'radar_reglages', jsonb_build_object('prix', coalesce(batiment_reglage('radar_prix'), 30)::integer,
                        'portee_km', coalesce(batiment_reglage('radar_portee_km'), 50)::integer,
                        'centre_rendu', coalesce(batiment_reglage('centre_rendu'), 20)::integer,
                        'voit_banques', true));
$f$;

create or replace function public.radar_reperer()
 returns integer language plpgsql security definer set search_path to 'public' as $f$
-- s2-115 ; s2-117 : les Banques aussi
declare
  n integer := 0;
  x record;
  v_portee numeric := coalesce(batiment_reglage('radar_portee_km'), 50);
begin
  if coalesce(batiment_reglage('radars_ouverts'), 0) < 1 then return 0; end if;
  insert into radar_reperages (radar_id, centre_id, radar_joueur, centre_joueur, centre_code, km)
  select r.id, c.id, r.joueur_id, c.joueur_id, c.commune_code,
         round(dist_km(a.latitude, a.longitude, k.latitude, k.longitude)::numeric, 1)
    from batiments r
    join communes a on a.code = r.commune_code
    join batiments c on c.type in ('centre', 'banque') and c.joueur_id <> r.joueur_id
    join communes k on k.code = c.commune_code
   where r.type = 'radar' and r.pret_le <= now()
     and k.latitude between a.latitude - v_portee / 110.0 and a.latitude + v_portee / 110.0
     and dist_km(a.latitude, a.longitude, k.latitude, k.longitude) <= v_portee
     and not meme_clan(r.joueur_id, c.joueur_id)
  on conflict do nothing;
  for x in
    select g.radar_id, g.centre_id, g.centre_joueur, g.km, j.pseudo, k.nom, c.type
      from radar_reperages g
      left join joueurs j on j.id = g.radar_joueur
      join communes k on k.code = g.centre_code
      join batiments c on c.id = g.centre_id
     where not g.prevenu
  loop
    if x.type = 'banque' then
      perform notifier_joueur(x.centre_joueur, 'Ta Banque est repérée',
        format('Le Radar de %s voit ta Banque à %s (à %s km). Déplace-la pour disparaître de son écran.',
               coalesce(x.pseudo, 'un joueur'), x.nom, x.km),
        './?onglet=defense', 'radar');
    else
      perform notifier_joueur(x.centre_joueur, 'Ton Centre est repéré',
        format('Le Radar de %s voit ton Centre de recherche à %s (à %s km). Déménage-le pour disparaître de son écran.',
               coalesce(x.pseudo, 'un joueur'), x.nom, x.km),
        './?onglet=defense', 'radar');
    end if;
    update radar_reperages set prevenu = true where radar_id = x.radar_id and centre_id = x.centre_id;
    n := n + 1;
  end loop;
  return n;
end;
$f$;
revoke execute on function public.radar_reperer() from public, anon, authenticated;

-- 4. Retouches : carte, « Les autres », annulation, mes_batiments
do $$
declare d text;
begin
  d := pg_get_functiondef('public.batiments_visibles()'::regprocedure);
  d := pg_temp.remp(d,
$a$(b.type = 'centre' and radar_voit(auth.uid()$a$,
$a$(b.type in ('centre', 'banque') /* s2-117 */ and radar_voit(auth.uid()$a$, 1, 'batiments_visibles');
  execute d;

  d := pg_get_functiondef('public.batiments_autres(text, text[], text, text, integer, integer)'::regprocedure);
  d := pg_temp.remp(d,
$a$       and b.type <> 'banque'$a$,
$a$       and (b.type <> 'banque' or radar_voit(v_uid, b.commune_code, b.joueur_id))   -- s2-117 : vue par mon Radar$a$, 1, 'batiments_autres (banque)');
  d := pg_temp.remp(d,
$a$case when b.type = 'centre' then not centre_devoile(b.joueur_id, b.commune_code) end as radar$a$,
$a$case when b.type = 'centre' then not centre_devoile(b.joueur_id, b.commune_code) when b.type = 'banque' then true end as radar$a$, 1, 'batiments_autres (radar)');
  execute d;

  d := pg_get_functiondef('public.batiment_annuler(text, text)'::regprocedure);
  d := pg_temp.remp(d,
$a$  if b.type = 'forteresse' and b.deplacee_le is not null then   -- s2-116
    raise exception 'Une forteresse en déplacement ne s''annule pas';$a$,
$a$  if b.type in ('forteresse', 'banque') and b.deplacee_le is not null then   -- s2-116, s2-117
    raise exception 'Un déplacement ne s''annule pas';$a$, 1, 'batiment_annuler');
  execute d;

  d := pg_get_functiondef('public.mes_batiments()'::regprocedure);
  d := pg_temp.remp(d,
$a$'contenu', floor(b.contenu)::integer)$a$,
$a$'contenu', floor(b.contenu)::integer, 'deplacee', b.deplacee_le is not null and b.pret_le > now())$a$, 1, 'mes_batiments (banque)');
  d := pg_temp.remp(d,
$a$'epargne', true,$a$,
$a$'epargne', true,
                      'deplacer_prix', coalesce(batiment_reglage('banque_deplacer_prix'), 10)::integer,   -- s2-117$a$, 1, 'mes_batiments (réglages)');
  execute d;
end $$;

commit;

-- Contrôle : t | t | t | t | t | 10
select has_function_privilege('authenticated', 'public.banque_deplacer(text)', 'execute')
         and not has_function_privilege('anon', 'public.banque_deplacer(text)', 'execute') as droits_ok,
       position('s2-117' in pg_get_functiondef('public.radar_infos(uuid)'::regprocedure)) > 0
         and position('s2-117' in pg_get_functiondef('public.radar_reperer()'::regprocedure)) > 0 as radar_ok,
       position('s2-117' in pg_get_functiondef('public.batiments_visibles()'::regprocedure)) > 0
         and position('s2-117' in pg_get_functiondef('public.batiments_autres(text, text[], text, text, integer, integer)'::regprocedure)) > 0 as vues_ok,
       position('s2-117' in pg_get_functiondef('public.batiment_annuler(text, text)'::regprocedure)) > 0 as annuler_ok,
       position('s2-117' in pg_get_functiondef('public.mes_batiments()'::regprocedure)) > 0 as mes_ok,
       public.batiment_reglage('banque_deplacer_prix') as prix;
