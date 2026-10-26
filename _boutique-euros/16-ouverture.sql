-- ===========================================================================
--  TerraFront — boutique en euros : 16. OUVERTURE à tous les joueurs
--  À passer seulement quand : clé Stripe réelle + webhook réel en place,
--  CGV v4 actives (15), un achat réel de contrôle fait puis remboursé.
--
--  1. Les commandes du MODE TEST sont effacées (session Stripe « cs_test_… »,
--     et les paniers abandonnés sans session) : elles ne comptent plus dans
--     le bandeau. Les commandes RÉELLES ne sont jamais touchées (on les garde
--     10 ans pour la comptabilité), même remboursées.
--  2. Les objets des testeurs restent à eux, en cadeau (sans commande) ; ils
--     reçoivent aussi tous les objets en vente qu'ils n'ont pas encore (pour
--     la promo). Le pass de saison n'est pas donné.
--  3. La boutique s'ouvre à tous : boutique_ouverte = true.
--  Rejouable. Contrôle attendu : 0 | 0 | (nombre d'objets) | true
-- ===========================================================================
begin;

-- 1. les commandes de test : on détache d'abord les objets qu'elles ont livrés
create temporary table cmd_test on commit drop as
  select id from public.euros_commandes
   where stripe_session like 'cs_test\_%'
      or (stripe_session is null and statut in ('creee', 'annulee'));

update public.euros_inventaire set commande_id = null
 where commande_id in (select id from cmd_test);
delete from public.euros_commandes where id in (select id from cmd_test);

-- 2. les testeurs : tout ce qui est en vente, en cadeau (sauf le pass)
insert into public.euros_inventaire(joueur_id, article_id, commande_id)
select t.id::uuid, a.id, null
  from jsonb_array_elements_text(coalesce(public.euros_reglage('testeurs'), '[]'::jsonb)) as t(id)
  cross join public.euros_articles a
 where a.actif and a.type not in ('pass', 'collection')
on conflict (joueur_id, article_id) do nothing;

-- 3. ouverture
insert into public.euros_reglages(cle, valeur) values ('boutique_ouverte', 'true')
on conflict (cle) do update set valeur = excluded.valeur;

commit;

-- contrôle : commandes de test restantes | objets encore liés à une commande de test |
--            objets offerts aux testeurs | boutique ouverte
select (select count(*) from public.euros_commandes where stripe_session like 'cs_test\_%')         as commandes_test,
       (select count(*) from public.euros_inventaire i
          join public.euros_commandes c on c.id = i.commande_id
         where c.stripe_session like 'cs_test\_%')                                                    as objets_test_lies,
       (select count(*) from public.euros_inventaire i
         where i.joueur_id::text in (select jsonb_array_elements_text(public.euros_reglage('testeurs')))
           and i.commande_id is null)                                                                 as offerts_testeurs,
       (select valeur from public.euros_reglages where cle = 'boutique_ouverte')                      as boutique_ouverte;
