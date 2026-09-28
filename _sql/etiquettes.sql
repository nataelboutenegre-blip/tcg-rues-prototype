-- ===========================================================================
--  TerraFront — les etiquettes
--
--  Un mot libre par commune, prive, pour s'organiser quand on en possede des
--  centaines. Vingt caracteres : assez pour « a echanger contre rare », trop
--  peu pour une phrase que la vignette ne pourrait pas afficher.
--
--  Une seule etiquette par commune, pas plusieurs. Plusieurs, c'est un
--  systeme de dossiers avec ses regles et ses conflits. Une, c'est un
--  post-it — et un post-it on le colle sans reflechir.
--
--  Aucun index ajoute. Le client charge deja toute la collection et filtre
--  chez lui ; poser un index sans besoin mesure, c'est ce que j'ai fait le
--  27 pour zero gain.
-- ===========================================================================

-- ---------------------------------------------------------------------------
--  1. La colonne
-- ---------------------------------------------------------------------------
alter table public.possessions
  add column if not exists etiquette text;

-- La longueur est bornee en base et pas seulement dans le navigateur : un
-- appel direct a l'API contournerait le champ de saisie.
alter table public.possessions
  drop constraint if exists possessions_etiquette_courte;
alter table public.possessions
  add constraint possessions_etiquette_courte
  check (etiquette is null or length(etiquette) between 1 and 20);


-- ---------------------------------------------------------------------------
--  2. Poser ou retirer une etiquette
--
--  Le texte est nettoye ici, pas dans le navigateur : espaces en trop
--  reduits, chaine vide traitee comme un retrait. Sans ca, « a echanger »
--  et « a  echanger » deviennent deux etiquettes differentes, et le filtre
--  ne sert plus a rien.
-- ---------------------------------------------------------------------------
create or replace function public.etiqueter(p_commune_code text, p_etiquette text)
returns text
language plpgsql
security definer
set search_path to 'public'
as $function$
declare
  v_uid uuid := auth.uid();
  v_propre text;
begin
  if v_uid is null then raise exception 'Non connecté'; end if;

  if not exists (select 1 from possessions
                  where commune_code = p_commune_code and joueur_id = v_uid) then
    raise exception 'Cette commune ne t''appartient pas';
  end if;

  -- espaces multiples reduits a un seul, bords rognes
  v_propre := nullif(btrim(regexp_replace(coalesce(p_etiquette, ''), '\s+', ' ', 'g')), '');
  if v_propre is not null and length(v_propre) > 20 then
    v_propre := btrim(left(v_propre, 20));
  end if;

  update possessions set etiquette = v_propre
   where commune_code = p_commune_code and joueur_id = v_uid;

  return v_propre;
end;
$function$;

revoke all on function public.etiqueter(text, text) from public, anon;
grant execute on function public.etiqueter(text, text) to authenticated;


-- ---------------------------------------------------------------------------
--  3. Mes etiquettes, les plus utilisees d'abord
--
--  Sert aux suggestions de la fiche et aux filtres de la collection. C'est
--  ce qui evite « a echanger », « à échanger » et « aechanger » cote a cote.
-- ---------------------------------------------------------------------------
create or replace function public.mes_etiquettes()
returns table(etiquette text, communes integer)
language sql
stable
security definer
set search_path to 'public'
as $function$
  select p.etiquette::text, count(*)::integer
    from possessions p
   where p.joueur_id = auth.uid()
     and p.etiquette is not null
   group by p.etiquette
   order by count(*) desc, p.etiquette;
$function$;

revoke all on function public.mes_etiquettes() from public, anon;
grant execute on function public.mes_etiquettes() to authenticated;


-- ---------------------------------------------------------------------------
--  4. Une etiquette ne suit pas la commune qui change de mains
--
--  Meme piege que les favoris, et la meme reponse : le declencheur pose ce
--  matin est etendu. Sans ca, le voleur heriterait de ton « a echanger ».
--
--  La fonction est remplacee, le declencheur reste le meme.
-- ---------------------------------------------------------------------------
create or replace function public.favori_ne_suit_pas_la_commune()
returns trigger
language plpgsql
set search_path to 'public'
as $function$
begin
  if new.joueur_id is distinct from old.joueur_id then
    new.gardee := false;
    new.etiquette := null;
  end if;
  return new;
end;
$function$;


-- ---------------------------------------------------------------------------
--  5. Ce que la cloture NE fait PAS, et pourquoi
--
--  cloturer_saison() n'est pas modifiee : les etiquettes survivent a la
--  saison.
--
--  C'est deliberе. Une etoile est propre a la saison — c'est la liste de ce
--  qu'on garde, elle n'a plus d'objet une fois la cloture passee. Une
--  etiquette decrit la commune elle-meme : « ma region » reste vrai d'une
--  saison a l'autre, et un joueur qui a range ses cinq communes gardees
--  serait agace de retrouver son rangement efface.
--
--  Les communes rendues au pot perdent leur ligne possessions, donc leur
--  etiquette avec. Seules celles qu'il garde conservent la leur.
-- ---------------------------------------------------------------------------


-- ---------------------------------------------------------------------------
--  Verification
-- ---------------------------------------------------------------------------
select 'A. colonne etiquette' as controle,
       coalesce((select data_type from information_schema.columns
                  where table_schema = 'public' and table_name = 'possessions'
                    and column_name = 'etiquette'), 'ABSENTE') as valeur
union all
select 'B. contrainte de longueur',
       coalesce((select 'oui' from pg_constraint
                  where conrelid = 'public.possessions'::regclass
                    and conname = 'possessions_etiquette_courte'), 'NON')
union all
select 'C. declencheur efface aussi l''etiquette',
       case when pg_get_functiondef(p.oid) like '%new.etiquette := null%'
            then 'oui' else 'NON' end
  from pg_proc p join pg_namespace n on n.oid = p.pronamespace
 where n.nspname = 'public' and p.proname = 'favori_ne_suit_pas_la_commune'
union all
select 'D. etiquettes posees', count(*)::text
  from possessions where etiquette is not null
order by 1;
