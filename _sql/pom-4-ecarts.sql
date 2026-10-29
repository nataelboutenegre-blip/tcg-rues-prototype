-- ===========================================================================
--  pom-4 — Plus ou moins : des écarts qui se devinent (29 octobre 2026)
--  Remarque de H34VEN sur Discord : « ça devient vraiment du pif et la photo
--  n'aide pas » (Remauville 471 hab. contre Irreville 472 hab.).
--
--  Le défaut : pour le duel le plus serré, le tirage visait 3 % d'écart, mais
--  la marge de ± 3 % laissait passer n'importe quelle paire entre 0 et 6 %.
--  Et ces duels serrés se jouaient entre villages de 300 habitants, que
--  personne ne connaît. Le dernier recours prenait même n'importe quelle
--  commune plus petite.
--
--  Désormais :
--    - l'écart demandé est un MINIMUM : la plus peuplée a au moins r fois les
--      habitants de l'autre, et au plus r × 1,1 ;
--    - de 5 fois (1er duel) à 1,25 fois, soit +25 %, pour le 10e (avant : 3 %) ;
--    - la plus peuplée des deux a au moins 2 000 habitants (3 000 pour les
--      premiers duels) : les petits villages restent, mais seulement face à
--      une ville nettement plus grande ;
--    - le dernier recours prend la commune la plus proche de l'écart voulu,
--      jamais plus serrée.
--  Réglages dans config_jeu 'plus_ou_moins' (ratios, planchers, marge),
--  modifiables sans code. S'applique tout de suite à l'entraînement et aux
--  nouveaux duels classés ; la partie du jour change à partir de demain
--  (celle d'aujourd'hui est déjà tirée et jouée par certains).
--
--  Rejouable. Le contrôle affiche 10 duels tirés avec les nouvelles règles
--  (un exemple, rien n'est enregistré) : la colonne ecart doit aller
--  d'environ 400 % à 25 % au moins.
-- ===========================================================================
begin;

insert into public.config_jeu (cle, valeur) values ('plus_ou_moins',
  '{"ratios": [5, 3.5, 2.6, 2.1, 1.8, 1.6, 1.5, 1.4, 1.3, 1.25],
    "planchers": [3000, 3000, 2500, 2500, 2000, 2000, 2000, 2000, 2000, 2000],
    "marge": 0.1}')
on conflict (cle) do update set valeur = excluded.valeur;

create or replace function public.pom_generer()
 returns jsonb language plpgsql volatile security definer set search_path to 'public'
as $f$
declare
  cfg       jsonb := coalesce((select c.valeur::jsonb from config_jeu c where c.cle = 'plus_ou_moins'), '{}'::jsonb);
  ratios    numeric[];
  planchers numeric[];
  marge     numeric := coalesce((cfg ->> 'marge')::numeric, 0.1);
  res jsonb := '[]'::jsonb;
  deja text[] := '{}';
  a_code text; a_pop numeric; a_dep text; b_code text;
  r numeric; pl numeric; k int; essai int;
begin
  select array_agg(x::numeric order by i) into ratios
    from jsonb_array_elements_text(coalesce(cfg -> 'ratios', '[]'::jsonb)) with ordinality t(x, i);
  select array_agg(x::numeric order by i) into planchers
    from jsonb_array_elements_text(coalesce(cfg -> 'planchers', '[]'::jsonb)) with ordinality t(x, i);
  ratios    := coalesce(ratios, array[5, 3.5, 2.6, 2.1, 1.8, 1.6, 1.5, 1.4, 1.3, 1.25]);
  planchers := coalesce(planchers, array[3000, 3000, 2500, 2500, 2000, 2000, 2000, 2000, 2000, 2000]);

  for k in 1..10 loop
    r  := greatest(1.1, coalesce(ratios[k], 1.25));   -- jamais moins de 10 % d'écart, quoi qu'on règle
    pl := coalesce(planchers[k], 2000);
    a_code := null; b_code := null;
    for essai in 1..40 loop
      select c.code, c.population, c.departement into a_code, a_pop, a_dep from communes c
       where c.photo is not null and c.population >= pl and c.code <> all (deja)
       order by random() limit 1;
      exit when a_code is null;
      -- la plus peuplée a entre r et r × (1 + marge) fois les habitants de l'autre
      select c.code into b_code from communes c
       where c.photo is not null and c.code <> all (deja) and c.code <> a_code
         and c.departement <> a_dep
         and c.population <= a_pop / r
         and c.population >= a_pop / (r * (1 + marge))
       order by random() limit 1;
      exit when b_code is not null;
    end loop;
    if a_code is not null and b_code is null then
      -- filet : la commune la plus proche de l'écart voulu, jamais plus serrée
      select c.code into b_code from communes c
       where c.photo is not null and c.code <> all (deja) and c.code <> a_code and c.population <= a_pop / r
       order by c.population desc limit 1;
    end if;
    if a_code is null or b_code is null then
      -- dernier filet (base presque vide) : deux communes avec photo, au moins 10 % d'écart
      select x.code, y.code into a_code, b_code
        from communes x join communes y on y.population <= x.population / 1.1 and y.code <> x.code
       where x.photo is not null and y.photo is not null and x.code <> all (deja) and y.code <> all (deja)
       order by random() limit 1;
    end if;
    deja := deja || a_code || b_code;
    -- la plus peuplée n'est pas toujours à gauche
    res := res || case when random() < 0.5 then jsonb_build_array(jsonb_build_object('a', a_code, 'b', b_code))
                                           else jsonb_build_array(jsonb_build_object('a', b_code, 'b', a_code)) end;
  end loop;
  return res;
end; $f$;

revoke all on function public.pom_generer() from public, anon, authenticated;

commit;

-- contrôle : 10 duels d'exemple tirés avec les nouvelles règles (rien n'est enregistré)
select e.i as duel,
       ca.nom || ' (' || ca.departement || ')' as commune_a, ca.population as hab_a,
       cb.nom || ' (' || cb.departement || ')' as commune_b, cb.population as hab_b,
       round(100.0 * greatest(ca.population, cb.population) / nullif(least(ca.population, cb.population), 0) - 100) || ' %' as ecart
  from jsonb_array_elements(public.pom_generer()) with ordinality e(x, i)
  join public.communes ca on ca.code = e.x ->> 'a'
  join public.communes cb on cb.code = e.x ->> 'b'
 order by e.i;
