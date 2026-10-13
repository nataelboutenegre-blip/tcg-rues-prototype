-- ===========================================================================
--  siege-suit-la-commune.sql — le siège suit la commune (13 octobre 2026)
--  Demandé par Wally, validé par Nataël (option B).
--
--  Avant : une commune assiégée ne pouvait plus être échangée ni passer par
--  la bourse (siege-vente-bloquee.sql), parce qu'un échange EFFAÇAIT les
--  sièges : c'était la faille signalée par Akan.
--  Maintenant :
--   - l'échange et la bourse redeviennent libres ;
--   - les sièges ne sont plus effacés : l'attaquant garde sa série contre le
--     nouveau propriétaire ;
--   - l'immunité de 3 h après acquisition ne protège pas d'un siège déjà
--     commencé (sinon passer la commune à un ami ferait gagner 3 h) ; elle
--     reste entière après une conquête ;
--   - si la commune arrive chez son propre attaquant, son siège disparaît ;
--   - vendre au jeu et le contrat restent bloqués pendant le siège (la
--     commune quitterait le jeu, le siège n'aurait plus rien à suivre).
--  Nouvelle lecture pour l'écran : sieges_communes(codes) = la série en
--  cours sur chaque commune (pour prévenir celui qui la reçoit).
--
--  Chaque fonction est modifiée à partir de sa définition EN PRODUCTION ;
--  s'il manque un repère, rien n'est touché. Rejouable.
--  Contrôle attendu : 0 | true | true | true | true
-- ===========================================================================

begin;

create or replace function pg_temp.remplacer(p_def text, p_avant text, p_apres text, p_etiquette text)
returns text language plpgsql as $$
declare n integer;
begin
  n := (length(p_def) - length(replace(p_def, p_avant, ''))) / length(p_avant);
  if n <> 1 then
    raise exception 'Repère « % » trouvé % fois (attendu 1) : rien n''a été modifié', p_etiquette, n;
  end if;
  return replace(p_def, p_avant, p_apres);
end $$;

-- 1. un siège commencé ignore l'immunité de 3 h, sauf après une conquête
create or replace function public.siege_ignore_immunite(p_code text, p_attaquant uuid)
 returns boolean language sql stable security definer set search_path to 'public'
as $f$
  select exists (select 1 from sieges s
                  where s.commune_code = p_code and s.attacker_id = p_attaquant
                    and coalesce(s.victoires_consecutives, 0) > 0)
     and exists (select 1 from possessions p
                  where p.commune_code = p_code
                    and (p.conquise_le is null or p.conquise_le < p.acquired_at - interval '1 second'));
$f$;
revoke all on function public.siege_ignore_immunite(text, uuid) from public, anon, authenticated;

-- 2. la commune arrive chez son attaquant : son siège n'a plus de sens
create or replace function public.siege_nettoyer_proprietaire()
 returns trigger language plpgsql security definer set search_path to 'public'
as $f$
begin
  delete from sieges where commune_code = new.commune_code and attacker_id = new.joueur_id;
  return null;
end;
$f$;
drop trigger if exists siege_nettoyer_proprietaire on public.possessions;
create trigger siege_nettoyer_proprietaire after update of joueur_id on public.possessions
  for each row when (new.joueur_id is distinct from old.joueur_id)
  execute function public.siege_nettoyer_proprietaire();

-- 3. pour l'écran : la série en cours sur des communes (lecture)
create or replace function public.sieges_communes(p_codes text[])
 returns table(commune_code text, serie integer, recent boolean)
 language sql stable security definer set search_path to 'public'
as $f$
  select s.commune_code::text, max(s.victoires_consecutives)::integer,
         bool_or(s.dernier_round > now() - interval '24 hours')
    from sieges s
   where auth.uid() is not null and s.commune_code = any(p_codes[1:300])
     and coalesce(s.victoires_consecutives, 0) > 0
   group by s.commune_code;
$f$;
revoke all on function public.sieges_communes(text[]) from public, anon;
grant execute on function public.sieges_communes(text[]) to authenticated;

do $do$
declare d text;
begin
  -- 4. attaquer : l'immunité de 3 h ne coupe pas un siège commencé
  d := pg_get_functiondef('public.attaquer(text, text)'::regprocedure);
  if d not like '%siege_ignore_immunite%' then
    d := pg_temp.remplacer(d,
      E'  if v_derniere_acquisition > now() - interval ''3 hours'' then',
      E'  if v_derniere_acquisition > now() - interval ''3 hours''\n'
   || E'     and not siege_ignore_immunite(p_commune_code, v_attaquant_id) then', 'attaquer');
    execute d;
  end if;

  -- 5. accepter un échange : ne plus effacer les sièges, ne plus bloquer
  d := pg_get_functiondef('public.accepter_echange(bigint)'::regprocedure);
  if d like '%commune_assiegee%' then
    d := pg_temp.remplacer(d,
      E'  if commune_assiegee(e.commune_proposant) or commune_assiegee(e.commune_destinataire) then\n'
   || E'    raise exception ''Une des deux communes est assiegee : pas d''''echange tant que le siege dure.'';\n'
   || E'  end if;\n\n', '', 'accepter_echange (blocage)');
  end if;
  if d like '%delete from sieges where commune_code in%' then
    d := pg_temp.remplacer(d,
      E'  -- les sieges en cours sur ces deux communes n''ont plus de sens\n'
   || E'  if to_regclass(''public.sieges'') is not null then\n'
   || E'    execute ''delete from sieges where commune_code in ($1, $2)''\n'
   || E'      using e.commune_proposant, e.commune_destinataire;\n'
   || E'  end if;\n',
      E'  -- siege-suit-la-commune : les sieges suivent les communes echangees\n', 'accepter_echange (sieges)');
  end if;
  execute d;

  -- 6. proposer un échange : plus de blocage
  d := pg_get_functiondef('public.proposer_echange(text, text, text)'::regprocedure);
  if d like '%commune_assiegee%' then
    d := pg_temp.remplacer(d,
      E'  if commune_assiegee(p_ma_commune) or commune_assiegee(p_sa_commune) then\n'
   || E'    raise exception ''Une des deux communes est assiegee : pas d''''echange tant que le siege dure.'';\n'
   || E'  end if;\n\n', '', 'proposer_echange');
    execute d;
  end if;

  -- 7. bourse : mettre en vente et acheter redeviennent possibles
  d := pg_get_functiondef('public.mettre_en_vente(text, integer)'::regprocedure);
  if d like '%commune_assiegee%' then
    d := pg_temp.remplacer(d,
      E'  if commune_assiegee(p_commune_code) then\n'
   || E'    raise exception ''Cette commune est assiegee : tu ne peux pas la mettre en vente tant que le siege dure'';\n'
   || E'  end if;\n\n', '', 'mettre_en_vente');
    execute d;
  end if;

  d := pg_get_functiondef('public.acheter(text, text)'::regprocedure);
  if d like '%commune_assiegee%' then
    d := pg_temp.remplacer(d,
      E'  if commune_assiegee(p_commune_code) then\n'
   || E'    raise exception ''Cette commune est assiegee : elle ne peut pas changer de main tant que le siege dure'';\n'
   || E'  end if;\n\n', '', 'acheter');
    execute d;
  end if;
  -- vendre_au_jeu et signer_contrat : inchangés (toujours bloqués pendant un siège)
end $do$;

commit;

-- contrôle : 0 | true | true | true | true
select (select count(*) from pg_proc p where p.pronamespace = 'public'::regnamespace
          and p.proname in ('mettre_en_vente', 'acheter', 'proposer_echange', 'accepter_echange')
          and pg_get_functiondef(p.oid) like '%commune_assiegee%')                         as blocages_restants_0,
       pg_get_functiondef('public.attaquer(text, text)'::regprocedure) like '%siege_ignore_immunite%' as attaque_ok,
       pg_get_functiondef('public.accepter_echange(bigint)'::regprocedure) not like '%delete from sieges where commune_code in%' as echange_garde_les_sieges,
       pg_get_functiondef('public.vendre_au_jeu(text)'::regprocedure) like '%commune_assiegee%' as vente_au_jeu_toujours_bloquee,
       has_function_privilege('authenticated', 'public.sieges_communes(text[])', 'execute') as lecture_ok;
