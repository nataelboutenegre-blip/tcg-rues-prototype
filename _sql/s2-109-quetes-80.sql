-- s2-109 (6/11/2026) : énergie des quêtes du Front, plafond de 50 à 80 par jour.
-- Décision de Nataël (6/11, 18 h 39), option 2. Constat : les joueurs actifs
-- atteignaient 50 ⚡ avec les quêtes simples ; les 3 quêtes de performance
-- (+10 chacune, s2-lot-8) ne leur rapportaient plus rien.
-- En plus, une seule fois : les 9 joueurs dont une quête de performance a été
-- bloquée aujourd'hui par l'ancien plafond reçoivent l'énergie manquante
-- (116 ⚡ en tout), et leurs réclamations sont corrigées à 10 pour que le
-- compte du jour reste juste. Le plafond de la réserve (100) s'applique.

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

begin;

do $$
declare d text := pg_get_functiondef('public.reclamer_quete(text)'::regprocedure);
begin
  if position('s2-109' in d) > 0 then raise notice 'reclamer_quete : déjà à jour'; return; end if;
  d := pg_temp.remp(d, '    v_e := least(q.energie, greatest(0, 50 - v_deja));',
                       '    v_e := least(q.energie, greatest(0, 80 - v_deja));   -- s2-109 : 80 par jour', 1, 'plafond');
  d := pg_temp.remp(d, '(50 / 50)', '(80 / 80)', 1, 'message');
  execute d;
end $$;

-- le rattrapage du 6/11 (une seule fois : les réclamations corrigées ne repassent plus)
create temp table rattrapage on commit drop as
select r.joueur_id, sum(10 - r.energie)::int as manque
  from quetes_reclamees r
 where r.jour = date '2026-11-06'
   and r.quete in ('f_radar_perf', 'f_rafale_perf', 'f_pom_perf')
   and r.energie < 10
 group by r.joueur_id;

update joueurs j
   set front_energie = least(front_energie_reglage('plafond'), front_energie_lire(j.front_energie, j.front_energie_maj) + x.manque),
       front_energie_maj = now()
  from rattrapage x
 where j.id = x.joueur_id;

update quetes_reclamees r set energie = 10
 where r.jour = date '2026-11-06'
   and r.quete in ('f_radar_perf', 'f_rafale_perf', 'f_pom_perf')
   and r.energie < 10;

select count(*) as joueurs, coalesce(sum(manque), 0) as energie_rendue from rattrapage;

commit;

-- Contrôle attendu : t | 0
select position('s2-109' in pg_get_functiondef('public.reclamer_quete(text)'::regprocedure)) > 0 as plafond_80,
       (select count(*) from quetes_reclamees r where r.jour = date '2026-11-06'
          and r.quete in ('f_radar_perf', 'f_rafale_perf', 'f_pom_perf') and r.energie < 10) as reste_a_rendre;
