-- ===========================================================================
--  LECTURE SEULE — saison 3, la Suisse : quelles fonctions TIRENT ou
--  RECONNAISSENT des communes sans filtre de pays ? (4/11/2026)
--  terra_ouvrir_paquet tire 5 communes au hasard dans toute la table : la
--  Suisse y entrerait dès son insertion. Cette lecture liste, sans leur code,
--  toutes les fonctions qui lisent la table communes et qui tirent au hasard
--  ou comparent des noms (mini-jeux, boutiques, paquets), avec ce qu'elles
--  filtrent déjà. Seulement des noms de fonctions et des oui/non.
--  Aucun pseudo, aucune donnée de joueur. Ne modifie rien.
-- ===========================================================================
with f as (
  select p.proname || '(' || pg_get_function_identity_arguments(p.oid) || ')' as nom, p.prosrc as s
    from pg_proc p
   where p.pronamespace = 'public'::regnamespace
     and p.prokind = 'f'
     and p.prosrc ~* '\mcommunes\M'
)
select count(*) over () as lignes,
       nom,
       (s ~* 'random\(\)')                                              as tire_au_hasard,
       (s ~* 'unaccent|lower\(\s*c?\.?nom|nom_norm|ilike|similarity')    as compare_des_noms,
       (s ~* 'est_metropole|est_canton')                                as filtre_s3,
       (s ~* 'length\(\s*(c\.)?departement\s*\)')                       as filtre_longueur,
       (s ~* 'photo')                                                   as parle_photo,
       length(s)                                                        as taille
  from f
 where s ~* 'random\(\)' or s ~* 'unaccent|lower\(\s*c?\.?nom|nom_norm|ilike|similarity'
 order by nom;
