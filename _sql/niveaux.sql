-- ===========================================================================
--  TerraFront — les niveaux et les statistiques du profil
--
--  Trois choses :
--    1. le bareme des lieues et la fonction qui donne le niveau
--    2. les compteurs d'un joueur (combats, assiduite, cartes tirees)
--    3. profil_joueur enrichi de tout ca
--
--  L'EXPERIENCE EST A VIE. Elle ne redescend jamais et la cloture de
--  saison n'y touche pas : c'est tout son interet. Le classement dit ce
--  qu'un joueur tient aujourd'hui, le niveau dit ce qu'il a fait.
--
--  AUCUNE LIEUE POUR LES PAQUETS OUVERTS. Les recompenser reviendrait a
--  payer precisement ce qui vide le pot et raccourcit la saison.
--
--  CALAGE. Les constantes viennent des compteurs reels du 30 septembre
--  2026 (voir _sql/niveaux-etat.sql). Avec ce bareme, le premier joueur
--  est au niveau 26 sur 60, les reguliers entre 10 et 16, les nouveaux
--  entre 1 et 5. Personne n'est au plafond et les deux derniers grades
--  sont l'horizon des saisons suivantes.
-- ===========================================================================

-- ---------------------------------------------------------------------------
--  1. Le bareme, en un seul endroit
--
--  Expose au client pour que la page des regles puisse l'afficher sans
--  recopier les valeurs : deux sources pour un meme chiffre finissent
--  toujours par diverger.
-- ---------------------------------------------------------------------------
create or replace function public.lieues_bareme()
returns jsonb
language sql
immutable
as $function$
  select jsonb_build_object(
    'conquete',    10,   -- une commune prise
    'defense',     30,   -- un assaut repousse : plus rare, et on veut l'encourager
    'contrat',     20,   -- dix communes rendues au pot
    'jour',        50,   -- un jour ou le joueur a agi : revenir est ce qui compte
    'departement', 20    -- par departement ou il tient au moins une commune
  );
$function$;

revoke all on function public.lieues_bareme() from public;
grant execute on function public.lieues_bareme() to anon, authenticated;


-- ---------------------------------------------------------------------------
--  2. Du total de lieues au niveau
--
--  Le cumul pour atteindre le niveau n vaut A x (n-1)^P. La reciproque
--  donne le niveau directement, sans table de paliers a maintenir.
--
--  A = 9,4 et P = 2,2 : 1 181 lieues pour le niveau 10, 6 114 pour le 20,
--  15 502 pour le 30, 73 960 pour le 60. Instantane au debut, long a la
--  fin. Rallonger l'echelle un jour = changer le 60 ci-dessous.
-- ---------------------------------------------------------------------------
create or replace function public.niveau_de(p_lieues integer)
returns integer
language sql
immutable
as $function$
  select greatest(1, least(60,
    floor(power(greatest(coalesce(p_lieues, 0), 0)::numeric / 9.4, 1.0 / 2.2)) + 1
  ))::integer;
$function$;

-- Le cumul exact d'un niveau, pour afficher la barre de progression.
create or replace function public.lieues_du_niveau(p_niveau integer)
returns integer
language sql
immutable
as $function$
  select case when coalesce(p_niveau, 1) <= 1 then 0
              else ceil(9.4 * power(p_niveau - 1, 2.2))::integer end;
$function$;

revoke all on function public.niveau_de(integer) from public;
revoke all on function public.lieues_du_niveau(integer) from public;
grant execute on function public.niveau_de(integer) to anon, authenticated;
grant execute on function public.lieues_du_niveau(integer) to anon, authenticated;


-- ---------------------------------------------------------------------------
--  3. Les compteurs d'un joueur
--
--  Une seule fonction, appelee par profil_joueur. Tout est deduit du
--  journal et de l'historique : les chiffres partent donc avec
--  l'anteriorite complete, pas a zero.
-- ---------------------------------------------------------------------------
create or replace function public.compteurs_joueur(p_joueur uuid)
returns jsonb
language sql
stable
security definer
set search_path to 'public'
as $function$
  with actifs as (
    -- Un jour "actif" est un jour ou le joueur a AGI. Subir une attaque ne
    -- compte pas : sinon un absent herite d'une serie parce qu'on
    -- l'attaque pendant son absence.
    select distinct jour from (
      select date_trunc('day', cree_le)::date as jour
        from journal where acteur = p_joueur
      union
      select date_trunc('day', acquired_at)::date
        from historique where joueur_id = p_joueur and acquired_at is not null
    ) x
  ),
  blocs as (
    -- Jours consecutifs : pour des dates qui se suivent, « date moins le
    -- numero de ligne » est constant. Chaque valeur distincte est un bloc.
    select jour, jour - (row_number() over (order by jour))::integer as bloc
      from actifs
  ),
  serie as (
    -- la serie EN COURS : le dernier bloc, et seulement s'il touche
    -- aujourd'hui ou hier
    select count(*)::integer as n
      from blocs
     where bloc = (select bloc from blocs order by jour desc limit 1)
       and (select max(jour) from blocs) >= current_date - 1
  ),
  c as (
    select
      (select count(*) from journal where type = 'conquete' and acteur = p_joueur)::integer as conquetes,
      (select count(*) from journal where type = 'conquete' and cible  = p_joueur)::integer as communes_perdues,
      (select count(*) from journal where type = 'defense'  and acteur = p_joueur)::integer as defenses_ok,
      (select count(*) from journal where type = 'defense'  and cible  = p_joueur)::integer as attaques_ratees,
      (select count(*) from journal where type = 'contrat'  and acteur = p_joueur)::integer as contrats,
      (select count(*) from journal where type = 'achat'    and acteur = p_joueur)::integer as achats,
      (select count(*) from journal where type = 'echange'
         and (acteur = p_joueur or cible = p_joueur))::integer                              as echanges,
      (select count(*) from historique where joueur_id = p_joueur)::integer                 as acquisitions,
      (select count(*) from actifs)::integer                                                as jours_actifs,
      coalesce((select n from serie), 0)                                                    as serie,
      (select count(distinct co.departement)
         from possessions p join communes co on co.code = p.commune_code
        where p.joueur_id = p_joueur)::integer                                              as departements
  ),
  d as (
    select c.*,
           -- Les cartes tirees se deduisent : tout ce qui est entre dans la
           -- collection, moins ce qui y est entre autrement. On ne divise PAS
           -- par 5 pour en faire des paquets : le bug du 19 septembre a
           -- produit des paquets tronques, le compte serait faux.
           greatest(0, c.acquisitions - c.conquetes - c.achats - c.echanges - c.contrats) as cartes_tirees,
           (select (b->>'conquete')::integer    from lieues_bareme() b) * c.conquetes
         + (select (b->>'defense')::integer     from lieues_bareme() b) * c.defenses_ok
         + (select (b->>'contrat')::integer     from lieues_bareme() b) * c.contrats
         + (select (b->>'jour')::integer        from lieues_bareme() b) * c.jours_actifs
         + (select (b->>'departement')::integer from lieues_bareme() b) * c.departements
             as lieues
      from c
  )
  select jsonb_build_object(
    'conquetes',        d.conquetes,
    'communes_perdues', d.communes_perdues,
    'defenses_ok',      d.defenses_ok,
    'attaques_ratees',  d.attaques_ratees,
    'contrats',         d.contrats,
    'cartes_tirees',    d.cartes_tirees,
    'jours_actifs',     d.jours_actifs,
    'serie',            d.serie,
    'lieues',           d.lieues,
    'niveau',           niveau_de(d.lieues),
    'lieues_niveau',    lieues_du_niveau(niveau_de(d.lieues)),
    'lieues_suivant',   lieues_du_niveau(niveau_de(d.lieues) + 1)
  )
  from d;
$function$;

revoke all on function public.compteurs_joueur(uuid) from public, anon;
grant execute on function public.compteurs_joueur(uuid) to authenticated;


-- ---------------------------------------------------------------------------
--  4. profil_joueur reprend tout ca
--
--  Les cles existantes ne bougent pas : le client actuel continue de
--  fonctionner sans etre redeploye.
-- ---------------------------------------------------------------------------
create or replace function public.profil_joueur(p_joueur uuid)
returns jsonb
language sql
stable
security definer
set search_path to 'public'
as $function$
  with totaux as (
    select p.joueur_id,
           sum(points_rarete(c.tier))::integer            as score,
           count(*)::integer                              as communes,
           sum(coalesce(c.population, 0))::bigint         as habitants,
           count(*) filter (where c.tier = 'legendaire')::integer as legendaires,
           count(*) filter (where c.tier = 'rare')::integer       as rares,
           count(distinct c.departement)::integer         as departements
      from possessions p
      join communes c on c.code = p.commune_code
     group by p.joueur_id
  ),
  classe as (
    select t.*, row_number() over (
             order by t.score desc, t.communes desc, t.habitants desc)::integer as rang
      from totaux t
  ),
  moi as (select * from classe where joueur_id = p_joueur),
  phares as (
    select jsonb_agg(x order by x.pop desc) as liste
      from (
        select c.nom, c.departement as dep, c.population as pop, c.tier
          from possessions p
          join communes c on c.code = p.commune_code
         where p.joueur_id = p_joueur
         order by c.population desc nulls last
         limit 5
      ) x
  ),
  deps as (
    select jsonb_agg(jsonb_build_object('dep', d.departement, 'n', d.n)) as liste
      from (
        select c.departement, count(*)::integer as n
          from possessions p
          join communes c on c.code = p.commune_code
         where p.joueur_id = p_joueur
         group by c.departement
      ) d
  )
  select jsonb_build_object(
    'id',            j.id,
    'pseudo',        coalesce(j.pseudo, 'Joueur'),
    'avatar',        j.avatar,
    'depuis',        j.created_at,
    'est_moi',       (j.id = auth.uid()),
    'rang',          coalesce(m.rang, 0),
    'score',         coalesce(m.score, 0),
    'communes',      coalesce(m.communes, 0),
    'habitants',     coalesce(m.habitants, 0),
    'legendaires',   coalesce(m.legendaires, 0),
    'rares',         coalesce(m.rares, 0),
    'departements',  coalesce(m.departements, 0),
    'phares',        coalesce((select liste from phares), '[]'::jsonb),
    'deps',          coalesce((select liste from deps), '[]'::jsonb)
  ) || compteurs_joueur(p_joueur)
  from joueurs j
  left join moi m on m.joueur_id = j.id
  where j.id = p_joueur;
$function$;

grant execute on function public.profil_joueur(uuid) to authenticated;


-- ---------------------------------------------------------------------------
--  Verification
-- ---------------------------------------------------------------------------
select 'A. paliers' as controle,
       string_agg(n || ' -> ' || lieues_du_niveau(n), '  ' order by n) as valeur
  from (values (10),(20),(30),(40),(50),(60)) t(n)
union all
select 'B. reciproque',
       string_agg(x || ' lieues -> niveau ' || niveau_de(x), chr(10) order by x)
  from (values (0),(70),(1230),(4120),(11250),(73960),(999999)) t(x)
union all
select 'C. bareme', lieues_bareme()::text
union all
select 'D. droits',
       coalesce(string_agg(p.proname || ' -> ' ||
                coalesce(array_to_string(p.proacl, ' '), 'defaut'), chr(10) order by p.proname), 'aucune')
  from pg_proc p join pg_namespace n on n.oid = p.pronamespace
 where n.nspname = 'public'
   and p.proname in ('lieues_bareme','niveau_de','lieues_du_niveau','compteurs_joueur')
order by 1;
