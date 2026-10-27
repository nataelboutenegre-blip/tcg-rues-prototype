-- ===========================================================================
--  TerraFront — Outre-mer v1 : DUMP LECTURE SEULE des fonctions à préparer
--  (NE MODIFIE RIEN. N'appelle aucune fonction du jeu. Aucun secret : aucune
--   de ces fonctions ne touche http/notification. Masquage de sécurité quand
--   même, par principe.)
--
--  BUT : écrire l'éditeur « séparation métropole / outre-mer » sur les
--  définitions EXACTES en production (elles diffèrent du dépôt).
--
--  Les 8 fonctions à filtrer en v1 (comptes globaux / listes de départements
--  / affichage), + cloturer_saison en LECTURE pour confirmer que la prod colle
--  au corps déjà prouvé sûr au banc (la clôture ne sera PAS modifiée).
--
--  Résultat : un tableau. Bouton « Download CSV » au-dessus, puis me le joindre.
-- ===========================================================================
select p.proname as nom,
       pg_get_function_identity_arguments(p.oid) as arguments,
       case
         when d.def ~* '(secret|x-terrafront|net\.http|extensions\.http|bearer |authorization)'
           then '*** MASQUÉ (corps contenant un éventuel secret, non exporté) ***'
         else d.def
       end as definition
  from pg_proc p
  join pg_namespace n on n.oid = p.pronamespace
  cross join lateral (select pg_get_functiondef(p.oid) as def) d
 where n.nspname = 'public'
   and p.prokind = 'f'
   and p.proname in (
     'saison_courante',
     'totaux_paliers',
     'taux_actuels',
     'front_territoires',
     'prendre_mesure',
     'quetes_liste',
     'rebasculer_paliers',
     'rebasculer_paliers_s2',
     'terra_signer_contrat',
     'cloturer_saison'
   )
 order by p.proname, 2;
