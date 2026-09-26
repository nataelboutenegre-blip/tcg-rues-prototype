-- =====================================================================
--  TerraFront — la colonne gentile
--
--  A lancer APRES avoir importe gentiles-propres.csv dans une table
--  nommee gentiles_import (voir le mode d'emploi en bas du fichier).
--
--  27 456 communes ont un gentile lisible, extrait des infobox de
--  Wikipedia FR. Rien n'est genere : ce qui ne se reduisait pas
--  proprement a un ou deux noms d'habitants a ete laisse vide plutot
--  que devine. Les communes sans gentile n'affichent simplement pas la
--  ligne, elles n'affichent pas « inconnu ».
--
--  Idempotent : relancable sans effet de bord.
-- =====================================================================

alter table public.communes add column if not exists gentile text;

-- ---------------------------------------------------------------------
-- 1. Report depuis la table importee
-- ---------------------------------------------------------------------
update public.communes c
   set gentile = nullif(btrim(g.gentile), '')
  from public.gentiles_import g
 where g.code = c.code
   and c.gentile is distinct from nullif(btrim(g.gentile), '');

-- ---------------------------------------------------------------------
-- 2. Les droits de lecture
-- ---------------------------------------------------------------------
-- Si communes est ouverte colonne par colonne, une colonne neuve n'est
-- lisible par personne tant qu'on ne l'a pas dit. Si elle est ouverte
-- en entier, ces deux lignes ne changent rien. Dans les deux cas elles
-- sont sans risque, et elles evitent une fiche muette.
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

-- Un coup d'oeil sur ce que ca donne, y compris les cas qu'on aime :
select nom, departement, gentile
  from public.communes
 where nom in ('Y', 'Ô-de-Selle', 'Strasbourg', 'Toulon', 'Caubous')
    or code in ('75056', '13055', '69123')
 order by nom;

-- ---------------------------------------------------------------------
-- 4. Menage
-- ---------------------------------------------------------------------
-- A ne lancer qu'une fois les chiffres ci-dessus verifies.
-- drop table if exists public.gentiles_import;


-- =====================================================================
--  MODE D'EMPLOI DE L'IMPORT DU CSV
--
--  Dans Supabase :
--    Table Editor  ->  New table  ->  Import data from CSV
--    fichier : gentiles-propres.csv
--    nom de la table : gentiles_import
--    Supabase devine deux colonnes text, code et gentile. Laisse comme ca.
--
--  Puis reviens ici et lance ce fichier en entier.
--
--  Pourquoi pas un gros fichier d'UPDATE ? Parce qu'il ferait 850 Ko de
--  SQL a coller dans l'editeur, ce qui passe mal. L'import CSV fait le
--  meme travail en dix secondes.
-- =====================================================================
