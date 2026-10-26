-- ===========================================================================
--  TerraFront — saison 2 : alertes d'échange (idée d'Arkhannou, 26 octobre)
--
--  Chaque joueur tient une liste de communes qu'il cherche (10 au plus).
--   - « Je cherche » : pour chacune, qui l'a en double (échangeable).
--   - « On cherche tes doublons » : mes doublons échangeables que d'autres
--     joueurs cherchent, et qui les cherche.
--   - « Les plus recherchées » : les communes en alerte chez au moins 2 joueurs.
--  Une commune que j'obtiens sort toute seule de ma liste.
--  Doublon échangeable = exemplaires − max(1, aurore + bloques) > 0, comme
--  terra_cibles_echange (s2-23 : les cartes achetées en points ne s'échangent pas).
--
--  Rejouable. Finit par un contrôle : true | true | true | true | 0
-- ===========================================================================
create table if not exists public.terra_recherches(
  joueur_id    uuid not null references public.joueurs(id) on delete cascade,
  commune_code text not null,
  cree_le      timestamptz not null default now(),
  primary key (joueur_id, commune_code)
);
create index if not exists terra_recherches_commune on public.terra_recherches(commune_code);
alter table public.terra_recherches enable row level security;
-- aucune politique : on ne passe que par les fonctions ci-dessous

-- nombre d'exemplaires échangeables d'une commune chez un joueur
create or replace function public.terra_libres_echange(p_joueur uuid, p_code text)
 returns integer language sql stable security definer set search_path to 'public'
as $f$
  select coalesce((select greatest(0, t.exemplaires - greatest(1, t.aurore + t.bloques))
                     from terra_collection t
                    where t.joueur_id = p_joueur and t.commune_code = p_code), 0)::integer;
$f$;
revoke all on function public.terra_libres_echange(uuid, text) from public, anon, authenticated;

-- suggestions pour ajouter une commune à ma liste (celles que je n'ai pas)
create or replace function public.terra_recherche_suggerer(p_texte text)
 returns table(code text, nom text, departement text, tier text)
 language plpgsql stable security definer set search_path to 'public'
as $f$
declare v_t text := btrim(coalesce(p_texte, ''));
begin
  if auth.uid() is null then raise exception 'Non connecte'; end if;
  if length(v_t) < 2 then return; end if;
  return query
  select c.code::text, c.nom::text, c.departement::text, c.tier::text
    from communes c
   where (c.nom ilike v_t || '%' or c.nom ilike '% ' || v_t || '%' or c.nom ilike '%-' || v_t || '%')
     and not exists (select 1 from terra_collection m
                      where m.joueur_id = auth.uid() and m.commune_code = c.code and m.exemplaires > 0)
   order by (lower(c.nom) = lower(v_t)) desc, (c.nom ilike v_t || '%') desc, c.population desc nulls last
   limit 8;
end;
$f$;

create or replace function public.terra_recherche_ajouter(p_code text)
 returns integer language plpgsql security definer set search_path to 'public'
as $f$
declare v_uid uuid := auth.uid(); v_n integer;
begin
  if v_uid is null then raise exception 'Non connecte'; end if;
  if not terra_ouverte() then raise exception 'Terra n''est pas encore ouvert'; end if;
  if not exists (select 1 from communes where code = p_code) then raise exception 'Commune inconnue'; end if;
  if exists (select 1 from terra_collection where joueur_id = v_uid and commune_code = p_code and exemplaires > 0) then
    raise exception 'Tu as déjà cette commune';
  end if;
  if exists (select 1 from terra_recherches where joueur_id = v_uid and commune_code = p_code) then
    return (select count(*) from terra_recherches where joueur_id = v_uid);
  end if;
  select count(*) into v_n from terra_recherches where joueur_id = v_uid;
  if v_n >= 10 then raise exception 'Ta liste est pleine (10 communes) : retires-en une d''abord'; end if;
  insert into terra_recherches(joueur_id, commune_code) values (v_uid, p_code);
  return v_n + 1;
end;
$f$;

create or replace function public.terra_recherche_retirer(p_code text)
 returns integer language plpgsql security definer set search_path to 'public'
as $f$
declare v_uid uuid := auth.uid();
begin
  if v_uid is null then raise exception 'Non connecte'; end if;
  delete from terra_recherches where joueur_id = v_uid and commune_code = p_code;
  return (select count(*) from terra_recherches where joueur_id = v_uid);
end;
$f$;

-- tout l'onglet « Mes alertes » en un appel
create or replace function public.terra_mes_alertes()
 returns jsonb language plpgsql security definer set search_path to 'public'
as $f$
declare v_uid uuid := auth.uid(); v_cherche jsonb; v_doublons jsonb; v_top jsonb;
begin
  if v_uid is null then raise exception 'Non connecte'; end if;
  if not terra_ouverte() then return jsonb_build_object('je_cherche', '[]'::jsonb, 'mes_doublons', '[]'::jsonb, 'plus_recherchees', '[]'::jsonb); end if;
  -- une commune obtenue sort de ma liste
  delete from terra_recherches r
   where r.joueur_id = v_uid
     and exists (select 1 from terra_collection m where m.joueur_id = v_uid and m.commune_code = r.commune_code and m.exemplaires > 0);

  select coalesce(jsonb_agg(x order by x->>'nom'), '[]'::jsonb) into v_cherche from (
    select jsonb_build_object('code', c.code, 'nom', c.nom, 'dept', c.departement, 'tier', c.tier,
             'dispo', coalesce((select jsonb_agg(jsonb_build_object('id', d.joueur_id, 'pseudo', d.pseudo) order by d.pseudo)
                                  from (select t.joueur_id, j.pseudo
                                          from terra_collection t join joueurs j on j.id = t.joueur_id
                                         where t.commune_code = r.commune_code and t.joueur_id <> v_uid
                                           and t.exemplaires - greatest(1, t.aurore + t.bloques) > 0
                                         order by j.pseudo limit 6) d), '[]'::jsonb)) as x
      from terra_recherches r join communes c on c.code = r.commune_code
     where r.joueur_id = v_uid) s;

  select coalesce(jsonb_agg(x order by (x->>'nb')::int desc, x->>'nom'), '[]'::jsonb) into v_doublons from (
    select jsonb_build_object('code', c.code, 'nom', c.nom, 'dept', c.departement, 'tier', c.tier,
             'libres', (t.exemplaires - greatest(1, t.aurore + t.bloques)),
             'nb', (select count(*) from terra_recherches r2 where r2.commune_code = t.commune_code and r2.joueur_id <> v_uid),
             'chercheurs', (select jsonb_agg(jsonb_build_object('id', q.joueur_id, 'pseudo', q.pseudo) order by q.cree_le desc)
                              from (select r.joueur_id, j.pseudo, r.cree_le
                                      from terra_recherches r join joueurs j on j.id = r.joueur_id
                                     where r.commune_code = t.commune_code and r.joueur_id <> v_uid
                                     order by r.cree_le desc limit 6) q)) as x
      from terra_collection t join communes c on c.code = t.commune_code
     where t.joueur_id = v_uid
       and t.exemplaires - greatest(1, t.aurore + t.bloques) > 0
       and exists (select 1 from terra_recherches r where r.commune_code = t.commune_code and r.joueur_id <> v_uid)) s;

  select coalesce(jsonb_agg(x order by (x->>'nb')::int desc, x->>'nom'), '[]'::jsonb) into v_top from (
    select jsonb_build_object('code', c.code, 'nom', c.nom, 'dept', c.departement, 'tier', c.tier, 'nb', n.nb) as x
      from (select commune_code, count(*) as nb from terra_recherches group by commune_code having count(*) >= 2
             order by count(*) desc limit 5) n
      join communes c on c.code = n.commune_code) s;

  return jsonb_build_object('je_cherche', v_cherche, 'mes_doublons', v_doublons, 'plus_recherchees', v_top);
end;
$f$;

-- ---------------------------------------------------------------------------
-- Contrôle : tables et fonctions en place, liste vide au départ
select to_regclass('public.terra_recherches') is not null                       as table_ok,
       to_regprocedure('public.terra_mes_alertes()') is not null                as alertes_ok,
       to_regprocedure('public.terra_recherche_ajouter(text)') is not null      as ajouter_ok,
       to_regprocedure('public.terra_recherche_suggerer(text)') is not null     as suggerer_ok,
       (select count(*) from public.terra_recherches)                           as recherches;
