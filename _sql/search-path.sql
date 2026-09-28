-- =====================================================================
--  TerraFront — fixer le search_path des fonctions SECURITY DEFINER
--
--  Le risque : une fonction SECURITY DEFINER s'exécute avec les droits
--  de son propriétaire. Si son search_path n'est pas figé, il est celui
--  de l'appelant — et un utilisateur capable de créer un schéma peut y
--  placer une table ou une fonction qui prendra la place de la vraie.
--  La fonction, elle, s'exécutera quand même avec les pleins droits.
--
--  Cinq fonctions sont dans ce cas : demarrer_paquet, mettre_en_vente,
--  retirer_de_la_vente, statut_paquets, vendre_au_jeu.
--
--  On ne devine pas leurs signatures : pg_proc les donne, correctement
--  échappées, via oid::regprocedure.
--
--  search_path = public, extensions : « public » parce que c'est là que
--  vivent tes tables, « extensions » parce que certaines fonctions
--  utilisent peut-être une fonction d'extension sans la qualifier, et
--  qu'un search_path trop étroit la casserait. Ni l'un ni l'autre n'est
--  modifiable par un joueur, donc la faille est fermée dans les deux cas.
--
--  Idempotent : relançable, il ne touche que ce qui n'est pas déjà réglé.
-- =====================================================================

do $$
declare
  r record;
  n integer := 0;
begin
  for r in
    select p.oid::regprocedure as signature
      from pg_proc p
      join pg_namespace ns on ns.oid = p.pronamespace
     where ns.nspname = 'public'
       and p.prosecdef
       and not exists (select 1 from unnest(coalesce(p.proconfig, '{}')) c
                        where c like 'search\_path=%')
     order by p.proname
  loop
    execute format('alter function %s set search_path to ''public'', ''extensions''',
                   r.signature);
    raise notice 'corrigé : %', r.signature;
    n := n + 1;
  end loop;
  raise notice '% fonction(s) corrigée(s)', n;
end $$;

-- ---------------------------------------------------------------------
--  Vérification : cette requête doit maintenant ne rien renvoyer
-- ---------------------------------------------------------------------
select p.proname,
       coalesce(array_to_string(p.proconfig, ', '), '(aucun réglage)') as reglages
  from pg_proc p
  join pg_namespace n on n.oid = p.pronamespace
 where n.nspname = 'public'
   and p.prosecdef
   and not exists (select 1 from unnest(coalesce(p.proconfig, '{}')) c
                    where c like 'search\_path=%')
 order by p.proname;

-- ---------------------------------------------------------------------
--  À TESTER DANS LE JEU APRÈS EXÉCUTION
-- ---------------------------------------------------------------------
--  Changer le search_path d'une fonction change la façon dont elle
--  résout les noms. Le risque est faible mais réel, et ces cinq
--  fonctions touchent à l'argent du jeu. Vérifie dans cet ordre :
--
--    1. Ouvrir un paquet gratuit        -> demarrer_paquet, statut_paquets
--    2. Mettre une commune en vente     -> mettre_en_vente
--    3. La retirer de la vente          -> retirer_de_la_vente
--    4. Vendre une commune au jeu       -> vendre_au_jeu
--
--  Si l'une d'elles échoue, annule-la seule :
--    alter function public.<nom>(<args>) reset search_path;
--  puis envoie-moi son message d'erreur.
-- =====================================================================
