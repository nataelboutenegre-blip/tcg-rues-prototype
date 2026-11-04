-- ===========================================================================
--  TerraFront — s2-98 : la roue du Front (4/11/2026)
--  Décidé avec Nataël le 4/11. La réserve d'accueil est atteinte : les
--  comptes de plus de 7 jours ne peuvent plus ouvrir de paquet du Front.
--  À la place, la roue : un tour par jeton de paquet (les MÊMES jetons :
--  1 toutes les 20 min, 3 en réserve), 15 tours par jour au plus. Gratuite,
--  jamais payante. Elle donne de l'énergie, des lingots, parfois un paquet
--  Terra. Les joueurs de moins de 7 jours gardent leurs paquets.
--
--  1. config_jeu 'roue_front' : ouvert, par_jour (15) et les 8 cases
--     (poids = chance en %, énergie, lingots, paquets Terra). Se règle sans
--     toucher au code (exemples en bas du fichier).
--  2. config_jeu 'reserve_accueil' : seuil porté à 1 000 000 de communes.
--     Décidé le 4/11 : une fois déclenchée, la réserve reste jusqu'à la fin
--     de la saison 2. Sinon elle s'ouvrirait et se fermerait au gré des
--     communes libérées (inactivité dès le 18/11), et les paquets des anciens
--     apparaîtraient puis disparaîtraient plusieurs fois par jour.
--  3. Table roue_front_tours : un tour = une ligne (compte du jour, historique).
--  4. front_energie_reglage(cle) : identique à celle du lot du 8/11
--     (s2-lot-5), créée dès maintenant pour que la roue suive le plafond
--     des bonus : 60 aujourd'hui, 100 après le lot. Le lot la remplacera
--     à l'identique, sans conflit.
--  5. roue_front_ouverte(uid) : la roue est pour ce joueur s'il est bloqué
--     par la réserve, ou si le pot est vide (plus personne n'a de paquet).
--  6. roue_front_etat() : ce que le jeu affiche (tours dispo, tours du jour,
--     cases et chances).
--  7. roue_front_tourner() : un tour. Le serveur tire la case et crédite ;
--     le jeu ne fait qu'animer la roue jusqu'à elle (rien à tricher côté
--     téléphone). Énergie jusqu'au plafond des bonus, lingots jusqu'à la
--     réserve de la Fonderie (30, ou 45 avec deux) : au-delà, rien n'entre,
--     et le jeu le dit.
--  Ne modifie aucune fonction existante. Rejouable.
--  Contrôle attendu : true | true | true | 15 | 8 | 100 | 1000000 | 0
-- ===========================================================================
begin;

-- 1. le réglage de la roue ---------------------------------------------------
insert into public.config_jeu (cle, valeur)
values ('roue_front', '{"ouvert": 1, "par_jour": 15, "cases": [
  {"id": "petit",   "nom": "Petit éclair", "poids": 27, "energie": 3,  "lingots": 0, "terra": 0},
  {"id": "lingots", "nom": "Lingots",      "poids": 20, "energie": 0,  "lingots": 2, "terra": 0},
  {"id": "eclair",  "nom": "Éclair",       "poids": 20, "energie": 5,  "lingots": 0, "terra": 0},
  {"id": "mixte",   "nom": "Mixte",        "poids": 15, "energie": 3,  "lingots": 1, "terra": 0},
  {"id": "gros",    "nom": "Gros éclair",  "poids": 8,  "energie": 10, "lingots": 0, "terra": 0},
  {"id": "coffre",  "nom": "Coffre",       "poids": 5,  "energie": 0,  "lingots": 4, "terra": 0},
  {"id": "terra",   "nom": "Paquet Terra", "poids": 3,  "energie": 0,  "lingots": 0, "terra": 1},
  {"id": "jackpot", "nom": "Jackpot",      "poids": 2,  "energie": 12, "lingots": 5, "terra": 0}]}')
on conflict (cle) do nothing;

-- 2. la réserve d'accueil reste en place jusqu'à la fin de la saison 2 ------
update public.config_jeu set valeur = (valeur::jsonb || '{"communes": 1000000}'::jsonb)
 where cle = 'reserve_accueil';

-- 3. les tours ---------------------------------------------------------------
create table if not exists public.roue_front_tours (
  id         bigint generated always as identity primary key,
  joueur_id  uuid not null references public.joueurs(id) on delete cascade,
  jour       date not null,                  -- jour de Paris
  case_id    text not null,
  energie    integer not null default 0,     -- réellement entrée
  lingots    integer not null default 0,     -- réellement entrés
  terra      integer not null default 0,
  le         timestamptz not null default now()
);
create index if not exists roue_front_tours_joueur_jour on public.roue_front_tours (joueur_id, jour);
alter table public.roue_front_tours enable row level security;
revoke all on public.roue_front_tours from public, anon, authenticated;

-- 4. le plafond des bonus d'énergie (identique au lot du 8/11) ---------------
create or replace function public.front_energie_reglage(p_cle text)
 returns numeric
 language sql
 stable security definer
 set search_path to 'public'
as $f$
  -- s2-lot5 : réglage de l'énergie du Front (valeurs d'avant le lot si absent)
  select coalesce(
    (select (c.valeur::jsonb ->> p_cle)::numeric from config_jeu c where c.cle = 'energie_front'),
    case p_cle when 'recharge_s' then 600 when 'max' then 50 when 'plafond' then 60 end);
$f$;
revoke all on function public.front_energie_reglage(text) from public, anon, authenticated;

-- 5. pour qui est la roue ----------------------------------------------------
create or replace function public.roue_front_ouverte(p_uid uuid)
 returns boolean language plpgsql stable security definer set search_path to 'public' as $f$
declare
  cfg jsonb := coalesce((select c.valeur::jsonb from config_jeu c where c.cle = 'roue_front'), '{}'::jsonb);
begin
  /* s2-98 */
  if p_uid is null or coalesce((cfg->>'ouvert')::int, 0) <> 1 then return false; end if;
  if reserve_accueil_bloque(p_uid) then return true; end if;
  /* pot vide : plus personne n'a de paquet à ouvrir, la roue est pour tous */
  return not exists (select 1 from communes c where not exists (select 1 from possessions po where po.commune_code = c.code));
end; $f$;
revoke all on function public.roue_front_ouverte(uuid) from public, anon, authenticated;

-- 6. ce que le jeu affiche ---------------------------------------------------
create or replace function public.roue_front_etat()
 returns jsonb language plpgsql stable security definer set search_path to 'public' as $f$
declare
  v_uid uuid := auth.uid();
  cfg   jsonb := coalesce((select c.valeur::jsonb from config_jeu c where c.cle = 'roue_front'), '{}'::jsonb);
  v_j   numeric;
  v_maj timestamptz;
  v_n   integer;
begin
  /* s2-98 */
  if v_uid is null then raise exception 'Non connecté'; end if;
  select coalesce(j.jetons_gratuits, 0), coalesce(j.jetons_maj, now()) into v_j, v_maj from joueurs j where j.id = v_uid;
  if not found then raise exception 'Joueur introuvable'; end if;
  /* les mêmes jetons que les paquets : 1 toutes les 20 min, 3 en réserve (un cadeau au-dessus de 3 est gardé) */
  if v_j < 3 then v_j := least(3, v_j + extract(epoch from (now() - v_maj)) / 1200.0); end if;
  select count(*) into v_n from roue_front_tours t
   where t.joueur_id = v_uid and t.jour = (now() at time zone 'Europe/Paris')::date;
  return jsonb_build_object(
    'ouverte',  roue_front_ouverte(v_uid),
    'jetons',   round(v_j, 4),
    'tours_jour', v_n,
    'par_jour', coalesce((cfg->>'par_jour')::int, 15),
    'cases',    coalesce(cfg->'cases', '[]'::jsonb));
end; $f$;
revoke all on function public.roue_front_etat() from public, anon;
grant execute on function public.roue_front_etat() to authenticated;

-- 7. un tour -----------------------------------------------------------------
create or replace function public.roue_front_tourner()
 returns jsonb language plpgsql volatile security definer set search_path to 'public' as $f$
declare
  v_uid    uuid := auth.uid();
  cfg      jsonb := coalesce((select c.valeur::jsonb from config_jeu c where c.cle = 'roue_front'), '{}'::jsonb);
  v_jour   date := (now() at time zone 'Europe/Paris')::date;
  v_par    integer := coalesce((cfg->>'par_jour')::int, 15);
  j        record;
  v_jet    numeric;
  v_n      integer;
  v_total  numeric;
  v_tir    numeric;
  v_acc    numeric := 0;
  r        record;
  v_case   jsonb;
  v_e      numeric;  v_e_reel integer := 0;
  v_l      numeric;  v_l_reel integer := 0;
  v_t      integer;
  v        numeric;
  v_nouv   numeric;
begin
  /* s2-98 */
  if v_uid is null then raise exception 'Non connecté'; end if;
  if not roue_front_ouverte(v_uid) then
    raise exception 'La roue du Front n''est pas pour toi en ce moment : tes paquets gratuits t''attendent !';
  end if;

  /* un seul tour à la fois par joueur : le compte du jour et les jetons restent justes */
  select jj.jetons_gratuits, jj.jetons_maj, jj.front_energie, jj.front_energie_maj
    into j from joueurs jj where jj.id = v_uid for update;
  if not found then raise exception 'Joueur introuvable'; end if;

  select count(*) into v_n from roue_front_tours t where t.joueur_id = v_uid and t.jour = v_jour;
  if v_n >= v_par then
    raise exception 'Tu as fait tes % tours du jour : la roue revient demain !', v_par;
  end if;

  v_jet := coalesce(j.jetons_gratuits, 0);
  if v_jet < 3 then v_jet := least(3, v_jet + extract(epoch from (now() - coalesce(j.jetons_maj, now()))) / 1200.0); end if;
  if v_jet < 1 then
    raise exception 'Pas de tour disponible pour le moment : un tour revient toutes les 20 minutes.';
  end if;

  /* le tirage : chaque case a sa chance (poids) */
  select sum(greatest(0, coalesce((e->>'poids')::numeric, 0))) into v_total from jsonb_array_elements(coalesce(cfg->'cases', '[]'::jsonb)) e;
  if coalesce(v_total, 0) <= 0 then raise exception 'La roue n''est pas réglée'; end if;
  v_tir := random() * v_total;
  for r in select e, n from jsonb_array_elements(cfg->'cases') with ordinality as x(e, n) order by n loop
    v_acc := v_acc + greatest(0, coalesce((r.e->>'poids')::numeric, 0));
    v_case := r.e;
    exit when v_tir < v_acc;
  end loop;

  v_e := greatest(0, coalesce((v_case->>'energie')::numeric, 0));
  v_l := greatest(0, coalesce((v_case->>'lingots')::numeric, 0));
  v_t := greatest(0, coalesce((v_case->>'terra')::int, 0));

  /* le jeton est consommé */
  update joueurs set jetons_gratuits = v_jet - 1, jetons_maj = now() where id = v_uid;

  /* énergie : jusqu'au plafond des bonus, jamais en dessous de ce qu'on avait */
  if v_e > 0 then
    v := front_energie_lire(j.front_energie, j.front_energie_maj);
    v_nouv := greatest(v, least(front_energie_reglage('plafond'), v + v_e));
    v_e_reel := greatest(0, floor(v_nouv) - floor(v))::integer;
    update joueurs set front_energie = v_nouv, front_energie_maj = now() where id = v_uid;
  end if;

  /* lingots : figer la réserve (production comprise), puis ajouter sans dépasser son maximum */
  if v_l > 0 then
    v := lingots_figer(v_uid);
    v_nouv := greatest(v, least(lingots_max(v_uid), v + v_l));
    v_l_reel := greatest(0, floor(v_nouv) - floor(v))::integer;
    update joueurs set lingots = v_nouv where id = v_uid;
  end if;

  /* paquet Terra : un jeton de plus (gardé même au-dessus de 3, comme un cadeau) */
  if v_t > 0 then
    update joueurs set terra_jetons = terra_jetons_lire(terra_jetons, terra_jetons_maj) + v_t, terra_jetons_maj = now()
     where id = v_uid;
  end if;

  insert into roue_front_tours (joueur_id, jour, case_id, energie, lingots, terra)
  values (v_uid, v_jour, coalesce(v_case->>'id', '?'), v_e_reel, v_l_reel, v_t);

  return jsonb_build_object(
    'case',          v_case->>'id',
    'energie',       v_e_reel,
    'energie_prevue', v_e::integer,
    'lingots',       v_l_reel,
    'lingots_prevus', v_l::integer,
    'terra',         v_t,
    'energie_totale', (select floor(front_energie_lire(jj.front_energie, jj.front_energie_maj))::integer from joueurs jj where jj.id = v_uid),
    'lingots_total', floor(coalesce(lingots_lire(v_uid), 0))::integer,
    'jetons',        round(v_jet - 1, 4),
    'tours_jour',    v_n + 1,
    'par_jour',      v_par);
end; $f$;
revoke all on function public.roue_front_tourner() from public, anon;
grant execute on function public.roue_front_tourner() to authenticated;

commit;

-- Contrôle : true | true | true | 15 | 8 | 100 | 1000000 | 0
select to_regclass('public.roue_front_tours') is not null                                   as table_ok,
       has_function_privilege('authenticated', 'public.roue_front_etat()', 'execute')      as etat_ok,
       has_function_privilege('authenticated', 'public.roue_front_tourner()', 'execute')   as tourner_ok,
       (select (c.valeur::jsonb ->> 'par_jour')::int from public.config_jeu c where c.cle = 'roue_front')                  as par_jour,
       (select jsonb_array_length(c.valeur::jsonb -> 'cases') from public.config_jeu c where c.cle = 'roue_front')         as cases,
       (select sum((e ->> 'poids')::int) from public.config_jeu c, jsonb_array_elements(c.valeur::jsonb -> 'cases') e where c.cle = 'roue_front') as chances_total,
       (select (c.valeur::jsonb ->> 'communes')::int from public.config_jeu c where c.cle = 'reserve_accueil')            as seuil_reserve,
       (select count(*) from public.roue_front_tours)                                                                      as tours_faits;

-- Réglages (à lancer seulement si besoin) :
-- Fermer la roue :                 update public.config_jeu set valeur = (valeur::jsonb || '{"ouvert": 0}'::jsonb) where cle = 'roue_front';
-- 20 tours par jour :              update public.config_jeu set valeur = (valeur::jsonb || '{"par_jour": 20}'::jsonb) where cle = 'roue_front';
-- Réserve au seuil de départ :     update public.config_jeu set valeur = (valeur::jsonb || '{"communes": 3000}'::jsonb) where cle = 'reserve_accueil';
-- Rendre les paquets à tous :      update public.config_jeu set valeur = (valeur::jsonb || '{"ouvert": 0}'::jsonb) where cle = 'reserve_accueil';
