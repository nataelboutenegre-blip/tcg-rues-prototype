-- ---------------------------------------------------------------------------
--  qui-vide-le-pot.sql — lecture seule, n'appelle aucune fonction du jeu
--
--  Le rythme de sortie du pot a double en deux semaines (377 -> 580 -> 729
--  par jour) et la consommation par joueur actif a triple en trois jours
--  (30 -> 48 -> 91). Une consommation par tete qui triple, ce n'est pas de
--  l'enthousiasme, c'est quelque chose qui a change.
--
--  Trois blocs :
--
--   A. jour par jour sur 14 jours — un pic isole ou une pente ?
--   B. par joueur sur 7 jours — concentre sur une ou deux personnes, ou
--      reparti ?
--   C. tirages ET conquetes cote a cote — c'est le test qui compte. Si les
--      gros consommateurs de paquets sont aussi les gros conquerants,
--      alors la refonte du combat finance les paquets : le combat ne vide
--      pas le pot directement, mais il le vide par ricochet, ce qui est
--      exactement le contraire de son but.
--
--  Une commune quitte le pot a sa PREMIERE acquisition, et uniquement
--  la : une conquete prend la commune d'un autre joueur, elle ne retire
--  rien au pot. Les sorties du pot sont donc toutes des tirages.
-- ---------------------------------------------------------------------------
with sorties as (
  select distinct on (commune_code)
         commune_code, joueur_id, acquired_at
    from historique
   order by commune_code, acquired_at
),
jours as (
  select (acquired_at at time zone 'Europe/Paris')::date as j,
         count(*)::int as n
    from sorties
   where acquired_at >= now() - interval '14 days'
   group by 1
),
par_joueur as (
  select s.joueur_id,
         coalesce(jo.pseudo, '(compte inconnu)') as pseudo,
         count(*)::int as j7,
         count(*) filter (where s.acquired_at >= now() - interval '3 days')::int as j3,
         count(*) filter (where s.acquired_at >= now() - interval '1 day')::int  as j1
    from sorties s
    left join joueurs jo on jo.id = s.joueur_id
   where s.acquired_at >= now() - interval '7 days'
   group by 1, 2
),
conquetes as (
  select acteur, count(*)::int as c7
    from journal
   where type = 'conquete'
     and cree_le >= now() - interval '7 days'
   group by 1
),
total as (select coalesce(sum(j7), 0)::numeric as n from par_joueur),
classe as (
  select p.*,
         coalesce(c.c7, 0) as c7,
         row_number() over (order by p.j7 desc) as rang
    from par_joueur p
    left join conquetes c on c.acteur = p.joueur_id
)

select 'A. ' || to_char(j, 'YYYY-MM-DD') || ' (' || to_char(j, 'Dy') || ')' as quoi,
       lpad(n::text, 4, ' ') || '  ' || repeat('#', greatest(1, (n / 25)::int)) as valeur
  from jours

union all

select 'B. ' || lpad(rang::text, 2, '0') || '. ' || pseudo,
       lpad(j7::text, 4, ' ') || ' communes tirees en 7 j  ('
       || lpad(round(100 * j7 / (select n from total), 1)::text, 4, ' ') || ' % du total)'
       || '   dont ' || j3 || ' sur 3 j, ' || j1 || ' sur 24 h'
  from classe

union all

select 'C. ' || lpad(rang::text, 2, '0') || '. ' || pseudo,
       lpad(j7::text, 4, ' ') || ' tirages  /  ' || lpad(c7::text, 3, ' ') || ' conquetes'
       || case when c7 = 0 then '   (ne conquiert pas)'
               else '   ' || round(j7::numeric / c7, 1) || ' tirage(s) par conquete' end
  from classe

union all

select 'D. verdict provisoire',
       case
         when (select max(j7) from classe) >= 0.5 * (select n from total)
           then 'CONCENTRE : un seul joueur fait la moitie ou plus des sorties du pot. '
                || 'Le rythme global ne decrit personne, et la projection de fin de '
                || 'saison depend d''une seule personne.'
         when (select sum(j7) from (select j7 from classe order by j7 desc limit 2) t)
              >= 0.6 * (select n from total)
           then 'CONCENTRE : deux joueurs font 60 % ou plus des sorties.'
         else 'REPARTI : aucun joueur ne domine. L''acceleration est collective, '
              || 'donc c''est bien le jeu qui s''emballe et pas un cas isole.'
       end

union all

select 'E. correlation tirages / conquetes',
       case
         when (select count(*) from classe where c7 > 0) < 3
           then 'trop peu de conquerants pour conclure'
         when (select corr(j7::numeric, c7::numeric) from classe) is null
           then 'non calculable'
         else 'coefficient ' || round((select corr(j7::numeric, c7::numeric) from classe)::numeric, 2)
              || case
                   when (select corr(j7::numeric, c7::numeric) from classe) > 0.6
                     then '  <-- FORTE : ceux qui conquierent le plus tirent le plus. '
                          || 'La piste « le combat finance les paquets » tient.'
                   when (select corr(j7::numeric, c7::numeric) from classe) < 0.2
                     then '  <-- FAIBLE : les gros tireurs ne sont pas les gros '
                          || 'conquerants. Le combat n''explique pas l''acceleration.'
                   else '  <-- MOYENNE : ni confirme ni infirme, regarder les lignes B et C.'
                 end
       end

order by 1;
