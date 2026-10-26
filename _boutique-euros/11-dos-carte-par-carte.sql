-- ===========================================================================
--  TerraFront — 11. le dos carte par carte (patch200). Rejouable.
--  26 octobre 2026. À passer APRÈS 6-garde-robe.sql, AVANT de pousser patch200.
--
--  Un joueur peut donner à une carte précise un autre dos que son dos
--  principal, en Terra comme sur le Front. Ce dos se voit quand on retourne
--  la carte (sa fiche, sa vitrine). Le Tirage garde le dos principal.
--  - Le dos doit être possédé (garde_robe_possede) ; « origine » = le dos
--    d'origine, toujours permis.
--  - Une carte vendue, échangée ou prise n'est plus lue : elle prend le dos
--    de son nouveau propriétaire. Le choix revient si on récupère la carte.
--  - Un autre joueur ne voit que les dos des cartes de la vitrine.
-- ===========================================================================
begin;

create table if not exists public.dos_cartes(
  joueur_id    uuid not null references public.joueurs(id) on delete cascade,
  source       text not null check (source in ('terra', 'front')),
  commune_code text not null,
  dos          text not null,
  modifie_le   timestamptz not null default now(),
  primary key (joueur_id, source, commune_code)
);
alter table public.dos_cartes enable row level security;
revoke all on public.dos_cartes from public, anon, authenticated;

-- la carte est-elle encore à ce joueur ?
create or replace function public.dos_carte_tenue(p_uid uuid, p_source text, p_code text)
 returns boolean language sql stable security definer set search_path to 'public'
as $f$
  select case p_source
    when 'terra' then exists(select 1 from terra_collection t
                              where t.joueur_id = p_uid and t.commune_code = p_code and t.exemplaires > 0)
    when 'front' then exists(select 1 from possessions p
                              where p.joueur_id = p_uid and p.commune_code = p_code)
    else false end
$f$;

-- les dos carte par carte d'un joueur (pour un autre : seulement sa vitrine)
create or replace function public.dos_cartes(p_joueur uuid)
 returns table(source text, code text, nom text, dos text)
 language plpgsql stable security definer set search_path to 'public'
as $f$
declare v_uid uuid := auth.uid();
begin
  if v_uid is null then raise exception 'Non connecte'; end if;
  return query
  select d.source, d.commune_code, c.nom::text, d.dos
    from dos_cartes d
    join communes c on c.code = d.commune_code
   where d.joueur_id = p_joueur
     and dos_carte_tenue(p_joueur, d.source, d.commune_code)
     and (d.dos = 'origine' or garde_robe_possede(p_joueur, 'dos', d.dos))
     and (p_joueur = v_uid or exists(select 1 from terra_vitrine v
                                      where v.joueur_id = p_joueur and v.source = d.source
                                        and v.commune_code = d.commune_code))
   order by d.source, c.nom;
end;
$f$;

-- donner un dos à une ou plusieurs cartes ; p_dos vide = elles reprennent mon dos
create or replace function public.dos_cartes_definir(p_source text, p_codes text[], p_dos text)
 returns integer
 language plpgsql security definer set search_path to 'public'
as $f$
declare
  v_uid uuid := auth.uid();
  v_codes text[] := coalesce(p_codes, '{}');
  v_dos text := nullif(p_dos, '');
begin
  if v_uid is null then raise exception 'Non connecte'; end if;
  if p_source not in ('terra', 'front') then raise exception 'Choix invalide'; end if;
  if cardinality(v_codes) > 500 then raise exception 'Trop de cartes d''un coup'; end if;
  if v_dos is null then
    delete from dos_cartes where joueur_id = v_uid and source = p_source and commune_code = any(v_codes);
    return cardinality(v_codes);
  end if;
  if v_dos <> 'origine' and not garde_robe_possede(v_uid, 'dos', v_dos) then
    raise exception 'Tu n''as pas ce dos';
  end if;
  if exists(select 1 from unnest(v_codes) x where not dos_carte_tenue(v_uid, p_source, x)) then
    raise exception 'Tu ne possèdes pas une de ces cartes';
  end if;
  insert into dos_cartes(joueur_id, source, commune_code, dos)
  select v_uid, p_source, x, v_dos from (select distinct x from unnest(v_codes) x) s
  on conflict (joueur_id, source, commune_code) do update set dos = excluded.dos, modifie_le = now();
  return cardinality(v_codes);
end;
$f$;

revoke all on function public.dos_carte_tenue(uuid, text, text)       from public, anon, authenticated;
revoke all on function public.dos_cartes(uuid)                        from public, anon;
revoke all on function public.dos_cartes_definir(text, text[], text)  from public, anon;
grant execute on function public.dos_cartes(uuid)                     to authenticated;
grant execute on function public.dos_cartes_definir(text, text[], text) to authenticated;

commit;

-- ---------- contrôle : attendu  true | true | false | false ----------
select to_regclass('public.dos_cartes') is not null                                            as table_ok,
       has_function_privilege('authenticated', 'public.dos_cartes_definir(text,text[],text)', 'execute') as definir_ok,
       has_function_privilege('anon', 'public.dos_cartes(uuid)', 'execute')                    as anon_doit_etre_false,
       has_function_privilege('authenticated', 'public.dos_carte_tenue(uuid,text,text)', 'execute') as interne_doit_etre_false;
