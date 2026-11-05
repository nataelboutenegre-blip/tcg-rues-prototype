-- ===========================================================================
--  TerraFront — s2-102 : la roue du Front à 30 tours par jour (5/11)
--  (les joueurs réclament plus de tours ; décision de Nataël du 5/11)
--
--  Le 5/11 à 14 h, 7 des 13 joueurs de la roue avaient déjà fait leurs 15
--  tours. Doubler les tours avec la même roue doublerait l'énergie et les
--  lingots des plus actifs (environ +50 ⚡ et +13 lingots par jour), le jour où
--  le lot rééquilibre le Front. Donc 30 tours, mais une roue plus variée : les
--  cases du Front plus rares, et trois cases nouvelles.
--    TerraPoints +10 TP (30 %), Cagnotte +50 TP (3 %) : Terra seulement.
--    Relance (12 %) : tour offert, le jeton est rendu et le tour ne compte pas
--    dans les 30.
--  Pour 30 tours : ~57 ⚡, ~15 lingots, ~1,7 paquet Terra et ~150 TP par jour
--  (avant, pour 15 tours : ~50 ⚡, ~13 lingots, ~0,5 paquet Terra).
--
--  1. roue_front_tours : colonnes tp et offert.
--  2. Réglage config_jeu 'roue_front' : par_jour 30, les 11 cases (petites cases
--     glissées entre les grandes, pour la lisibilité). Chaque case peut donner energie, lingots, terra (paquets), tp, ou relance (1).
--  3. roue_front_tourner : TerraPoints (motif « roue »), tour offert ; le
--     compte du jour ignore les tours offerts. roue_front_etat aussi.
--  Modifiées en place à partir de leur définition en production : si un texte
--  attendu manque, rien ne change. Rejouable. Indépendant du lot (aucun de ses
--  fichiers ne touche la roue). Le jeu : patch351.
--
--  Contrôle attendu : 30 | 11 | 100 | true | true | true
--  Retour à l'ancienne roue (le jeu s'adapte seul) :
--    update public.config_jeu set valeur = '{"ouvert": 1, "par_jour": 15, "cases": [
--      {"id": "petit", "nom": "Petit éclair", "poids": 27, "energie": 3, "lingots": 0, "terra": 0},
--      {"id": "lingots", "nom": "Lingots", "poids": 20, "energie": 0, "lingots": 2, "terra": 0},
--      {"id": "eclair", "nom": "Éclair", "poids": 20, "energie": 5, "lingots": 0, "terra": 0},
--      {"id": "mixte", "nom": "Mixte", "poids": 15, "energie": 3, "lingots": 1, "terra": 0},
--      {"id": "gros", "nom": "Gros éclair", "poids": 8, "energie": 10, "lingots": 0, "terra": 0},
--      {"id": "coffre", "nom": "Coffre", "poids": 5, "energie": 0, "lingots": 4, "terra": 0},
--      {"id": "terra", "nom": "Paquet Terra", "poids": 3, "energie": 0, "lingots": 0, "terra": 1},
--      {"id": "jackpot", "nom": "Jackpot", "poids": 2, "energie": 12, "lingots": 5, "terra": 0}]}'
--    where cle = 'roue_front';
-- ===========================================================================
begin;

create or replace function pg_temp.remp(d text, avant text, apres text, nb int, quoi text)
 returns text language plpgsql as $f$
begin
  if (length(d) - length(replace(d, avant, ''))) / length(avant) <> nb then
    raise exception '% : texte attendu % fois, trouvé % fois — rien n''a changé : %',
      quoi, nb, (length(d) - length(replace(d, avant, ''))) / length(avant), avant;
  end if;
  return replace(d, avant, apres);
end;
$f$;

-- 1. les tours : TerraPoints et tours offerts ------------------------------------------
alter table public.roue_front_tours add column if not exists tp integer not null default 0;
alter table public.roue_front_tours add column if not exists offert boolean not null default false;

-- 2. le réglage -------------------------------------------------------------------------
update public.config_jeu set valeur = jsonb_build_object(
  'ouvert',   coalesce((valeur::jsonb ->> 'ouvert')::int, 1),
  'par_jour', 30,
  'cases', '[
    {"id": "tp",       "nom": "TerraPoints",  "poids": 30, "tp": 10},
    {"id": "gros",     "nom": "Gros éclair",  "poids": 4,  "energie": 10, "lingots": 0, "terra": 0},
    {"id": "petit",    "nom": "Petit éclair", "poids": 16, "energie": 3,  "lingots": 0, "terra": 0},
    {"id": "cagnotte", "nom": "Cagnotte",     "poids": 3,  "tp": 50},
    {"id": "eclair",   "nom": "Éclair",       "poids": 10, "energie": 5,  "lingots": 0, "terra": 0},
    {"id": "coffre",   "nom": "Coffre",       "poids": 3,  "energie": 0,  "lingots": 4, "terra": 0},
    {"id": "relance",  "nom": "Relance",      "poids": 12, "relance": 1},
    {"id": "jackpot",  "nom": "Jackpot",      "poids": 1,  "energie": 12, "lingots": 5, "terra": 0},
    {"id": "lingots",  "nom": "Lingots",      "poids": 10, "energie": 0,  "lingots": 2, "terra": 0},
    {"id": "terra",    "nom": "Paquet Terra", "poids": 5,  "energie": 0,  "lingots": 0, "terra": 1},
    {"id": "mixte",    "nom": "Mixte",        "poids": 6,  "energie": 3,  "lingots": 1, "terra": 0}
  ]'::jsonb)::text
 where cle = 'roue_front';

-- 3. le tour ------------------------------------------------------------------------------
do $$
declare d text;
begin
  d := pg_get_functiondef('public.roue_front_tourner()'::regprocedure);
  if position('s2-102' in d) > 0 then raise notice 'roue_front_tourner : déjà à jour';
  else
    d := pg_temp.remp(d, '  v_nouv   numeric;
begin',
'  v_nouv   numeric;
  v_tp     integer;
  v_off    boolean;
begin', 1, 'roue_front_tourner (variables)');
    d := pg_temp.remp(d,
      '  select count(*) into v_n from roue_front_tours t where t.joueur_id = v_uid and t.jour = v_jour;',
      '  select count(*) into v_n from roue_front_tours t where t.joueur_id = v_uid and t.jour = v_jour
     and not t.offert;   -- s2-102 : un tour offert ne compte pas', 1, 'roue_front_tourner (compte)');
    d := pg_temp.remp(d,
      '  v_t := greatest(0, coalesce((v_case->>''terra'')::int, 0));',
      '  v_t := greatest(0, coalesce((v_case->>''terra'')::int, 0));
  v_tp := greatest(0, coalesce((v_case->>''tp'')::int, 0));           -- s2-102 : TerraPoints
  v_off := coalesce((v_case->>''relance'')::int, 0) = 1;              -- s2-102 : tour offert', 1, 'roue_front_tourner (case)');
    d := pg_temp.remp(d,
      '  update joueurs set jetons_gratuits = v_jet - 1, jetons_maj = now() where id = v_uid;',
      '  if not v_off then   -- s2-102 : un tour offert rend son jeton
    update joueurs set jetons_gratuits = v_jet - 1, jetons_maj = now() where id = v_uid;
  end if;', 1, 'roue_front_tourner (jeton)');
    d := pg_temp.remp(d,
      '  insert into roue_front_tours (joueur_id, jour, case_id, energie, lingots, terra)
  values (v_uid, v_jour, coalesce(v_case->>''id'', ''?''), v_e_reel, v_l_reel, v_t);',
      '  /* s2-102 : TerraPoints, au solde de Terra (tracé avec le motif « roue ») */
  if v_tp > 0 then
    perform set_config(''terrafront.motif'', ''roue'', true);
    update joueurs set solde = coalesce(solde, 0) + v_tp where id = v_uid;
  end if;

  insert into roue_front_tours (joueur_id, jour, case_id, energie, lingots, terra, tp, offert)
  values (v_uid, v_jour, coalesce(v_case->>''id'', ''?''), v_e_reel, v_l_reel, v_t, v_tp, v_off);', 1, 'roue_front_tourner (insertion)');
    d := pg_temp.remp(d,
      '    ''terra'',         v_t,',
      '    ''terra'',         v_t,
    ''tp'',            v_tp,
    ''relance'',       v_off,
    ''solde'',         (select coalesce(jj.solde, 0) from joueurs jj where jj.id = v_uid),', 1, 'roue_front_tourner (réponse)');
    d := pg_temp.remp(d,
      '    ''jetons'',        round(v_jet - 1, 4),
    ''tours_jour'',    v_n + 1,',
      '    ''jetons'',        round(v_jet - case when v_off then 0 else 1 end, 4),
    ''tours_jour'',    v_n + case when v_off then 0 else 1 end,', 1, 'roue_front_tourner (jetons)');
    execute d;
  end if;

  d := pg_get_functiondef('public.roue_front_etat()'::regprocedure);
  if position('s2-102' in d) > 0 then raise notice 'roue_front_etat : déjà à jour';
  else
    d := pg_temp.remp(d,
      '   where t.joueur_id = v_uid and t.jour = (now() at time zone ''Europe/Paris'')::date;',
      '   where t.joueur_id = v_uid and t.jour = (now() at time zone ''Europe/Paris'')::date
     and not t.offert;   -- s2-102 : un tour offert ne compte pas', 1, 'roue_front_etat');
    execute d;
  end if;
end $$;

commit;

-- Contrôle : 30 | 11 | 100 | true | true | true
select (c.valeur::jsonb ->> 'par_jour')::int                                                    as par_jour,
       jsonb_array_length(c.valeur::jsonb -> 'cases')                                           as cases,
       (select sum((e ->> 'poids')::int) from jsonb_array_elements(c.valeur::jsonb -> 'cases') e) as poids,
       position('s2-102' in pg_get_functiondef('public.roue_front_tourner()'::regprocedure)) > 0
       and position('s2-102' in pg_get_functiondef('public.roue_front_etat()'::regprocedure)) > 0 as fonctions_ok,
       (select count(*) from information_schema.columns
         where table_schema = 'public' and table_name = 'roue_front_tours' and column_name in ('tp', 'offert')) = 2 as colonnes_ok,
       has_function_privilege('authenticated', 'public.roue_front_tourner()', 'execute')
       and has_function_privilege('authenticated', 'public.roue_front_etat()', 'execute')        as droits_ok
  from public.config_jeu c where c.cle = 'roue_front';
