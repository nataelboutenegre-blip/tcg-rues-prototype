-- ===========================================================================
--  TerraFront — le contrat
--
--  Sacrifier dix communes pour en obtenir une d'un palier au-dessus.
--
--    10 communs      -> 1 peu commun
--    10 peu communs  -> 1 rare
--
--  Les taux viennent de la carte elle-meme : 29 318 communs pour 4 392 peu
--  communs (6,7 pour 1), 4 392 peu communs pour 981 rares (4,5 pour 1).
--  Dix dans les deux cas : une seule regle a retenir, et le contrat coute
--  un peu plus cher que le hasard, donc il complete le tirage au lieu de
--  le remplacer.
--
--  RIEN NE MONTE JUSQU'A LA LEGENDAIRE. Il n'y en a que 48 dans tout le
--  jeu. A 100 communs le rare, le plus gros joueur s'en fabrique une
--  vingtaine par semaine — supportable sur 981 rares. S'il pouvait
--  continuer, meme a 25 rares pour 1, il frapperait une a deux legendaires
--  par semaine et le palier du haut ne passerait pas le mois.
--
--  Pourquoi c'est surtout un PUITS : les dix communes sacrifiees
--  retournent au pot, une seule en sort. Net +9 communes disponibles a
--  chaque contrat, +99 pour un rare parti de communs. C'est ce que
--  cherchait l'idee des cartes perdues a l'attaque, sans punir personne.
-- ===========================================================================

-- ---------------------------------------------------------------------------
--  1. Ce que le joueur peut sacrifier
--
--  Renvoyee au client pour qu'il propose exactement ce que le serveur
--  acceptera. Sans ca, le joueur compose un lot et se fait refuser sans
--  comprendre.
--
--  Sont ecartees :
--   - les communes gardees (favoris) : sacrifier une des cinq places par
--     megarde serait irreversible
--   - celles en vente a la bourse, ou engagees dans un echange en attente :
--     sinon on vend deux fois la meme chose
-- ---------------------------------------------------------------------------
create or replace function public.contrat_candidates(p_tier text)
returns table(commune_code text, nom text, departement text, population integer)
language sql
stable
security definer
set search_path to 'public'
as $function$
  select p.commune_code, c.nom::text, c.departement::text, c.population
    from possessions p
    join communes c on c.code = p.commune_code
   where p.joueur_id = auth.uid()
     and c.tier = p_tier
     and not p.gardee
     and not exists (select 1 from annonces a
                      where a.commune_code = p.commune_code)
     and not exists (select 1 from echanges e
                      where e.etat = 'en_attente'
                        and (e.commune_proposant = p.commune_code
                          or e.commune_destinataire = p.commune_code))
   order by c.population asc nulls first, p.commune_code;
$function$;

revoke all on function public.contrat_candidates(text) from public, anon;
grant execute on function public.contrat_candidates(text) to authenticated;


-- ---------------------------------------------------------------------------
--  2. Signer
--
--  Tout se passe dans une seule transaction : une fonction plpgsql est
--  atomique. Si le tirage echoue, les dix communes ne sont pas perdues.
-- ---------------------------------------------------------------------------
create or replace function public.signer_contrat(p_codes text[], p_vers text)
returns jsonb
language plpgsql
security definer
set search_path to 'public'
as $function$
declare
  v_uid uuid := auth.uid();
  v_de text;
  v_n integer := 10;
  v_saison text;
  v_valides integer;
  v_code text;
  v_essai integer;
  v_carte jsonb;
begin
  if v_uid is null then raise exception 'Non connecté'; end if;

  v_de := case p_vers when 'peucommun' then 'commun'
                      when 'rare'      then 'peucommun' end;
  if v_de is null then
    raise exception 'Seuls les contrats vers peu commun et rare existent';
  end if;

  if p_codes is null or array_length(p_codes, 1) is distinct from v_n then
    raise exception 'Il faut exactement % communes', v_n;
  end if;
  if (select count(distinct x) from unnest(p_codes) x) <> v_n then
    raise exception 'Deux fois la même commune dans le lot';
  end if;

  select id into v_saison from saisons where etat <> 'terminee'
   order by debut desc limit 1;

  -- On verrouille les dix lignes avant de verifier : sans ca, deux contrats
  -- lances en meme temps pourraient sacrifier la meme commune deux fois.
  perform 1 from possessions
   where commune_code = any(p_codes) and joueur_id = v_uid
   for update;

  -- Les memes conditions que contrat_candidates, revalidees ici : le client
  -- peut avoir change d'avis, ou la situation avoir bouge entre-temps.
  select count(*) into v_valides
    from possessions p
    join communes c on c.code = p.commune_code
   where p.commune_code = any(p_codes)
     and p.joueur_id = v_uid
     and c.tier = v_de
     and not p.gardee
     and not exists (select 1 from annonces a where a.commune_code = p.commune_code)
     and not exists (select 1 from echanges e
                      where e.etat = 'en_attente'
                        and (e.commune_proposant = p.commune_code
                          or e.commune_destinataire = p.commune_code));

  if v_valides <> v_n then
    raise exception 'Une des communes ne convient plus : vérifie qu''elles t''appartiennent toutes, qu''elles sont bien du bon palier, et qu''aucune n''est gardée, en vente ou dans un échange';
  end if;

  -- --- le tirage, avant toute suppression --------------------------------
  -- Si rien n'est libre dans le palier vise, on refuse SANS avoir rien
  -- detruit. Donner un palier plus bas serait une punition.
  v_code := null;
  for v_essai in 1..5 loop
    select c.code into v_code
      from communes c
      left join possessions p on p.commune_code = c.code
     where c.tier = p_vers and p.commune_code is null
     order by random()
     limit 1;
    exit when v_code is not null;
  end loop;

  if v_code is null then
    raise exception 'Plus aucune commune % n''est libre : le contrat est impossible pour le moment', p_vers;
  end if;

  -- --- les dix partent ----------------------------------------------------
  update historique h
     set released_at = now()
   where h.released_at is null
     and h.joueur_id = v_uid
     and h.commune_code = any(p_codes);

  delete from possessions
   where commune_code = any(p_codes) and joueur_id = v_uid;

  -- --- celle-ci arrive ----------------------------------------------------
  begin
    insert into possessions (commune_code, joueur_id, saison)
      values (v_code, v_uid, coalesce(v_saison, 'saison-1'));
  exception when unique_violation then
    -- quelqu'un l'a prise entre le select et l'insert : tout est annule,
    -- les dix communes sont intactes
    raise exception 'Cette commune vient d''être prise par un autre joueur, réessaie';
  end;

  insert into historique (commune_code, joueur_id, saison, acquired_at)
    values (v_code, v_uid, coalesce(v_saison, 'saison-1'), now());

  insert into journal (type, acteur, commune_code, commune_nom, tier, cree_le)
  select 'contrat', v_uid, c.code, c.nom, c.tier, now()
    from communes c where c.code = v_code;

  select to_jsonb(t) into v_carte from (
    select c.code, c.nom, c.departement, c.population,
           c.latitude, c.longitude, c.tier, c.rang, c.palier_total
      from communes c where c.code = v_code
  ) t;

  return v_carte || jsonb_build_object('sacrifiees', v_n, 'depuis', v_de);
end;
$function$;

revoke all on function public.signer_contrat(text[], text) from public, anon;
grant execute on function public.signer_contrat(text[], text) to authenticated;


-- ---------------------------------------------------------------------------
--  3. Le defile montre de vraies communes du palier vise
--
--  Uniquement des communes LIBRES du palier : faire defiler une rarete que
--  le contrat ne peut pas donner afficherait un resultat qui n'etait pas
--  possible. Ce n'est pas du suspense, c'est un mensonge.
-- ---------------------------------------------------------------------------
create or replace function public.contrat_defile(p_tier text, p_combien integer default 40)
returns table(nom text, departement text, population integer)
language sql
stable
security definer
set search_path to 'public'
as $function$
  select c.nom::text, c.departement::text, c.population
    from communes c
    left join possessions p on p.commune_code = c.code
   where c.tier = p_tier
     and p.commune_code is null
     and auth.uid() is not null
   order by random()
   limit least(greatest(coalesce(p_combien, 40), 1), 60);
$function$;

revoke all on function public.contrat_defile(text, integer) from public, anon;
grant execute on function public.contrat_defile(text, integer) to authenticated;


-- ---------------------------------------------------------------------------
--  Verification
-- ---------------------------------------------------------------------------
select 'A. fonctions creees' as controle,
       string_agg(p.proname, ', ' order by p.proname) as valeur
  from pg_proc p join pg_namespace n on n.oid = p.pronamespace
 where n.nspname = 'public'
   and p.proname in ('contrat_candidates', 'signer_contrat', 'contrat_defile')
union all
select 'B. droits (aucun anon)',
       coalesce(string_agg(p.proname || ' -> ' || coalesce(array_to_string(p.proacl, ' '), 'defaut'),
                chr(10) order by p.proname), 'aucune')
  from pg_proc p join pg_namespace n on n.oid = p.pronamespace
 where n.nspname = 'public'
   and p.proname in ('contrat_candidates', 'signer_contrat', 'contrat_defile')
union all
select 'C. communes libres par palier',
       string_agg(t.tier || ' : ' || t.n, chr(10) order by t.n desc)
  from (select c.tier, count(*) as n
          from communes c left join possessions p on p.commune_code = c.code
         where p.commune_code is null
         group by c.tier) t
order by 1;
