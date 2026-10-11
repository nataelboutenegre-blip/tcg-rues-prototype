-- ===========================================================================
--  echange-recherche.sql — onglet Échange : recherche par joueur et
--  critères multiples (idée de Wally, 11 octobre). Rejouable.
--
--  Le champ accepte plusieurs critères séparés par des virgules :
--    « 16, 17, Maroli » = les communes de Maroli en Charente OU en
--    Charente-Maritime.
--  Chaque critère est reconnu ainsi :
--    - le pseudo exact d'un joueur (majuscules indifférentes) -> ce joueur ;
--    - un numéro de département (le jeu traduit « Charente » en 16) ;
--    - sinon, un morceau de nom de commune.
--  Plusieurs critères du même genre s'additionnent (OU), des genres
--  différents se combinent (ET).
--  En plus : les communes assiégées ne sont plus proposées (l'échange est
--  refusé pendant un siège depuis siege-vente-bloquee.sql).
--  Mêmes colonnes renvoyées qu'avant : le jeu actuel continue de marcher.
--  Contrôle attendu : true | true
-- ===========================================================================

begin;

-- découpe la recherche en trois listes : joueurs, départements, noms
create or replace function public.echange_criteres(p_recherche text,
  out joueurs uuid[], out deps text[], out noms text[])
 language plpgsql stable security definer set search_path to 'public'
as $f$
declare t text; v_j uuid;
begin
  joueurs := '{}'; deps := '{}'; noms := '{}';
  foreach t in array regexp_split_to_array(coalesce(p_recherche, ''), '\s*[,;]\s*') loop
    t := btrim(t);
    continue when t = '';
    select j.id into v_j from joueurs j where lower(normalize(j.pseudo, NFC)) = lower(normalize(t, NFC)) limit 1;
    if v_j is not null then joueurs := joueurs || v_j; v_j := null; continue; end if;
    if t ~* '^(\d{2,3}|2a|2b)$' then deps := deps || upper(t); continue; end if;
    noms := noms || t;
  end loop;
end;
$f$;
revoke all on function public.echange_criteres(text) from public, anon, authenticated;

create or replace function public.cibles_echange(p_tier text, p_recherche text default ''::text)
 returns table(commune_code text, nom text, departement text, tier text, proprietaire uuid, pseudo text)
 language plpgsql stable security definer set search_path to 'public'
as $function$
declare k record;
begin
  select * into k from echange_criteres(p_recherche);
  return query
  select p.commune_code::text, c.nom::text, c.departement::text, c.tier::text, p.joueur_id, j.pseudo::text
    from possessions p
    join communes c on c.code = p.commune_code
    join joueurs  j on j.id = p.joueur_id
   where p.joueur_id <> auth.uid()
     and c.tier = p_tier
     and (p.bouclier_jusqua is null or p.bouclier_jusqua <= now())
     and not exists (select 1 from annonces a where a.commune_code = p.commune_code)
     and not exists (select 1 from echanges e
                      where e.etat = 'en_attente'
                        and (e.commune_proposant = p.commune_code
                          or e.commune_destinataire = p.commune_code))
     and not commune_assiegee(p.commune_code)
     and (cardinality(k.joueurs) = 0 or p.joueur_id = any(k.joueurs))
     and (cardinality(k.deps) = 0 or c.departement = any(k.deps))
     and (cardinality(k.noms) = 0 or exists (select 1 from unnest(k.noms) n where c.nom ilike '%' || n || '%'))
   order by c.nom
   limit 120;
end;
$function$;

create or replace function public.terra_cibles_echange(p_tier text, p_recherche text default ''::text)
 returns table(commune_code text, nom text, departement text, tier text, proprietaire uuid, pseudo text, nouvelle boolean)
 language plpgsql stable security definer set search_path to 'public'
as $function$
declare k record;
begin
  if auth.uid() is null then raise exception 'Non connecte'; end if;
  if not terra_ouverte() then raise exception 'Terra n''est pas encore ouvert'; end if;
  select * into k from echange_criteres(p_recherche);
  return query
  select t.commune_code::text, c.nom::text, c.departement::text, c.tier::text, t.joueur_id, j.pseudo::text,
         not exists (select 1 from terra_collection m
                      where m.joueur_id = auth.uid() and m.commune_code = t.commune_code and m.exemplaires > 0)
    from terra_collection t
    join communes c on c.code = t.commune_code
    join joueurs j on j.id = t.joueur_id
   where t.joueur_id <> auth.uid()
     and c.tier = p_tier
     and t.exemplaires - greatest(1, t.aurore) > 0
     and (cardinality(k.joueurs) = 0 or t.joueur_id = any(k.joueurs))
     and (cardinality(k.deps) = 0 or c.departement = any(k.deps))
     and (cardinality(k.noms) = 0 or exists (select 1 from unnest(k.noms) n where c.nom ilike '%' || n || '%'))
   -- d'abord celles qui manquent a ma collection
   order by 7 desc, c.nom, j.pseudo
   limit 120;
end;
$function$;

grant execute on function public.cibles_echange(text, text) to authenticated;
grant execute on function public.terra_cibles_echange(text, text) to authenticated;

commit;

-- contrôle : true | true
select pg_get_functiondef('public.cibles_echange(text, text)'::regprocedure) like '%echange_criteres%'       as front_ok,
       pg_get_functiondef('public.terra_cibles_echange(text, text)'::regprocedure) like '%echange_criteres%' as terra_ok;
