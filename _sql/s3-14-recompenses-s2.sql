-- ===========================================================================
--  s3-14 — les récompenses de fin de saison 2 (annoncées le 11/11, patch419)
--  Installe le calcul et l'attribution. NE DONNE RIEN : l'attribution se lance
--  le jour J, juste avant la clôture, par cloture_s2_s3(true) (s3-15).
--
--  Ce qui est calculé (recompenses_s2_calcul, lecture seule) :
--   - podium (podium-1, -2, -3) et top 10 (top10) : ordre du palmarès,
--     exclus du classement retirés (config_jeu 'exclus_classement') ;
--   - clan champion : 1er de la moyenne par membre actif (comme
--     clans_classement), 3 membres au moins ; badge pour les membres présents
--     depuis 7 jours au moins ;
--   - 13 distinctions, une par joueur (même règle que distinctions_calcul de
--     la S1 : la distinction la plus nette d'abord, ex aequo tous) ;
--   - seigneurs (département tenu à 50 % ou plus) et maîtres de région
--     (bonus de région du score) ;
--   - pionniers : tous ceux qui ont tenu une commune du Front en S2.
--  L'attribution écrit joueur_badges (saison 'saison-2'), les dos du podium
--  (boutique_inventaire), le trophée du clan (clan_trophees) et un paquet Terra
--  par pionnier (terra_jetons + 1, une seule fois). Rejouable.
--  Contrôle attendu (dernière ligne) : une ligne par récompense, 0 doublon.
-- ===========================================================================

create table if not exists public.clan_trophees (
  clan_id uuid not null references public.clans(id) on delete cascade,
  saison  text not null,
  rang    integer not null,
  nom     text,
  tag     text,
  moyenne integer,
  le      timestamptz not null default now(),
  primary key (clan_id, saison));
alter table public.clan_trophees enable row level security;
drop policy if exists clan_trophees_lecture on public.clan_trophees;
create policy clan_trophees_lecture on public.clan_trophees for select to authenticated using (true);
grant select on public.clan_trophees to authenticated;

-- ---------- les exclus du classement, en tableau ----------
create or replace function public.exclus_classement_liste()
 returns text[] language sql stable security definer set search_path to 'public'
as $$
  select coalesce(array_agg(x), array[]::text[])
    from jsonb_array_elements_text(coalesce((select valeur::jsonb from config_jeu where cle = 'exclus_classement'), '[]'::jsonb)) x;
$$;

-- ---------- les chiffres des 13 distinctions de la saison 2 ----------
create or replace function public.recompenses_s2_chiffres()
 returns table(badge text, joueur_id uuid, valeur integer)
 language sql stable security definer set search_path to 'public'
as $$
  with d as (select debut from saisons where id = 'saison-2'),
  chiffres as (
    -- 🗺️ conquêtes de la saison
    select 'conquerant'::text as badge, j.acteur as jid, count(*)::int as v
      from journal j, d where j.type = 'conquete' and j.acteur is not null and j.cree_le >= d.debut group by j.acteur
    -- 🛡️ défenses réussies
    union all select 'rempart', f.defenseur, count(*)::int
      from front_defenses f, d where f.reussie and f.le >= d.debut group by f.defenseur
    -- 🏰 attaques repoussées par ses garnisons
    union all select 'gardien', g.defenseur, count(*)::int
      from front_garnison_journal g, d where g.reussie and g.le >= d.debut group by g.defenseur
    -- 🧱 bâtiments terminés
    union all select 'batisseur', h.joueur_id, count(distinct h.batiment_id)::int
      from batiments_historique h where h.saison = 'saison-2' and h.pret_le <= now() group by h.joueur_id
    -- 💣 bombes lancées
    union all select 'artificier', b.lanceur, count(*)::int from bombes b where b.lanceur is not null group by b.lanceur
    -- ✊ lingots mis dans des rébellions (financer et étouffer)
    union all select 'rebelle', x.jid, sum(x.l)::int from (
        select r.financeur as jid, coalesce(r.mise, 0) as l from rebellions r
        union all select e.defenseur, coalesce(e.lingots, 0) from rebellions_etouffements e) x group by x.jid
    -- 🤝 échanges de clan conclus (les deux joueurs)
    union all select 'diplomate', x.jid, count(*)::int from (
        select c.proposant as jid from clan_echanges c where c.etat = 'accepte'
        union all select c.destinataire from clan_echanges c where c.etat = 'accepte') x group by x.jid
    -- 🎯 le plus attaqué : rounds perdus + défenses à mener
    union all select 'cible', x.jid, count(*)::int from (
        select v.adversaire as jid from front_victoires v where v.saison = 'saison-2' and v.type = 'conquete' and v.adversaire is not null
        union all select v.joueur_id from front_victoires v where v.saison = 'saison-2' and v.type = 'defense') x group by x.jid
    -- 🃏 communes différentes dans la collection Terra
    union all select 'collectionneur', t.joueur_id, count(*)::int from terra_collection t where t.exemplaires > 0 group by t.joueur_id
    -- 📍 Communes du jour trouvées pendant la saison
    union all select 'geographe', e.joueur_id, count(distinct e.jour)::int
      from cdj_essais e, d where e.km = 0 and e.jour >= (d.debut at time zone 'Europe/Paris')::date group by e.joueur_id
    -- 📡 ⚡ 🔮 les Elo (5 duels classés au moins)
    union all select 'navigateur', r.joueur_id, r.elo from radar_joueurs r where r.parties >= 5
    union all select 'eclair', r.joueur_id, r.elo from rafale_joueurs r where r.parties >= 5
    union all select 'flair', r.joueur_id, r.elo from pom_joueurs r where r.parties >= 5
  )
  select c.badge, c.jid, c.v from chiffres c join joueurs j on j.id = c.jid
   where c.v > 0 and not est_exclu_classement(j.pseudo);
$$;

-- ---------- tout ce que la fin de saison 2 donne, sans rien écrire ----------
create or replace function public.recompenses_s2_calcul()
 returns table(cle text, joueur_id uuid, pseudo text, valeur integer, info text)
 language plpgsql security definer set search_path to 'public'
as $$
declare
  v_badges text[] := array['conquerant','rempart','gardien','batisseur','artificier','rebelle','diplomate',
                           'cible','collectionneur','geographe','navigateur','eclair','flair'];
  v_pris uuid[] := '{}';
  r record;
  v_clan record;
begin
  -- 1. podium et top 10
  return query
    select case when ps.rang <= 3 then 'podium-' || ps.rang else 'top10' end, ps.joueur_id, ps.pseudo, ps.score, ps.rang::text
      from palmares_saison(exclus_classement_liste()) ps where ps.rang <= 10;

  -- 2. clan champion (calcul de clans_classement, sans connexion)
  select c.id, c.nom, c.tag, x.moyenne into v_clan
    from clans c
    join lateral (
      select count(*) n, count(*) filter (where a.actif) actifs,
             case when count(*) filter (where a.actif) > 0
                  then round(coalesce(sum(a.communes) filter (where a.actif), 0)::numeric / count(*) filter (where a.actif))::integer
                  else 0 end as moyenne
        from clan_membres m
        cross join lateral (
          select (select count(*) from possessions p where p.joueur_id = m.joueur_id) communes,
                 exists (select 1 from jours_joues d where d.joueur_id = m.joueur_id and d.jour >= quete_jour() - 6) actif) a
       where m.clan_id = c.id) x on true
   where x.n >= 3
   order by x.moyenne desc, c.nom
   limit 1;
  if v_clan.id is not null then
    return query
      select 'clan-champion'::text, m.joueur_id, j.pseudo, v_clan.moyenne, v_clan.tag::text || ' · ' || v_clan.nom::text
        from clan_membres m join joueurs j on j.id = m.joueur_id
       where m.clan_id = v_clan.id and m.depuis <= now() - interval '7 days';
    return query select 'clan-trophee'::text, null::uuid, v_clan.tag::text, v_clan.moyenne, v_clan.id::text;
  end if;

  -- 3. les 13 distinctions, une par joueur
  create temp table if not exists tmp_rs2(badge text, jid uuid, v integer) on commit drop;
  truncate tmp_rs2;
  insert into tmp_rs2 select * from recompenses_s2_chiffres();
  loop
    select x.badge, x.v1 into r from (
      select d.badge, max(d.v) as v1,
             (select max(d2.v) from tmp_rs2 d2 where d2.badge = d.badge and not (d2.jid = any(v_pris)) and d2.v < max(d.v)) as v2
        from tmp_rs2 d
       where d.badge = any(v_badges) and not (d.jid = any(v_pris))
       group by d.badge) x
     order by case when x.v2 is null then 1e12 else x.v1::numeric / greatest(x.v2, 1) end desc, x.v1 desc, x.badge
     limit 1;
    exit when r.badge is null;
    return query select r.badge, d.jid, j.pseudo, d.v, null::text
                   from tmp_rs2 d join joueurs j on j.id = d.jid
                  where d.badge = r.badge and d.v = r.v1 and not (d.jid = any(v_pris));
    v_pris := v_pris || array(select d.jid from tmp_rs2 d where d.badge = r.badge and d.v = r.v1 and not (d.jid = any(v_pris)));
    v_badges := array_remove(v_badges, r.badge);
  end loop;

  -- 4. seigneurs : département tenu à 50 % ou plus (outre-mer compris, cantons suisses exclus)
  return query
    with tailles as (select c.departement, count(*)::numeric n from communes c where not est_canton(c.departement) group by 1),
    parts as (select c.departement, p.joueur_id, count(*)::numeric n
                from possessions p join communes c on c.code = p.commune_code
               where not est_canton(c.departement) group by 1, 2)
    select 'seigneur-' || pa.departement, pa.joueur_id, j.pseudo, round(100 * pa.n / t.n)::integer, pa.departement
      from parts pa join tailles t on t.departement = pa.departement join joueurs j on j.id = pa.joueur_id
     where pa.n / t.n >= 0.5 and not est_exclu_classement(j.pseudo);

  -- 5. maîtres de région : le bonus de région du score (front_territoires)
  return query
    with tailles as (select c.departement, count(*)::numeric n from communes c where length(c.departement) = 2 and not est_canton(c.departement) group by 1),
    parts as (select c.departement, p.joueur_id, count(*)::numeric n
                from possessions p join communes c on c.code = p.commune_code
               where length(c.departement) = 2 and not est_canton(c.departement) group by 1, 2),
    tetes as (select pa.departement, max(pa.n) maxi from parts pa group by 1),
    seuls as (select pa.departement, pa.joueur_id from parts pa join tetes t on t.departement = pa.departement and pa.n = t.maxi
               where (select count(*) from parts p2 where p2.departement = pa.departement and p2.n = t.maxi) = 1),
    deps as (select pa.joueur_id, pa.departement from parts pa join tailles ta on ta.departement = pa.departement
               left join seuls s on s.departement = pa.departement and s.joueur_id = pa.joueur_id
              where pa.n / ta.n >= 0.5 or (s.joueur_id is not null and pa.n / ta.n >= 0.10)),
    reg_tailles as (select cdj_region(t.departement) region, count(*) n from tailles t group by 1),
    regs as (select d.joueur_id, cdj_region(d.departement) region, count(*) n from deps d group by 1, 2)
    select 'maitre-' || translate(lower(replace(replace(rg.region, ' ', '-'), '''', '-')), 'éèêàâôîïûùç', 'eeeaaoiiuuc'),
           rg.joueur_id, j.pseudo, rg.n::integer, rg.region
      from regs rg join reg_tailles rt on rt.region = rg.region join joueurs j on j.id = rg.joueur_id
     where rg.n * 2 > rt.n and not est_exclu_classement(j.pseudo);

  -- 6. pionniers : une commune du Front tenue en saison 2 (tout le monde, exclus compris)
  return query
    select 'pionnier'::text, j.id, j.pseudo, null::integer, null::text
      from joueurs j where exists (select 1 from historique h where h.joueur_id = j.id and h.saison = 'saison-2');
end;
$$;

-- ---------- attribuer (rejouable) ----------
create or replace function public.recompenses_s2_attribuer(p_confirmer boolean default false)
 returns table(etape text, valeur text)
 language plpgsql security definer set search_path to 'public'
as $$
declare
  v_badges integer := 0; v_dos integer := 0; v_paquets integer := 0; v_trophee integer := 0;
  t record;
begin
  create temp table if not exists tmp_rs2_res(cle text, joueur_id uuid, pseudo text, valeur integer, info text) on commit drop;
  truncate tmp_rs2_res;
  insert into tmp_rs2_res select * from recompenses_s2_calcul();

  if p_confirmer then
    -- badges (tout sauf la ligne du trophée de clan)
    insert into joueur_badges(joueur_id, badge, saison, valeur)
    select r.joueur_id, r.cle, 'saison-2', r.valeur from tmp_rs2_res r
     where r.joueur_id is not null and r.cle <> 'clan-trophee'
    on conflict do nothing;
    get diagnostics v_badges = row_count;
    -- les dos du podium
    insert into boutique_inventaire(joueur_id, article_id)
    select r.joueur_id, case r.cle when 'podium-1' then 'dos-podium-s2-or' when 'podium-2' then 'dos-podium-s2-argent' else 'dos-podium-s2-bronze' end
      from tmp_rs2_res r where r.cle in ('podium-1', 'podium-2', 'podium-3')
    on conflict do nothing;
    get diagnostics v_dos = row_count;
    -- le trophée du clan
    insert into clan_trophees(clan_id, saison, rang, nom, tag, moyenne)
    select c.id, 'saison-2', 1, c.nom, c.tag, r.valeur from tmp_rs2_res r join clans c on c.id::text = r.info
     where r.cle = 'clan-trophee'
    on conflict do nothing;
    get diagnostics v_trophee = row_count;
    -- un paquet Terra par pionnier, une seule fois (marque : parrainage_recompenses)
    with neufs as (
      insert into parrainage_recompenses(joueur_id, quoi, saison, paquets)
      select r.joueur_id, 'pionnier', 'saison-2', 1 from tmp_rs2_res r where r.cle = 'pionnier'
      on conflict do nothing
      returning joueur_id)
    update joueurs j set terra_jetons = terra_jetons_lire(j.terra_jetons, j.terra_jetons_maj) + 1, terra_jetons_maj = now()
      from neufs n where n.joueur_id = j.id;
    get diagnostics v_paquets = row_count;
  end if;

  return query select case when p_confirmer then 'ATTRIBUÉ' else 'SIMULATION' end,
                      case when p_confirmer then v_badges || ' badges, ' || v_dos || ' dos, ' || v_trophee || ' trophée, ' || v_paquets || ' paquets Terra'
                           else 'rien n''a été modifié' end;
  for t in
    select r.cle, string_agg(coalesce(r.pseudo, '?') || coalesce(' (' || r.valeur || ')', ''), ', ' order by r.valeur desc nulls last, r.pseudo) as qui, count(*) n
      from tmp_rs2_res r where r.cle not in ('pionnier') group by r.cle
      order by case when r.cle like 'podium-%' then 0 when r.cle = 'top10' then 1 when r.cle like 'clan-%' then 2
                    when r.cle like 'seigneur-%' then 4 when r.cle like 'maitre-%' then 5 else 3 end, r.cle
  loop
    return query select t.cle, t.qui;
  end loop;
  return query select 'pionnier'::text, (select count(*) from tmp_rs2_res r where r.cle = 'pionnier') || ' joueurs (1 paquet Terra chacun)';
  return query select 'contrôle : doublons', (select count(*) from (select r.joueur_id, r.cle from tmp_rs2_res r where r.joueur_id is not null group by 1, 2 having count(*) > 1) x)::text;
  return query select 'contrôle : distinctions par joueur (max)', coalesce((select max(n) from (select count(*) n from tmp_rs2_res r
                       where r.cle in ('conquerant','rempart','gardien','batisseur','artificier','rebelle','diplomate','cible','collectionneur','geographe','navigateur','eclair','flair')
                       group by r.joueur_id) x), 0)::text;
end;
$$;

revoke all on function public.recompenses_s2_chiffres() from public, anon, authenticated;
revoke all on function public.recompenses_s2_calcul() from public, anon, authenticated;
revoke all on function public.recompenses_s2_attribuer(boolean) from public, anon, authenticated;
revoke all on function public.exclus_classement_liste() from public, anon, authenticated;

-- ---------- les titres gagnés à la fin de la saison 2 ----------
create or replace function public.titres_possibles(p_joueur uuid)
 returns text[]
 language sql
 stable security definer
 set search_path to 'public'
as $function$
  select coalesce(array_agg(x.titre order by x.titre), '{}')
    from (select t.titre
            from (values ('parrain', 'parrain')) as t(titre, badge)
           where exists (select 1 from joueur_badges b where b.joueur_id = p_joueur and b.badge = t.badge)
          union
          -- s2-53 : les titres gagnés dans un pass de saison
          select r.valeur
            from pass_reclames c join pass_recompenses r on r.saison = c.saison and r.niveau = c.niveau
           where c.joueur_id = p_joueur and r.type = 'titre'
          union
          -- s2-68 : la quête d'Halloween (Terra ou Front)
          select coalesce(halloween_hantees_cfg() ->> 'titre', 'halloween-2026')
            from halloween_quete q
           where q.joueur_id = p_joueur and (q.reclame_le is not null or q.front_reclame_le is not null)
          union
          -- s3-10 : le Mess (trois couronnes à la Machine à chiffrer)
          select distinct x.gain ->> 'titre' from mess_tirages x where x.joueur_id = p_joueur and x.gain ? 'titre'
          union
          -- s3-14 : la fin de la saison 2 (classement, seigneurs, maîtres de région)
          select case b.badge when 'podium-1' then 'champion-s2' when 'podium-2' then 'vice-champion-s2'
                              when 'podium-3' then 'troisieme-s2' when 'top10' then 'top10-s2'
                              else replace(replace(b.badge, 'seigneur-', 'seigneur-s2-'), 'maitre-', 'maitre-s2-') end
            from joueur_badges b
           where b.joueur_id = p_joueur and b.saison = 'saison-2'
             and (b.badge in ('podium-1', 'podium-2', 'podium-3', 'top10') or b.badge like 'seigneur-%' or b.badge like 'maitre-%')) x;
$function$;

-- contrôle : la simulation, rien n'est écrit
select * from public.recompenses_s2_attribuer(false);
