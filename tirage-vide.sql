-- =====================================================================
--  TerraFront — un tirage vide : le rendre gratuit, visible et tracé
--
--  Constat : depuis le 19 septembre, 24 paquets sur 1 293 se sont
--  arrêtés avant la cinquième carte, sans aucun message. Le défaut a
--  traversé la réécriture complète de draw_commune du 24 septembre,
--  donc il n'est pas dans draw_commune : il est dans tirer_carte, créée
--  vers le 19, ou dans la boucle du navigateur.
--
--  Ce fichier ne corrige PAS la cause, qui reste inconnue. Il fait
--  trois choses qui sont justes quelle que soit la cause :
--
--   1. Il rend le tirage au joueur. Aujourd'hui le compteur est
--      décrémenté avant le tirage ; quand le tirage revient vide il n'y
--      a pas d'exception, donc rien n'est annulé, et le joueur paie une
--      carte qu'il ne reçoit pas.
--
--   2. Il rend l'échec visible. La fonction renvoyait NULL, ce que le
--      navigateur interprète comme « arrête-toi », sans rien afficher.
--
--   3. Il laisse une trace. RAISE WARNING écrit dans les logs Postgres
--      et n'est PAS annulé par le rollback : la prochaine occurrence
--      sera donc datée, nominative, et lisible en cherchant le mot
--      TERRAFRONT dans Logs → Postgres.
--
--  Idempotent. La signature ne change pas : rien à redéployer côté site.
-- =====================================================================

create or replace function public.tirer_carte(p_saison text)
returns jsonb
language plpgsql
security definer
set search_path to 'public'
as $function$
declare
  v_uid uuid := auth.uid();
  v_reste integer;
  v_carte jsonb;
  v_libres integer;
begin
  if v_uid is null then raise exception 'Non connecté'; end if;

  -- consomme un tirage (la ligne est verrouillée : deux appels simultanés
  -- ne peuvent pas tricher)
  update joueurs set tirages_restants = tirages_restants - 1
    where id = v_uid and tirages_restants > 0
    returning tirages_restants into v_reste;
  if not found then
    raise exception 'Aucun tirage disponible : ouvre d''abord un paquet';
  end if;

  -- si le tirage échoue, tout est annulé, y compris le tirage consommé
  select to_jsonb(d) into v_carte from draw_commune(p_saison) d limit 1;

  -- LA GARDE.
  -- draw_commune est censée lever une exception quand elle ne trouve
  -- rien. Il arrive qu'elle renvoie zéro ligne à la place. Sans ce test,
  -- v_carte reste NULL, « NULL || jsonb_build_object(...) » vaut NULL,
  -- la fonction rend NULL sans erreur, le compteur reste décrémenté, et
  -- le joueur perd une carte sans le savoir.
  if v_carte is null then
    -- combien de communes restent libres, au moment exact de l'incident :
    -- si ce nombre est grand, le pot n'y est pour rien
    select count(*) into v_libres
      from communes c
      left join possessions p on p.commune_code = c.code
     where p.commune_code is null;

    -- écrit dans les logs Postgres et survit à l'annulation qui suit
    raise warning 'TERRAFRONT tirage_vide joueur=% saison=% reste=% libres=%',
                  v_uid, coalesce(p_saison, '(null)'), v_reste, v_libres;

    raise exception 'Le tirage n''a rien renvoyé. Ton tirage t''est rendu, réessaie.';
  end if;

  return v_carte || jsonb_build_object('tirages_restants', v_reste);
end;
$function$;

-- ---------------------------------------------------------------------
--  Vérification immédiate : un tirage normal doit toujours marcher
-- ---------------------------------------------------------------------
-- Rien à lancer ici : ouvre simplement un paquet dans le jeu. Cinq
-- cartes = la garde ne gêne pas.

-- ---------------------------------------------------------------------
--  Retrouver les incidents, plus tard
-- ---------------------------------------------------------------------
--  Dashboard -> Logs -> Postgres Logs -> chercher : TERRAFRONT
--  Chaque ligne donne le joueur, la saison passée par le navigateur, le
--  compteur et le nombre de communes libres à la seconde près.
-- =====================================================================
