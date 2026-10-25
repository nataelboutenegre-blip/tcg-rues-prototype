-- ===========================================================================
--  TerraFront — le dos de carte OG (25 octobre 2026, aperçu « Nacre » validé)
--  Offert à tous les joueurs qui ont le badge OG de la saison 1 (48).
--  Hors catalogue (actif = false) : on ne peut ni l'acheter ni le gagner
--  autrement ; boutique() le montre déjà possédé à ceux qui l'ont.
--  Le paquet nacré suit le dos (côté jeu, rien en base).
--  Rejouable. Finit par un contrôle : attendu 48 / 48 / true.
-- ===========================================================================
begin;

insert into public.boutique_articles (id, type, nom, description, prix, actif, ordre) values
  ('dos-og', 'dos', 'OG · Saison 1', 'Offert aux joueurs de la saison 1', 0, false, 1)
on conflict (id) do update set nom = excluded.nom, description = excluded.description,
                               actif = false, ordre = excluded.ordre;

insert into public.boutique_inventaire (joueur_id, article_id)
select distinct b.joueur_id, 'dos-og'
  from public.joueur_badges b
 where b.badge = 'og' and b.saison = 'saison-1'
on conflict do nothing;

commit;

select (select count(distinct joueur_id) from public.joueur_badges where badge = 'og' and saison = 'saison-1') as joueurs_og,
       (select count(*) from public.boutique_inventaire where article_id = 'dos-og')                         as dos_og_offerts,
       (select not actif from public.boutique_articles where id = 'dos-og')                                  as hors_catalogue;
