-- ===========================================================================
--  TerraFront — boutique en euros : 13. les skins de carte (patch201)
--  26 octobre 2026. À passer APRÈS 11-dos-carte-par-carte.sql, AVANT de
--  pousser patch201. Rejouable.
--
--  - 9 articles « skin » (inactifs : la boutique les montrera au patch202).
--  - Un skin se pose carte par carte, en Terra et sur le Front, comme le dos
--    (table skin_cartes, même règles que dos_cartes).
--  - Les comptes testeurs reçoivent les 9 skins en cadeau (sans commande),
--    pour les essayer et faire la promo. Gardés à l'ouverture de la boutique.
-- ===========================================================================
begin;

insert into public.euros_articles(id, type, nom, description, prix_centimes, reserve_og, actif, ordre) values
  ('skin-comete',  'skin', 'Skin Comète',     'La photo passe en nocturne, les étoiles sortent dans le ciel', 499, false, false, 210),
  ('skin-juillet', 'skin', 'Skin 14 Juillet', 'Le ciel de la photo s''illumine d''un feu d''artifice',        499, false, false, 220),
  ('skin-maree',   'skin', 'Skin Marée',      'Le bas de la photo ondule comme un reflet dans l''eau',        399, false, false, 230),
  ('skin-feu',     'skin', 'Skin Brasier',    'Des flammes montent du bas de la photo, le cadre rougeoie',    699, false, false, 240),
  ('skin-prisme',  'skin', 'Skin Prisme',     'Une feuille holographique qui change avec l''angle',          799, false, false, 250),
  ('skin-orfondu', 'skin', 'Skin Or fondu',   'Photo dorée, cadre d''or et poussière d''or qui s''élève',     499, false, false, 260),
  ('skin-neon',    'skin', 'Skin Néon',       'Les contours de la photo deviennent des néons',                399, false, false, 270),
  ('skin-gravure', 'skin', 'Skin Gravure',    'La photo retracée à l''encre, sur papier ancien',              249, false, false, 280),
  ('skin-orage',   'skin', 'Skin Orage',      'Pluie et éclairs, la photo s''éclaire d''un coup',             699, false, false, 290)
on conflict (id) do nothing;

-- les skins offerts aux testeurs (Nataël)
insert into public.euros_inventaire(joueur_id, article_id, commande_id)
select t.id::uuid, a.id, null
  from jsonb_array_elements_text(coalesce(public.euros_reglage('testeurs'), '[]'::jsonb)) as t(id)
  cross join public.euros_articles a
 where a.type = 'skin'
on conflict (joueur_id, article_id) do nothing;

-- posséder un skin (en plus du dos et de l'habillage)
create or replace function public.garde_robe_possede(p_uid uuid, p_rangee text, p_id text)
 returns boolean language sql stable security definer set search_path to 'public'
as $f$
  select case
    when p_id is null then true
    when p_rangee = 'dos' then
         exists(select 1 from boutique_inventaire i join boutique_articles a on a.id = i.article_id
                 where i.joueur_id = p_uid and i.article_id = p_id and a.type = 'dos')
      or exists(select 1 from euros_inventaire i join euros_articles a on a.id = i.article_id
                 where i.joueur_id = p_uid and i.article_id = p_id and a.type = 'dos')
    when p_rangee = 'habillage' then
      case when p_id = 'nacre'
           then exists(select 1 from boutique_inventaire i where i.joueur_id = p_uid and i.article_id = 'dos-og')
           else exists(select 1 from euros_inventaire i join euros_articles a on a.id = i.article_id
                        where i.joueur_id = p_uid and i.article_id = p_id and a.type = 'habillage') end
    when p_rangee = 'skin' then
         exists(select 1 from euros_inventaire i join euros_articles a on a.id = i.article_id
                 where i.joueur_id = p_uid and i.article_id = p_id and a.type = 'skin')
    else false end
$f$;

-- mes skins
create or replace function public.garde_robe_skins()
 returns table(id text, nom text)
 language plpgsql stable security definer set search_path to 'public'
as $f$
begin
  if auth.uid() is null then raise exception 'Non connecte'; end if;
  return query
  select a.id, a.nom from euros_inventaire i join euros_articles a on a.id = i.article_id
   where i.joueur_id = auth.uid() and a.type = 'skin' order by a.ordre;
end;
$f$;

create table if not exists public.skin_cartes(
  joueur_id    uuid not null references public.joueurs(id) on delete cascade,
  source       text not null check (source in ('terra', 'front')),
  commune_code text not null,
  skin         text not null,
  modifie_le   timestamptz not null default now(),
  primary key (joueur_id, source, commune_code)
);
alter table public.skin_cartes enable row level security;
revoke all on public.skin_cartes from public, anon, authenticated;

-- les skins posés par un joueur (pour un autre : seulement sa vitrine)
create or replace function public.skin_cartes(p_joueur uuid)
 returns table(source text, code text, nom text, skin text)
 language plpgsql stable security definer set search_path to 'public'
as $f$
declare v_uid uuid := auth.uid();
begin
  if v_uid is null then raise exception 'Non connecte'; end if;
  return query
  select s.source, s.commune_code, c.nom::text, s.skin
    from skin_cartes s
    join communes c on c.code = s.commune_code
   where s.joueur_id = p_joueur
     and dos_carte_tenue(p_joueur, s.source, s.commune_code)
     and garde_robe_possede(p_joueur, 'skin', s.skin)
     and (p_joueur = v_uid or exists(select 1 from terra_vitrine v
                                      where v.joueur_id = p_joueur and v.source = s.source
                                        and v.commune_code = s.commune_code))
   order by s.source, c.nom;
end;
$f$;

-- poser un skin sur une ou plusieurs cartes ; p_skin vide = on l'enlève
create or replace function public.skin_cartes_definir(p_source text, p_codes text[], p_skin text)
 returns integer
 language plpgsql security definer set search_path to 'public'
as $f$
declare
  v_uid uuid := auth.uid();
  v_codes text[] := coalesce(p_codes, '{}');
  v_skin text := nullif(p_skin, '');
begin
  if v_uid is null then raise exception 'Non connecte'; end if;
  if p_source not in ('terra', 'front') then raise exception 'Choix invalide'; end if;
  if cardinality(v_codes) > 500 then raise exception 'Trop de cartes d''un coup'; end if;
  if v_skin is null then
    delete from skin_cartes where joueur_id = v_uid and source = p_source and commune_code = any(v_codes);
    return cardinality(v_codes);
  end if;
  if not garde_robe_possede(v_uid, 'skin', v_skin) then raise exception 'Tu n''as pas ce skin'; end if;
  if exists(select 1 from unnest(v_codes) x where not dos_carte_tenue(v_uid, p_source, x)) then
    raise exception 'Tu ne possèdes pas une de ces cartes';
  end if;
  insert into skin_cartes(joueur_id, source, commune_code, skin)
  select v_uid, p_source, x, v_skin from (select distinct x from unnest(v_codes) x) s
  on conflict (joueur_id, source, commune_code) do update set skin = excluded.skin, modifie_le = now();
  return cardinality(v_codes);
end;
$f$;

revoke all on function public.garde_robe_skins()                        from public, anon;
revoke all on function public.skin_cartes(uuid)                         from public, anon;
revoke all on function public.skin_cartes_definir(text, text[], text)   from public, anon;
grant execute on function public.garde_robe_skins()                     to authenticated;
grant execute on function public.skin_cartes(uuid)                      to authenticated;
grant execute on function public.skin_cartes_definir(text, text[], text) to authenticated;

commit;

-- ---------- contrôle : attendu  9 | 0 | 9 | true | false ----------
-- skins : les 9 articles ; actifs : aucun (la boutique viendra) ; offerts :
-- les skins dans l'inventaire des testeurs ; table_ok ; anon_doit_etre_false
select (select count(*) from public.euros_articles where type = 'skin')               as skins,
       (select count(*) from public.euros_articles where type = 'skin' and actif)     as actifs,
       (select count(*) from public.euros_inventaire i join public.euros_articles a on a.id = i.article_id
         where a.type = 'skin' and i.commande_id is null)                             as offerts,
       to_regclass('public.skin_cartes') is not null                                 as table_ok,
       has_function_privilege('anon', 'public.skin_cartes(uuid)', 'execute')         as anon_doit_etre_false;
