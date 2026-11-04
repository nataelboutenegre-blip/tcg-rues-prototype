-- ===========================================================================
--  TerraFront — s2-97 : un échange de clan ne casse plus un siège (faille
--  signalée par un joueur le 4/11).
--
--  La faille : une commune attaquée (1/3, 2/3, ou remise à 0/3 par une
--  défense) passait à un coéquipier par un échange de clan. Le changement de
--  propriétaire EFFAÇAIT tous les sièges (vieux déclencheur trg_reset_sieges,
--  créé hors du dépôt) et la commune repartait avec 3 h de protection :
--  l'attaquant perdait sa série et devait attendre 3 h. Vérifié sur la base
--  de test avec les vraies fonctions de production.
--  Or la règle décidée le 13/10 (siege-suit-la-commune.sql, option B) était
--  l'inverse : le siège suit la commune, l'attaquant garde sa série contre le
--  nouveau propriétaire, et la protection de 3 h ne joue pas contre lui. Ce
--  vieux déclencheur l'annulait.
--
--  1. reset_sieges_changement_proprietaire() : les sièges ne sont plus
--     effacés quand la commune change de main SANS conquête (échange de clan).
--     Ils restent effacés après une conquête et quand la commune quitte le
--     jeu. L'annonce de l'ancien propriétaire part toujours.
--  2. siege_ignore_immunite() : la protection de 3 h après un échange ne joue
--     pas contre un attaquant qui a une série en cours OU qui a mené un assaut
--     dans les dernières 24 h (même si une défense l'a remis à 0/3). Elle
--     protège toujours contre tous les autres, et reste entière après une
--     conquête.
--  Indépendant du lot du 8/11 : s2-lot-2 s'applique par-dessus (vérifié).
--  Rejouable. Contrôle attendu : true | true
-- ===========================================================================
begin;

create or replace function public.reset_sieges_changement_proprietaire()
 returns trigger
 language plpgsql
 security definer
 set search_path to 'public'
as $function$
begin
  -- s2-97 : le siège suit la commune ; seuls une conquête ou un départ du jeu l'effacent
  if tg_op = 'DELETE' then
    delete from sieges where commune_code = old.commune_code;
  elsif new.joueur_id is distinct from old.joueur_id
        and new.conquise_le is not null and new.conquise_le is distinct from old.conquise_le then
    delete from sieges where commune_code = old.commune_code;
  end if;
  if tg_op = 'DELETE' or new.joueur_id is distinct from old.joueur_id then
    -- l'annonce de l'ancien proprietaire n'a plus lieu d'etre
    delete from annonces a
      where a.commune_code = old.commune_code and a.joueur_id = old.joueur_id;
  end if;
  return null;
end;
$function$;

do $$
declare d text := pg_get_functiondef('public.siege_ignore_immunite(text, uuid)'::regprocedure);
begin
  if position('s2-97' in d) > 0 then raise notice 'siege_ignore_immunite : déjà à jour'; return; end if;
  execute format($def$
create or replace function public.siege_ignore_immunite(p_code text, p_attaquant uuid)
 returns boolean
 language sql
 stable security definer
 set search_path to 'public'
as $function$
  select (exists (select 1 from sieges s
                  where s.commune_code = p_code and s.attacker_id = p_attaquant
                    and coalesce(s.victoires_consecutives, 0) > 0%s)
          -- s2-97 : un assaut dans les dernières 24 h compte aussi, même remis à 0/3 par une défense%s
          or exists (select 1 from sieges s
                      where s.commune_code = p_code and s.attacker_id = p_attaquant
                        and s.dernier_round > now() - interval '24 hours'))
     and exists (select 1 from possessions p
                  where p.commune_code = p_code
                    and (p.conquise_le is null or p.conquise_le < p.acquired_at - interval '1 second'));
$function$
$def$,
    -- si s2-lot-2 est déjà passé, on garde sa condition (siège expiré)
    case when position('s2-lot2' in d) > 0 then E'\n                    and s.dernier_round > siege_limite()' else '' end,
    case when position('s2-lot2' in d) > 0 then ' (s2-lot2 : siège expiré exclu)' else '' end);
end $$;

commit;

-- Contrôle : true | true
select position('s2-97' in pg_get_functiondef('public.reset_sieges_changement_proprietaire()'::regprocedure)) > 0
       and exists (select 1 from pg_trigger where tgname = 'trg_reset_sieges' and not tgisinternal)            as echange_garde_le_siege,
       position('s2-97' in pg_get_functiondef('public.siege_ignore_immunite(text, uuid)'::regprocedure)) > 0   as immunite_ok;
