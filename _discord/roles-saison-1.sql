-- ===========================================================================
--  TerraFront — les pseudos qui reçoivent un rôle Discord de la saison 1
--  (lecture seule). Copie le résultat (le JSON) et envoie-le à Claude, ou
--  colle-le dans _discord/roles-saison-1.json.
-- ===========================================================================
select jsonb_pretty(jsonb_build_object(
  '🏆 Champion · Saison 1', (select jsonb_agg(c.pseudo order by c.rang)
                               from public.classement_saisons c
                              where c.saison = 'saison-1' and c.rang <= 3),
  '🎖️ Distinction · Saison 1', (select jsonb_agg(distinct j.pseudo)
                                  from public.joueur_badges b join public.joueurs j on j.id = b.joueur_id
                                 where b.saison = 'saison-1' and b.badge <> 'og'),
  '🏅 OG', (select jsonb_agg(distinct j.pseudo)
              from public.joueur_badges b join public.joueurs j on j.id = b.joueur_id
             where b.saison = 'saison-1' and b.badge = 'og')
)) as roles_saison_1;
