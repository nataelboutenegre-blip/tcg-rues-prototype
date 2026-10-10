-- ===========================================================================
--  TerraFront — départements à défendre en priorité (10 octobre 2026)
--
--  Chaque joueur choisit jusqu'à 5 départements : leurs communes attaquées
--  passent en tête du volet Défendre, avec un filtre « Mes départements ».
--  Réglage du compte (tous les appareils). Rien d'autre ne change : aucune
--  règle de combat n'est touchée.
--  Rejouable. Finit par un contrôle.
-- ===========================================================================

create table if not exists public.defense_departements(
  joueur_id   uuid not null references public.joueurs(id) on delete cascade,
  departement text not null,
  ajoute_le   timestamptz not null default now(),
  primary key (joueur_id, departement)
);
alter table public.defense_departements enable row level security;
revoke all on public.defense_departements from public, anon, authenticated;

create or replace function public.mes_departements_defense()
 returns table(departement text)
 language plpgsql stable security definer set search_path to 'public'
as $f$
begin
  if auth.uid() is null then raise exception 'Non connecte'; end if;
  return query select d.departement from defense_departements d
                where d.joueur_id = auth.uid() order by d.ajoute_le;
end;
$f$;

-- ajoute le département s'il n'y est pas, le retire sinon ; renvoie la liste
create or replace function public.basculer_departement_defense(p_dep text)
 returns table(departement text)
 language plpgsql security definer set search_path to 'public'
as $f$
declare
  v_uid uuid := auth.uid();
  v_dep text := upper(btrim(coalesce(p_dep, '')));
begin
  if v_uid is null then raise exception 'Non connecte'; end if;
  if not exists (select 1 from communes c where c.departement = v_dep) then
    raise exception 'Département inconnu';
  end if;
  if exists (select 1 from defense_departements d where d.joueur_id = v_uid and d.departement = v_dep) then
    delete from defense_departements d where d.joueur_id = v_uid and d.departement = v_dep;
  else
    if (select count(*) from defense_departements d where d.joueur_id = v_uid) >= 5 then
      raise exception '5 départements au maximum : retires-en un avant';
    end if;
    insert into defense_departements(joueur_id, departement) values (v_uid, v_dep);
  end if;
  return query select d.departement from defense_departements d
                where d.joueur_id = v_uid order by d.ajoute_le;
end;
$f$;

revoke all on function public.mes_departements_defense() from public, anon;
revoke all on function public.basculer_departement_defense(text) from public, anon;
grant execute on function public.mes_departements_defense() to authenticated;
grant execute on function public.basculer_departement_defense(text) to authenticated;

-- Contrôle ---------------------------------------------------------------------------------
select (select count(*) from pg_proc where proname in ('mes_departements_defense', 'basculer_departement_defense')) as fonctions_doit_etre_2,
       has_function_privilege('anon', 'public.basculer_departement_defense(text)', 'execute') as anon_doit_etre_false;
