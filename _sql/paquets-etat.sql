-- ---------------------------------------------------------------------------
--  paquets-etat.sql — lecture seule, ne modifie rien, n'appelle aucune
--  fonction du jeu
--
--  Question unique : d'ou viennent 247 cartes par jour pour un seul joueur,
--  alors que le bouton d'achat se bloque a 5 paquets ?
--
--  Trois reponses possibles :
--   1. le plafond n'est verifie que dans le navigateur (app.js ligne 3973)
--      et pas en base
--   2. les jetons gratuits se regenerent assez vite pour tout expliquer
--   3. un paquet contient beaucoup plus de 5 cartes
--
--  Les definitions des fonctions repondent aux trois. Les compteurs reels
--  des joueurs disent lequel est le bon sans avoir a interpreter le code :
--  si paquets_achetes_jour depasse 5 chez quelqu'un, le plafond n'est pas
--  tenu en base.
--
--  Les colonnes des joueurs sont lues via to_jsonb plutot qu'en direct :
--  une colonne qui porte un autre nom affiche « (colonne absente) » au
--  lieu de faire echouer toute la requete. Et seules les six clefs utiles
--  sont extraites, pas la ligne entiere : inutile de faire remonter des
--  emails dans une conversation.
-- ---------------------------------------------------------------------------
with fonctions as (
  select 'A. ' || p.proname as quoi,
         pg_get_functiondef(p.oid) as detail
    from pg_proc p
    join pg_namespace n on n.oid = p.pronamespace
   where n.nspname = 'public'
     and (p.proname in ('demarrer_paquet', 'ouvrir_paquet', 'mon_etat',
                        'acheter_paquet', 'tirer_carte')
          or p.proname like '%jeton%')
),
config as (
  select 'B. config_jeu' as quoi,
         coalesce(string_agg(t::text, chr(10)), '(table vide)') as detail
    from config_jeu t
),
colonnes as (
  select 'C. colonnes de joueurs' as quoi,
         string_agg(column_name, ', ' order by ordinal_position) as detail
    from information_schema.columns
   where table_schema = 'public' and table_name = 'joueurs'
),
compteurs as (
  select 'D. compteurs des 6 plus gros soldes' as quoi,
         string_agg(ligne, chr(10) order by ordre) as detail
    from (
      select row_number() over (
               order by (to_jsonb(j)->>'solde')::numeric desc nulls last) as ordre,
             coalesce(to_jsonb(j)->>'pseudo', '?')
             || '  solde ' || coalesce(to_jsonb(j)->>'solde', '(colonne absente)')
             || '  achetes_jour ' || coalesce(to_jsonb(j)->>'paquets_achetes_jour', '(absente)')
             || ' du ' || coalesce(to_jsonb(j)->>'paquets_achetes_date', '(absente)')
             || '  tirages_restants ' || coalesce(to_jsonb(j)->>'tirages_restants', '(absente)')
             || '  jetons ' || coalesce(to_jsonb(j)->>'jetons_gratuits', '(absente)')
             || '  maj ' || coalesce(to_jsonb(j)->>'jetons_maj', '(absente)')
             as ligne
        from joueurs j
       order by (to_jsonb(j)->>'solde')::numeric desc nulls last
       limit 6
    ) t
)
select * from fonctions
union all select * from config
union all select * from colonnes
union all select * from compteurs
order by 1;
