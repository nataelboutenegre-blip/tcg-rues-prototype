-- ===========================================================================
--  TerraFront — s2-87 : la course à la commune + le journal des rounds
--  (3/11/2026, avec patch326). Idée d'Oshannir, validée par Nataël le 3/11
--  (« ok pour effacer les sièges et prévenir les joueurs, ok pour les lectures »).
--
--  1. Quand un joueur PREND une commune (une ligne dans front_prises, écrite
--     par front_gain_conquete à chaque conquête), les sièges des AUTRES
--     attaquants sur cette commune sont effacés : ils repartent de zéro contre
--     le nouveau propriétaire. Avant : ils gardaient leur série et, passé les
--     3 h d'immunité, une seule victoire pouvait suffire à reprendre la commune.
--     Chaque siège effacé (1 victoire ou plus) est noté dans sieges_effaces ;
--     mes_sieges_effaces() le donne à la cloche (7 derniers jours).
--     Un déclencheur sur front_prises : aucune fonction de combat n'est touchée.
--  2. front_rounds : une ligne par round d'attaque (attaquant, commune, rareté,
--     gagné ou non, série après le round). Un déclencheur sur sieges, qui est
--     écrit à chaque round (dernier_round). Sert à lire combien d'attaques
--     visent les légendaires (lecture-attaques-rarete.sql). Gardé 30 jours.
--
--  Rejouable. Finit par un contrôle (une ligne) :
--  true | true | true | true | (conquêtes ces 7 derniers jours, plus de 0 attendu)
-- ===========================================================================
begin;

-- ---------- 1. la course à la commune ----------
create table if not exists public.sieges_effaces(
  id           bigserial primary key,
  attaquant_id uuid not null,
  commune_code text not null,
  par          uuid,
  victoires    integer not null default 0,
  le           timestamptz not null default now()
);
create index if not exists sieges_effaces_attaquant on public.sieges_effaces(attaquant_id, le desc);
create index if not exists sieges_effaces_le on public.sieges_effaces(le);
alter table public.sieges_effaces enable row level security;
revoke all on public.sieges_effaces from public, anon, authenticated;

create or replace function public.siege_course_effacer()
 returns trigger language plpgsql security definer set search_path to 'public' as $f$
begin
  insert into sieges_effaces(attaquant_id, commune_code, par, victoires)
  select s.attacker_id, s.commune_code, new.attaquant, s.victoires_consecutives
    from sieges s
   where s.commune_code = new.commune_code
     and s.attacker_id is distinct from new.attaquant
     and coalesce(s.victoires_consecutives, 0) > 0;
  delete from sieges where commune_code = new.commune_code and attacker_id is distinct from new.attaquant;
  delete from sieges_effaces where le < now() - interval '30 days';
  return null;
end; $f$;
revoke all on function public.siege_course_effacer() from public, anon, authenticated;
drop trigger if exists siege_course_effacer on public.front_prises;
create trigger siege_course_effacer after insert on public.front_prises
  for each row execute function public.siege_course_effacer();

create or replace function public.mes_sieges_effaces()
 returns table(commune_code text, commune_nom text, par_pseudo text, victoires integer, le timestamptz)
 language sql stable security definer set search_path to 'public' as $f$
  select e.commune_code, c.nom::text, j.pseudo::text, e.victoires, e.le
    from sieges_effaces e
    left join communes c on c.code = e.commune_code
    left join joueurs j on j.id = e.par
   where auth.uid() is not null and e.attaquant_id = auth.uid()
     and e.le > now() - interval '7 days'
   order by e.le desc
   limit 30;
$f$;
revoke all on function public.mes_sieges_effaces() from public, anon;
grant execute on function public.mes_sieges_effaces() to authenticated;

-- ---------- 2. le journal des rounds ----------
create table if not exists public.front_rounds(
  id           bigserial primary key,
  attaquant_id uuid not null,
  commune_code text not null,
  tier         text,
  gagne        boolean not null,
  victoires    integer,
  le           timestamptz not null default now()
);
create index if not exists front_rounds_le on public.front_rounds(le);
alter table public.front_rounds enable row level security;
revoke all on public.front_rounds from public, anon, authenticated;

create or replace function public.front_round_noter()
 returns trigger language plpgsql security definer set search_path to 'public' as $f$
begin
  if new.dernier_round is null then return null; end if;
  if tg_op = 'UPDATE' and new.dernier_round is not distinct from old.dernier_round then return null; end if;
  insert into front_rounds(attaquant_id, commune_code, tier, gagne, victoires)
  values (new.attacker_id, new.commune_code,
          (select c.tier from communes c where c.code = new.commune_code),
          coalesce(new.victoires_consecutives, 0) > (case when tg_op = 'UPDATE' then coalesce(old.victoires_consecutives, 0) else 0 end),
          new.victoires_consecutives);
  -- ménage, de temps en temps
  if random() < 0.002 then delete from front_rounds where le < now() - interval '30 days'; end if;
  return null;
end; $f$;
revoke all on function public.front_round_noter() from public, anon, authenticated;
drop trigger if exists front_round_noter on public.sieges;
create trigger front_round_noter after insert or update of dernier_round on public.sieges
  for each row execute function public.front_round_noter();

commit;

-- Contrôle : true | true | true | true | (conquêtes ces 7 derniers jours)
select exists (select 1 from pg_trigger where tgname = 'siege_course_effacer' and not tgisinternal)          as course_ok,
       has_function_privilege('authenticated', 'public.mes_sieges_effaces()', 'execute')                       as cloche_ok,
       exists (select 1 from pg_trigger where tgname = 'front_round_noter' and not tgisinternal)              as rounds_ok,
       to_regclass('public.front_rounds') is not null and to_regclass('public.sieges_effaces') is not null    as tables_ok,
       (select count(*) from public.front_prises where le > now() - interval '7 days')                         as conquetes_7j;
