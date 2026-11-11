-- s2-136 (11/11/2026) : les points d'une bombe suivent son niveau (idée d'Oshannir, validée par Nataël à 10 h 46)
--
-- Avant : +300 par bombe lancée, quel que soit son niveau → les joueurs lâchaient surtout des bombes de niveau 1
-- (24 h, jamais dévoilées) : 11 bombes de niveau 1 sur 18.
-- Maintenant : niveau 1 +150, niveau 2 +300, niveau 3 +500 (réglages score_s2 bombe_1, bombe_2, bombe_3).
-- Rétroactif seulement à la hausse : une bombe lancée avant ce script garde au moins ses 300 points
-- (réglage bombe_bareme_depuis = l'heure du script, en secondes depuis 1970 ; 'bombe' = 300 reste le plancher).
--
-- Contrôle attendu : 150 | 300 | 500 | true

update public.config_jeu
   set valeur = (valeur::jsonb || jsonb_build_object('bombe_1', 150, 'bombe_2', 300, 'bombe_3', 500,
                                                     'bombe_bareme_depuis', floor(extract(epoch from now()))))::text
 where cle = 'score_s2';

create or replace function public.score_batiments()
 returns table(joueur_id uuid, points integer)
 language sql
 stable security definer
 set search_path to 'public'
as $function$
  with s as (select sa.id, sa.debut from saisons sa where sa.etat <> 'terminee' order by sa.debut desc limit 1),
  bat as (
    select h.joueur_id,
           least(count(*) filter (where h.type = 'fonderie'),   batiment_reglage('fonderies_max'))  * coalesce(score_reglage('bat_fonderie'), 50)
         + least(count(*) filter (where h.type = 'forteresse'), batiment_reglage('forteresse_max')) * coalesce(score_reglage('bat_forteresse'), 80)
         + least(count(*) filter (where h.type = 'centre'), 1) * coalesce(score_reglage('bat_centre'), 150)
         + least(count(*) filter (where h.type = 'banque'), 1) * coalesce(score_reglage('bat_banque'), 80)
         + least(count(*) filter (where h.type = 'radar'), 1) * coalesce(score_reglage('bat_radar'), 80) as pts   -- s2-115
      from batiments_historique h
     where h.saison = (select id from s) and h.pret_le <= now()
     group by h.joueur_id
  ),
  bo as (   -- s2-136 : selon le niveau ; les bombes d'avant le barème gardent au moins l'ancien montant
    select b.lanceur as joueur_id,
           sum(case when b.le < to_timestamp(coalesce(score_reglage('bombe_bareme_depuis'), 0))
                    then greatest(coalesce(score_reglage('bombe'), 300), coalesce(score_reglage('bombe_' || b.niveau), score_reglage('bombe'), 300))
                    else coalesce(score_reglage('bombe_' || b.niveau), score_reglage('bombe'), 300) end) as pts
      from bombes b where b.le >= (select debut from s) group by b.lanceur
  ),
  lingots_jour as (
    select r.financeur as joueur_id, (r.debut at time zone 'Europe/Paris')::date as jour, r.mise as lingots
      from rebellions r where r.debut >= (select debut from s)
    union all
    select e.defenseur, (e.le at time zone 'Europe/Paris')::date, e.lingots
      from rebellions_etouffements e where e.le >= (select debut from s)
  ),
  re as (
    select x.joueur_id, sum(x.p) as pts
      from (select l.joueur_id, least(sum(l.lingots) * coalesce(score_reglage('rebellion_lingot'), 2),
                                      coalesce(score_reglage('rebellion_jour'), 60)) as p
              from lingots_jour l group by l.joueur_id, l.jour) x
     group by x.joueur_id
  ),
  ids as (select joueur_id from bat union select joueur_id from bo union select joueur_id from re)
  select i.joueur_id, (coalesce(bat.pts, 0) + coalesce(bo.pts, 0) + coalesce(re.pts, 0))::integer
    from ids i
    left join bat on bat.joueur_id = i.joueur_id
    left join bo  on bo.joueur_id  = i.joueur_id
    left join re  on re.joueur_id  = i.joueur_id
   where score_bonus_actif();
$function$;

select score_reglage('bombe_1') as niveau_1, score_reglage('bombe_2') as niveau_2, score_reglage('bombe_3') as niveau_3,
       to_timestamp(score_reglage('bombe_bareme_depuis')) > now() - interval '5 minutes' as date_posee;
