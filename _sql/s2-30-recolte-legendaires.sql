-- ===========================================================================
--  s2-30 — Les légendaires rapportent de l'énergie (Front, saison 2)
--  Décision de Nataël (26 octobre) : seulement les légendaires, +2 énergie par
--  légendaire tenue depuis au moins 24 h, 10 au plus par jour, à récolter à la
--  main une fois par jour (jour de Paris, comme les quêtes). Pas de cumul d'un
--  jour sur l'autre. L'énergie récoltée peut dépasser 40, jusqu'à 60 (comme
--  les quêtes).
--  Rejouable. À passer AVANT de pousser le patch211.
-- ===========================================================================
begin;

create table if not exists public.front_recoltes(
  joueur_id   uuid not null references public.joueurs(id) on delete cascade,
  jour        date not null,
  legendaires integer not null,
  energie     integer not null,
  le          timestamptz not null default now(),
  primary key (joueur_id, jour)
);
alter table public.front_recoltes enable row level security;
revoke all on public.front_recoltes from public, anon, authenticated;

-- les légendaires d'un joueur qui comptent (tenues depuis 24 h)
create or replace function public.front_recolte_pretes(p_uid uuid)
 returns integer language sql stable security definer set search_path to 'public'
as $f$
  select count(*)::integer
    from possessions p join communes c on c.code = p.commune_code
   where p.joueur_id = p_uid and c.tier = 'legendaire'
     and coalesce(p.acquired_at, now()) <= now() - interval '24 hours';
$f$;

create or replace function public.front_recolte_etat()
 returns table(pretes integer, energie integer, recoltee boolean, recoltee_energie integer, bientot jsonb)
 language plpgsql stable security definer set search_path to 'public'
as $f$
declare v_uid uuid := auth.uid(); v_n integer; r record;
begin
  if v_uid is null then raise exception 'Non connecte'; end if;
  if not saison2_active() then return; end if;
  v_n := front_recolte_pretes(v_uid);
  select * into r from front_recoltes f where f.joueur_id = v_uid and f.jour = quete_jour();
  return query select v_n, least(10, 2 * v_n), r.joueur_id is not null, coalesce(r.energie, 0),
    coalesce((select jsonb_agg(jsonb_build_object('nom', x.nom, 'heures', x.h) order by x.h)
                from (select c.nom, greatest(1, ceil(extract(epoch from (p.acquired_at + interval '24 hours' - now())) / 3600))::integer h
                        from possessions p join communes c on c.code = p.commune_code
                       where p.joueur_id = v_uid and c.tier = 'legendaire'
                         and p.acquired_at > now() - interval '24 hours'
                       order by p.acquired_at limit 3) x), '[]'::jsonb);
end;
$f$;

create or replace function public.front_recolter()
 returns table(message text, energie integer)
 language plpgsql security definer set search_path to 'public'
as $f$
declare v_uid uuid := auth.uid(); v_jour date := quete_jour(); v_n integer; v_e integer; v numeric; v_reel integer;
begin
  if v_uid is null then raise exception 'Non connecte'; end if;
  if not saison2_active() then raise exception 'La récolte arrive avec la saison 2'; end if;
  perform 1 from joueurs where id = v_uid for update;
  if exists (select 1 from front_recoltes f where f.joueur_id = v_uid and f.jour = v_jour) then
    raise exception 'Récolte déjà faite aujourd''hui, reviens demain';
  end if;
  v_n := front_recolte_pretes(v_uid);
  if v_n = 0 then raise exception 'Aucune légendaire tenue depuis 24 h'; end if;
  v_e := least(10, 2 * v_n);
  select front_energie_lire(j.front_energie, j.front_energie_maj) into v from joueurs j where j.id = v_uid;
  v_reel := greatest(0, least(60, floor(v + v_e)) - floor(v))::integer;
  update joueurs set front_energie = least(60, v + v_e), front_energie_maj = now() where id = v_uid;
  insert into front_recoltes(joueur_id, jour, legendaires, energie) values (v_uid, v_jour, v_n, v_reel);
  return query select
    (case when v_reel < v_e then '+' || v_reel || ' énergie (réserve au maximum, 60)'
          else '+' || v_e || ' énergie grâce à ' || v_n || ' légendaire' || case when v_n > 1 then 's' else '' end end)::text,
    v_reel;
end;
$f$;

revoke all on function public.front_recolte_pretes(uuid) from public, anon, authenticated;
revoke all on function public.front_recolte_etat() from public, anon;
revoke all on function public.front_recolter() from public, anon;
grant execute on function public.front_recolte_etat() to authenticated;
grant execute on function public.front_recolter() to authenticated;

commit;

-- contrôle : true | true | false | <nombre de joueurs qui pourraient récolter aujourd'hui>
select to_regclass('public.front_recoltes') is not null as table_ok,
       has_function_privilege('authenticated', 'public.front_recolter()', 'execute') as recolter_ok,
       has_function_privilege('anon', 'public.front_recolter()', 'execute') as anon_doit_etre_false,
       (select count(distinct p.joueur_id) from possessions p join communes c on c.code = p.commune_code
         where c.tier = 'legendaire' and p.acquired_at <= now() - interval '24 hours') as joueurs_eligibles;
