-- s2-106 (6/11/2026) : « Tes dés au Front » dans le Profil (idée d'Arkhannou).
-- Pour le joueur connecté seulement : ses rounds d'attaque, ses défenses et
-- ses garnisons de la saison en cours, avec les chances réellement affichées
-- au moment du lancer (enregistrées depuis le 4/11) pour comparer le résultat
-- à ce qui était attendu.
-- Un round gagné aux dés puis annulé par une garnison compte comme gagné aux
-- dés (front_rounds.garnison) : c'est la garnison qui l'a repoussé, pas le dé.
-- Lecture seule, rien n'est modifié.

create or replace function public.mes_stats_combat()
 returns jsonb
 language sql
 stable security definer
 set search_path to 'public'
as $f$
  with s as (select coalesce((select sa.debut from saisons sa where sa.id = saison_en_cours_id()), now() - interval '30 days') as debut),
  r as (select * from front_rounds x where x.attaquant_id = auth.uid() and x.le >= (select debut from s)),
  d as (select * from front_defenses x where x.defenseur = auth.uid() and x.le >= (select debut from s)),
  g as (select * from front_garnison_journal x where x.defenseur = auth.uid() and x.le >= (select debut from s))
  select case when auth.uid() is null then null else jsonb_build_object(
    'depuis', (select debut from s),
    'attaque', jsonb_build_object(
      'total',      (select count(*) from r),
      'gagnes',     (select count(*) from r where r.gagne),
      'garnison',   (select count(*) from r where r.garnison),
      'mesures',    (select count(*) from r where r.chances is not null),
      'des_gagnes', (select count(*) from r where r.chances is not null and (r.gagne or coalesce(r.garnison, false))),
      'attendu',    (select coalesce(sum(r.chances), 0) / 100.0 from r where r.chances is not null),
      'variance',   (select coalesce(sum(r.chances * (100 - r.chances)), 0) / 10000.0 from r where r.chances is not null)),
    'defense', jsonb_build_object(
      'total',      (select count(*) from d),
      'reussies',   (select count(*) from d where d.reussie),
      'mesures',    (select count(*) from d where d.chances is not null),
      'des_gagnes', (select count(*) from d where d.chances is not null and d.reussie),
      'attendu',    (select coalesce(sum(d.chances), 0) / 100.0 from d where d.chances is not null),
      'variance',   (select coalesce(sum(d.chances * (100 - d.chances)), 0) / 10000.0 from d where d.chances is not null)),
    'garnison', jsonb_build_object(
      'total',      (select count(*) from g),
      'reussies',   (select count(*) from g where g.reussie))
  ) end;
$f$;
revoke all on function public.mes_stats_combat() from public, anon;
grant execute on function public.mes_stats_combat() to authenticated, service_role;

-- Contrôle attendu : t | t
select has_function_privilege('authenticated', 'public.mes_stats_combat()', 'execute') as jeu_ok,
       not has_function_privilege('anon', 'public.mes_stats_combat()', 'execute')      as prive_ok;
