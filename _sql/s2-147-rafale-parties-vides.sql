-- ===========================================================================
--  s2-147 (16/11/2026) — Rafale : « des défaites pour des parties pas jouées » (Maroli)
--  Une partie lancée sans aucun essai (0 mot tapé, fermée au bout de 30 s) restait
--  en attente comme une vraie partie : le premier venu gagnait et le propriétaire
--  prenait une défaite, parfois des jours après (jusqu'à 12 jours).
--  1. rafale_lancer ne donne plus une partie sans essai, ni une partie en attente
--     depuis plus de peremption_j jours (réglage 'rafale_appariement', 3 par défaut).
--  2. rafale_etat ne les compte plus dans « en attente d'adversaire ».
--  3. L'Elo perdu sur les parties sans essai déjà prises est rendu (les gagnants
--     gardent leur victoire et leurs TP).
--  Rejouable. Contrôle attendu (dernière ligne) : true | true | 0
-- ===========================================================================
create or replace function public.rafale_peremption()
 returns interval language sql stable security definer set search_path to 'public'
as $$ select make_interval(days => coalesce((select (valeur::jsonb ->> 'peremption_j')::int from config_jeu where cle = 'rafale_appariement'), 3)); $$;
revoke all on function public.rafale_peremption() from public, anon;
grant execute on function public.rafale_peremption() to authenticated, service_role;

do $do$
declare
  d text; a text; b text;
begin
  -- 1. le lancement
  d := pg_get_functiondef('public.rafale_lancer()'::regprocedure);
  if position('s2-147' in d) = 0 then
    a := 'or p.fin_le < now() - make_interval(hours => v_attente))';
    if (length(d) - length(replace(d, a, ''))) / length(a) <> 1 then raise exception 's2-147 : rafale_lancer a changé, repère introuvable'; end if;
    execute replace(d, a, a || E'\n     and p.essais > 0 and p.fin_le > now() - rafale_peremption()   -- s2-147 : ni partie sans essai, ni partie périmée');
  end if;
  -- 2. l'état : ces parties ne sont plus « en attente »
  d := pg_get_functiondef('public.rafale_etat()'::regprocedure);
  if position('s2-147' in d) = 0 then
    a := 'where joueur_id = v_uid and fini and source_id is null and resultat is null and cible_id is null)';
    b := 'where p.joueur_id = v_uid and p.fini and p.source_id is null and p.resultat is null and p.cible_id is null';
    if (length(d) - length(replace(d, a, ''))) / length(a) <> 1 or (length(d) - length(replace(d, b, ''))) / length(b) <> 1 then
      raise exception 's2-147 : rafale_etat a changé, repère introuvable';
    end if;
    d := replace(d, a, 'where joueur_id = v_uid and fini and source_id is null and resultat is null and cible_id is null' || E'\n                      and essais > 0 and fin_le > now() - rafale_peremption() /* s2-147 */)');
    d := replace(d, b, b || E'\n           and p.essais > 0 and p.fin_le > now() - rafale_peremption()   -- s2-147');
    execute d;
  end if;
end $do$;

-- 3. rendre l'Elo (une seule fois : la partie réparée a elo_apres = elo_avant)
with cible as (
  select s.id, s.joueur_id, s.elo_avant - s.elo_apres as rendu
    from rafale_parties s
   where s.source_id is null and s.essais = 0 and s.cible_id is null and not s.amical
     and s.utilisee and s.resultat = 'defaite' and s.elo_apres < s.elo_avant
), maj as (
  update rafale_parties p set elo_apres = p.elo_avant from cible c where p.id = c.id returning c.joueur_id, c.rendu
), tot as (
  select joueur_id, sum(rendu)::int as rendu, count(*)::int as n from maj group by joueur_id
)
update rafale_joueurs r set elo = r.elo + t.rendu, parties = greatest(0, r.parties - t.n)
  from tot t where r.joueur_id = t.joueur_id;

select position('s2-147' in pg_get_functiondef('public.rafale_lancer()'::regprocedure)) > 0 as lancer_ok,
       position('s2-147' in pg_get_functiondef('public.rafale_etat()'::regprocedure)) > 0 as etat_ok,
       (select count(*) from rafale_parties s where s.source_id is null and s.essais = 0 and s.cible_id is null and not s.amical
          and s.utilisee and s.resultat = 'defaite' and s.elo_apres < s.elo_avant) as reste_a_rendre;
