-- ===========================================================================
--  TerraFront — Ne jamais sacrifier certaines communes au contrat
--
--  LE BESOIN
--    Le lot de dix est composé automatiquement, des moins peuplées aux plus
--    peuplées. Les mêmes communes reviennent donc à chaque contrat, et il
--    faut les retirer à la main à chaque fois. Une liste d'exclusions règle
--    ça une fois pour toutes.
--
--  POURQUOI EN BASE ET PAS DANS LE NAVIGATEUR
--    Les étiquettes et les bandeaux fermés sont gardés dans le navigateur :
--    en perdre une n'a aucune conséquence. Ici, perdre la liste en changeant
--    d'appareil signifie sacrifier des communes qu'on voulait garder, et un
--    contrat ne se défait pas. Ça vaut une table.
--
--  DEUX NIVEAUX
--    Une exclusion vise soit une commune précise, soit un département
--    entier. Le second évite d'avoir à cocher cent communes pour protéger
--    sa région.
--
--  CE QUE ÇA NE FAIT PAS
--    Ça ne protège de rien d'autre : ni du combat, ni de la vente, ni des
--    échanges. C'est une protection contre sa propre main sur le contrat,
--    pas un bouclier.
--
--  LA PROTECTION EST POSÉE DES DEUX CÔTÉS
--    contrat_candidates cesse de proposer les communes exclues, et
--    signer_contrat les refuse. Le premier suffirait pour l'usage normal ;
--    le second couvre la page restée ouverte depuis avant l'exclusion.
--
--    signer_contrat n'a pas été réécrite à la main : elle a été reprise
--    telle quelle depuis contrat.sql, avec une seule condition ajoutée. Le
--    reste est identique au caractère près.
-- ===========================================================================


-- ---------------------------------------------------------------------------
--  1. La liste
-- ---------------------------------------------------------------------------
create table if not exists public.contrat_exclusions (
  joueur_id    uuid not null references public.joueurs(id) on delete cascade,
  commune_code text references public.communes(code),
  departement  text,
  cree_le      timestamptz not null default now(),
  -- une ligne vise une commune OU un département, jamais les deux ni aucun
  constraint contrat_exclusions_cible check (
    (commune_code is not null and departement is null)
    or (commune_code is null and departement is not null))
);

create unique index if not exists contrat_exclusions_commune
  on public.contrat_exclusions (joueur_id, commune_code)
  where commune_code is not null;
create unique index if not exists contrat_exclusions_departement
  on public.contrat_exclusions (joueur_id, departement)
  where departement is not null;

comment on table public.contrat_exclusions is
  'Communes et départements qu''un joueur refuse de voir proposés au contrat.';

-- Chacun ne voit et ne modifie que ses propres lignes.
alter table public.contrat_exclusions enable row level security;
drop policy if exists contrat_exclusions_miennes on public.contrat_exclusions;
create policy contrat_exclusions_miennes on public.contrat_exclusions
  for all using (joueur_id = auth.uid()) with check (joueur_id = auth.uid());
grant select, insert, delete on table public.contrat_exclusions to authenticated;


-- ---------------------------------------------------------------------------
--  2. Lire, ajouter, retirer
-- ---------------------------------------------------------------------------
drop function if exists public.mes_exclusions_contrat();

create function public.mes_exclusions_contrat()
returns table(commune_code text, departement text, nom text, dept_commune text)
language sql
stable
security definer
set search_path to 'public'
as $function$
  select x.commune_code, x.departement, c.nom::text, c.departement::text
    from contrat_exclusions x
    left join communes c on c.code = x.commune_code
   where x.joueur_id = auth.uid()
   order by x.departement nulls last, c.nom;
$function$;

revoke all on function public.mes_exclusions_contrat() from public, anon;
grant execute on function public.mes_exclusions_contrat() to authenticated;


create or replace function public.exclure_du_contrat(
  p_commune text default null, p_departement text default null)
returns void
language plpgsql
security definer
set search_path to 'public'
as $function$
declare v_uid uuid := auth.uid();
begin
  if v_uid is null then raise exception 'Non connecté'; end if;
  if (p_commune is null) = (p_departement is null) then
    raise exception 'Il faut une commune OU un département, pas les deux';
  end if;
  if p_commune is not null then
    if not exists (select 1 from communes where code = p_commune) then
      raise exception 'Commune inconnue';
    end if;
    insert into contrat_exclusions (joueur_id, commune_code)
      values (v_uid, p_commune) on conflict do nothing;
  else
    if not exists (select 1 from communes where departement = p_departement) then
      raise exception 'Département inconnu';
    end if;
    insert into contrat_exclusions (joueur_id, departement)
      values (v_uid, p_departement) on conflict do nothing;
  end if;
end;
$function$;

create or replace function public.inclure_au_contrat(
  p_commune text default null, p_departement text default null)
returns void
language plpgsql
security definer
set search_path to 'public'
as $function$
declare v_uid uuid := auth.uid();
begin
  if v_uid is null then raise exception 'Non connecté'; end if;
  delete from contrat_exclusions
   where joueur_id = v_uid
     and ((p_commune is not null and commune_code = p_commune)
       or (p_departement is not null and departement = p_departement));
end;
$function$;

revoke all on function public.exclure_du_contrat(text, text) from public, anon;
revoke all on function public.inclure_au_contrat(text, text) from public, anon;
grant execute on function public.exclure_du_contrat(text, text) to authenticated;
grant execute on function public.inclure_au_contrat(text, text) to authenticated;


-- ---------------------------------------------------------------------------
--  3. Le lot cesse de les proposer
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
     -- la protection posée par le joueur lui-même
     and not exists (select 1 from contrat_exclusions x
                      where x.joueur_id = auth.uid()
                        and (x.commune_code = p.commune_code
                          or x.departement = c.departement))
   order by c.population asc nulls first, p.commune_code;
$function$;
revoke all on function public.contrat_candidates(text) from public, anon;
grant execute on function public.contrat_candidates(text) to authenticated;


-- ---------------------------------------------------------------------------
--  4. Signer refuse une commune exclue
--
--  Fonction reprise telle quelle depuis contrat.sql par un script, avec une
--  seule condition ajoutée dans la validation. Rien d'autre n'a bougé.
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
                          or e.commune_destinataire = p.commune_code))
     -- la protection posée par le joueur lui-même
     and not exists (select 1 from contrat_exclusions x
                      where x.joueur_id = v_uid
                        and (x.commune_code = p.commune_code
                          or x.departement = c.departement));

  if v_valides <> v_n then
    raise exception 'Une des communes ne convient plus : vérifie qu''elles t''appartiennent toutes, qu''elles sont bien du bon palier, et qu''aucune n''est gardée, en vente, dans un échange ou protégée par ta liste d''exclusions';
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


-- ---------------------------------------------------------------------------
--  Contrôle
-- ---------------------------------------------------------------------------
select 'A. table creee' as controle,
       case when to_regclass('public.contrat_exclusions') is null
            then 'NON' else 'oui' end as valeur
union all
select 'B. RLS active',
       case when (select relrowsecurity from pg_class
                   where oid = 'public.contrat_exclusions'::regclass)
            then 'oui' else 'NON' end
union all
select 'C. le lot filtre les exclusions',
       case when pg_get_functiondef('public.contrat_candidates(text)'::regprocedure)
                 like '%contrat_exclusions%' then 'oui' else 'NON' end
union all
select 'D. signer refuse les exclusions',
       case when pg_get_functiondef('public.signer_contrat(text[],text)'::regprocedure)
                 like '%contrat_exclusions%' then 'oui' else 'NON' end
union all
select 'E. exclusions posees',
       (select count(*)::text from public.contrat_exclusions)
order by 1;
