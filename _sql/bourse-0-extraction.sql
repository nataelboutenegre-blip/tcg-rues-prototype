-- ===========================================================================
--  TerraFront — Récupérer le code du circuit de la Bourse
--
--  LECTURE SEULE. Ne crée rien, ne modifie rien, n'appelle aucune fonction
--  du jeu (surtout pas saison_courante).
--
--  POURQUOI
--    Oshannir a trouvé un trou : il met une légendaire en vente à 1 point,
--    son partenaire fait pareil, ils s'achètent mutuellement. Coût total :
--    2 points. Le même échange par l'onglet Échange coûte 200 points à
--    chacun, soit 400. La Bourse contourne la commission.
--
--    Pour le corriger il faut modifier `acheter` et `mettre_en_vente`. Or
--    leur code n'existe nulle part dans le dépôt : il n'est que dans
--    Supabase. Je refuse de les réécrire de mémoire — c'est la meilleure
--    façon de casser la Bourse un vendredi soir.
--
--    Ce fichier sort leur code exact. Je partirai de là.
--
--  CE QUE TU EN FAIS
--    Colle-le dans l'éditeur SQL de Supabase. Le résultat est UNE seule
--    cellule : clique dessus pour la déployer, copie tout, renvoie-le moi.
--
--  AU PASSAGE, UN PROBLÈME PLUS LARGE
--    16 des 48 fonctions que le jeu appelle ne sont dans aucun fichier du
--    dépôt. Ton propre principe — tout le SQL exécuté doit être versionné —
--    n'est donc pas tenu sur un tiers du serveur. Ce n'est pas urgent ce
--    soir, mais c'est le genre de dette qui se paie le jour où une
--    fonction se casse et où plus personne ne sait ce qu'elle contenait.
--    On rapatriera le reste plus tard.
-- ===========================================================================

select string_agg(def, E'\n\n-- ' || repeat('=', 70) || E'\n\n' order by nom)
       as code_des_fonctions
  from (
    select p.proname || '(' || pg_get_function_identity_arguments(p.oid) || ')'
             as nom,
           pg_get_functiondef(p.oid) as def
      from pg_proc p
      join pg_namespace n on n.oid = p.pronamespace
     where n.nspname = 'public'
       and p.proname in ('acheter',
                         'mettre_en_vente',
                         'retirer_de_la_vente',
                         'vendre_au_jeu',
                         'prix_rachat',
                         'commission_echange')
  ) f;
