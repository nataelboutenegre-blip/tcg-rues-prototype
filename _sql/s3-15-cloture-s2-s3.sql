-- ===========================================================================
--  s3-15 — la clôture de la saison 2 et l'ouverture de la saison 3, en un appel
--  Installe cloture_s2_s3(p_confirmer). NE CLÔTURE RIEN.
--
--  cloture_s2_s3(false) : simulation, rien n'est écrit.
--  cloture_s2_s3(true)  : le jour J, après une sauvegarde. Dans l'ordre :
--   1. les récompenses de la saison 2 (s3-14, rejouable) ;
--   2. cloturer_saison('saison-2' → 'saison-3') : palmarès, 5 communes ★,
--      historique, purge des sièges / garnisons / Radar ;
--      - les TP sont GARDÉS (décision du 16/11 : p_solde_depart null) ;
--      - pas de cartes Terra pour les départements tenus (p_seuil_terra 101) ;
--   3. tous les bâtiments rasés (★ comprises), bombes en préparation perdues,
--      zones de bombe et rébellions terminées ;
--   4. Rafale et Plus ou moins repartent de 1 000 (comme jour-j-4b) ;
--   5. fin de la saison 3 : dimanche 13/12/2026, 10 h (Paris) ;
--   6. le classement est recalculé.
--  Tout se fait dans une seule transaction : une erreur annule tout.
--  Contrôle attendu (dernière ligne) : true | true
-- ===========================================================================

-- ---------- cloturer_saison : p_solde_depart null = garder les soldes ----------
do $do$
declare d text; a text; b text;
begin
  d := pg_get_functiondef('public.cloturer_saison(text,text,text,boolean,integer,text[],numeric)'::regprocedure);
  if position('s3-15' in d) = 0 then
    a := 'set solde = p_solde_depart,';
    b := 'union all select ''soldes remis a'', p_solde_depart::text';
    if (length(d) - length(replace(d, a, ''))) / length(a) <> 1
       or (length(d) - length(replace(d, b, ''))) / length(b) <> 2 then
      raise exception 's3-15 : cloturer_saison a changé, repères introuvables';
    end if;
    d := replace(d, a, 'set solde = coalesce(p_solde_depart, solde),   -- s3-15 : null = les soldes (TP) sont gardés');
    d := replace(d, b, 'union all select ''soldes remis a'', coalesce(p_solde_depart::text, ''(gardes)'')');
    execute d;
  end if;
end $do$;

create or replace function public.cloture_s2_s3(p_confirmer boolean default false)
 returns table(etape text, valeur text)
 language plpgsql security definer set search_path to 'public'
as $$
declare
  v_fin constant timestamptz := '2026-12-13 09:00:00+00';   -- 10 h à Paris
  v_bat integer; v_prep integer; v_bombes integer; v_rebel integer;
  v_rafale integer; v_pom integer; v_exclus text[] := exclus_classement_liste();
  x record;
begin
  if (select etat from saisons where id = 'saison-2') is distinct from 'en_cours' then
    raise exception 'La saison 2 n''est pas en cours';
  end if;

  select count(*) into v_bat from batiments;
  select count(*) into v_prep from bombes_preparations where etat = 'en_cours';
  select count(*) into v_bombes from bombes where fin > now();
  select count(*) into v_rebel from rebellions where fin > now() and etouffee_le is null;
  select count(*) into v_rafale from rafale_joueurs;
  select count(*) into v_pom from pom_joueurs;

  -- 1. les récompenses (avant la clôture : elles lisent possessions, classement et Elo)
  for x in select * from recompenses_s2_attribuer(p_confirmer) loop
    return query select 'récompenses · ' || x.etape, x.valeur;
  end loop;

  -- 2. la clôture
  for x in select * from cloturer_saison('saison-2', 'saison-3', 'Saison 3', p_confirmer, null, v_exclus, 101) loop
    return query select 'clôture · ' || x.etape, x.valeur;
  end loop;

  if p_confirmer then
    -- 3. on rase tout
    update bombes_preparations set etat = 'perdue', fini_le = now() where etat = 'en_cours';
    delete from batiments;
    update bombes set fin = now() where fin > now();
    update rebellions set fin = now() where fin > now() and etouffee_le is null;
    -- 4. Rafale et Plus ou moins à 1 000 (les lignes sont recréées au premier duel)
    delete from rafale_parties;
    delete from rafale_joueurs;
    delete from pom_duels;
    delete from pom_joueurs;
    -- 5. la date de fin de la saison 3
    update saisons set fin_prevue = v_fin where id = 'saison-3';
    -- 6. le classement
    perform classement_cache_maj();
  end if;

  return query select 'bâtiments rasés', v_bat::text
    union all select 'bombes en préparation perdues', v_prep::text
    union all select 'zones de bombe terminées', v_bombes::text
    union all select 'rébellions terminées', v_rebel::text
    union all select 'Rafale : joueurs remis à 1 000', v_rafale::text
    union all select 'Plus ou moins : joueurs remis à 1 000', v_pom::text
    union all select 'fin de la saison 3', to_char(v_fin at time zone 'Europe/Paris', 'DD/MM/YYYY HH24:MI') || ' (Paris)'
    union all select case when p_confirmer then 'FAIT' else 'SIMULATION' end,
                     case when p_confirmer then 'saison 3 ouverte' else 'rien n''a été modifié · pour agir : cloture_s2_s3(true)' end;
end;
$$;
revoke all on function public.cloture_s2_s3(boolean) from public, anon, authenticated;

select position('s3-15' in pg_get_functiondef('public.cloturer_saison(text,text,text,boolean,integer,text[],numeric)'::regprocedure)) > 0 as cloture_garde_les_tp,
       exists (select 1 from pg_proc where proname = 'cloture_s2_s3') as cloture_s2_s3_installee;
