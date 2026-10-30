-- ===========================================================================
--  TerraFront — LECTURE SEULE (30 octobre 2026) — à exporter en CSV
--  Avant de coder la quête d'Halloween (communes hantées) : le texte exact
--  des fonctions qu'on va retoucher, et l'état des 3 communes.
--  Une seule table : quoi | detail. Ne modifie rien. Aucun pseudo.
-- ===========================================================================
select 'fonction ' || p.proname || '(' || pg_get_function_identity_arguments(p.oid) || ')' as quoi,
       case when pg_get_functiondef(p.oid) ~* '(secret|x-terrafront|net\.http|bearer|authorization|apikey)'
            then '[masqué : contient un secret ou un envoi réseau]'
            else pg_get_functiondef(p.oid) end as detail
  from pg_proc p join pg_namespace n on n.oid = p.pronamespace
 where n.nspname = 'public' and p.prokind = 'f'
   and p.proname in ('terra_ouvrir_paquet', 'draw_commune', 'titres_possibles', 'halloween_options',
                     'terra_ouvrir_paquet_b', 'boutique_ouvrir_paquet')
union all
select 'config halloween', coalesce((select valeur::text from config_jeu where cle = 'halloween'), 'absente')
union all
select 'commune ' || c.code || ' ' || c.nom,
       'palier=' || c.tier || ' ; front=' || case when exists (select 1 from possessions p where p.commune_code = c.code) then 'possédée' else 'libre' end
  from communes c where c.code in ('49050', '86203', '24255')
order by 1;
