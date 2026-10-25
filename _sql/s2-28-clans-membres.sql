-- ===========================================================================
--  s2-28-clans-membres.sql — voir les membres de n'importe quel clan
--  (26 octobre 2026, aperçu validé par Nataël : « parfait »)
--
--  clan_membres_voir(clan) : pour chaque membre, son pseudo, s'il est chef,
--  ses communes en Front et son dernier jour joué (point vert / gris dans le
--  jeu). PAS l'activité détaillée du jour : elle reste réservée au clan
--  lui-même (clan_activite). Lecture seule, joueurs connectés seulement.
--  Rejouable. Contrôle attendu : true | N (N = nombre de clans)
-- ===========================================================================

create or replace function public.clan_membres_voir(p_clan uuid)
 returns table(joueur_id uuid, pseudo text, chef boolean, communes integer, dernier_jour date)
 language sql
 stable security definer
 set search_path to 'public'
as $f$
  select j.id, j.pseudo::text, (c.chef = j.id),
         (select count(*) from possessions p where p.joueur_id = j.id)::integer,
         (select max(d.jour) from jours_joues d where d.joueur_id = j.id)
    from clan_membres m
    join clans c on c.id = m.clan_id
    join joueurs j on j.id = m.joueur_id
   where m.clan_id = p_clan and auth.uid() is not null
   order by (c.chef = j.id) desc, 4 desc, j.pseudo;
$f$;

revoke all on function public.clan_membres_voir(uuid) from public, anon;
grant execute on function public.clan_membres_voir(uuid) to authenticated;

-- contrôle : ouverte aux joueurs | nombre de clans
select has_function_privilege('authenticated', 'public.clan_membres_voir(uuid)', 'execute') as ouvert_aux_joueurs,
       (select count(*) from public.clans)                                                  as clans;
