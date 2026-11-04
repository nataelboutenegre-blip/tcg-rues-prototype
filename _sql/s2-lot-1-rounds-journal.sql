-- ===========================================================================
--  TerraFront — lot du 8/11, 1/7 : chaque round et chaque défense gardent
--  l'engagement, la chance et le coût (demande d'Oshannir, 4/11).
--
--  Avant : front_rounds (s2-87) ne notait que l'attaquant, la commune, la
--  rareté, gagné ou non, la série et l'heure. L'engagement n'était
--  enregistré nulle part (vérifié en production le 4/11).
--  Après :
--   1. front_rounds gagne 4 colonnes : intensite, chances (%), cout
--      (énergie), garnison (vrai quand la garnison a annulé la victoire).
--      attaquer() les remplit juste après l'écriture du siège : le round
--      noté par front_round_noter dans la même transaction a la même heure
--      (now()) ; on complète le dernier de ces rounds (le plus grand id).
--   2. Nouvelle table front_defenses : une ligne par défense à la main
--      (défenseur, attaquant, commune, rareté, engagement, chance, coût,
--      réussie). Remplie par defendre(). Ménage au-delà de 30 jours.
--  Rien ne change pour les joueurs. Les rounds d'avant restent sans ces
--  colonnes (vides).
--  Modifiées en place à partir de leur définition en production : si un
--  texte attendu manque, rien ne change. Rejouable.
--  Contrôle attendu : true | true | true | true
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

-- 1. les colonnes des rounds ------------------------------------------------
alter table public.front_rounds add column if not exists intensite text;
alter table public.front_rounds add column if not exists chances   integer;
alter table public.front_rounds add column if not exists cout      integer;
alter table public.front_rounds add column if not exists garnison  boolean;

-- 2. la table des défenses --------------------------------------------------
create table if not exists public.front_defenses(
  id           bigserial primary key,
  defenseur    uuid not null,
  attaquant    uuid,
  commune_code text not null,
  tier         text,
  intensite    text,
  chances      integer,
  cout         integer,
  reussie      boolean not null,
  le           timestamptz not null default now()
);
create index if not exists front_defenses_le on public.front_defenses(le);
alter table public.front_defenses enable row level security;
revoke all on public.front_defenses from public, anon, authenticated;

-- 3. attaquer : compléter le round ------------------------------------------
do $$
declare d text;
begin
  d := pg_get_functiondef('public.attaquer(text, text)'::regprocedure);
  if position('s2-lot1' in d) > 0 then raise notice 'attaquer : déjà à jour'; return; end if;
  d := pg_temp.remp(d,
    'defenses_faites = sieges.defenses_faites;   -- s2-94 : plus de remise à zéro',
    'defenses_faites = sieges.defenses_faites;   -- s2-94 : plus de remise à zéro

  -- s2-lot1 : le round que front_round_noter vient de noter garde l''engagement, la chance et le coût
  update front_rounds r
     set intensite = p_intensite, chances = round(v_chance * 100)::integer, cout = v_cout, garnison = v_par_garnison
   where r.id = (select max(r2.id) from front_rounds r2
                  where r2.attaquant_id = v_attaquant_id and r2.commune_code = p_commune_code and r2.le = now());',
    1, 'attaquer (round)');
  execute d;
end $$;

-- 4. defendre : noter la défense --------------------------------------------
do $$
declare d text;
begin
  d := pg_get_functiondef('public.defendre(text, uuid, text)'::regprocedure);
  if position('s2-lot1' in d) > 0 then raise notice 'defendre : déjà à jour'; return; end if;
  d := pg_temp.remp(d,
    '  v_reussie := random() < v_chance;',
    '  v_reussie := random() < v_chance;
  -- s2-lot1 : chaque défense à la main est notée (engagement, chance, coût)
  insert into front_defenses(defenseur, attaquant, commune_code, tier, intensite, chances, cout, reussie)
  values (v_uid, p_attaquant, p_commune_code, v_tier, p_intensite, round(v_chance * 100)::integer, v_cout, v_reussie);
  if random() < 0.002 then delete from front_defenses where le < now() - interval ''30 days''; end if;',
    1, 'defendre (journal)');
  execute d;
end $$;

commit;

-- Contrôle : true | true | true | true
select (select count(*) = 4 from information_schema.columns
         where table_schema = 'public' and table_name = 'front_rounds'
           and column_name in ('intensite', 'chances', 'cout', 'garnison'))                                as colonnes_ok,
       to_regclass('public.front_defenses') is not null                                                    as table_ok,
       position('s2-lot1' in pg_get_functiondef('public.attaquer(text, text)'::regprocedure)) > 0
       and has_function_privilege('authenticated', 'public.attaquer(text, text)', 'execute')               as attaquer_ok,
       position('s2-lot1' in pg_get_functiondef('public.defendre(text, uuid, text)'::regprocedure)) > 0
       and has_function_privilege('authenticated', 'public.defendre(text, uuid, text)', 'execute')        as defendre_ok;
