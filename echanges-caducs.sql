-- =====================================================================
--  TerraFront — une proposition d'échange devient caduque quand la
--  commune change de main
--
--  Constat : un échange proposé reste affiché même quand le joueur ne
--  possède plus la commune. Il ne peut pas aboutir — accepter_echange
--  revérifie la propriété sous verrou et refuse — mais les deux joueurs
--  l'ignorent et attendent une réponse qui ne viendra pas.
--
--  Le défaut est dans mes_echanges() : elle ne filtre que sur
--  etat = 'en_attente' et ne regarde jamais possessions.
--
--  Choix : on ANNULE la proposition plutôt que de simplement la cacher.
--  La cacher laisserait une ligne « en_attente » éternelle en base, que
--  rien ne nettoierait, et qui ressortirait au premier changement de
--  requête. L'annulation est un état, donc une explication.
--
--  Idempotent.
-- =====================================================================

drop function if exists public.mes_echanges();

create function public.mes_echanges()
returns table(id bigint, sens text, autre_pseudo text, autre_id uuid,
              je_donne_code text, je_donne_nom text, je_donne_dept text,
              je_recois_code text, je_recois_nom text, je_recois_dept text,
              tier text, commission integer, expire_le timestamptz, mot text)
language plpgsql
security definer
set search_path to 'public'
as $function$
declare
  v_uid uuid := auth.uid();
begin
  perform expirer_echanges();

  -- Une commune a pu être vendue, conquise ou échangée depuis la
  -- proposition. Dans ce cas l'échange ne peut plus aboutir : on le clôt
  -- au lieu de le laisser traîner. Limité aux échanges du joueur qui
  -- appelle, pour ne pas balayer toute la table à chaque affichage —
  -- l'autre partie verra l'annulation dès sa prochaine consultation.
  update echanges e
     set etat = 'annule', repondu_le = now()
   where e.etat = 'en_attente'
     and (e.proposant = v_uid or e.destinataire = v_uid)
     and (not exists (select 1 from possessions p
                       where p.commune_code = e.commune_proposant
                         and p.joueur_id = e.proposant)
       or not exists (select 1 from possessions p
                       where p.commune_code = e.commune_destinataire
                         and p.joueur_id = e.destinataire));

  return query
  select
    e.id,
    case when e.proposant = v_uid then 'envoye' else 'recu' end,
    j.pseudo,
    j.id,
    cd.code, cd.nom, cd.departement,
    cr.code, cr.nom, cr.departement,
    cd.tier,
    commission_echange(cd.tier),
    e.expire_le,
    e.message
  from echanges e
  join joueurs  j  on j.id = case when e.proposant = v_uid then e.destinataire else e.proposant end
  -- "je donne" et "je recois" dependent du cote ou je me trouve
  join communes cd on cd.code = case when e.proposant = v_uid
                                     then e.commune_proposant else e.commune_destinataire end
  join communes cr on cr.code = case when e.proposant = v_uid
                                     then e.commune_destinataire else e.commune_proposant end
  where e.etat = 'en_attente'
    and (e.proposant = v_uid or e.destinataire = v_uid)
  order by e.cree_le desc;
end;
$function$;

grant execute on function public.mes_echanges() to authenticated;

-- ---------------------------------------------------------------------
--  Combien de propositions étaient déjà caduques
-- ---------------------------------------------------------------------
select count(*) as propositions_caduques
  from echanges e
 where e.etat = 'en_attente'
   and (not exists (select 1 from possessions p
                     where p.commune_code = e.commune_proposant
                       and p.joueur_id = e.proposant)
     or not exists (select 1 from possessions p
                     where p.commune_code = e.commune_destinataire
                       and p.joueur_id = e.destinataire));
-- =====================================================================
