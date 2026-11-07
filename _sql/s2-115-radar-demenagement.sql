-- s2-115 (7/11/2026) : le Radar de détection et le déménagement du Centre de recherche.
-- Décisions de Nataël (7/11, 22 h 39) : le Radar ne voit pas les Banques ; le
-- joueur repéré est prévenu ; le déménagement du Centre se fait en même temps.
--
-- Radar (version du 5/11) :
--   30 lingots, une Fonderie demandée, 6 h, un seul par joueur, visible de tous,
--   détruit si on prend sa commune (comme les autres bâtiments) ;
--   montre à son propriétaire les Centres de recherche des autres joueurs (hors
--   clan) à moins de 50 km, même secrets, même en construction ;
--   le propriétaire du Centre repéré est prévenu (cloche + notification), une
--   fois par couple Radar / Centre (tâche radar-reperer toutes les 5 min) ;
--   classement : +80 une fois construit, comme la Banque.
-- Déménager le Centre (idée d'Arkhannou, option B du 5/11) :
--   l'ancien rend 20 lingots, le nouveau en coûte 40 : 20 de sa poche ; 6 h ;
--   refusé si le Centre est encore en construction (l'annuler rend tout) ou si
--   sa commune est attaquée ;
--   la bombe en préparation suit : elle est en pause pendant le chantier (sa
--   préparation recule de 6 h, on ne peut pas la lâcher avant la fin) ;
--   l'alerte publique annonce le nouveau département ;
--   un Centre dévoilé le reste à sa nouvelle adresse.
-- Les Radars d'un ancien Centre l'oublient ; s'il retombe dans la portée d'un
-- Radar, son propriétaire est prévenu à nouveau.

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

-- 1. Réglages et styles
update public.config_jeu
   set valeur = (valeur::jsonb || '{"radars_ouverts": 1, "radar_prix": 30, "radar_portee_km": 50, "centre_rendu": 20}'::jsonb)::text
 where cle = 'batiments';
update public.config_jeu
   set valeur = (valeur::jsonb || '{"radar": ["parabole", "dome", "pylone"]}'::jsonb)::text
 where cle = 'batiments_styles';

-- 2. Le type « radar », les colonnes du dévoilement qui suit un déménagement
alter table public.batiments drop constraint if exists batiments_type_check;
alter table public.batiments add constraint batiments_type_check
  check (type = any (array['fonderie', 'forteresse', 'centre', 'banque', 'radar']));
alter table public.batiments add column if not exists devoile_jusqua timestamptz;
alter table public.bombes_preparations add column if not exists devoile_force boolean not null default false;

-- 3. Les repérages (pour prévenir une seule fois, et dire au repéré qui le voit)
create table if not exists public.radar_reperages (
  radar_id      bigint not null references public.batiments(id) on delete cascade,
  centre_id     bigint not null references public.batiments(id) on delete cascade,
  radar_joueur  uuid not null,
  centre_joueur uuid not null,
  centre_code   text not null,
  km            numeric not null,
  vu_le         timestamptz not null default now(),
  prevenu       boolean not null default false,
  primary key (radar_id, centre_id)
);
create index if not exists radar_reperages_centre_joueur on public.radar_reperages (centre_joueur);
alter table public.radar_reperages enable row level security;
revoke all on public.radar_reperages from anon, authenticated;

-- 4. Ce que voit un Radar (calculé à la lecture : rien n'attend la tâche)
create or replace function public.radar_voit(p_uid uuid, p_code text, p_proprio uuid)
 returns boolean language sql stable security definer set search_path to 'public' as $f$
  select p_uid is not null and p_proprio is distinct from p_uid
     and coalesce(batiment_reglage('radars_ouverts'), 0) >= 1
     and not meme_clan(p_uid, p_proprio)
     and exists (select 1 from batiments r join communes a on a.code = r.commune_code, communes c
                  where r.joueur_id = p_uid and r.type = 'radar' and r.pret_le <= now() and c.code = p_code
                    and dist_km(a.latitude, a.longitude, c.latitude, c.longitude) <= coalesce(batiment_reglage('radar_portee_km'), 50));
$f$;
revoke execute on function public.radar_voit(uuid, text, uuid) from public, anon, authenticated;

-- 5. Un Centre dévoilé le reste après un déménagement
create or replace function public.centre_devoile(p_uid uuid, p_code text)
 returns boolean language sql stable security definer set search_path to 'public' as $f$
  select exists (select 1 from bombes_preparations p
                  where p.joueur_id = p_uid and p.etat = 'en_cours' and p.centre_code = p_code
                    and (p.devoile_force   -- s2-115
                         or now() - p.commence_le >= make_interval(hours => batiment_reglage('bombe_devoile_h')::integer)))
      or exists (select 1 from bombes b
                  where b.lanceur = p_uid and b.centre_code = p_code
                    and b.le > now() - make_interval(hours => batiment_reglage('bombe_duree_h')::integer))
      or exists (select 1 from batiments c   -- s2-115 : dévoilé par un lâcher récent, avant le déménagement
                  where c.joueur_id = p_uid and c.commune_code = p_code and c.type = 'centre' and c.devoile_jusqua > now());
$f$;

-- 6. Construire et annuler un Radar
do $$
declare d text := pg_get_functiondef('public.batiment_construire(text, text)'::regprocedure);
begin
  if position('s2-115' in d) > 0 then raise notice 'batiment_construire : déjà à jour'; return; end if;
  d := pg_temp.remp(d,
$a$if p_type not in ('fonderie', 'forteresse', 'centre', 'banque') then raise exception 'Bâtiment inconnu'; end if;   -- s2-104$a$,
$a$if p_type not in ('fonderie', 'forteresse', 'centre', 'banque', 'radar') then raise exception 'Bâtiment inconnu'; end if;   -- s2-104, s2-115$a$, 1, 'batiment_construire (types)');
  d := pg_temp.remp(d,
$a$  else
    if v_nf = 0 then raise exception 'Il te faut d''abord une Fonderie'; end if;
    if (select count(*) from batiments b where b.joueur_id = v_uid and b.type = 'forteresse')$a$,
$a$  elsif p_type = 'radar' then   -- s2-115 : le Radar
    if coalesce(batiment_reglage('radars_ouverts'), 0) < 1 then raise exception 'Le Radar n''est pas encore ouvert'; end if;
    if v_nf = 0 then raise exception 'Il te faut d''abord une Fonderie'; end if;
    if exists (select 1 from batiments b where b.joueur_id = v_uid and b.type = 'radar') then
      raise exception 'Tu as déjà un Radar';
    end if;
    v_prix := coalesce(batiment_reglage('radar_prix'), 30);
    v := lingots_figer(v_uid);
    if v < v_prix then raise exception 'Il te faut % lingots (tu en as %)', v_prix::integer, floor(v)::integer; end if;
    update joueurs set lingots = lingots - v_prix where id = v_uid;
  else
    if v_nf = 0 then raise exception 'Il te faut d''abord une Fonderie'; end if;
    if (select count(*) from batiments b where b.joueur_id = v_uid and b.type = 'forteresse')$a$, 1, 'batiment_construire (radar)');
  execute d;
end $$;

do $$
declare d text := pg_get_functiondef('public.batiment_annuler(text, text)'::regprocedure);
begin
  if position('s2-115' in d) > 0 then raise notice 'batiment_annuler : déjà à jour'; return; end if;
  d := pg_temp.remp(d,
$a$    when 'banque'     then batiment_reglage('banque_prix')   -- s2-104$a$,
$a$    when 'banque'     then batiment_reglage('banque_prix')   -- s2-104
    when 'radar'      then coalesce(batiment_reglage('radar_prix'), 30)   -- s2-115$a$, 1, 'batiment_annuler');
  d := pg_temp.remp(d,
$a$  if b.pret_le <= now() then raise exception 'Ce bâtiment est déjà construit : on ne peut plus l''annuler'; end if;
$a$,
$a$  if b.pret_le <= now() then raise exception 'Ce bâtiment est déjà construit : on ne peut plus l''annuler'; end if;
  if b.type = 'centre' and exists (select 1 from bombes_preparations p
                                    where p.joueur_id = v_uid and p.etat = 'en_cours' and p.centre_code = p_code) then   -- s2-115
    raise exception 'Ton Centre déménage avec ta bombe : ce chantier ne s''annule pas';
  end if;
$a$, 1, 'batiment_annuler (déménagement)');
  execute d;
end $$;

-- 7. Le classement : +80 pour un Radar construit
do $$
declare d text := pg_get_functiondef('public.score_batiments()'::regprocedure);
begin
  if position('s2-115' in d) > 0 then raise notice 'score_batiments : déjà à jour'; return; end if;
  d := pg_temp.remp(d,
$a$         + least(count(*) filter (where h.type = 'banque'), 1) * coalesce(score_reglage('bat_banque'), 80) as pts$a$,
$a$         + least(count(*) filter (where h.type = 'banque'), 1) * coalesce(score_reglage('bat_banque'), 80)
         + least(count(*) filter (where h.type = 'radar'), 1) * coalesce(score_reglage('bat_radar'), 80) as pts   -- s2-115$a$, 1, 'score_batiments');
  execute d;
end $$;

-- 8. La carte et la liste des autres : les Centres vus par mon Radar
do $$
declare d text := pg_get_functiondef('public.batiments_visibles()'::regprocedure);
begin
  if position('s2-115' in d) > 0 then raise notice 'batiments_visibles : déjà à jour'; return; end if;
  d := pg_temp.remp(d,
$a$(b.type = 'centre' and centre_devoile(b.joueur_id, b.commune_code)));$a$,
$a$(b.type = 'centre' and centre_devoile(b.joueur_id, b.commune_code))
          or (b.type = 'centre' and radar_voit(auth.uid(), b.commune_code, b.joueur_id)));   -- s2-115 : vu par mon Radar$a$, 1, 'batiments_visibles');
  execute d;
end $$;

do $$
declare d text := pg_get_functiondef('public.batiments_autres(text, text[], text, text, integer, integer)'::regprocedure);
begin
  if position('s2-115' in d) > 0 then raise notice 'batiments_autres : déjà à jour'; return; end if;
  d := pg_temp.remp(d,
$a$             case when exists (select 1 from bombes_preparations p where p.joueur_id = b.joueur_id and p.etat = 'en_cours')
                  then 'preparation' else 'lancee' end end as centre$a$,
$a$             case when exists (select 1 from bombes_preparations p where p.joueur_id = b.joueur_id and p.etat = 'en_cours')
                  then 'preparation'
                  when exists (select 1 from bombes x where x.lanceur = b.joueur_id and x.centre_code = b.commune_code)
                  then 'lancee' else 'calme' end end as centre,
           case when b.type = 'centre' then not centre_devoile(b.joueur_id, b.commune_code) end as radar   -- s2-115 : vu seulement par mon Radar$a$, 1, 'batiments_autres (colonnes)');
  d := pg_temp.remp(d,
$a$       and (b.type <> 'centre' or centre_devoile(b.joueur_id, b.commune_code))$a$,
$a$       and (b.type <> 'centre' or centre_devoile(b.joueur_id, b.commune_code) or radar_voit(v_uid, b.commune_code, b.joueur_id))   -- s2-115$a$, 1, 'batiments_autres (filtre)');
  execute d;
end $$;

-- 9. Ce que le jeu reçoit : mon Radar et ce qu'il voit, qui voit mon Centre
create or replace function public.radar_infos(p_uid uuid)
 returns jsonb language sql stable security definer set search_path to 'public' as $f$
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
    'radar_reglages', jsonb_build_object('prix', coalesce(batiment_reglage('radar_prix'), 30)::integer,
                        'portee_km', coalesce(batiment_reglage('radar_portee_km'), 50)::integer,
                        'centre_rendu', coalesce(batiment_reglage('centre_rendu'), 20)::integer));
$f$;
revoke execute on function public.radar_infos(uuid) from public, anon, authenticated;

do $$
declare d text := pg_get_functiondef('public.mes_batiments()'::regprocedure);
begin
  if position('s2-115' in d) > 0 then raise notice 'mes_batiments : déjà à jour'; return; end if;
  d := pg_temp.remp(d,
$a$batiment_reglage('bombe_rayon3')::integer)));
end;$a$,
$a$batiment_reglage('bombe_rayon3')::integer))) || radar_infos(v_uid);   -- s2-115
end;$a$, 1, 'mes_batiments');
  execute d;
end $$;

-- 10. Prévenir le joueur repéré (une fois par couple Radar / Centre)
create or replace function public.radar_reperer()
 returns integer language plpgsql security definer set search_path to 'public' as $f$
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
    join batiments c on c.type = 'centre' and c.joueur_id <> r.joueur_id
    join communes k on k.code = c.commune_code
   where r.type = 'radar' and r.pret_le <= now()
     and k.latitude between a.latitude - v_portee / 110.0 and a.latitude + v_portee / 110.0
     and dist_km(a.latitude, a.longitude, k.latitude, k.longitude) <= v_portee
     and not meme_clan(r.joueur_id, c.joueur_id)
  on conflict do nothing;
  for x in
    select g.radar_id, g.centre_id, g.centre_joueur, g.km, j.pseudo, k.nom
      from radar_reperages g left join joueurs j on j.id = g.radar_joueur join communes k on k.code = g.centre_code
     where not g.prevenu
  loop
    perform notifier_joueur(x.centre_joueur, 'Ton Centre est repéré',
      format('Le Radar de %s voit ton Centre de recherche à %s (à %s km). Déménage-le pour disparaître de son écran.',
             coalesce(x.pseudo, 'un joueur'), x.nom, x.km),
      './?onglet=defense', 'radar');
    update radar_reperages set prevenu = true where radar_id = x.radar_id and centre_id = x.centre_id;
    n := n + 1;
  end loop;
  return n;
end;
$f$;
revoke execute on function public.radar_reperer() from public, anon, authenticated;

-- 11. Déménager son Centre de recherche
create or replace function public.centre_demenager(p_code text)
 returns jsonb language plpgsql security definer set search_path to 'public' as $f$
-- s2-115 : l'ancien rend centre_rendu (20), le nouveau coûte centre_prix (40) ; la bombe suit, en pause pendant le chantier
declare
  v_uid uuid := auth.uid();
  v_old record;
  v_dept text;
  v_net numeric;
  v numeric;
  v_dev_prep boolean;
  v_fin timestamptz;
  v_h integer := batiment_reglage('construction_h')::integer;
begin
  if v_uid is null then raise exception 'Non connecte'; end if;
  if not bombes_ouvertes() then raise exception 'Le Centre de recherche n''est pas encore ouvert'; end if;
  perform 1 from joueurs where id = v_uid for update;
  select * into v_old from batiments where joueur_id = v_uid and type = 'centre';
  if v_old.id is null then raise exception 'Tu n''as pas de Centre de recherche'; end if;
  if v_old.pret_le > now() then raise exception 'Ton Centre est encore en construction : attends la fin du chantier pour le déménager'; end if;
  if v_old.commune_code = p_code then raise exception 'Ton Centre est déjà ici'; end if;
  if not exists (select 1 from possessions p where p.commune_code = p_code and p.joueur_id = v_uid) then
    raise exception 'Cette commune ne t''appartient pas';
  end if;
  if exists (select 1 from sieges s where s.commune_code = v_old.commune_code and coalesce(s.victoires_consecutives, 0) > 0) then
    raise exception 'Ton Centre est attaqué : impossible de déménager pendant l''assaut';
  end if;
  v_net := greatest(0, batiment_reglage('centre_prix') - coalesce(batiment_reglage('centre_rendu'), 20));
  v := lingots_figer(v_uid);
  if v < v_net then raise exception 'Il te faut % lingots (tu en as %)', v_net::integer, floor(v)::integer; end if;
  select departement into v_dept from communes where code = p_code;
  -- ce qui le dévoile : la préparation (36 h, ou déjà forcée), ou un lâcher de moins de 24 h
  select bool_or(p.devoile_force or now() - p.commence_le >= make_interval(hours => batiment_reglage('bombe_devoile_h')::integer))
    into v_dev_prep from bombes_preparations p where p.joueur_id = v_uid and p.etat = 'en_cours';
  select max(b.le + make_interval(hours => batiment_reglage('bombe_duree_h')::integer)) into v_fin
    from bombes b where b.lanceur = v_uid and b.centre_code = v_old.commune_code;
  v_fin := greatest(v_fin, v_old.devoile_jusqua);
  delete from batiments where id = v_old.id;
  insert into batiments (joueur_id, commune_code, type, pret_le, style, devoile_jusqua)
  values (v_uid, p_code, 'centre', now() + make_interval(hours => v_h), v_old.style, case when v_fin > now() then v_fin end);
  update bombes_preparations
     set centre_code = p_code, dept = v_dept,
         commence_le = commence_le + make_interval(hours => v_h),
         devoile_force = devoile_force or coalesce(v_dev_prep, false)
   where joueur_id = v_uid and etat = 'en_cours';
  if v_net > 0 then update joueurs set lingots = lingots - v_net where id = v_uid; end if;
  return mes_batiments();
end;
$f$;
revoke execute on function public.centre_demenager(text) from public, anon;
grant execute on function public.centre_demenager(text) to authenticated;

-- 12. Pas de bombe lâchée depuis un Centre en chantier
do $$
declare d text := pg_get_functiondef('public.bombe_lacher(text)'::regprocedure);
begin
  if position('s2-115' in d) > 0 then raise notice 'bombe_lacher : déjà à jour'; return; end if;
  d := pg_temp.remp(d,
$a$    raise exception 'Ton Centre de recherche a été détruit : la bombe est perdue';
  end if;
$a$,
$a$    raise exception 'Ton Centre de recherche a été détruit : la bombe est perdue';
  end if;
  if exists (select 1 from batiments b where b.joueur_id = v_uid and b.type = 'centre'
               and b.commune_code = v_prep.centre_code and b.pret_le > now()) then   -- s2-115
    raise exception 'Ton Centre de recherche déménage : la bombe est en pause jusqu''à la fin du chantier';
  end if;
$a$, 1, 'bombe_lacher');
  execute d;
end $$;

-- 13. La tâche qui prévient les repérés
select cron.schedule('radar-reperer', '*/5 * * * *', 'select public.radar_reperer()');

commit;

-- Contrôle : t | t | t | t | t | t | t | t
select exists (select 1 from pg_constraint where conname = 'batiments_type_check' and pg_get_constraintdef(oid) like '%radar%') as type_ok,
       to_regclass('public.radar_reperages') is not null as table_ok,
       position('s2-115' in pg_get_functiondef('public.batiment_construire(text, text)'::regprocedure)) > 0
         and position('s2-115' in pg_get_functiondef('public.batiment_annuler(text, text)'::regprocedure)) > 0 as construire_ok,
       position('s2-115' in pg_get_functiondef('public.mes_batiments()'::regprocedure)) > 0
         and position('s2-115' in pg_get_functiondef('public.batiments_visibles()'::regprocedure)) > 0
         and position('s2-115' in pg_get_functiondef('public.batiments_autres(text, text[], text, text, integer, integer)'::regprocedure)) > 0 as vues_ok,
       position('s2-115' in pg_get_functiondef('public.score_batiments()'::regprocedure)) > 0 as score_ok,
       position('s2-115' in pg_get_functiondef('public.bombe_lacher(text)'::regprocedure)) > 0 as lacher_ok,
       has_function_privilege('authenticated', 'public.centre_demenager(text)', 'execute')
         and not has_function_privilege('authenticated', 'public.radar_voit(uuid, text, uuid)', 'execute')
         and not has_function_privilege('authenticated', 'public.radar_reperer()', 'execute') as droits_ok,
       exists (select 1 from cron.job where jobname = 'radar-reperer') as tache_ok;
