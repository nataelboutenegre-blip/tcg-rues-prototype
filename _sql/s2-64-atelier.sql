-- ===========================================================================
--  s2-64 — L'atelier des cartes, V1 : finitions et halos (patch270)
--  (aperçus validés : canevas « Atelier des cartes TerraFront » le 21/10,
--  puis Chrome et Cristal le 29/10 « C'est parfait », et l'achat depuis
--  l'atelier « c'est parfait »)
--
--  À LANCER AU MOMENT DE L'ANNONCE : le code est déjà en ligne mais reste
--  caché tant que atelier_etat() n'existe pas.
--
--  Ce que ça allume (Terra seulement, jamais le Front) :
--    - une COMPOSITION par joueur, posée sur toutes ses cartes Terra : une
--      finition et un halo (avec sa couleur : or pâle, ciel, corail,
--      tilleul, mauve) ;
--    - FINITIONS : Encre (50 quêtes du jour réclamées), Chrome et Cristal
--      (2,99 € chacune) ; Or est montré « bientôt » (pas dans le pass de
--      la saison 2) ;
--    - HALOS : Lueur (une quête du jour réclamée 7 jours d'affilée),
--      Étoiles et Braises (1,99 € chacun) ;
--    - ce qui se gagne est gardé à vie (meilleure série, total de quêtes) ;
--    - les 4 objets payants sont des articles de la boutique en euros
--      (type « effet ») : même fiche d'achat, mêmes fonctions de paiement
--      que les dos et les skins, rien à redéployer côté Stripe ;
--    - les testeurs les reçoivent en cadeau (comme les skins) ;
--    - le serveur vérifie tout : on n'enregistre que ce qu'on possède, et
--      une vitrine ne montre que ce qui est encore possédé (un achat
--      remboursé disparaît tout seul).
--  Côté jeu : une brillante ou un éclat garde sa propre lumière ; une
--  carte qui porte un skin garde son skin (seul le halo s'ajoute).
--
--  Réglages (config_jeu 'atelier') : ouvert (1/0), encre_quetes (50),
--  lueur_jours (7).
--  Pour couper (plus rien ne s'affiche, plus de vente ; les achats restent) :
--  s2-64-atelier-couper.sql
--  Rejouable. Contrôle attendu : 1 | 4 | true | true | true | false
--  (+ « offerts » = 4 par compte testeur)
-- ===========================================================================
begin;

-- 1. Le réglage -------------------------------------------------------------------
insert into public.config_jeu (cle, valeur)
values ('atelier', '{"ouvert": 1, "encre_quetes": 50, "lueur_jours": 7}')
on conflict (cle) do update set valeur = excluded.valeur;

create or replace function public.atelier_reglages()
 returns jsonb language sql stable security definer set search_path to 'public'
as $f$
  select coalesce((select c.valeur::jsonb from config_jeu c where c.cle = 'atelier'), '{}'::jsonb)
$f$;
create or replace function public.atelier_ouvert()
 returns boolean language sql stable security definer set search_path to 'public'
as $f$
  select coalesce((atelier_reglages() ->> 'ouvert')::int, 0) = 1
$f$;

-- 2. Les 4 objets en vente (type « effet » : déjà prévu par la boutique) ----------
--    rejouable : ne réécrit pas un prix changé à la main, remet en vente après une coupure
insert into public.euros_articles(id, type, nom, description, prix_centimes, reserve_og, actif, ordre) values
  ('atelier-chrome',  'effet', 'Finition Chrome',  'L''argent poli : deux reflets francs qui glissent sur la carte',      299, false, true, 400),
  ('atelier-cristal', 'effet', 'Finition Cristal', 'Des facettes taillées, teintées de la rareté, et des éclats blancs',  299, false, true, 410),
  ('atelier-etoiles', 'effet', 'Halo Étoiles',     'Des étoiles jaillissent autour de la carte',                         199, false, true, 420),
  ('atelier-braises', 'effet', 'Halo Braises',     'Des braises montent autour de la carte',                             199, false, true, 430)
on conflict (id) do update set actif = true;

-- les testeurs les reçoivent en cadeau (sans commande), comme les skins
insert into public.euros_inventaire(joueur_id, article_id, commande_id)
select t.id::uuid, a.id, null
  from jsonb_array_elements_text(coalesce(public.euros_reglage('testeurs'), '[]'::jsonb)) as t(id)
  cross join public.euros_articles a
 where a.id in ('atelier-chrome', 'atelier-cristal', 'atelier-etoiles', 'atelier-braises')
on conflict (joueur_id, article_id) do nothing;

-- 3. La composition de chaque joueur ------------------------------------------------
create table if not exists public.atelier_compositions(
  joueur_id  uuid primary key references public.joueurs(id) on delete cascade,
  finition   text not null default 'aucune' check (finition in ('aucune', 'encre', 'chrome', 'cristal', 'or')),
  halo       text not null default 'aucun'  check (halo in ('aucun', 'lueur', 'etoiles', 'braises')),
  couleur    text not null default 'or'     check (couleur in ('or', 'ciel', 'corail', 'vert', 'mauve')),
  modifie_le timestamptz not null default now()
);
alter table public.atelier_compositions enable row level security;
revoke all on public.atelier_compositions from public, anon, authenticated;

-- 4. Ce qui se gagne -----------------------------------------------------------------
-- les quêtes du jour réclamées (les quêtes uniques ont le jour 2000-01-01)
create or replace function public.atelier_quetes(p_uid uuid)
 returns integer language sql stable security definer set search_path to 'public'
as $f$
  select count(*)::integer from quetes_reclamees r
   where r.joueur_id = p_uid and r.jour <> date '2000-01-01'
$f$;
-- la plus longue série de jours d'affilée avec au moins une quête du jour réclamée
create or replace function public.atelier_serie(p_uid uuid)
 returns integer language sql stable security definer set search_path to 'public'
as $f$
  select coalesce(max(n), 0)::integer from (
    select count(*) as n from (
      select d.jour, d.jour - (row_number() over (order by d.jour))::integer as ilot
        from (select distinct r.jour from quetes_reclamees r
               where r.joueur_id = p_uid and r.jour <> date '2000-01-01') d
    ) x group by x.ilot
  ) y
$f$;

-- posséder un élément : 'aucune' / 'aucun' toujours ; Encre et Lueur se gagnent ;
-- le reste est un objet de la boutique en euros (Or : plus tard, par un pass)
create or replace function public.atelier_possede(p_uid uuid, p_famille text, p_id text)
 returns boolean language plpgsql stable security definer set search_path to 'public'
as $f$
declare r jsonb := atelier_reglages();
begin
  if p_uid is null then return false; end if;
  if p_famille = 'finition' then
    if p_id = 'aucune' then return true; end if;
    if p_id = 'encre' then return atelier_quetes(p_uid) >= coalesce((r ->> 'encre_quetes')::int, 50); end if;
    if p_id not in ('chrome', 'cristal', 'or') then return false; end if;
  elsif p_famille = 'halo' then
    if p_id = 'aucun' then return true; end if;
    if p_id = 'lueur' then return atelier_serie(p_uid) >= coalesce((r ->> 'lueur_jours')::int, 7); end if;
    if p_id not in ('etoiles', 'braises') then return false; end if;
  else
    return false;
  end if;
  return exists(select 1 from euros_inventaire i where i.joueur_id = p_uid and i.article_id = 'atelier-' || p_id);
end;
$f$;

-- la composition qui se voit : seulement ce qui est encore possédé
create or replace function public.atelier_vue(p_uid uuid)
 returns jsonb language sql stable security definer set search_path to 'public'
as $f$
  select jsonb_build_object(
           'finition', case when atelier_possede(p_uid, 'finition', c.finition) then c.finition else 'aucune' end,
           'halo',     case when atelier_possede(p_uid, 'halo', c.halo) then c.halo else 'aucun' end,
           'couleur',  c.couleur)
    from atelier_compositions c where c.joueur_id = p_uid
$f$;

-- 5. Ce que voit le joueur ------------------------------------------------------------
create or replace function public.atelier_etat()
 returns jsonb language plpgsql stable security definer set search_path to 'public'
as $f$
declare
  v_uid uuid := auth.uid();
  r jsonb := atelier_reglages();
  v_q integer;
  v_s integer;
  v_inv text[];
begin
  if v_uid is null then raise exception 'Non connecte'; end if;
  v_q := atelier_quetes(v_uid);
  v_s := atelier_serie(v_uid);
  select coalesce(array_agg(i.article_id), '{}') into v_inv
    from euros_inventaire i where i.joueur_id = v_uid and i.article_id like 'atelier-%';
  return jsonb_build_object(
    'ouvert', atelier_ouvert(),
    'composition', coalesce(atelier_vue(v_uid), '{"finition": "aucune", "halo": "aucun", "couleur": "or"}'::jsonb),
    'encre_quetes', coalesce((r ->> 'encre_quetes')::int, 50),
    'lueur_jours', coalesce((r ->> 'lueur_jours')::int, 7),
    'quetes', v_q,
    'serie', v_s,
    'possede', jsonb_build_object(
      'encre',   v_q >= coalesce((r ->> 'encre_quetes')::int, 50),
      'lueur',   v_s >= coalesce((r ->> 'lueur_jours')::int, 7),
      'chrome',  'atelier-chrome'  = any(v_inv),
      'cristal', 'atelier-cristal' = any(v_inv),
      'or',      'atelier-or'      = any(v_inv),
      'etoiles', 'atelier-etoiles' = any(v_inv),
      'braises', 'atelier-braises' = any(v_inv)));
end;
$f$;

-- enregistrer sa composition (posée sur toutes ses cartes Terra)
create or replace function public.atelier_enregistrer(p_finition text, p_halo text, p_couleur text)
 returns jsonb language plpgsql security definer set search_path to 'public'
as $f$
declare
  v_uid uuid := auth.uid();
  v_f text := coalesce(nullif(p_finition, ''), 'aucune');
  v_h text := coalesce(nullif(p_halo, ''), 'aucun');
  v_c text := coalesce(nullif(p_couleur, ''), 'or');
begin
  if v_uid is null then raise exception 'Non connecte'; end if;
  if not atelier_ouvert() then raise exception 'L''atelier n''est pas encore ouvert'; end if;
  if v_f not in ('aucune', 'encre', 'chrome', 'cristal', 'or')
     or v_h not in ('aucun', 'lueur', 'etoiles', 'braises')
     or v_c not in ('or', 'ciel', 'corail', 'vert', 'mauve') then
    raise exception 'Choix invalide';
  end if;
  if not atelier_possede(v_uid, 'finition', v_f) then raise exception 'Tu n''as pas encore cette finition'; end if;
  if not atelier_possede(v_uid, 'halo', v_h) then raise exception 'Tu n''as pas encore ce halo'; end if;
  insert into atelier_compositions(joueur_id, finition, halo, couleur)
  values (v_uid, v_f, v_h, v_c)
  on conflict (joueur_id) do update
    set finition = excluded.finition, halo = excluded.halo, couleur = excluded.couleur, modifie_le = now();
  return atelier_etat();
end;
$f$;

-- la composition d'un autre joueur (pour sa vitrine) ; null = rien de posé
create or replace function public.atelier_composition(p_joueur uuid)
 returns jsonb language plpgsql stable security definer set search_path to 'public'
as $f$
begin
  if auth.uid() is null then raise exception 'Non connecte'; end if;
  if p_joueur is null or not atelier_ouvert() then return null; end if;
  return atelier_vue(p_joueur);
end;
$f$;

-- 6. Les droits -----------------------------------------------------------------------
revoke all on function public.atelier_reglages()                         from public, anon, authenticated;
revoke all on function public.atelier_ouvert()                           from public, anon, authenticated;
revoke all on function public.atelier_quetes(uuid)                       from public, anon, authenticated;
revoke all on function public.atelier_serie(uuid)                        from public, anon, authenticated;
revoke all on function public.atelier_possede(uuid, text, text)          from public, anon, authenticated;
revoke all on function public.atelier_vue(uuid)                          from public, anon, authenticated;
revoke all on function public.atelier_etat()                             from public, anon;
revoke all on function public.atelier_enregistrer(text, text, text)      from public, anon;
revoke all on function public.atelier_composition(uuid)                  from public, anon;
grant execute on function public.atelier_etat()                          to authenticated;
grant execute on function public.atelier_enregistrer(text, text, text)   to authenticated;
grant execute on function public.atelier_composition(uuid)               to authenticated;

commit;

-- ---------- contrôle : attendu  1 | 4 | true | true | true | false ----------
-- ouvert ; articles en vente ; table ; fonctions du joueur ; un réglage interne
-- fermé aux joueurs ; anon_doit_etre_false. « offerts » : 4 par compte testeur.
select coalesce((public.atelier_reglages() ->> 'ouvert')::int, 0)                         as ouvert,
       (select count(*) from public.euros_articles
         where id like 'atelier-%' and type = 'effet' and actif)                          as articles,
       to_regclass('public.atelier_compositions') is not null                             as table_ok,
       has_function_privilege('authenticated', 'public.atelier_etat()', 'execute')
         and has_function_privilege('authenticated', 'public.atelier_enregistrer(text,text,text)', 'execute')
         and has_function_privilege('authenticated', 'public.atelier_composition(uuid)', 'execute') as droits,
       not has_function_privilege('authenticated', 'public.atelier_possede(uuid,text,text)', 'execute') as interne_ferme,
       has_function_privilege('anon', 'public.atelier_etat()', 'execute')                 as anon_doit_etre_false,
       (select count(*) from public.euros_inventaire
         where article_id like 'atelier-%' and commande_id is null)                       as offerts;
