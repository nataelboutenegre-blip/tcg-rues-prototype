-- ===========================================================================
--  TerraFront — classements de Communauté : Terra et Palmarès (9 octobre 2026)
--
--  Lecture seule pour les joueurs, aucun effet sur le jeu en cours.
--   - palmares_saisons() : les saisons terminées qui ont un palmarès archivé
--     (classement_saisons, rempli par cloturer_saison) ;
--   - palmares(saison, limite) : le classement figé d'une saison terminée,
--     mêmes colonnes que classement() ;
--   - terra_classement(limite) : la collection Terra, rangée par points de
--     rareté des communes DIFFÉRENTES (un doublon ne compte pas), puis par
--     nombre de communes. Vide tant que Terra n'est pas ouvert.
--  Rejouable. Finit par un contrôle.
-- ===========================================================================

create or replace function public.palmares_saisons()
 returns table(saison text, nom text, fin timestamptz, joueurs integer)
 language sql stable security definer set search_path to 'public'
as $f$
  select s.id::text, s.nom::text, coalesce(s.fin_reelle, s.fin_prevue), count(*)::integer
    from classement_saisons cs join saisons s on s.id = cs.saison
   where auth.uid() is not null and s.etat = 'terminee'
   group by s.id, s.nom, s.fin_reelle, s.fin_prevue, s.debut
   order by s.debut desc;
$f$;

create or replace function public.palmares(p_saison text, p_limite integer default 10)
 returns table(rang integer, joueur_id uuid, pseudo text, score integer, communes integer,
               legendaires integer, rares integer, departements integer, est_moi boolean)
 language sql stable security definer set search_path to 'public'
as $f$
  select cs.rang, cs.joueur_id, coalesce(cs.pseudo, 'Joueur')::text, cs.points, cs.communes,
         cs.legendaires, cs.rares, cs.departements, (cs.joueur_id = auth.uid())
    from classement_saisons cs join saisons s on s.id = cs.saison and s.etat = 'terminee'
   where auth.uid() is not null and cs.saison = p_saison
     and (cs.rang <= greatest(least(coalesce(p_limite, 10), 100), 3) or cs.joueur_id = auth.uid())
   order by cs.rang;
$f$;

create or replace function public.terra_classement(p_limite integer default 10)
 returns table(rang integer, joueur_id uuid, pseudo text, score integer, communes integer,
               habitants bigint, legendaires integer, rares integer, est_moi boolean)
 language sql stable security definer set search_path to 'public'
as $f$
  with totaux as (
    select t.joueur_id,
           sum(points_rarete(c.tier))::integer as score,
           count(*)::integer as communes,
           sum(coalesce(c.population, 0))::bigint as habitants,
           count(*) filter (where c.tier = 'legendaire')::integer as legendaires,
           count(*) filter (where c.tier = 'rare')::integer as rares
      from terra_collection t join communes c on c.code = t.commune_code
     where t.exemplaires > 0
     group by t.joueur_id
  ),
  classe as (
    select row_number() over (order by x.score desc, x.communes desc, x.habitants desc)::integer as rang,
           x.*, coalesce(j.pseudo, 'Joueur')::text as pseudo
      from totaux x join joueurs j on j.id = x.joueur_id
  )
  select c.rang, c.joueur_id, c.pseudo, c.score, c.communes, c.habitants,
         c.legendaires, c.rares, (c.joueur_id = auth.uid())
    from classe c
   where auth.uid() is not null and terra_ouverte()
     and (c.rang <= greatest(least(coalesce(p_limite, 10), 100), 3) or c.joueur_id = auth.uid())
   order by c.rang;
$f$;

revoke all on function public.palmares_saisons() from public, anon;
revoke all on function public.palmares(text, integer) from public, anon;
revoke all on function public.terra_classement(integer) from public, anon;
grant execute on function public.palmares_saisons() to authenticated;
grant execute on function public.palmares(text, integer) to authenticated;
grant execute on function public.terra_classement(integer) to authenticated;

-- Contrôle ---------------------------------------------------------------------------------
select (select count(*) from pg_proc where proname in ('palmares_saisons', 'palmares', 'terra_classement')) as fonctions_doit_etre_3,
       (select count(distinct saison) from classement_saisons) as saisons_archivees,
       has_function_privilege('anon', 'public.palmares(text,integer)', 'execute') as anon_doit_etre_false;
