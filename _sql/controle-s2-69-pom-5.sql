-- Contrôle en lecture seule de s2-69 (quêtes « Joue 2 duels ») et pom-5 (carte de Plus ou moins).
-- Ne modifie rien. Une seule ligne de résultat.
-- Attendu : true | true | false | true | true | 0
select position('Joue 2 duels Radar'  in pg_get_functiondef('public.quetes_liste(uuid)'::regprocedure)) > 0 as s269_radar,
       position('Joue 2 duels Rafale' in pg_get_functiondef('public.quetes_liste(uuid)'::regprocedure)) > 0 as s269_rafale,
       position('Gagne un duel R'     in pg_get_functiondef('public.quetes_liste(uuid)'::regprocedure)) > 0 as s269_reste_gagne,
       (select (public.pom_carte(c.code, false) ->> 'lat') is not null
          from public.communes c where c.photo is not null and c.latitude is not null limit 1)        as pom5_position_envoyee,
       (select (public.pom_carte(c.code, false) ->> 'population') is null
          from public.communes c where c.photo is not null and c.latitude is not null limit 1)        as pom5_population_cachee,
       (select count(*) from public.communes x
         where x.photo is not null and x.population >= 500 and x.latitude is null)                     as pom5_communes_sans_position;
