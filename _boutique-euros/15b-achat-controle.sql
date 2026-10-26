-- ===========================================================================
--  TerraFront — achat réel de contrôle : retire le skin Gravure au compte
--  testeur pour pouvoir l'acheter une fois avec une vraie carte (2,49 €).
--  Le skin revient en cadeau avec 16-ouverture.sql. Rejouable.
--  Contrôle attendu : skin_gravure_possede = false | en_vente = true
-- ===========================================================================
delete from public.euros_inventaire i
 using jsonb_array_elements_text(coalesce(public.euros_reglage('testeurs'), '[]'::jsonb)) as t(id)
 where i.joueur_id = t.id::uuid and i.article_id = 'skin-gravure';

select exists(select 1 from public.euros_inventaire i
               where i.article_id = 'skin-gravure'
                 and i.joueur_id::text in (select jsonb_array_elements_text(public.euros_reglage('testeurs')))) as skin_gravure_possede,
       (select actif from public.euros_articles where id = 'skin-gravure')                                        as en_vente;
