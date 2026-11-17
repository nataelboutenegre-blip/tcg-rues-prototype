-- ===========================================================================
--  s3-18 (17/11/2026) — la roue du Front ouverte en saison 3, avec ses propres jetons
--  Décision de Nataël (17/11 midi) : « qu'un joueur actif ne manque pas d'énergie ».
--  En saison 2, la roue ne s'ouvre que pot vide et prend les jetons des paquets.
--  Le 22/11 le pot se remplit (≈ 34 000 communes) : sans ce fichier, la roue se
--  fermerait pour tous. Deux réglages de config_jeu 'roue_front', À 0 ICI (rien ne
--  change avant le jour J) ; s3-jj-4-ouverture les met à 1 :
--    toujours       : 1 = la roue est ouverte même quand le pot n'est pas vide ;
--    jetons_propres : 1 = la roue a ses jetons à elle (même rythme : 1 toutes les
--                     20 min, 3 en réserve), les paquets gardent les leurs.
--  roue_front_etat renvoie en plus « avec_paquets » (la roue s'ajoute aux paquets,
--  le jeu ne les cache plus) et « propres ».
--  Contrôle attendu (dernière ligne) : 0 | 0 | true | true | true
-- ===========================================================================

alter table public.joueurs
  add column if not exists roue_jetons numeric not null default 3,
  add column if not exists roue_jetons_maj timestamptz not null default now();

update public.config_jeu
   set valeur = (valeur::jsonb || '{"toujours": 0, "jetons_propres": 0}'::jsonb)::text
 where cle = 'roue_front' and not (valeur::jsonb ? 'toujours');

create or replace function public.roue_cfg_int(p_cle text)
 returns integer language sql stable security definer set search_path to 'public'
as $f$ select coalesce((select (c.valeur::jsonb ->> p_cle)::int from config_jeu c where c.cle = 'roue_front'), 0); $f$;

-- la roue s'ajoute aux paquets (pot non vide, pas de réserve d'accueil pour ce joueur)
create or replace function public.roue_avec_paquets(p_uid uuid)
 returns boolean language sql stable security definer set search_path to 'public'
as $f$
  select roue_cfg_int('toujours') = 1
     and not reserve_accueil_bloque(p_uid)
     and exists (select 1 from communes c where not exists (select 1 from possessions po where po.commune_code = c.code));
$f$;

create or replace function public.roue_front_ouverte(p_uid uuid)
 returns boolean language plpgsql stable security definer set search_path to 'public'
as $function$
declare
  cfg jsonb := coalesce((select c.valeur::jsonb from config_jeu c where c.cle = 'roue_front'), '{}'::jsonb);
begin
  /* s2-98 */
  if p_uid is null or coalesce((cfg->>'ouvert')::int, 0) <> 1 then return false; end if;
  if coalesce((cfg->>'toujours')::int, 0) = 1 then return true; end if;   -- s3-18 : saison 3
  if reserve_accueil_bloque(p_uid) then return true; end if;
  /* pot vide : plus personne n'a de paquet à ouvrir, la roue est pour tous */
  return not exists (select 1 from communes c where not exists (select 1 from possessions po where po.commune_code = c.code));
end; $function$;

-- roue_front_etat et roue_front_tourner : les jetons de la roue quand jetons_propres = 1
do $do$
declare d text; a text; b text;
begin
  -- l'état
  d := pg_get_functiondef('public.roue_front_etat()'::regprocedure);
  if position('s3-18' in d) = 0 then
    a := 'select coalesce(j.jetons_gratuits, 0), coalesce(j.jetons_maj, now()),';
    b := $b$select coalesce(case when roue_cfg_int('jetons_propres') = 1 then j.roue_jetons else j.jetons_gratuits end, 0),   -- s3-18
         coalesce(case when roue_cfg_int('jetons_propres') = 1 then j.roue_jetons_maj else j.jetons_maj end, now()),$b$;
    if (length(d) - length(replace(d, a, ''))) / length(a) <> 1 then raise exception 's3-18 : roue_front_etat a changé (jetons)'; end if;
    d := replace(d, a, b);
    a := $a$'ouverte',  roue_front_ouverte(v_uid),$a$;
    b := $b$'ouverte',  roue_front_ouverte(v_uid),
    'avec_paquets', roue_avec_paquets(v_uid),             -- s3-18
    'propres',  roue_cfg_int('jetons_propres') = 1,$b$;
    if (length(d) - length(replace(d, a, ''))) / length(a) <> 1 then raise exception 's3-18 : roue_front_etat a changé (ouverte)'; end if;
    d := replace(d, a, b);
    execute d;
  end if;

  -- le tour
  d := pg_get_functiondef('public.roue_front_tourner()'::regprocedure);
  if position('s3-18' in d) = 0 then
    a := 'select jj.jetons_gratuits, jj.jetons_maj, jj.front_energie, jj.front_energie_maj,';
    b := $b$select case when roue_cfg_int('jetons_propres') = 1 then jj.roue_jetons else jj.jetons_gratuits end as jetons_gratuits,   -- s3-18
           case when roue_cfg_int('jetons_propres') = 1 then jj.roue_jetons_maj else jj.jetons_maj end as jetons_maj,
           jj.front_energie, jj.front_energie_maj,$b$;
    if (length(d) - length(replace(d, a, ''))) / length(a) <> 1 then raise exception 's3-18 : roue_front_tourner a changé (lecture)'; end if;
    d := replace(d, a, b);
    a := 'update joueurs set jetons_gratuits = v_jet - 1, jetons_maj = now() where id = v_uid;';
    b := $b$if roue_cfg_int('jetons_propres') = 1 then   -- s3-18 : les jetons de la roue
      update joueurs set roue_jetons = v_jet - 1, roue_jetons_maj = now() where id = v_uid;
    else
      update joueurs set jetons_gratuits = v_jet - 1, jetons_maj = now() where id = v_uid;
    end if;$b$;
    if (length(d) - length(replace(d, a, ''))) / length(a) <> 1 then raise exception 's3-18 : roue_front_tourner a changé (jetons)'; end if;
    d := replace(d, a, b);
    execute d;
  end if;
end $do$;

revoke all on function public.roue_cfg_int(text) from public, anon;
revoke all on function public.roue_avec_paquets(uuid) from public, anon;

select roue_cfg_int('toujours') as toujours, roue_cfg_int('jetons_propres') as jetons_propres,
       position('s3-18' in pg_get_functiondef('public.roue_front_etat()'::regprocedure)) > 0 as etat,
       position('s3-18' in pg_get_functiondef('public.roue_front_tourner()'::regprocedure)) > 0 as tourner,
       exists (select 1 from information_schema.columns where table_name = 'joueurs' and column_name = 'roue_jetons') as colonnes;
