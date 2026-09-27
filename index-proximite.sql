-- =====================================================================
--  TerraFront — trois index, aucune règle changée
--
--  communes_proches met 46 ms par commune. Ce n'est pas la fonction qui
--  est en cause : elle fait déjà le pré-filtre par rectangle. C'est
--  qu'aucun index ne l'aide.
--
--  Aujourd'hui, pour chaque cible, Postgres parcourt toutes les communes
--  du joueur — 1 181 pour Maroli — et va chercher les coordonnées de
--  chacune, avant d'en jeter 99 % sur le rectangle.
--
--  Avec un index sur les coordonnées il peut commencer par le rectangle :
--  un carré de 40 km sur 40 contient environ cent communes sur les
--  34 739 du pays. Le reste n'est jamais regardé.
--
--  CE FICHIER NE CHANGE AUCUNE FORMULE. Les chances de combat, les
--  coûts, les distances : rien n'est touché. Un index ne modifie jamais
--  un résultat, seulement le chemin pour l'obtenir. C'est pour ça qu'il
--  est sans risque sur une fonction qui décide des combats.
--
--  Idempotent.
-- =====================================================================

-- 1. Le rectangle de proximité, cœur du problème.
create index if not exists communes_coord_idx
  on public.communes (latitude, longitude);

-- 2. « Les communes de ce joueur » — utilisé par communes_proches, mais
--    aussi par le chargement de la collection et de la carte.
create index if not exists possessions_joueur_idx
  on public.possessions (joueur_id);

-- 3. Le filtre des raretés de l'onglet Combat. Dans la mesure précédente,
--    il écartait 33 710 lignes en 92 ms, à chaque chargement.
create index if not exists communes_tier_idx
  on public.communes (tier);

-- Les statistiques du planificateur doivent connaître les nouveaux index
-- avant de s'en servir.
analyze public.communes;
analyze public.possessions;

-- =====================================================================
--  LA MÊME MESURE QU'AVANT
-- =====================================================================
--  Exactement la requête précédente, pour que les deux chiffres soient
--  comparables. Avant : 9 191 ms.

select set_config(
  'request.jwt.claims',
  json_build_object('sub', (select id from joueurs where pseudo = 'Maroli'))::text,
  true);

explain analyze
select * from public.apercu_attaques(
  array(select p.commune_code
          from possessions p
          join communes c on c.code = p.commune_code
         where c.tier in ('rare', 'legendaire')
           and p.joueur_id <> (select id from joueurs where pseudo = 'Maroli')
         limit 200),
  'normale');

--  Ce que j'attends : entre 300 ms et 1 s. Si on descend là, l'onglet
--  Combat peut demander ses chances au serveur en un appel, et le
--  désaccord vu par Oshannir disparaît.
--
--  Si ça reste au-dessus de 2 s, il faudra recopier les coordonnées dans
--  possessions pour que tout tienne dans un seul index. C'est faisable
--  mais ça ajoute une colonne et un déclencheur — on ne le fait que si
--  la mesure l'exige.
-- =====================================================================
