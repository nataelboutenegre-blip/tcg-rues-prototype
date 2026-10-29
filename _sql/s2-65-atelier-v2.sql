-- ===========================================================================
--  s2-65 — L'atelier des cartes, V2 (patch271) : styles, bordures,
--  « Appliquer à » et l'atelier depuis la fiche d'une carte
--  (aperçus validés le 29/10 : planches « Appliquer à » et « L'atelier
--  depuis la fiche d'une carte » : « ok parfait ! », « c'est parfait ! »)
--
--  À LANCER APRÈS s2-64-atelier.sql (il le vérifie), au moment de l'annonce.
--
--  Ce que ça ajoute :
--    - STYLES : Carte postale (200 communes Terra dans la collection),
--      État-major (un département fini en Terra : toutes ses communes) ;
--    - BORDURES : Nuit (une quête du jour réclamée 14 jours d'affilée),
--      Tricolore (3 départements finis en Terra), Dorée (1,99 €, article
--      « effet » atelier-doree, offerte aux testeurs) ;
--    - tout ce qui se gagne est GARDÉ À VIE : la 1re fois que la condition
--      est remplie, c'est noté (atelier_debloques) ; vendre une carte
--      ensuite ne retire rien ;
--    - « APPLIQUER À » : toutes les cartes Terra sauf des cartes exclues, ou
--      seulement des cartes choisies (atelier_compositions.mode) ;
--    - une carte peut avoir sa PROPRE composition, réglée depuis sa fiche
--      (seulement avec ce que le joueur possède).
--  Une vitrine montre, carte par carte, ce que le joueur a posé (et
--  seulement ce qu'il possède encore).
--  Rejouable. Contrôle attendu : true | 1 | true | true | true | false
-- ===========================================================================
do $$ begin
  if not exists(select 1 from public.config_jeu where cle = 'atelier') or to_regclass('public.atelier_compositions') is null then
    raise exception 'Lance d''abord s2-64-atelier.sql';
  end if;
end $$;

begin;

-- 1. Les réglages (on fusionne avec ceux de s2-64) --------------------------------
update public.config_jeu
   set valeur = (valeur::jsonb || '{"postale_communes": 200, "etat_departements": 1, "tricolore_departements": 3, "nuit_jours": 14}'::jsonb)::text
 where cle = 'atelier';

-- 2. La bordure Dorée (1,99 €), offerte aux testeurs ----------------------------------
insert into public.euros_articles(id, type, nom, description, prix_centimes, reserve_og, actif, ordre) values
  ('atelier-doree', 'effet', 'Bordure Dorée', 'Un cadre d''or qui tourne doucement autour de la carte', 199, false, true, 440)
on conflict (id) do update set actif = true;
insert into public.euros_inventaire(joueur_id, article_id, commande_id)
select t.id::uuid, 'atelier-doree', null
  from jsonb_array_elements_text(coalesce(public.euros_reglage('testeurs'), '[]'::jsonb)) as t(id)
on conflict (joueur_id, article_id) do nothing;

-- 3. Les tables --------------------------------------------------------------------------
alter table public.atelier_compositions add column if not exists style   text not null default 'classique';
alter table public.atelier_compositions add column if not exists bordure text not null default 'rarete';
alter table public.atelier_compositions add column if not exists mode    text not null default 'toutes';
do $$ begin
  alter table public.atelier_compositions add constraint atelier_compositions_v2_ok check (
    style in ('classique', 'postale', 'etat') and bordure in ('rarete', 'nuit', 'tricolore', 'doree') and mode in ('toutes', 'choisies'));
exception when duplicate_object then null; end $$;

-- ce qui a été gagné une fois (gardé à vie)
create table if not exists public.atelier_debloques(
  joueur_id uuid not null references public.joueurs(id) on delete cascade,
  element   text not null,
  le        timestamptz not null default now(),
  primary key (joueur_id, element)
);
alter table public.atelier_debloques enable row level security;
revoke all on public.atelier_debloques from public, anon, authenticated;

-- carte par carte : exclue (mode « toutes »), choisie (mode « choisies »), ou sa propre composition
create table if not exists public.atelier_cartes(
  joueur_id    uuid not null references public.joueurs(id) on delete cascade,
  commune_code text not null,
  exclue       boolean not null default false,
  choisie      boolean not null default false,
  propre       jsonb,
  modifie_le   timestamptz not null default now(),
  primary key (joueur_id, commune_code)
);
alter table public.atelier_cartes enable row level security;
revoke all on public.atelier_cartes from public, anon, authenticated;

-- 4. Ce qui se gagne -----------------------------------------------------------------------
create or replace function public.atelier_communes(p_uid uuid)
 returns integer language sql stable security definer set search_path to 'public'
as $f$
  select count(*)::integer from terra_collection t where t.joueur_id = p_uid and t.exemplaires > 0
$f$;
-- départements finis en Terra : toutes leurs communes dans la collection
create or replace function public.atelier_departements(p_uid uuid)
 returns integer language sql stable security definer set search_path to 'public'
as $f$
  select count(*)::integer from (
    select c.departement
      from communes c
      left join terra_collection t on t.commune_code = c.code and t.joueur_id = p_uid and t.exemplaires > 0
     group by c.departement
    having count(*) = count(t.commune_code)) x
$f$;
-- la condition, aujourd'hui
create or replace function public.atelier_condition(p_uid uuid, p_element text)
 returns boolean language plpgsql stable security definer set search_path to 'public'
as $f$
declare r jsonb := atelier_reglages();
begin
  return case p_element
    when 'encre'     then atelier_quetes(p_uid) >= coalesce((r ->> 'encre_quetes')::int, 50)
    when 'lueur'     then atelier_serie(p_uid) >= coalesce((r ->> 'lueur_jours')::int, 7)
    when 'nuit'      then atelier_serie(p_uid) >= coalesce((r ->> 'nuit_jours')::int, 14)
    when 'postale'   then atelier_communes(p_uid) >= coalesce((r ->> 'postale_communes')::int, 200)
    when 'etat'      then atelier_departements(p_uid) >= coalesce((r ->> 'etat_departements')::int, 1)
    when 'tricolore' then atelier_departements(p_uid) >= coalesce((r ->> 'tricolore_departements')::int, 3)
    else false end;
end;
$f$;
-- gagné : noté une fois, ou rempli aujourd'hui
create or replace function public.atelier_gagne(p_uid uuid, p_element text)
 returns boolean language plpgsql stable security definer set search_path to 'public'
as $f$
begin
  if exists(select 1 from atelier_debloques d where d.joueur_id = p_uid and d.element = p_element) then return true; end if;
  return atelier_condition(p_uid, p_element);
end;
$f$;
-- noter ce qui vient d'être gagné (appelé quand le joueur ouvre l'atelier ou enregistre)
create or replace function public.atelier_noter(p_uid uuid)
 returns void language plpgsql security definer set search_path to 'public'
as $f$
declare e text;
begin
  foreach e in array array['encre', 'lueur', 'nuit', 'postale', 'etat', 'tricolore'] loop
    if not exists(select 1 from atelier_debloques d where d.joueur_id = p_uid and d.element = e)
       and atelier_condition(p_uid, e) then
      insert into atelier_debloques(joueur_id, element) values (p_uid, e) on conflict do nothing;
    end if;
  end loop;
end;
$f$;

-- posséder un élément (remplace la version de s2-64)
create or replace function public.atelier_possede(p_uid uuid, p_famille text, p_id text)
 returns boolean language plpgsql stable security definer set search_path to 'public'
as $f$
begin
  if p_uid is null then return false; end if;
  if (p_famille, p_id) in (('finition', 'aucune'), ('halo', 'aucun'), ('style', 'classique'), ('bordure', 'rarete')) then return true; end if;
  if (p_famille, p_id) in (('finition', 'encre'), ('halo', 'lueur'), ('style', 'postale'), ('style', 'etat'), ('bordure', 'nuit'), ('bordure', 'tricolore')) then
    return atelier_gagne(p_uid, p_id);
  end if;
  if (p_famille, p_id) in (('finition', 'chrome'), ('finition', 'cristal'), ('finition', 'or'), ('halo', 'etoiles'), ('halo', 'braises'), ('bordure', 'doree')) then
    return exists(select 1 from euros_inventaire i where i.joueur_id = p_uid and i.article_id = 'atelier-' || p_id);
  end if;
  return false;
end;
$f$;

-- une composition, réduite à ce qui est encore possédé
create or replace function public.atelier_filtrer(p_uid uuid, p jsonb)
 returns jsonb language sql stable security definer set search_path to 'public'
as $f$
  select case when p is null then null else jsonb_build_object(
    'finition', case when atelier_possede(p_uid, 'finition', coalesce(p ->> 'finition', 'aucune')) then coalesce(p ->> 'finition', 'aucune') else 'aucune' end,
    'halo',     case when atelier_possede(p_uid, 'halo', coalesce(p ->> 'halo', 'aucun')) then coalesce(p ->> 'halo', 'aucun') else 'aucun' end,
    'couleur',  case when coalesce(p ->> 'couleur', 'or') in ('or', 'ciel', 'corail', 'vert', 'mauve') then coalesce(p ->> 'couleur', 'or') else 'or' end,
    'style',    case when atelier_possede(p_uid, 'style', coalesce(p ->> 'style', 'classique')) then coalesce(p ->> 'style', 'classique') else 'classique' end,
    'bordure',  case when atelier_possede(p_uid, 'bordure', coalesce(p ->> 'bordure', 'rarete')) then coalesce(p ->> 'bordure', 'rarete') else 'rarete' end) end
$f$;

-- la composition qui se voit (remplace la version de s2-64)
create or replace function public.atelier_vue(p_uid uuid)
 returns jsonb language sql stable security definer set search_path to 'public'
as $f$
  select atelier_filtrer(p_uid, jsonb_build_object('finition', c.finition, 'halo', c.halo, 'couleur', c.couleur, 'style', c.style, 'bordure', c.bordure))
         || jsonb_build_object('mode', c.mode)
    from atelier_compositions c where c.joueur_id = p_uid
$f$;

-- les réglages carte par carte d'un joueur (p_codes null = toutes)
create or replace function public.atelier_cartes_de(p_uid uuid, p_codes text[])
 returns jsonb language sql stable security definer set search_path to 'public'
as $f$
  select coalesce(jsonb_object_agg(a.commune_code, jsonb_build_object('e', a.exclue, 'c', a.choisie, 'p', atelier_filtrer(p_uid, a.propre))), '{}'::jsonb)
    from atelier_cartes a
   where a.joueur_id = p_uid and (p_codes is null or a.commune_code = any(p_codes))
$f$;

-- 5. Ce que voit le joueur (remplace la version de s2-64) ---------------------------------
create or replace function public.atelier_etat()
 returns jsonb language plpgsql volatile security definer set search_path to 'public'
as $f$
declare
  v_uid uuid := auth.uid();
  r jsonb := atelier_reglages();
  v_inv text[];
  v_deb text[];
begin
  if v_uid is null then raise exception 'Non connecte'; end if;
  perform atelier_noter(v_uid);
  select coalesce(array_agg(i.article_id), '{}') into v_inv
    from euros_inventaire i where i.joueur_id = v_uid and i.article_id like 'atelier-%';
  select coalesce(array_agg(d.element), '{}') into v_deb from atelier_debloques d where d.joueur_id = v_uid;
  return jsonb_build_object(
    'ouvert', atelier_ouvert(),
    'v2', true,
    'composition', coalesce(atelier_vue(v_uid),
      '{"finition": "aucune", "halo": "aucun", "couleur": "or", "style": "classique", "bordure": "rarete", "mode": "toutes"}'::jsonb),
    'cartes', atelier_cartes_de(v_uid, null),
    'encre_quetes', coalesce((r ->> 'encre_quetes')::int, 50),
    'lueur_jours', coalesce((r ->> 'lueur_jours')::int, 7),
    'nuit_jours', coalesce((r ->> 'nuit_jours')::int, 14),
    'postale_communes', coalesce((r ->> 'postale_communes')::int, 200),
    'etat_departements', coalesce((r ->> 'etat_departements')::int, 1),
    'tricolore_departements', coalesce((r ->> 'tricolore_departements')::int, 3),
    'quetes', atelier_quetes(v_uid),
    'serie', atelier_serie(v_uid),
    'communes', atelier_communes(v_uid),
    'departements', atelier_departements(v_uid),
    'possede', jsonb_build_object(
      'encre', 'encre' = any(v_deb), 'lueur', 'lueur' = any(v_deb), 'nuit', 'nuit' = any(v_deb),
      'postale', 'postale' = any(v_deb), 'etat', 'etat' = any(v_deb), 'tricolore', 'tricolore' = any(v_deb),
      'chrome',  'atelier-chrome'  = any(v_inv), 'cristal', 'atelier-cristal' = any(v_inv), 'or', 'atelier-or' = any(v_inv),
      'etoiles', 'atelier-etoiles' = any(v_inv), 'braises', 'atelier-braises' = any(v_inv), 'doree', 'atelier-doree' = any(v_inv)));
end;
$f$;

-- enregistrer sa composition et son mode
create or replace function public.atelier_enregistrer(p_finition text, p_halo text, p_couleur text, p_style text, p_bordure text, p_mode text)
 returns jsonb language plpgsql security definer set search_path to 'public'
as $f$
declare
  v_uid uuid := auth.uid();
  v_f text := coalesce(nullif(p_finition, ''), 'aucune');
  v_h text := coalesce(nullif(p_halo, ''), 'aucun');
  v_c text := coalesce(nullif(p_couleur, ''), 'or');
  v_s text := coalesce(nullif(p_style, ''), 'classique');
  v_b text := coalesce(nullif(p_bordure, ''), 'rarete');
  v_m text := coalesce(nullif(p_mode, ''), 'toutes');
begin
  if v_uid is null then raise exception 'Non connecte'; end if;
  if not atelier_ouvert() then raise exception 'L''atelier n''est pas encore ouvert'; end if;
  if v_f not in ('aucune', 'encre', 'chrome', 'cristal', 'or') or v_h not in ('aucun', 'lueur', 'etoiles', 'braises')
     or v_c not in ('or', 'ciel', 'corail', 'vert', 'mauve') or v_s not in ('classique', 'postale', 'etat')
     or v_b not in ('rarete', 'nuit', 'tricolore', 'doree') or v_m not in ('toutes', 'choisies') then
    raise exception 'Choix invalide';
  end if;
  perform atelier_noter(v_uid);
  if not atelier_possede(v_uid, 'finition', v_f) then raise exception 'Tu n''as pas encore cette finition'; end if;
  if not atelier_possede(v_uid, 'halo', v_h) then raise exception 'Tu n''as pas encore ce halo'; end if;
  if not atelier_possede(v_uid, 'style', v_s) then raise exception 'Tu n''as pas encore ce style'; end if;
  if not atelier_possede(v_uid, 'bordure', v_b) then raise exception 'Tu n''as pas encore cette bordure'; end if;
  insert into atelier_compositions(joueur_id, finition, halo, couleur, style, bordure, mode)
  values (v_uid, v_f, v_h, v_c, v_s, v_b, v_m)
  on conflict (joueur_id) do update
    set finition = excluded.finition, halo = excluded.halo, couleur = excluded.couleur,
        style = excluded.style, bordure = excluded.bordure, mode = excluded.mode, modifie_le = now();
  return atelier_etat();
end;
$f$;
-- l'ancienne forme (jeu pas encore rechargé) : garde le style, la bordure et le mode
create or replace function public.atelier_enregistrer(p_finition text, p_halo text, p_couleur text)
 returns jsonb language plpgsql security definer set search_path to 'public'
as $f$
declare c atelier_compositions%rowtype;
begin
  select * into c from atelier_compositions where joueur_id = auth.uid();
  return atelier_enregistrer(p_finition, p_halo, p_couleur, coalesce(c.style, 'classique'), coalesce(c.bordure, 'rarete'), coalesce(c.mode, 'toutes'));
end;
$f$;

-- exclure (mode « toutes ») ou choisir (mode « choisies ») des cartes, par lots
create or replace function public.atelier_cartes_definir(p_champ text, p_oui text[], p_non text[])
 returns jsonb language plpgsql security definer set search_path to 'public'
as $f$
declare
  v_uid uuid := auth.uid();
  v_oui text[] := coalesce(p_oui, '{}');
  v_non text[] := coalesce(p_non, '{}');
begin
  if v_uid is null then raise exception 'Non connecte'; end if;
  if not atelier_ouvert() then raise exception 'L''atelier n''est pas encore ouvert'; end if;
  if p_champ not in ('exclue', 'choisie') then raise exception 'Choix invalide'; end if;
  if cardinality(v_oui) + cardinality(v_non) > 5000 then raise exception 'Trop de cartes d''un coup'; end if;
  if p_champ = 'exclue' then
    insert into atelier_cartes(joueur_id, commune_code, exclue)
    select v_uid, x, true from (select distinct x from unnest(v_oui) x) s
    on conflict (joueur_id, commune_code) do update set exclue = true, modifie_le = now();
    update atelier_cartes set exclue = false, modifie_le = now() where joueur_id = v_uid and commune_code = any(v_non);
  else
    insert into atelier_cartes(joueur_id, commune_code, choisie)
    select v_uid, x, true from (select distinct x from unnest(v_oui) x) s
    on conflict (joueur_id, commune_code) do update set choisie = true, modifie_le = now();
    update atelier_cartes set choisie = false, modifie_le = now() where joueur_id = v_uid and commune_code = any(v_non);
  end if;
  delete from atelier_cartes where joueur_id = v_uid and not exclue and not choisie and propre is null;
  return atelier_cartes_de(v_uid, null);
end;
$f$;

-- la composition propre à une carte, depuis sa fiche ; null = elle suit l'atelier
create or replace function public.atelier_carte_propre(p_code text, p_propre jsonb)
 returns jsonb language plpgsql security definer set search_path to 'public'
as $f$
declare
  v_uid uuid := auth.uid();
  v_p jsonb;
begin
  if v_uid is null then raise exception 'Non connecte'; end if;
  if not atelier_ouvert() then raise exception 'L''atelier n''est pas encore ouvert'; end if;
  if p_propre is null then
    update atelier_cartes set propre = null, modifie_le = now() where joueur_id = v_uid and commune_code = p_code;
    delete from atelier_cartes where joueur_id = v_uid and commune_code = p_code and not exclue and not choisie;
    return atelier_cartes_de(v_uid, array[p_code]);
  end if;
  if not exists(select 1 from terra_collection t where t.joueur_id = v_uid and t.commune_code = p_code and t.exemplaires > 0) then
    raise exception 'Tu ne possèdes pas cette carte';
  end if;
  perform atelier_noter(v_uid);
  v_p := atelier_filtrer(v_uid, p_propre);
  if v_p is distinct from jsonb_build_object(
       'finition', coalesce(p_propre ->> 'finition', 'aucune'), 'halo', coalesce(p_propre ->> 'halo', 'aucun'),
       'couleur', coalesce(p_propre ->> 'couleur', 'or'), 'style', coalesce(p_propre ->> 'style', 'classique'),
       'bordure', coalesce(p_propre ->> 'bordure', 'rarete')) then
    raise exception 'Tu n''as pas encore cet element';
  end if;
  insert into atelier_cartes(joueur_id, commune_code, propre) values (v_uid, p_code, v_p)
  on conflict (joueur_id, commune_code) do update set propre = excluded.propre, modifie_le = now();
  return atelier_cartes_de(v_uid, array[p_code]);
end;
$f$;

-- la composition d'un autre joueur, avec les réglages des cartes de sa vitrine (remplace s2-64)
create or replace function public.atelier_composition(p_joueur uuid)
 returns jsonb language plpgsql stable security definer set search_path to 'public'
as $f$
declare v jsonb;
begin
  if auth.uid() is null then raise exception 'Non connecte'; end if;
  if p_joueur is null or not atelier_ouvert() then return null; end if;
  v := coalesce(atelier_vue(p_joueur),
    '{"finition": "aucune", "halo": "aucun", "couleur": "or", "style": "classique", "bordure": "rarete", "mode": "toutes"}'::jsonb);
  return v || jsonb_build_object('cartes', atelier_cartes_de(p_joueur,
    (select coalesce(array_agg(t.commune_code), '{}') from terra_vitrine t where t.joueur_id = p_joueur and t.source = 'terra')));
end;
$f$;

-- 6. Les droits ------------------------------------------------------------------------------
revoke all on function public.atelier_communes(uuid)                     from public, anon, authenticated;
revoke all on function public.atelier_departements(uuid)                 from public, anon, authenticated;
revoke all on function public.atelier_condition(uuid, text)              from public, anon, authenticated;
revoke all on function public.atelier_gagne(uuid, text)                  from public, anon, authenticated;
revoke all on function public.atelier_noter(uuid)                        from public, anon, authenticated;
revoke all on function public.atelier_possede(uuid, text, text)          from public, anon, authenticated;
revoke all on function public.atelier_filtrer(uuid, jsonb)               from public, anon, authenticated;
revoke all on function public.atelier_vue(uuid)                          from public, anon, authenticated;
revoke all on function public.atelier_cartes_de(uuid, text[])            from public, anon, authenticated;
revoke all on function public.atelier_etat()                                              from public, anon;
revoke all on function public.atelier_enregistrer(text, text, text)                       from public, anon;
revoke all on function public.atelier_enregistrer(text, text, text, text, text, text)     from public, anon;
revoke all on function public.atelier_cartes_definir(text, text[], text[])                from public, anon;
revoke all on function public.atelier_carte_propre(text, jsonb)                           from public, anon;
revoke all on function public.atelier_composition(uuid)                                   from public, anon;
grant execute on function public.atelier_etat()                                           to authenticated;
grant execute on function public.atelier_enregistrer(text, text, text)                    to authenticated;
grant execute on function public.atelier_enregistrer(text, text, text, text, text, text)  to authenticated;
grant execute on function public.atelier_cartes_definir(text, text[], text[])             to authenticated;
grant execute on function public.atelier_carte_propre(text, jsonb)                        to authenticated;
grant execute on function public.atelier_composition(uuid)                                to authenticated;

commit;

-- ---------- contrôle : attendu  true | 1 | true | true | true | false ----------
-- réglages V2 ; la Dorée en vente ; tables ; fonctions du joueur ; interne fermé ; anon_doit_etre_false
select (public.atelier_reglages() ? 'nuit_jours')                                        as reglages_v2,
       (select count(*) from public.euros_articles where id = 'atelier-doree' and actif) as doree,
       to_regclass('public.atelier_cartes') is not null and to_regclass('public.atelier_debloques') is not null as tables_ok,
       has_function_privilege('authenticated', 'public.atelier_cartes_definir(text,text[],text[])', 'execute')
         and has_function_privilege('authenticated', 'public.atelier_carte_propre(text,jsonb)', 'execute')
         and has_function_privilege('authenticated', 'public.atelier_enregistrer(text,text,text,text,text,text)', 'execute') as droits,
       not has_function_privilege('authenticated', 'public.atelier_condition(uuid,text)', 'execute') as interne_ferme,
       has_function_privilege('anon', 'public.atelier_etat()', 'execute')                as anon_doit_etre_false;
