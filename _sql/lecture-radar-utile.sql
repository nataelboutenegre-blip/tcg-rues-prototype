-- ===========================================================================
--  LECTURE SEULE — Faut-il un Radar ? (3/11/2026)
--  Le Radar servirait à trouver les centres de recherche qui préparent une
--  bombe EN SECRET, c'est-à-dire avant d'être dévoilés (réglage
--  bombe_devoile_h, 48 h). Cette lecture dit si les bombes sont utilisées,
--  et combien partent d'un centre que personne ne pouvait voir.
--  « Actif » = a ouvert le jeu dans les 2 derniers jours ET tient au moins
--  une commune au Front (même définition que lecture-batiments-avancement).
--  Aucun pseudo. Ne modifie rien.
--  Un seul tableau (l'éditeur Supabase n'affiche que le dernier résultat).
-- ===========================================================================
with reg as (
  select make_interval(hours => batiment_reglage('bombe_devoile_h')::integer) as devoile,
         (now() at time zone 'Europe/Paris')::date                            as auj
),
actifs as (
  select j.id
    from joueurs j
   where exists (select 1 from possessions p where p.joueur_id = j.id)
     and (select max(jj.jour) from jours_joues jj where jj.joueur_id = j.id) >= (select auj from reg) - 2
),
centres as (
  select x.joueur_id, x.pret_le <= now() as pret
    from batiments x where x.type = 'centre'
),
preps as (
  select p.*,
         coalesce(p.fini_le, now()) - p.commence_le as duree
    from bombes_preparations p
),
lachees as (
  select b.*, p.commence_le,
         case when p.id is null then null else b.le - p.commence_le < (select devoile from reg) end as cachee
    from bombes b left join bombes_preparations p on p.id = b.preparation_id
)
select '01. joueurs actifs au Front' as ligne,
       (select count(*) from actifs) as nombre,
       null::text as detail
union all
select '02. Centres de recherche posés',
       count(*),
       'prêts : ' || count(*) filter (where pret)
       || ' · tenus par un joueur actif : ' || count(*) filter (where joueur_id in (select id from actifs))
  from centres
union all
select '03. bombes en préparation maintenant',
       count(*),
       'encore cachées (moins de ' || extract(epoch from (select devoile from reg))::integer / 3600 || ' h) : '
       || count(*) filter (where duree < (select devoile from reg))
       || ' · déjà dévoilées : ' || count(*) filter (where duree >= (select devoile from reg))
  from preps where etat = 'en_cours'
union all
select '04. préparations depuis le début',
       count(*),
       'lâchées : ' || count(*) filter (where etat = 'lachee')
       || ' · perdues (centre pris) : ' || count(*) filter (where etat = 'perdue')
       || ' · en cours : ' || count(*) filter (where etat = 'en_cours')
  from preps
union all
select '05. préparations perdues alors que le centre était encore caché',
       count(*) filter (where etat = 'perdue' and duree < (select devoile from reg)),
       'perdues après avoir été dévoilées : ' || count(*) filter (where etat = 'perdue' and duree >= (select devoile from reg))
  from preps
union all
select '06. bombes lâchées',
       count(*),
       '7 derniers jours : ' || count(*) filter (where le > now() - interval '7 days')
       || ' · 24 dernières heures : ' || count(*) filter (where le > now() - interval '24 hours')
       || ' · lanceurs différents : ' || count(distinct lanceur)
  from lachees
union all
select '07. bombes lâchées d''un centre encore caché',
       count(*) filter (where cachee),
       'd''un centre déjà dévoilé : ' || count(*) filter (where cachee = false)
       || ' · inconnu : ' || count(*) filter (where cachee is null)
  from lachees
union all
select '08. taille des bombes lâchées',
       count(*),
       'niveau 1 : ' || count(*) filter (where niveau = 1)
       || ' · niveau 2 : ' || count(*) filter (where niveau = 2)
       || ' · niveau 3 : ' || count(*) filter (where niveau = 3)
  from lachees
union all
select '09. joueurs touchés par une bombe',
       (select count(distinct d.joueur_id) from bombes_degats d),
       'garnisons détruites : ' || coalesce(sum(garnisons), 0)
       || ' · forteresses détruites : ' || coalesce(sum(forteresses), 0)
       || ' · communes dans les zones : ' || coalesce(sum(communes), 0)
  from lachees
union all
select '10. première et dernière bombe',
       count(*),
       coalesce('première : ' || to_char(min(le) at time zone 'Europe/Paris', 'DD/MM HH24"h"MI')
       || ' · dernière : ' || to_char(max(le) at time zone 'Europe/Paris', 'DD/MM HH24"h"MI'), 'aucune')
  from lachees
order by 1;
