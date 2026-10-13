-- ===========================================================================
--  TerraFront — surveillance des paires de joueurs (12 octobre 2026)
--  LECTURE SEULE : rien n'est créé ni modifié. À relancer quand tu veux.
--
--  Pour chaque paire de joueurs qui s'affrontent (30 derniers jours, journal) :
--   - conquêtes dans chaque sens, défenses réussies dans chaque sens ;
--   - « aller-retour » : communes que chacun a prises à l'autre (le même
--     village qui change de main en boucle est le signe le plus net) ;
--   - échanges conclus entre eux (des amis, ce n'est pas interdit) ;
--   - saison 2 : victoires refusées par le plafond « 2 par jour contre le
--     même adversaire » (front_victoires).
--  Limite : une attaque RATÉE ne laisse aucune trace par adversaire. On ne
--  peut donc pas mesurer « l'un perd exprès » directement ; on voit les
--  victoires, les allers-retours et les échanges.
--  Classement : les paires les plus suspectes d'abord (indice simple, à lire
--  avec bon sens : deux vrais rivaux voisins font aussi des allers-retours).
-- ===========================================================================
with ev as (
  select jl.type, jl.acteur, jl.cible, jl.commune_code, jl.cree_le
    from public.journal jl
   where jl.type in ('conquete', 'defense', 'echange') and jl.acteur is not null and jl.cible is not null
     and jl.acteur <> jl.cible
), paires as (
  select least(acteur, cible) as a, greatest(acteur, cible) as b, ev.*
    from ev
), stats as (
  select a, b,
         count(*) filter (where type = 'conquete' and acteur = a) as conquetes_a_sur_b,
         count(*) filter (where type = 'conquete' and acteur = b) as conquetes_b_sur_a,
         count(*) filter (where type = 'defense'  and acteur = a) as defenses_a_contre_b,
         count(*) filter (where type = 'defense'  and acteur = b) as defenses_b_contre_a,
         count(*) filter (where type = 'echange') / 2             as echanges,
         count(distinct commune_code) filter (where type = 'conquete') as communes_touchees,
         min(cree_le) as premier, max(cree_le) as dernier
    from paires group by a, b
), allers_retours as (
  select p.a, p.b, count(distinct p.commune_code) as n
    from paires p
   where p.type = 'conquete' and p.acteur = p.a
     and exists (select 1 from paires q where q.a = p.a and q.b = p.b and q.type = 'conquete'
                   and q.acteur = p.b and q.commune_code = p.commune_code)
   group by p.a, p.b
), plafond as (
  select least(v.joueur_id, v.adversaire) as a, greatest(v.joueur_id, v.adversaire) as b, count(*) as n
    from public.front_victoires v
   where v.raison = 'plafond_adversaire' and v.adversaire is not null
   group by 1, 2
)
select ja.pseudo as joueur_a, jb.pseudo as joueur_b,
       s.conquetes_a_sur_b, s.conquetes_b_sur_a,
       s.defenses_a_contre_b, s.defenses_b_contre_a,
       coalesce(ar.n, 0) as allers_retours,
       s.echanges,
       coalesce(pl.n, 0) as refus_plafond_s2,
       (coalesce(ar.n, 0) * 3 + s.echanges * 2 + coalesce(pl.n, 0) * 2
        + least(s.conquetes_a_sur_b, s.conquetes_b_sur_a)) as indice,
       to_char(s.premier at time zone 'Europe/Paris', 'DD/MM') as depuis,
       to_char(s.dernier at time zone 'Europe/Paris', 'DD/MM HH24:MI') as dernier
  from stats s
  join public.joueurs ja on ja.id = s.a
  join public.joueurs jb on jb.id = s.b
  left join allers_retours ar on ar.a = s.a and ar.b = s.b
  left join plafond pl on pl.a = s.a and pl.b = s.b
 where s.conquetes_a_sur_b + s.conquetes_b_sur_a + s.defenses_a_contre_b + s.defenses_b_contre_a > 0
 order by indice desc, s.conquetes_a_sur_b + s.conquetes_b_sur_a desc
 limit 30;
