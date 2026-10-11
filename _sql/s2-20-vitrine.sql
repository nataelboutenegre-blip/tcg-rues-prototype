-- ===========================================================================
--  s2-20-vitrine.sql — la vitrine de profil (saison 2). Rejouable.
--
--  Chaque joueur expose jusqu'à 5 cartes de sa collection Terra sur sa
--  fiche de profil, visibles par tout le monde.
--  - L'ordre compte : la place 1 est la première montrée.
--  - Une carte vendue, échangée ou passée en contrat disparaît d'elle-même
--    de la vitrine (la lecture ne garde que les cartes encore possédées).
--  - Une carte montrée n'est pas bloquée : on peut toujours la vendre.
--  - La carte s'affiche en Aurore si le joueur en possède une Aurore.
--  Contrôle attendu : true | true | false
-- ===========================================================================

begin;

create table if not exists public.terra_vitrine(
  joueur_id     uuid not null references public.joueurs(id) on delete cascade,
  place         smallint not null check (place between 1 and 5),
  commune_code  text not null references public.communes(code),
  primary key (joueur_id, place),
  unique (joueur_id, commune_code)
);
alter table public.terra_vitrine enable row level security;
revoke all on public.terra_vitrine from public, anon, authenticated;

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
  if cardinality(v_codes) > 5 then raise exception 'La vitrine montre 5 cartes au plus'; end if;
  if (select count(distinct x) from unnest(v_codes) x) <> cardinality(v_codes) then
    raise exception 'Une carte est en double dans la vitrine';
  end if;
  if exists (select 1 from unnest(v_codes) x
              where not exists (select 1 from terra_collection t
                                 where t.joueur_id = auth.uid() and t.commune_code = x and t.exemplaires > 0)) then
    raise exception 'Tu ne possèdes pas une de ces cartes';
  end if;
  delete from terra_vitrine where joueur_id = auth.uid();
  insert into terra_vitrine(joueur_id, place, commune_code)
  select auth.uid(), o.n, o.x from unnest(v_codes) with ordinality as o(x, n);
  return cardinality(v_codes);
end;
$f$;

-- La vitrine d'un joueur, pour sa fiche de profil.
create or replace function public.terra_vitrine(p_joueur uuid)
 returns table(place integer, code text, nom text, departement text, tier text, population integer,
               rang integer, palier_total integer, aurore boolean)
 language plpgsql
 stable security definer
 set search_path to 'public'
as $f$
begin
  if auth.uid() is null then raise exception 'Non connecte'; end if;
  return query
  select v.place::integer, c.code::text, c.nom::text, c.departement::text, c.tier::text,
         c.population::integer, c.rang::integer, c.palier_total::integer, t.aurore > 0
    from terra_vitrine v
    join terra_collection t on t.joueur_id = v.joueur_id and t.commune_code = v.commune_code and t.exemplaires > 0
    join communes c on c.code = v.commune_code
   where v.joueur_id = p_joueur
   order by v.place;
end;
$f$;

revoke all on function public.terra_vitrine_definir(text[]) from public, anon;
revoke all on function public.terra_vitrine(uuid)           from public, anon;
grant execute on function public.terra_vitrine_definir(text[]) to authenticated;
grant execute on function public.terra_vitrine(uuid)           to authenticated;

commit;

-- contrôle : true | true | false
select to_regclass('public.terra_vitrine') is not null                                  as table_ok,
       has_function_privilege('authenticated', 'public.terra_vitrine(uuid)', 'execute')  as lecture_ok,
       has_function_privilege('anon', 'public.terra_vitrine_definir(text[])', 'execute') as anon_doit_etre_false;
