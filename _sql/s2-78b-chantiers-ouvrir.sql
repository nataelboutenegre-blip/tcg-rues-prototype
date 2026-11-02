-- ===========================================================================
--  TerraFront — s2-78b : ouvrir les grands chantiers à tout le monde
--  À lancer APRÈS s2-78, une fois l'essai fini, le jour de l'annonce.
--
--  Les essais des comptes testeurs sont effacés, pour que personne ne parte
--  avec de l'avance (ni chantier, ni nom gravé, ni heures sur la merveille) :
--  les TP dépensés en ouvriers et en outils leur sont rendus, leur équipe
--  repart à 3 ouvriers, et Notre-Dame repart de zéro.
--
--  Rejouable sans dégât tant que personne n'a joué : à ne lancer qu'une fois
--  le module ouvert (sinon il effacerait les vrais chantiers des joueurs).
--  Contrôle en une ligne.
-- ===========================================================================
begin;

-- 1) on rend les TP dépensés pendant l'essai (seulement si le module était encore fermé)
select set_config('terrafront.motif', 'chantier_essai_rendu', true);
update public.joueurs j
   set solde = coalesce(j.solde, 0) + x.depense
  from (select joueur_id, -sum(montant)::integer as depense
          from public.mouvements_points
         where motif in ('chantier_equipe', 'chantier_outils')
         group by joueur_id) x
 where j.id = x.joueur_id and x.depense > 0
   and coalesce((select (valeur::jsonb->>'ouvert')::int from public.config_jeu where cle = 'chantiers'), 0) = 0;

-- 2) on efface les essais (seulement si le module était encore fermé)
do $o$
begin
  if coalesce((select (valeur::jsonb->>'ouvert')::int from public.config_jeu where cle = 'chantiers'), 0) = 0 then
    delete from public.chantiers_mecenes;
    delete from public.chantiers_merveilles;
    delete from public.chantiers_restaurations;
    delete from public.chantiers;
    delete from public.chantiers_equipes;
    insert into public.chantiers_merveilles (commune_code, total, ouverte_le)
    select cm.commune_code, coalesce((public.chantiers_reglages()->>'merveille')::numeric, 20000), now()
      from public.chantiers_monuments cm
     where cm.taille = 'merveille'
     order by cm.ordre nulls last
     limit 1;
  end if;
end $o$;

-- 3) on ouvre
update public.config_jeu set valeur = (valeur::jsonb || '{"ouvert": 1}'::jsonb) where cle = 'chantiers';

commit;

-- contrôle : ouvert = 1, aucun chantier, la merveille ouverte (75104 = Notre-Dame)
select (select valeur::jsonb->>'ouvert' from public.config_jeu where cle = 'chantiers')   as ouvert,
       (select count(*) from public.chantiers)                                          as chantiers,
       (select count(*) from public.chantiers_restaurations)                            as restaurations,
       (select commune_code from public.chantiers_merveilles where finie_le is null)     as merveille_ouverte;
