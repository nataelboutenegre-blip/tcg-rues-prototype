-- ===========================================================================
--  s2-24-vitrine-front.sql — la vitrine accepte les cartes du Front. Rejouable.
--
--  Deux vitrines par joueur, 20 places chacune : Terra et Front.
--  - terra_vitrine_definir(codes)       : la vitrine Terra (inchangée).
--  - terra_vitrine_definir_front(codes) : la vitrine Front.
--  - Une carte du Front ne reste visible que tant que le joueur la tient :
--    si on la lui prend, elle disparaît d'elle-même de sa vitrine Front.
--  - L'Aurore du Front suit la liste aurore_communes, comme dans le jeu.
--  - terra_vitrine(joueur) renvoie les deux, avec la colonne « source ».
--  Contrôle attendu : true | true | false | false | 20
-- ===========================================================================

begin;

alter table public.terra_vitrine add column if not exists source text not null default 'terra';

-- la clé : une place par vitrine (Terra et Front ont chacune leurs places)
alter table public.terra_vitrine drop constraint if exists terra_vitrine_pkey;
alter table public.terra_vitrine add constraint terra_vitrine_pkey primary key (joueur_id, source, place);

-- les anciennes contraintes (place 1..5, une commune une fois) cèdent la place
do $d$
declare r record;
begin
  for r in select conname from pg_constraint
            where conrelid = 'public.terra_vitrine'::regclass
              and contype in ('c', 'u')
              and conname not in ('terra_vitrine_place_20', 'terra_vitrine_source_ok', 'terra_vitrine_carte_unique', 'terra_vitrine_pkey')
  loop
    execute format('alter table public.terra_vitrine drop constraint %I', r.conname);
  end loop;
end $d$;

do $d$
begin
  if not exists (select 1 from pg_constraint where conname = 'terra_vitrine_place_20') then
    alter table public.terra_vitrine add constraint terra_vitrine_place_20 check (place between 1 and 20);
  end if;
  if not exists (select 1 from pg_constraint where conname = 'terra_vitrine_source_ok') then
    alter table public.terra_vitrine add constraint terra_vitrine_source_ok check (source in ('terra', 'front'));
  end if;
  if not exists (select 1 from pg_constraint where conname = 'terra_vitrine_carte_unique') then
    alter table public.terra_vitrine add constraint terra_vitrine_carte_unique unique (joueur_id, commune_code, source);
  end if;
end $d$;

-- Ma vitrine, dans l'ordre voulu. Tableau vide = vitrine vidée.
create or replace function public.terra_vitrine_definir(p_codes text[])
 returns integer
 language plpgsql
 security definer
 set search_path to 'public'
as $f$
declare v_codes text[] := coalesce(p_codes, '{}');
begin
  if auth.uid() is null then raise exception 'Non connecte'; end if;
  if not terra_ouverte() then raise exception 'Terra n''est pas encore ouvert'; end if;
  if cardinality(v_codes) > 20 then raise exception 'La vitrine montre 20 cartes au plus'; end if;
  if (select count(distinct x) from unnest(v_codes) x) <> cardinality(v_codes) then
    raise exception 'Une carte est en double dans la vitrine';
  end if;
  if exists (select 1 from unnest(v_codes) x
              where not exists (select 1 from terra_collection t
                                 where t.joueur_id = auth.uid() and t.commune_code = x and t.exemplaires > 0)) then
    raise exception 'Tu ne possèdes pas une de ces cartes';
  end if;
  delete from terra_vitrine where joueur_id = auth.uid() and source = 'terra';
  insert into terra_vitrine(joueur_id, place, commune_code, source)
  select auth.uid(), o.n, o.x, 'terra' from unnest(v_codes) with ordinality as o(x, n);
  return cardinality(v_codes);
end;
$f$;

-- Ma vitrine Front : les communes que je tiens en ce moment.
create or replace function public.terra_vitrine_definir_front(p_codes text[])
 returns integer
 language plpgsql
 security definer
 set search_path to 'public'
as $f$
declare v_codes text[] := coalesce(p_codes, '{}');
begin
  if auth.uid() is null then raise exception 'Non connecte'; end if;
  if cardinality(v_codes) > 20 then raise exception 'La vitrine montre 20 cartes au plus'; end if;
  if (select count(distinct x) from unnest(v_codes) x) <> cardinality(v_codes) then
    raise exception 'Une carte est en double dans la vitrine';
  end if;
  if exists (select 1 from unnest(v_codes) x
              where not exists (select 1 from possessions p
                                 where p.joueur_id = auth.uid() and p.commune_code = x)) then
    raise exception 'Tu ne possèdes pas une de ces communes';
  end if;
  delete from terra_vitrine where joueur_id = auth.uid() and source = 'front';
  insert into terra_vitrine(joueur_id, place, commune_code, source)
  select auth.uid(), o.n, o.x, 'front' from unnest(v_codes) with ordinality as o(x, n);
  return cardinality(v_codes);
end;
$f$;

-- Les deux vitrines d'un joueur, pour sa fiche de profil. La colonne « source » est
-- nouvelle : il faut supprimer l'ancienne fonction pour changer son retour.
drop function if exists public.terra_vitrine(uuid);
create function public.terra_vitrine(p_joueur uuid)
 returns table(place integer, code text, nom text, departement text, tier text, population integer,
               rang integer, palier_total integer, aurore boolean, source text)
 language plpgsql
 stable security definer
 set search_path to 'public'
as $f$
begin
  if auth.uid() is null then raise exception 'Non connecte'; end if;
  return query
  select v.place::integer, c.code::text, c.nom::text, c.departement::text, c.tier::text,
         c.population::integer, c.rang::integer, c.palier_total::integer,
         case when v.source = 'front' then exists (select 1 from aurore_communes a where a.code = v.commune_code)
              else coalesce(t.aurore, 0) > 0 end,
         v.source::text
    from terra_vitrine v
    join communes c on c.code = v.commune_code
    left join possessions p
           on v.source = 'front' and p.joueur_id = v.joueur_id and p.commune_code = v.commune_code
    left join terra_collection t
           on v.source = 'terra' and t.joueur_id = v.joueur_id and t.commune_code = v.commune_code and t.exemplaires > 0
   where v.joueur_id = p_joueur
     and (p.commune_code is not null or t.commune_code is not null)
   order by v.source desc, v.place;
end;
$f$;

revoke all on function public.terra_vitrine_definir(text[]) from public, anon;
revoke all on function public.terra_vitrine(uuid)           from public, anon;
revoke all on function public.terra_vitrine_definir_front(text[]) from public, anon;
grant execute on function public.terra_vitrine_definir_front(text[]) to authenticated;
grant execute on function public.terra_vitrine_definir(text[]) to authenticated;
grant execute on function public.terra_vitrine(uuid)           to authenticated;

commit;

-- contrôle : true | true | false | false | 20
select (select count(*) from information_schema.columns
         where table_schema = 'public' and table_name = 'terra_vitrine' and column_name = 'source') = 1 as colonne_ok,
       has_function_privilege('authenticated', 'public.terra_vitrine(uuid)', 'execute')  as lecture_ok,
       has_function_privilege('anon', 'public.terra_vitrine_definir(text[])', 'execute') as anon_doit_etre_false,
       has_function_privilege('anon', 'public.terra_vitrine_definir_front(text[])', 'execute') as anon_front_false,
       (select 20 from pg_constraint where conname = 'terra_vitrine_place_20')           as places;
