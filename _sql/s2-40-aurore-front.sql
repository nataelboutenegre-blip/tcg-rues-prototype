-- ===========================================================================
--  TerraFront — l'Aurore se tire aussi en Front (27 octobre 2026)
--  Décision de Nataël : en Front, une commune de la liste Aurore n'est plus
--  Aurore d'office. Comme en Terra, elle sort en Aurore 1 fois sur 3 au
--  tirage (aurore_tirage, la même fonction et le même réglage qu'en Terra).
--
--  - possessions.aurore : la marque. Elle suit la commune : conquête,
--    échange, achat ne font que changer le propriétaire (UPDATE), donc une
--    Aurore conquise reste Aurore. Une commune qui redevient libre perd sa
--    marque ; si elle ressort d'un paquet, on retire au sort.
--  - Les communes de la liste tenues aujourd'hui (51) gardent leur éclat :
--    marquées une seule fois, à l'ajout de la colonne.
--  - Le tirage : un déclencheur avant chaque nouvelle possession (le tirage
--    Front, draw_commune, est le seul endroit qui en crée en saison 2).
--    Aucune fonction existante n'est modifiée.
--  - front_aurores() : la liste des communes Aurore du Front, pour la carte,
--    le Combat et la collection.
--  Rejouable. Contrôle à la fin.
-- ===========================================================================
begin;

do $m$
begin
  if not exists (select 1 from information_schema.columns
                  where table_schema = 'public' and table_name = 'possessions' and column_name = 'aurore') then
    alter table public.possessions add column aurore boolean not null default false;
    -- une seule fois : les Aurore tenues aujourd'hui gardent leur éclat
    update public.possessions p set aurore = true
     where exists (select 1 from public.aurore_communes a where a.code = p.commune_code);
  end if;
end
$m$;

create or replace function public.possession_aurore_tirage()
 returns trigger language plpgsql security definer set search_path to 'public'
as $f$
begin
  new.aurore := coalesce(aurore_tirage(new.commune_code), false);
  return new;
end;
$f$;
revoke all on function public.possession_aurore_tirage() from public, anon, authenticated;
drop trigger if exists trg_aurore_tirage on public.possessions;
create trigger trg_aurore_tirage before insert on public.possessions
  for each row execute function public.possession_aurore_tirage();

create or replace function public.front_aurores()
 returns table(commune_code text) language sql stable security definer set search_path to 'public'
as $f$
  select p.commune_code from possessions p where p.aurore;
$f$;
revoke all on function public.front_aurores() from public, anon;
grant execute on function public.front_aurores() to authenticated;

commit;

-- Contrôle : colonne_ok, declencheur_ok, joueurs_ok, anon_ferme = true ; aurore_tenues ≈ 51 ; chance = 0.33…
select
  exists (select 1 from information_schema.columns where table_schema = 'public' and table_name = 'possessions' and column_name = 'aurore') as colonne_ok,
  exists (select 1 from pg_trigger where tgname = 'trg_aurore_tirage')                                         as declencheur_ok,
  has_function_privilege('authenticated', 'public.front_aurores()', 'execute')                                 as joueurs_ok,
  not has_function_privilege('anon', 'public.front_aurores()', 'execute')                                      as anon_ferme,
  (select count(*) from public.possessions where aurore)                                                      as aurore_tenues,
  public.aurore_chance()                                                                                       as chance;
