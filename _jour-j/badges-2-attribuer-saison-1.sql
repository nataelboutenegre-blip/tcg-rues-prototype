-- ===========================================================================
--  TerraFront — attribuer les distinctions et le badge OG de la saison 1
--
--  À LANCER JUSTE AVANT LA CLÔTURE (jour J, avant l'étape 2, ou la veille au
--  soir) : après la clôture, les possessions et le Radar sont remis à zéro et
--  le calcul serait faux.
--  Rejouable : les badges saison-1 sont effacés puis recalculés.
--  Avant badges-1-installation.sql : non (il faut la table et le calcul).
-- ===========================================================================
delete from public.joueur_badges where saison = 'saison-1';
insert into public.joueur_badges(joueur_id, badge, saison, valeur)
select joueur_id, badge, 'saison-1', valeur from public.distinctions_calcul('saison-1');

select badge, count(*) as joueurs,
       string_agg(j.pseudo || coalesce(' (' || b.valeur || ')', ''), ', ' order by j.pseudo) filter (where badge <> 'og') as gagnants
  from public.joueur_badges b join public.joueurs j on j.id = b.joueur_id
 where b.saison = 'saison-1'
 group by badge
 order by badge = 'og', badge;
