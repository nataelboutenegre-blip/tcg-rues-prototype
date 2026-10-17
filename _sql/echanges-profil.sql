-- ===========================================================================
--  TerraFront — stat « Échanges » du profil (17 octobre 2026, demande d'Arkhannou)
--
--  echanges_joueur(joueur) -> { echanges, partenaires }
--    Saison 1 : journal, type 'echange'. Chaque échange y laisse UNE ligne
--               par joueur (acteur = le joueur, cible = l'autre) : on compte
--               les lignes où le joueur est acteur, donc 1 par échange.
--    Saison 2 : terra_echanges acceptés (ils n'écrivent pas dans le journal,
--               pas de double compte).
--  Ni le journal ni terra_echanges ne sont vidés à la clôture : la stat
--  couvre toutes les saisons.
--
--  Ne touche ni à profil_joueur ni au calcul du niveau. Lecture seule,
--  rejouable. Sans ce fichier, le profil s'affiche sans le bloc Échanges.
-- ===========================================================================

create or replace function public.echanges_joueur(p_joueur uuid)
returns jsonb
language sql
stable
security definer
set search_path to 'public'
as $function$
  with tous as (
    select j.cible as autre
      from journal j
     where j.type = 'echange' and j.acteur = p_joueur
    union all
    select case when e.proposant = p_joueur then e.destinataire else e.proposant end
      from terra_echanges e
     where e.etat = 'accepte'
       and (e.proposant = p_joueur or e.destinataire = p_joueur)
  )
  select jsonb_build_object(
    'echanges',    count(*)::integer,
    'partenaires', count(distinct autre)::integer
  )
  from tous;
$function$;

revoke all on function public.echanges_joueur(uuid) from public, anon;
grant execute on function public.echanges_joueur(uuid) to authenticated;

-- ---------------------------------------------------------------------------
--  Contrôle : les 5 plus gros échangeurs (affichage seulement, rien d'écrit)
-- ---------------------------------------------------------------------------
select jo.pseudo,
       (echanges_joueur(jo.id)->>'echanges')::integer    as echanges,
       (echanges_joueur(jo.id)->>'partenaires')::integer as partenaires
  from joueurs jo
 order by 2 desc
 limit 5;
