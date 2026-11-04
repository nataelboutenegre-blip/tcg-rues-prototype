-- ===========================================================================
--  LECTURE SEULE — saison 3, la Suisse côté serveur (5e partie : boutiques, Ta boutique, défilé de contrat, Plus ou moins, ancien contrat)
--  (4/11/2026). Code en production des fonctions qui font « métropole =
--  département de 2 caractères » (length(departement) = 2), qui ont une
--  liste de départements en dur ou qui rangent les départements en régions.
--  Un canton suisse fait 2 lettres : chaque fonction doit être relue pour
--  décider si la Suisse y entre ou non, avant d'insérer la moindre commune.
--  Code encodé en base64, par morceaux de 6 000 caractères ; la colonne
--  « lignes » doit rester sous 100 (l'éditeur coupe au-delà).
--  Aucun pseudo, aucune donnée de joueur. Ne modifie rien.
-- ===========================================================================
with fonctions as (
  select p.oid,
         p.proname || '(' || pg_get_function_identity_arguments(p.oid) || ')' as nom,
         replace(encode(convert_to(pg_get_functiondef(p.oid), 'UTF8'), 'base64'), E'\n', '') as b
    from pg_proc p
   where p.pronamespace = 'public'::regnamespace
     and p.prokind = 'f'
     and p.proname in ('boutique_ouvrir_collection','boutique_ouvrir_paquet','bt_tirer','contrat_defile','pom_generer','signer_contrat')
),
tout(nom, partie, contenu) as (
  select f.nom, g.i, substr(f.b, (g.i - 1) * 6000 + 1, 6000)
    from fonctions f
   cross join lateral generate_series(1, greatest(1, ceil(length(f.b) / 6000.0)::int)) as g(i)
)
select count(*) over () as lignes, nom, partie, contenu
  from tout
 order by nom, partie;
