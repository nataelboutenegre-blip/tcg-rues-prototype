-- ---------------------------------------------------------------------------
--  fin-saison-1.sql — quand la saison 1 se termine-t-elle ? Lecture seule.
--
--  ATTENTION : ce script n'appelle PAS saison_courante(). Cette fonction a
--  un effet de bord — elle arme le compte a rebours si elle voit le pot
--  sous le seuil. Une mesure ne doit pas declencher la fin de la saison.
--  On lit la table saisons directement.
--
--  Une commune quitte le pot a sa PREMIERE acquisition. Les conquetes et
--  les echanges ulterieurs creent d'autres lignes dans historique mais ne
--  vident rien : la commune avait deja un proprietaire. D'ou le min().
--
--  Trois rythmes (3, 7 et 14 jours) plutot qu'un seul : si le rythme a 3
--  jours est nettement superieur a celui a 14, la base de joueurs grandit
--  et la projection longue est trop optimiste.
-- ---------------------------------------------------------------------------
with sorties as (
  select commune_code, min(acquired_at) as sortie
    from historique
   group by commune_code
),
pot as (
  select
    (select count(*) from communes)::numeric as total,
    (select count(*)
       from communes c
       left join possessions p on p.commune_code = c.code
      where p.commune_code is null)::numeric as libres,
    (select seuil_communes from saisons
      where etat <> 'terminee'
      order by debut desc limit 1)::numeric as seuil,
    (select etat from saisons
      where etat <> 'terminee'
      order by debut desc limit 1) as etat_saison,
    (select debut::date from saisons
      where etat <> 'terminee'
      order by debut desc limit 1) as debut_saison
),
rythme as (
  select
    (count(*) filter (where sortie >= now() - interval '3 days'))::numeric  / 3  as j3,
    (count(*) filter (where sortie >= now() - interval '7 days'))::numeric  / 7  as j7,
    (count(*) filter (where sortie >= now() - interval '14 days'))::numeric / 14 as j14,
    min(sortie)::date as premiere_sortie
  from sorties
),
actifs as (
  select
    count(distinct joueur_id) filter (where acquired_at >= now() - interval '3 days')::numeric as a3,
    count(distinct joueur_id) filter (where acquired_at >= now() - interval '7 days')::numeric as a7,
    (select count(*) from joueurs)::numeric as inscrits
  from historique
),
calc as (
  select p.*, r.*, a.*,
         greatest(p.libres - p.seuil, 0) as marge
    from pot p, rythme r, actifs a
),
jours as (
  select c.*,
         case when c.j3  > 0 then c.marge / c.j3  end as d3,
         case when c.j7  > 0 then c.marge / c.j7  end as d7,
         case when c.j14 > 0 then c.marge / c.j14 end as d14
    from calc c
)
select 'A. le pot' as quoi,
       to_char(libres, 'FM999G999') || ' libres sur ' || to_char(total, 'FM999G999')
       || ' (' || round(100 * libres / total, 1) || ' %), soit '
       || to_char(total - libres, 'FM999G999') || ' prises' as valeur
  from jours
union all
select 'B. saison en cours',
       'etat ' || etat_saison || ', ouverte le ' || debut_saison
       || ', compte a rebours au passage sous ' || to_char(seuil, 'FM999G999')
       || ' libres (marge actuelle : ' || to_char(marge, 'FM999G999') || ')'
  from jours
union all
select 'C. rythme de sortie du pot',
       round(j3, 0) || ' / jour sur 3 jours, ' || round(j7, 0) || ' sur 7 jours, '
       || round(j14, 0) || ' sur 14 jours'
       || case when j14 > 0 and j3 > j14 * 1.25 then '  <-- ca accelere'
               when j14 > 0 and j3 < j14 * 0.75 then '  <-- ca ralentit'
               else '' end
  from jours
union all
select 'D. joueurs',
       inscrits || ' inscrits, ' || a7 || ' actifs sur 7 jours, ' || a3 || ' sur 3 jours'
       || case when a7 > 0 then ' — ' || round(j7 / a7, 1) || ' communes par joueur actif et par jour'
               else '' end
  from jours
union all
select 'E. jours restants avant le seuil',
       coalesce(round(d3, 0)::text, '—') || ' au rythme de 3 jours, '
       || coalesce(round(d7, 0)::text, '—') || ' au rythme de 7 jours, '
       || coalesce(round(d14, 0)::text, '—') || ' au rythme de 14 jours'
  from jours
union all
select 'F. date de declenchement estimee',
       coalesce((current_date + (d3 || ' days')::interval)::date::text, '—')
       || '  /  ' || coalesce((current_date + (d7 || ' days')::interval)::date::text, '—')
       || '  /  ' || coalesce((current_date + (d14 || ' days')::interval)::date::text, '—')
  from jours
union all
select 'G. fin de saison estimee (seuil + 5 jours)',
       coalesce((current_date + ((d7 + 5) || ' days')::interval)::date::text, '—')
       || ' au rythme median, entre '
       || coalesce((current_date + ((least(d3, d7, d14) + 5) || ' days')::interval)::date::text, '—')
       || ' et '
       || coalesce((current_date + ((greatest(d3, d7, d14) + 5) || ' days')::interval)::date::text, '—')
  from jours
union all
select 'H. premiere commune sortie du pot', premiere_sortie::text from jours
order by 1;
