-- ===========================================================================
--  s2-72b — Lingots des combats : rallumer + rattrapage (1er novembre 2026)
--  Constat (diagnostic du 1/11, 8 h 55) : le réglage lingots_combat_ouvert
--  valait 0 (comme après s2-72-lingots-combat-couper.sql). Le déclencheur
--  ne versait donc plus rien ; tout le reste marche (vérifié : lecture,
--  mise à jour de la réserve, enregistrement du gain).
--
--  1. Rallume : lingots_combat_ouvert = 1.
--  2. Rattrapage : chaque victoire COMPTÉE par le score depuis le 1/11 à
--     0 h 26 (lancement de s2-72) qui n'a rien rapporté reçoit ce qu'elle
--     aurait dû rapporter (+2 conquête, +1 défense), dans l'ordre où elle a
--     eu lieu, sans dépasser 10 lingots de combat par jour et par joueur.
--     Chaque versement est noté dans lingots_gains (donc compté dans le
--     plafond du jour, et jamais versé deux fois si on relance le fichier).
--  Réserve : par défaut, le rattrapage est versé EN ENTIER, même si la
--     réserve dépasse son plafond (30 ou 45) : c'est notre bug, les joueurs
--     ne doivent pas le payer. La production s'arrête tant que la réserve
--     est au-dessus du plafond ; un achat la fait redescendre.
--     Pour respecter le plafond à la place : mettre « true » à la ligne
--     marquée ← (étape 2).
--  Rejouable sans double versement.
--  Contrôle attendu : true | nombre de joueurs | lingots versés | 0
-- ===========================================================================
drop table if exists pg_temp.rattrapage_lingots;
drop table if exists pg_temp.rattrapage_controle;

begin;

-- 1. Rallumer ------------------------------------------------------------------
update public.config_jeu
   set valeur = (valeur::jsonb || '{"lingots_combat_ouvert": 1}'::jsonb)::text
 where cle = 'batiments';

-- 2. Ce qui est dû, victoire par victoire --------------------------------------
create temp table rattrapage_lingots as
with v as (
  select fv.id, fv.joueur_id, fv.saison, fv.type, fv.le,
         (fv.le at time zone 'Europe/Paris')::date as jour,
         (case fv.type when 'conquete' then coalesce(batiment_reglage('lingots_conquete'), 2)
                       else coalesce(batiment_reglage('lingots_defense'), 1) end)::integer as gain
    from front_victoires fv
   where fv.compte
     and fv.le >= timestamp '2026-11-01 00:26' at time zone 'Europe/Paris'
     and fv.saison = saison_en_cours_id()
     and not exists (select 1 from lingots_gains g where g.victoire_id = fv.id)
),
c as (
  select v.*,
         sum(v.gain) over (partition by v.joueur_id, v.jour order by v.le, v.id) - v.gain as avant_elle,
         coalesce((select sum(g.quantite) from lingots_gains g
                    where g.joueur_id = v.joueur_id and g.jour = v.jour), 0)          as deja_verses
    from v
)
select c.id, c.joueur_id, c.saison, c.type, c.jour,
       greatest(0, least(c.gain, coalesce(batiment_reglage('lingots_combat_jour'), 10)::integer
                                  - c.deja_verses - c.avant_elle))::integer as quantite,
       false as respecter_plafond_reserve      -- ← mettre true pour ne pas dépasser 30 / 45
  from c;

-- 3. Verser ---------------------------------------------------------------------
-- la réserve est d'abord figée (production comprise), puis le rattrapage s'ajoute
select count(lingots_figer(d.joueur_id)) as reserves_figees
  from (select distinct joueur_id from rattrapage_lingots where quantite > 0) d;

update public.joueurs j
   set lingots = case when t.respecter then least(greatest(j.lingots, lingots_max(j.id)), j.lingots + t.total)
                      else j.lingots + t.total end
  from (select joueur_id, sum(quantite) as total, bool_or(respecter_plafond_reserve) as respecter
          from rattrapage_lingots where quantite > 0 group by joueur_id) t
 where j.id = t.joueur_id;

insert into public.lingots_gains(joueur_id, saison, jour, source, victoire_id, quantite)
select joueur_id, saison, jour, type, id, quantite
  from rattrapage_lingots where quantite > 0
on conflict (victoire_id) do nothing;

-- Contrôle (calculé avant la fin de la transaction, affiché après)
create temp table rattrapage_controle as
select coalesce(batiment_reglage('lingots_combat_ouvert'), 0) = 1                     as ouvert,
       (select count(distinct joueur_id) from rattrapage_lingots where quantite > 0)  as joueurs_rattrapes,
       (select coalesce(sum(quantite), 0) from rattrapage_lingots)                    as lingots_verses,
       (select count(*) from front_victoires fv
         where fv.compte and fv.le >= timestamp '2026-11-01 00:26' at time zone 'Europe/Paris'
           and fv.saison = saison_en_cours_id()
           and not exists (select 1 from lingots_gains g where g.victoire_id = fv.id)
           and coalesce((select sum(g.quantite) from lingots_gains g
                          where g.joueur_id = fv.joueur_id
                            and g.jour = (fv.le at time zone 'Europe/Paris')::date), 0)
               < coalesce(batiment_reglage('lingots_combat_jour'), 10))           as encore_dus;

commit;

select * from rattrapage_controle;
