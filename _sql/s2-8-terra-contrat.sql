-- ===========================================================================
--  TerraFront — saison 2, Terra : le contrat sur les doublons (9 octobre 2026)
--
--  SANS EFFET EN SAISON 1 : les deux fonctions refusent tant que
--  terra_ouverte() est faux. Le contrat de la saison 1 (signer_contrat, sur
--  les possessions) n'est pas touché. À lancer APRÈS s2-5-terra-jeu.sql.
--
--  Règles :
--   - 10 doublons d'un palier -> 1 commune du palier au-dessus
--     (commun -> peu commun, peu commun -> rare) ;
--   - seuls les doublons partent : on garde toujours au moins un exemplaire
--     de chaque commune (et les exemplaires Aurore ne partent jamais) ;
--   - une même commune peut fournir plusieurs doublons du lot ;
--   - la commune reçue est tirée parmi celles du palier visé que le joueur
--     n'a pas encore ; s'il les a toutes, parmi tout le palier (doublon).
--
--  Fonctions pour le jeu (authenticated) :
--    terra_contrat_candidates(tier)    les doublons utilisables, par commune
--    terra_signer_contrat(codes[], vers)  codes : 10 entrées, répétitions permises
--  Rejouable. Finit par un contrôle.
-- ===========================================================================

create or replace function public.terra_contrat_candidates(p_tier text)
 returns table(commune_code text, nom text, departement text, population integer, dispo integer)
 language plpgsql
 stable security definer
 set search_path to 'public'
as $f$
begin
  if auth.uid() is null then raise exception 'Non connecte'; end if;
  if not terra_ouverte() then raise exception 'Terra n''est pas encore ouvert'; end if;
  return query
  select t.commune_code::text, c.nom::text, c.departement::text, c.population,
         (t.exemplaires - greatest(1, t.aurore))::integer
    from terra_collection t
    join communes c on c.code = t.commune_code
   where t.joueur_id = auth.uid()
     and c.tier = p_tier
     and t.exemplaires - greatest(1, t.aurore) > 0
   order by t.exemplaires - greatest(1, t.aurore) desc, c.population asc nulls first, t.commune_code;
end;
$f$;

create or replace function public.terra_signer_contrat(p_codes text[], p_vers text)
 returns jsonb
 language plpgsql
 security definer
 set search_path to 'public'
as $f$
declare
  v_uid uuid := auth.uid();
  v_de text;
  v_n integer := 10;
  r record;
  v_code text;
  v_nouvelle boolean := true;
  v_ex integer;
  v_carte jsonb;
  v_decor jsonb;
begin
  if v_uid is null then raise exception 'Non connecte'; end if;
  if not terra_ouverte() then raise exception 'Terra n''est pas encore ouvert'; end if;

  v_de := case p_vers when 'peucommun' then 'commun'
                      when 'rare'      then 'peucommun' end;
  if v_de is null then
    raise exception 'Seuls les contrats vers peu commun et rare existent';
  end if;
  if p_codes is null or array_length(p_codes, 1) is distinct from v_n then
    raise exception 'Il faut exactement % doublons', v_n;
  end if;

  -- verrou sur les lignes concernees, puis verification commune par commune
  perform 1 from terra_collection t
   where t.joueur_id = v_uid and t.commune_code = any(p_codes)
   for update;

  for r in
    select x.code, count(*)::integer as n
      from unnest(p_codes) as x(code)
     group by x.code
  loop
    if not exists (
      select 1 from terra_collection t join communes c on c.code = t.commune_code
       where t.joueur_id = v_uid and t.commune_code = r.code
         and c.tier = v_de
         and t.exemplaires - greatest(1, t.aurore) >= r.n
    ) then
      raise exception 'Un des doublons ne convient plus : vérifie que tu as encore assez d''exemplaires de chaque commune, du bon palier';
    end if;
  end loop;

  -- le tirage, avant toute modification : d'abord une commune que le joueur
  -- n'a pas encore
  select c.code into v_code
    from communes c
   where c.tier = p_vers
     and not exists (select 1 from terra_collection t
                      where t.joueur_id = v_uid and t.commune_code = c.code and t.exemplaires > 0)
   order by random()
   limit 1;
  if v_code is null then
    v_nouvelle := false;
    select c.code into v_code from communes c where c.tier = p_vers order by random() limit 1;
  end if;
  if v_code is null then raise exception 'Aucune commune % n''existe', p_vers; end if;

  -- les dix doublons partent
  update terra_collection t
     set exemplaires = t.exemplaires - x.n
    from (select code, count(*)::integer as n from unnest(p_codes) as u(code) group by code) x
   where t.joueur_id = v_uid and t.commune_code = x.code;

  -- celle-ci arrive
  insert into terra_collection as tc (joueur_id, commune_code, exemplaires, origine)
  values (v_uid, v_code, 1, 'contrat')
  on conflict (joueur_id, commune_code) do update set exemplaires = tc.exemplaires + 1
  returning tc.exemplaires into v_ex;

  select to_jsonb(t) into v_carte from (
    select c.code, c.nom, c.departement, c.population,
           c.latitude, c.longitude, c.tier, c.rang, c.palier_total
      from communes c where c.code = v_code
  ) t;

  -- le decor du defile : de vraies communes du palier vise
  select coalesce(jsonb_agg(to_jsonb(d)), '[]'::jsonb) into v_decor from (
    select c.code, c.nom, c.departement, c.population
      from communes c where c.tier = p_vers and c.code <> v_code
     order by random() limit 45
  ) d;

  return v_carte || jsonb_build_object('sacrifiees', v_n, 'depuis', v_de,
    'nouvelle', v_nouvelle, 'exemplaires', v_ex, 'decor', v_decor);
end;
$f$;

revoke all on function public.terra_contrat_candidates(text) from public, anon;
revoke all on function public.terra_signer_contrat(text[], text) from public, anon;
grant execute on function public.terra_contrat_candidates(text) to authenticated;
grant execute on function public.terra_signer_contrat(text[], text) to authenticated;

-- Contrôle ---------------------------------------------------------------------------------
select terra_ouverte() as terra_ouverte_doit_etre_false,
       (select count(*) from pg_proc where proname in ('terra_contrat_candidates', 'terra_signer_contrat')) as fonctions_doit_etre_2,
       has_function_privilege('anon', 'public.terra_signer_contrat(text[],text)', 'execute') as anon_doit_etre_false;
