-- s3-8 (10/11/2026) : le paquet Terra suisse (saison 3)
--
-- terra_ouvrir_paquet et terra_ouvrir_paquet_b prennent un pays : 'FR' (par défaut, comme avant) ou 'CH'.
--  - 'FR' : exactement le tirage d'avant (5 communes hors cantons, au hasard, la commune hantée d'Halloween d'abord).
--  - 'CH' : pour chaque carte, la rareté est tirée avec les chances d'un paquet France (part de chaque rareté
--    parmi les communes hors cantons), puis une commune suisse de cette rareté ; 5 communes différentes.
--  - 'CH' est refusé tant qu'aucune commune suisse n'est dans `communes` (elles entrent le jour J avec s3-5).
-- Mêmes jetons, même prix, même limite d'achats que le paquet France.
-- Un jeu qui n'envoie pas p_pays continue de marcher (paquet France).
--
-- Contrôle attendu : true | true | 2 | false | false
-- (nouvelle signature, variante brillantes, 2 fonctions, anon n'appelle pas, plus d'ancienne signature)

begin;

drop function if exists public.terra_ouvrir_paquet_b(boolean);
drop function if exists public.terra_ouvrir_paquet(boolean);

create function public.terra_ouvrir_paquet(p_paye boolean default false, p_pays text default 'FR')
 returns table(code text, nom text, departement text, tier text, population integer, nouvelle boolean, exemplaires integer,
               rang integer, palier_total integer, latitude double precision, longitude double precision, aurore boolean)
 language plpgsql
 security definer
 set search_path to 'public'
as $function$
declare
  v_uid uuid := auth.uid();
  j joueurs%rowtype;
  v numeric;
  v_jour date := (now() at time zone 'Europe/Paris')::date;
  v_achetes integer;
  v_pays text := upper(coalesce(p_pays, 'FR'));
  v_codes text[] := '{}';
  v_tiers text[];
  v_cumul numeric[];
  v_total numeric;
  v_x numeric;
  v_tier text;
  v_code text;
  i integer;
  k integer;
begin
  if v_uid is null then raise exception 'Non connecte'; end if;
  if not terra_ouverte() then raise exception 'Terra n''est pas encore ouvert'; end if;
  if v_pays not in ('FR', 'CH') then raise exception 'Paquet inconnu'; end if;
  -- s3-8 : le paquet suisse n'existe qu'une fois les communes suisses entrées (s3-5, le jour J)
  if v_pays = 'CH' and not exists (select 1 from communes c where est_canton(c.departement)) then
    raise exception 'Le paquet suisse arrive avec la saison 3';
  end if;
  -- verrou : deux ouvertures simultanees ne depensent pas le meme jeton
  select * into j from joueurs where id = v_uid for update;
  if not found then raise exception 'Joueur inconnu'; end if;

  if p_paye then
    v_achetes := case when j.paquets_achetes_date = v_jour then coalesce(j.paquets_achetes_jour, 0) else 0 end;
    if v_achetes >= 5 then raise exception 'Tu as deja achete 5 paquets aujourd''hui'; end if;
    if coalesce(j.solde, 0) < 200 then raise exception 'Solde insuffisant'; end if;
    perform set_config('terrafront.motif', 'terra_paquet', true);
    update joueurs set solde = solde - 200,
                       paquets_achetes_jour = v_achetes + 1,
                       paquets_achetes_date = v_jour
     where id = v_uid;
  else
    v := terra_jetons_lire(j.terra_jetons, j.terra_jetons_maj);
    if v < 1 then raise exception 'Pas de paquet gratuit disponible'; end if;
    update joueurs set terra_jetons = v - 1, terra_jetons_maj = now() where id = v_uid;
  end if;

  perform quete_noter(v_uid, 'terra_paquet', 1);

  if v_pays = 'CH' then
    -- les chances d'un paquet France : la part de chaque rareté parmi les communes hors cantons
    select array_agg(f.tier order by f.tier), array_agg(f.cumul order by f.tier), max(f.total)
      into v_tiers, v_cumul, v_total
      from (select g.tier, sum(g.n) over (order by g.tier) as cumul, sum(g.n) over () as total
              from (select c.tier, count(*)::numeric as n from communes c where not est_canton(c.departement) group by c.tier) g) f;
    for i in 1..5 loop
      v_x := random() * v_total;
      v_tier := v_tiers[array_length(v_tiers, 1)];
      for k in 1..array_length(v_tiers, 1) loop
        if v_x < v_cumul[k] then v_tier := v_tiers[k]; exit; end if;
      end loop;
      select c.code into v_code from communes c
       where est_canton(c.departement) and c.tier = v_tier and c.code <> all(v_codes)
       order by random() limit 1;
      if v_code is null then   -- rareté absente en Suisse (ou épuisée dans ce paquet) : une autre commune suisse
        select c.code into v_code from communes c
         where est_canton(c.departement) and c.code <> all(v_codes)
         order by random() limit 1;
      end if;
      if v_code is not null then v_codes := v_codes || v_code; end if;
    end loop;
  else
    select array_agg(x.code) into v_codes from (
      select y.code from (   -- s2-68 : Halloween, 1 paquet sur 3 contient une commune hantée
        select h.code, 0 as o from (select halloween_tirage_terra() as code) h where h.code is not null
        union all
        (select c.code, 1 from communes c where c.code <> all((select halloween_codes_actifs())::text[]) and not est_canton(c.departement) /* s3-3 */ order by random() limit 5)
      ) y order by y.o limit 5) x;
  end if;

  return query
  with tirage as (
    select u.code, aurore_tirage(u.code) as aur from unnest(v_codes) as u(code)
  ), avant as (
    select t.commune_code, t.exemplaires from terra_collection t
     where t.joueur_id = v_uid and t.commune_code in (select tirage.code from tirage)
  ), ajout as (
    insert into terra_collection as tc (joueur_id, commune_code, exemplaires, aurore, origine)
    select v_uid, tirage.code, 1, tirage.aur::integer, 'paquet' from tirage
    on conflict (joueur_id, commune_code) do update set exemplaires = tc.exemplaires + 1,
                                                        aurore = tc.aurore + excluded.aurore
    returning tc.commune_code, tc.exemplaires
  )
  select c.code::text, c.nom::text, c.departement::text, c.tier::text, c.population::integer,
         coalesce(av.exemplaires, 0) = 0, a.exemplaires::integer, c.rang::integer, c.palier_total::integer,
         c.latitude::double precision, c.longitude::double precision, ti.aur
    from ajout a
    join communes c on c.code = a.commune_code
    join tirage ti on ti.code = a.commune_code
    left join avant av on av.commune_code = a.commune_code;
end;
$function$;

create function public.terra_ouvrir_paquet_b(p_paye boolean default false, p_pays text default 'FR')
 returns jsonb
 language plpgsql
 security definer
 set search_path to 'public'
as $function$
declare
  v_uid uuid := auth.uid();
  r record;
  res jsonb := '[]'::jsonb;
begin
  for r in select * from terra_ouvrir_paquet(p_paye, p_pays) loop
    res := res || jsonb_build_array(to_jsonb(r) || jsonb_build_object('brillante', brillante_tirer(v_uid, r.code::text, 'paquet')));
  end loop;
  return res;
end $function$;

revoke all on function public.terra_ouvrir_paquet(boolean, text), public.terra_ouvrir_paquet_b(boolean, text) from public, anon;
grant execute on function public.terra_ouvrir_paquet(boolean, text), public.terra_ouvrir_paquet_b(boolean, text) to authenticated;

select to_regprocedure('public.terra_ouvrir_paquet(boolean, text)') is not null as nouvelle_signature,
       to_regprocedure('public.terra_ouvrir_paquet_b(boolean, text)') is not null as variante_brillantes,
       (select count(*) from pg_proc p join pg_namespace n on n.oid = p.pronamespace where n.nspname = 'public' and p.proname in ('terra_ouvrir_paquet', 'terra_ouvrir_paquet_b')) as fonctions,
       has_function_privilege('anon', 'public.terra_ouvrir_paquet(boolean, text)', 'execute') as anon_appelle,
       to_regprocedure('public.terra_ouvrir_paquet(boolean)') is not null as ancienne_signature;

commit;
