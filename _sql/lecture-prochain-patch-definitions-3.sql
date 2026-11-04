-- ===========================================================================
--  LECTURE SEULE — prochain patch d'équilibrage, 3e partie (4/11/2026)
--  Le plafond d'énergie des bonus (60) est écrit en dur dans plusieurs
--  fonctions (quêtes, récolte, garnison, parrainage…). Avec un maximum à 90
--  le jour J, chacune doit suivre, sinon un bonus ferait PERDRE de l'énergie
--  à un joueur au-dessus de 60. Cette lecture renvoie le code de toutes les
--  fonctions qui touchent à l'énergie du Front et contiennent un « 60 »,
--  sauf celles déjà lues.
--  Aucun pseudo, aucune donnée de joueur. Ne modifie rien.
-- ===========================================================================
with fonctions as (
  select p.oid,
         p.proname || '(' || pg_get_function_identity_arguments(p.oid) || ')' as nom,
         replace(encode(convert_to(pg_get_functiondef(p.oid), 'UTF8'), 'base64'), E'\n', '') as b
    from pg_proc p
   where p.pronamespace = 'public'::regnamespace
     and p.prokind = 'f'
     and p.prosrc ~ 'front_energie'
     and p.prosrc ~ '\m60\M'
     and p.proname not in ('front_energie', 'front_energie_lire', 'garnison_retirer', 'parrainage_jour',
                           'front_recolter', 'reclamer_quete')
),
tout(section, nom, partie, contenu) as (
  select '1. fonction', f.nom, g.i,
         substr(f.b, (g.i - 1) * 6000 + 1, 6000)
    from fonctions f
   cross join lateral generate_series(1, greatest(1, ceil(length(f.b) / 6000.0)::int)) as g(i)
)
select count(*) over () as lignes, section, nom, partie, contenu
  from tout
 order by section, nom, partie;
