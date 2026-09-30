-- ===========================================================================
--  TerraFront — de quoi caler la courbe des niveaux
--
--  LECTURE SEULE. Aucune ecriture, aucun appel a saison_courante().
--
--  But : connaitre, pour chaque joueur, les compteurs dont l'experience
--  sera tiree. Sans ces chiffres on ne peut pas regler la courbe : soit
--  le plus gros joueur est au plafond des le premier jour, soit personne
--  n'atteint le dernier grade avant la fin de la saison.
--
--  Les sources d'experience sont volontairement celles qui NE VIDENT PAS
--  le pot. Les paquets ouverts en sont exclus : les compter reviendrait a
--  recompenser precisement ce qui raccourcit la saison.
-- ===========================================================================

with actifs as (
  -- Un joueur est "actif" un jour donne s'il a AGI ce jour-la. Subir une
  -- attaque ne compte pas : sinon un joueur absent depuis une semaine
  -- herite d'une serie parce qu'on l'attaque pendant son absence.
  select j.joueur_id, j.jour
    from (
      select acteur as joueur_id, date_trunc('day', cree_le) as jour
        from journal where acteur is not null
      union
      select joueur_id, date_trunc('day', acquired_at)
        from historique where acquired_at is not null
    ) j
   group by j.joueur_id, j.jour
),
blocs as (
  -- Jours consecutifs : pour des dates qui se suivent, « date moins le
  -- numero de ligne » est constant. Chaque valeur distincte est un bloc.
  select joueur_id, jour::date as d,
         jour::date - (row_number() over (partition by joueur_id order by jour))::integer as bloc
    from actifs
),
series as (
  -- la serie EN COURS : le dernier bloc, et seulement s'il touche
  -- aujourd'hui ou hier
  select b.joueur_id, count(*)::integer as serie
    from blocs b
    join (select joueur_id, max(d) as dernier from blocs group by joueur_id) m
      on m.joueur_id = b.joueur_id
    join blocs bd on bd.joueur_id = b.joueur_id and bd.d = m.dernier
   where b.bloc = bd.bloc
     and m.dernier >= current_date - 1
   group by b.joueur_id
),
compteurs as (
  select
    jo.id                                                        as joueur_id,
    coalesce(jo.pseudo, '?')                                     as pseudo,
    (select count(*) from journal e
      where e.type = 'conquete' and e.acteur = jo.id)::integer    as conquetes,
    (select count(*) from journal e
      where e.type = 'defense'  and e.acteur = jo.id)::integer    as defenses_ok,
    (select count(*) from journal e
      where e.type = 'defense'  and e.cible  = jo.id)::integer    as attaques_ratees,
    (select count(*) from journal e
      where e.type = 'conquete' and e.cible  = jo.id)::integer    as communes_perdues,
    (select count(*) from journal e
      where e.type = 'contrat'  and e.acteur = jo.id)::integer    as contrats,
    (select count(*) from actifs a where a.joueur_id = jo.id)::integer as jours_actifs,
    coalesce((select serie from series s where s.joueur_id = jo.id), 0)::integer as serie,
    (select count(distinct c.departement)
       from possessions p join communes c on c.code = p.commune_code
      where p.joueur_id = jo.id)::integer                         as departements,
    (select count(*) from possessions p where p.joueur_id = jo.id)::integer as communes,
    (select count(*) from historique h where h.joueur_id = jo.id)::integer  as acquisitions
  from joueurs jo
)
select pseudo,
       conquetes, defenses_ok, attaques_ratees, communes_perdues,
       contrats, jours_actifs, serie, departements, communes,
       -- toutes les acquisitions, tous moyens confondus : c'est d'elle
       -- qu'on deduira les cartes tirees
       acquisitions
  from compteurs
 where communes > 0 or acquisitions > 0
 order by conquetes desc, communes desc;
