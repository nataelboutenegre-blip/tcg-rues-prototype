-- ===========================================================================
--  TerraFront — Outre-mer v2 : le FRONT s'ouvre à l'outre-mer
--  + les paquets Front donnent de nouveau des ÉPIQUES (27 octobre 2026)
--
--  Décisions de Nataël (27/10) :
--   - chaque carte d'un paquet Front a une petite chance FIXE d'être une
--     commune d'outre-mer libre : 1,5 % par défaut, réglable sans patch
--     (config_jeu, clé 'outremer', champ 'chance_front') ;
--   - les DOM rapportent les points de leur rareté, SANS bonus de département
--     ni de région (déjà le cas depuis s2-34 : front_territoires ne compte que
--     la métropole) ;
--   - les paquets Front ne donnaient jamais d'épique (« épique » absent de
--     draw_commune et de poids_tirage depuis la création du palier) : corrigé,
--     poids 1,0 par commune libre comme la légendaire (~2,7 % par carte avec
--     le stock actuel : 946 épiques libres).
--
--  4 fonctions, modifiées à partir de leur définition EN BASE, chaque
--  remplacement contrôlé à 1 occurrence. UNE transaction : tout ou rien.
--  Rejouable. Finit par un contrôle.
--
--  À passer AVANT le push du patch220 (sinon un DOM tiré dans le Front
--  n'aurait pas encore sa carte Outre-mer sur le site — rien de cassé, mais
--  invisible sur la carte).
-- ===========================================================================
begin;

create or replace function pg_temp.remp(p_def text, p_avant text, p_apres text, p_etq text)
returns text language plpgsql as $$
declare n int;
begin
  n := (length(p_def) - length(replace(p_def, p_avant, ''))) / nullif(length(p_avant), 0);
  if n is distinct from 1 then
    raise exception 'Repère « % » trouvé % fois (attendu 1) : rien changé', p_etq, n;
  end if;
  return replace(p_def, p_avant, p_apres);
end $$;

-- 0. la chance de tirer un DOM dans un paquet Front (réglable sans patch)
create or replace function public.outremer_chance_front()
returns numeric language sql stable security definer set search_path to 'public' as $$
  select coalesce(
    (select (c.valeur::jsonb ->> 'chance_front')::numeric from config_jeu c where c.cle = 'outremer'),
    0.015);
$$;
revoke all on function public.outremer_chance_front() from public, anon, authenticated;

do $do$
declare d text;
begin
  -- 1. poids_tirage : un 5e palier, l'épique (même poids par commune que la légendaire)
  d := pg_get_functiondef('public.poids_tirage()'::regprocedure);
  if d not like '%''epique''%' then
    d := pg_temp.remp(d,
      $x$count(*) filter (where c.tier = 'rare')$x$,
      $x$count(*) filter (where c.tier = 'epique') * 1.0,   -- s2-37 : l'épique entre au tirage Front
    count(*) filter (where c.tier = 'rare')$x$,
      'poids_tirage');
    execute d;
  end if;

  -- 2. taux_actuels : les chances affichées suivent les 5 paliers
  d := pg_get_functiondef('public.taux_actuels()'::regprocedure);
  if d not like '%''legendaire'',''epique''%' then
    d := pg_temp.remp(d,
      $x$unnest(array['legendaire','rare','peucommun','commun'], p.w)$x$,
      $x$unnest(array['legendaire','epique','rare','peucommun','commun'], p.w)$x$,
      'taux_actuels');
    execute d;
  end if;

  -- 3. draw_commune : 5 paliers + la petite chance d'un DOM libre
  d := pg_get_functiondef('public.draw_commune(text)'::regprocedure);
  if d not like '%outremer_chance_front%' then
    d := pg_temp.remp(d,
      $x$v_tiers text[] := array['legendaire','rare','peucommun','commun'];$x$,
      $x$v_tiers text[] := array['legendaire','epique','rare','peucommun','commun'];$x$,
      'draw_commune (paliers)');
    d := pg_temp.remp(d,
      $x$v_total := v_poids[1] + v_poids[2] + v_poids[3] + v_poids[4];$x$,
      $x$v_total := v_poids[1] + v_poids[2] + v_poids[3] + v_poids[4] + coalesce(v_poids[5], 0);$x$,
      'draw_commune (total)');
    d := pg_temp.remp(d,
      $x$v_start_tier := 4;$x$,
      $x$v_start_tier := 5;$x$,
      'draw_commune (palier par défaut)');
    d := pg_temp.remp(d,
      $x$for v_i in 1..4 loop$x$,
      $x$for v_i in 1..5 loop$x$,
      'draw_commune (choix du palier)');
    d := pg_temp.remp(d,
      $x$v_code := null;
    for v_i in v_start_tier..4 loop$x$,
      $x$v_code := null;
    -- s2-37 : une petite chance fixe que la carte soit une commune d'outre-mer libre
    if random() < outremer_chance_front() then
      select c.code into v_code
        from communes c
        left join possessions p on p.commune_code = c.code
       where length(c.departement) <> 2 and p.commune_code is null
       order by random()
       limit 1;
    end if;
    for v_i in v_start_tier..5 loop
      exit when v_code is not null;   -- s2-37 : un DOM vient d'être tiré$x$,
      'draw_commune (outre-mer)');
    execute d;
  end if;
end $do$;

commit;

-- Contrôle : tout doit être true.
select
  pg_get_functiondef('public.poids_tirage()'::regprocedure)       like '%''epique''%'                  as poids_epique,
  pg_get_functiondef('public.taux_actuels()'::regprocedure)       like '%''legendaire'',''epique''%'   as taux_epique,
  pg_get_functiondef('public.draw_commune(text)'::regprocedure)   like '%''legendaire'',''epique''%'   as tirage_epique,
  pg_get_functiondef('public.draw_commune(text)'::regprocedure)   like '%outremer_chance_front%'      as tirage_outremer,
  pg_get_functiondef('public.draw_commune(text)'::regprocedure)   ~ 'length\((c\.)?departement\) = 2' as metropole_toujours_filtree,
  public.outremer_chance_front() = 0.015                                                               as chance_1_5_pct,
  array_length(public.poids_tirage(), 1) = 5                                                           as cinq_paliers;
