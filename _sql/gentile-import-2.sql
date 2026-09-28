-- =====================================================================
--  TerraFront — la colonne gentile  (version 2, corrigee)
--
--  Ce que corrige cette version : 293 codes INSEE ont DEUX articles sur
--  Wikipedia — celui de la commune actuelle et celui d'une commune
--  absorbee. Pour 140 d'entre eux les deux gentiles different, et la
--  version 1 prenait le premier venu. Surjoux-Lhopital recevait ainsi
--  « Hospitaliers », le nom des habitants de Lhopital, absorbee.
--
--  Seul le nom de la commune dans TA base permet de trancher. C'est donc
--  ici que ca se joue, pas dans le fichier.
--
--  A lancer apres avoir reimporte le NOUVEAU gentiles-propres.csv
--  (trois colonnes : code, titre, gentile) dans la table gentiles_import.
--
--  Idempotent.
-- =====================================================================

-- Les titres de Wikipedia n'ont pas toujours les accents de l'INSEE :
-- « Surjoux-Lhopital » contre « Surjoux-Lhôpital ». On compare sans.
create extension if not exists unaccent;

alter table public.communes add column if not exists gentile text;

-- ---------------------------------------------------------------------
-- 1. Un seul article par commune, choisi par son nom
-- ---------------------------------------------------------------------
with choisi as (
  select distinct on (g.code)
         g.code,
         nullif(btrim(g.gentile), '') as gentile
    from public.gentiles_import g
    join public.communes c on c.code = g.code
   order by g.code,
         -- le titre est exactement le nom de la commune
         (unaccent(lower(g.titre)) = unaccent(lower(c.nom))) desc,
         -- ou le nom suivi d'une parenthese d'homonymie : « Y (Somme) »
         (unaccent(lower(g.titre)) like unaccent(lower(c.nom)) || ' (%') desc,
         -- ou le nom est contenu dedans
         (unaccent(lower(g.titre)) like '%' || unaccent(lower(c.nom)) || '%') desc,
         length(g.titre) desc
)
update public.communes c
   set gentile = choisi.gentile
  from choisi
 where choisi.code = c.code
   and choisi.gentile is not null
   and c.gentile is distinct from choisi.gentile;

-- ---------------------------------------------------------------------
-- 2. Les droits de lecture
-- ---------------------------------------------------------------------
grant select (gentile) on public.communes to authenticated;
grant select (faits)   on public.communes to authenticated;

-- ---------------------------------------------------------------------
-- 3. Verification
-- ---------------------------------------------------------------------
select count(*)                                   as communes,
       count(gentile)                             as avec_gentile,
       round(100.0 * count(gentile) / count(*), 1) as taux_pourcent,
       count(*) filter (where gentile like '%·%')  as avec_feminin
  from public.communes;

-- Les cas qui etaient faux en version 1 : ils doivent maintenant porter
-- le gentile de la commune actuelle.
select c.nom, c.departement, c.gentile
  from public.communes c
 where c.code in ('01215', '08105', '01033', '09334')
 order by c.nom;

-- Et quelques reperes
select nom, departement, gentile
  from public.communes
 where nom in ('Y', 'Strasbourg', 'Toulon', 'Caubous')
 order by nom, departement;

-- ---------------------------------------------------------------------
-- 4. Menage, une fois les chiffres verifies
-- ---------------------------------------------------------------------
-- drop table if exists public.gentiles_import;


-- =====================================================================
--  AVANT DE LANCER CE FICHIER
--
--    1. Table Editor -> gentiles_import -> supprimer la table
--       (ou : drop table public.gentiles_import;)
--    2. New table -> Import data from CSV -> le NOUVEAU
--       gentiles-propres.csv, nom de table gentiles_import
--       Trois colonnes cette fois : code, titre, gentile.
--    3. Lancer ce fichier.
--
--  Si « create extension unaccent » echoue : Database -> Extensions ->
--  activer unaccent, puis relancer.
-- =====================================================================
