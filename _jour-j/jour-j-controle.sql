-- ===========================================================================
--  TerraFront — JOUR J : contrôle après la bascule (lecture seule)
--  À lancer à la fin du jour J (et à la fin de la répétition dans la
--  branche). Ne modifie rien. Un seul résultat (JSON) à envoyer à Claude.
--  N'appelle PAS saison_courante() (qui arme le compte à rebours).
-- ===========================================================================
select jsonb_pretty(jsonb_build_object(
  'saisons', (select jsonb_agg(jsonb_build_object('id', id, 'etat', etat, 'debut', debut, 'fin_reelle', fin_reelle) order by debut desc)
                from (select * from public.saisons order by debut desc limit 3) s),
  'saison2_active_doit_etre_true', public.saison2_active(),
  'palmares_saison_1', (select jsonb_build_object('lignes', count(*), 'podium',
                           (select jsonb_agg(pseudo || ' (' || points || ')' order by rang) from public.classement_saisons
                             where saison = 'saison-1' and rang <= 3))
                          from public.classement_saisons where saison = 'saison-1'),
  'raretes_attendu_302_1015_3406_12841_17183', (select jsonb_object_agg(tier, n) from
                         (select tier, count(*) n from public.communes group by tier) x),
  'numeros_coherents', (select bool_and(rang between 1 and palier_total) from public.communes),
  'front_possessions', (select jsonb_build_object('communes', count(*), 'joueurs', count(distinct joueur_id),
                          'gardees', count(*) filter (where gardee)) from public.possessions),
  'terra_collection', (select jsonb_build_object('joueurs', count(distinct joueur_id), 'cartes', coalesce(sum(exemplaires), 0),
                          'par_origine', (select jsonb_object_agg(origine, n) from
                             (select origine, count(*) n from public.terra_collection group by origine) o))
                         from public.terra_collection),
  'soldes', (select jsonb_build_object('joueurs', count(*), 'non_nuls', count(*) filter (where coalesce(solde, 0) <> 0),
                     'total', coalesce(sum(solde), 0)) from public.joueurs),
  'restes_doivent_etre_0', jsonb_build_object(
     'sieges', (select count(*) from public.sieges),
     'garnisons', (select count(*) from public.front_garnisons),
     'radar_parties', (select count(*) from public.radar_parties),
     'annonces_s1', (select count(*) from public.annonces))
)) as controle_jour_j;
