-- =====================================================================
--  TerraFront — réponse aux alertes de sécurité de Supabase (5 octobre)
--
--  1. « Function Search Path Mutable » (18 fonctions + 4 des derniers
--     fichiers) : on fixe search_path = public. Une fonction sans
--     search_path fixe peut, en théorie, appeler une autre fonction du même
--     nom placée ailleurs. Aucun changement de résultat.
--
--  2. « anon … security definer … executable » (23 fonctions) : un visiteur
--     NON CONNECTÉ pouvait appeler 21 fonctions qui ne servent qu'aux
--     joueurs connectés (amis, échanges, profil, saison…). On retire ce
--     droit au visiteur. Les joueurs connectés gardent tout.
--     Restent ouvertes aux visiteurs, volontairement :
--       - totaux_paliers   (les chiffres de la page d'accueil)
--       - taux_actuels     (la page des règles)
--       - cdj_invite       (la Commune du jour sans compte)
--
--  Ce que ce fichier NE fait PAS :
--  - « authenticated … executable » (62) : c'est le fonctionnement normal
--    du jeu, toutes les actions passent par ces fonctions. Rien à changer.
--  - « unaccent dans public » : la déplacer casserait les fonctions qui
--    s'en servent (pseudos, gentilés). Risque faible, on laisse.
--  - « leaked password protection » : c'est un réglage du tableau de bord,
--    pas du SQL.
--
--  Rejouable. Ne touche à aucune donnée.
-- =====================================================================

-- ---------------------------------------------------------------------
-- 1. search_path fixe
-- ---------------------------------------------------------------------
do $$
declare
  f record;
  n int := 0;
begin
  for f in
    select p.oid::regprocedure as sig
      from pg_proc p join pg_namespace s on s.oid = p.pronamespace
     where s.nspname = 'public'
       and p.proname in (
         'ajouter_fait', 'bonus_proximite', 'cdj_cap', 'cdj_km', 'chance_intensite',
         'commission_echange', 'cout_attaque', 'cout_intensite', 'delai_attaque',
         'lieues_bareme', 'lieues_du_niveau', 'marquer_paquet_notif', 'nettoyer_pseudo',
         'niveau_de', 'points_rarete', 'prix_bouclier', 'prix_rachat',
         'reset_bouclier_changement_proprietaire',
         'cdj_region', 'radar_reglage', 'radar_rang')
  loop
    execute format('alter function %s set search_path = public', f.sig);
    n := n + 1;
  end loop;
  raise notice 'search_path fixé sur % fonctions', n;
end $$;

-- ---------------------------------------------------------------------
-- 2. Plus d'appel sans connexion, sauf les trois fonctions publiques
-- ---------------------------------------------------------------------
-- Le droit d'un visiteur vient soit d'un droit donné à anon, soit du droit
-- par défaut donné à tout le monde (PUBLIC). On retire les deux, puis on
-- redonne explicitement le droit aux joueurs connectés pour ne rien leur
-- enlever.
do $$
declare
  f record;
  n int := 0;
begin
  for f in
    select p.oid::regprocedure as sig
      from pg_proc p join pg_namespace s on s.oid = p.pronamespace
     where s.nspname = 'public'
       and p.proname in (
         'accepter_ami', 'apercu_attaques', 'bloquer_joueur', 'cibles_echange',
         'communes_proches', 'debloquer_joueur', 'demander_ami', 'enregistrer_commune_vue',
         'est_ma_commune', 'expirer_echanges', 'ma_france_resume', 'marquer_gardee',
         'mes_amis', 'mes_communes_perdues', 'mes_echanges', 'mon_etat',
         'monuments_catalogue', 'profil_joueur', 'retirer_ami', 'saison_courante', 'succes')
  loop
    execute format('revoke execute on function %s from public, anon', f.sig);
    execute format('grant execute on function %s to authenticated', f.sig);
    n := n + 1;
  end loop;
  raise notice 'droit des visiteurs retiré sur % fonctions', n;
end $$;

-- ---------------------------------------------------------------------
-- 3. Vérification : ce qu'un visiteur peut encore appeler
-- ---------------------------------------------------------------------
-- Doit lister seulement totaux_paliers, taux_actuels et cdj_invite
-- (cdj_invite seulement si cdj-3-invite.sql est déjà passé).
select p.proname as encore_ouverte_aux_visiteurs
  from pg_proc p join pg_namespace s on s.oid = p.pronamespace
 where s.nspname = 'public'
   and p.prosecdef
   and p.prorettype <> 'trigger'::regtype
   and has_function_privilege('anon', p.oid, 'execute')
 order by 1;
