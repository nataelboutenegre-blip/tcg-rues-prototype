-- ===========================================================================
--  TerraFront — les favoris, et la regle de la legendaire unique
--
--  Cinq communes gardees par joueur a la cloture, dont AU PLUS UNE
--  legendaire.
--
--  Pourquoi cette limite. Il y a 48 legendaires dans tout le jeu, dont
--  environ 44 deja detenues. Sans limite, quelques joueurs qui en
--  possedent plusieurs peuvent en garder cinq chacun : trente a quarante
--  des quarante-huit ne retourneraient jamais au pot. Et l'effet s'empile,
--  saison apres saison — un joueur arrivant en saison 3 jouerait pour un
--  palier du haut deja verrouille aux trois quarts. Avec la limite, le
--  maximum retenu tombe a dix-huit, une par joueur, et trente legendaires
--  repartent a chaque saison.
--
--  Les rares ne sont pas limitees : il y en a 981, et les 90 communes
--  gardees au total n'en representeraient au pire que 9 %. Pas de probleme
--  de circulation, donc pas de regle en plus a expliquer.
--
--  DEUX endroits doivent l'appliquer, et le second est celui qu'on
--  oublierait :
--
--    1. marquer_gardee(), pour le choix du joueur
--    2. la completion automatique de cloturer_saison(), qui remplit par
--       rarete decroissante — un joueur qui n'a rien choisi et possede des
--       legendaires en recevrait cinq d'office, et la regle serait
--       contournee par le filet cense l'appliquer
--
--  Ce fichier contient aussi mes_favoris(), que l'interface appellera pour
--  afficher le compteur sans avoir a recharger toute la collection.
-- ===========================================================================


-- ---------------------------------------------------------------------------
--  1. marquer_gardee() — plafond de 5, dont au plus une legendaire
--
--  Le compte se fait toujours en excluant la commune visee, pour que
--  re-marquer une commune deja favorite ne la compte pas deux fois.
-- ---------------------------------------------------------------------------
create or replace function public.marquer_gardee(p_commune_code text, p_gardee boolean)
returns integer                                  -- combien sont marquees ensuite
language plpgsql
security definer
set search_path to 'public'
as $function$
declare
  v_uid uuid := auth.uid();
  v_saison text;
  v_deja integer;
  v_tier text;
  v_legendaires integer;
begin
  if v_uid is null then raise exception 'Non connecté'; end if;

  select id into v_saison from saisons where etat <> 'terminee'
   order by debut desc limit 1;
  if v_saison is null then raise exception 'Aucune saison en cours'; end if;

  select c.tier into v_tier
    from possessions p
    join communes c on c.code = p.commune_code
   where p.commune_code = p_commune_code and p.joueur_id = v_uid;
  if v_tier is null then
    raise exception 'Cette commune ne t''appartient pas';
  end if;

  -- combien sont deja gardees, sans compter celle qu'on est en train de
  -- marquer ou de demarquer
  select count(*) into v_deja
    from possessions
   where joueur_id = v_uid and saison = v_saison and gardee = true
     and commune_code <> p_commune_code;

  if p_gardee then
    if v_deja >= 5 then
      raise exception 'Tu ne peux garder que 5 communes : retires-en une d''abord';
    end if;

    -- la regle de la legendaire unique
    if v_tier = 'legendaire' then
      select count(*) into v_legendaires
        from possessions p
        join communes c on c.code = p.commune_code
       where p.joueur_id = v_uid and p.saison = v_saison and p.gardee = true
         and c.tier = 'legendaire'
         and p.commune_code <> p_commune_code;
      if v_legendaires >= 1 then
        raise exception 'Une seule légendaire peut être gardée : les autres retournent au pot en fin de saison, pour que le palier du haut continue de circuler';
      end if;
    end if;
  end if;

  update possessions set gardee = p_gardee
   where commune_code = p_commune_code and joueur_id = v_uid;

  return v_deja + case when p_gardee then 1 else 0 end;
end;
$function$;

grant execute on function public.marquer_gardee(text, boolean) to authenticated;


-- ---------------------------------------------------------------------------
--  2. mes_favoris() — ce que l'interface affiche
--
--  Renvoie une ligne par favori, plus de quoi remplir le compteur sans
--  recharger la collection entiere.
-- ---------------------------------------------------------------------------
create or replace function public.mes_favoris()
returns table(commune_code text, nom text, departement text, tier text,
              population integer, marquee_le timestamptz)
language sql
stable
security definer
set search_path to 'public'
as $function$
  select p.commune_code, c.nom::text, c.departement::text, c.tier::text,
         c.population, p.acquired_at
    from possessions p
    join communes c on c.code = p.commune_code
   where p.joueur_id = auth.uid()
     and p.gardee = true
   order by case c.tier when 'legendaire' then 1 when 'rare' then 2
                        when 'peucommun' then 3 else 4 end,
            c.population desc nulls last;
$function$;

revoke all on function public.mes_favoris() from public, anon;
grant execute on function public.mes_favoris() to authenticated;


-- ---------------------------------------------------------------------------
--  3. cloturer_saison() — la completion automatique respecte la regle
--
--  Seule l'etape c) change. Elle remplissait par rarete decroissante sans
--  distinction ; elle classe maintenant les legendaires au-dela de la
--  premiere tout en bas de la liste des candidates, pour qu'elles ne
--  soient retenues que s'il n'y a rien d'autre a garder.
--
--  La completion applique exactement la meme regle que marquer_gardee, ce
--  qui evite qu'un joueur obtienne d'office ce que l'interface lui refuse.
-- ---------------------------------------------------------------------------
drop function if exists public.cloturer_saison(text, text, text, boolean, integer);

create function public.cloturer_saison(
  p_saison        text,
  p_nouvelle_id   text,
  p_nouveau_nom   text,
  p_confirmer     boolean default false,   -- false = simulation, rien n'est ecrit
  p_solde_depart  integer default 0)
returns table(etape text, valeur text)
language plpgsql
security definer
set search_path to 'public'
as $function$
declare
  v_etat text;
  v_joueurs integer;
  v_possessions integer;
  v_gardees integer;
  v_rendues integer;
  v_sans_favori integer;
  v_gardees_apres integer;
  v_legendaires_gardees integer;
  v_sieges integer;
  v_annonces integer;
  v_echanges integer;
  v_hist integer;
  v_lignes integer;
begin
  -- --- a) la saison existe-t-elle, et est-elle fermable ? -----------------
  select etat into v_etat from saisons where id = p_saison for update;
  if v_etat is null then
    raise exception 'Saison % inconnue', p_saison;
  end if;
  if v_etat = 'terminee' then
    raise exception 'La saison % est deja terminee', p_saison;
  end if;
  if p_nouvelle_id is null or p_nouveau_nom is null then
    raise exception 'Il faut un identifiant et un nom pour la saison suivante';
  end if;
  if p_confirmer and exists (select 1 from saisons where id = p_nouvelle_id) then
    raise exception 'La saison % existe deja', p_nouvelle_id;
  end if;

  -- --- ce que la cloture va toucher, compte avant d'agir ------------------
  select count(*) into v_possessions from possessions;
  select count(distinct joueur_id) into v_joueurs from possessions;
  select count(*) into v_gardees from possessions where gardee;
  select count(*) into v_sieges from sieges;
  select count(*) into v_annonces from annonces;
  select count(*) into v_echanges from echanges;

  select count(*) into v_sans_favori from (
    select joueur_id
      from possessions
     group by joueur_id
    having count(*) filter (where gardee) < least(5, count(*))
  ) t;

  -- Combien seront gardees apres completion. Pas « 5 par joueur » : un
  -- joueur qui possede moins de 5 communes garde tout ce qu'il a.
  select coalesce(sum(least(5, n)), 0) into v_gardees_apres from (
    select count(*) as n from possessions group by joueur_id
  ) t;

  -- --- mode simulation : on s'arrete la ----------------------------------
  if not p_confirmer then
    return query
      select 'SIMULATION'::text, 'rien n''a ete modifie'::text
      union all select 'saison', p_saison || ' (' || v_etat || ') -> ' || p_nouvelle_id
      union all select 'joueurs concernes', v_joueurs::text
      union all select 'possessions', v_possessions::text
      union all select 'deja marquees favorites', v_gardees::text
      union all select 'joueurs a completer d''office', v_sans_favori::text
      union all select 'gardees apres completion', v_gardees_apres::text
      union all select 'rendues au pot', (v_possessions - v_gardees_apres)::text
      union all select 'sieges purges', v_sieges::text
      union all select 'annonces purgees', v_annonces::text
      union all select 'echanges purges', v_echanges::text
      union all select 'soldes remis a', p_solde_depart::text
      union all select 'pour agir', 'relancer avec p_confirmer => true';
    return;
  end if;

  -- =======================================================================
  --  A PARTIR D'ICI, ON ECRIT
  -- =======================================================================

  -- --- b) archiver le classement AVANT toute suppression ------------------
  insert into classement_saisons (saison, joueur_id, pseudo, rang, communes,
                                  legendaires, rares, departements, points)
  select p_saison,
         t.joueur_id,
         t.pseudo,
         row_number() over (order by t.communes desc, t.legendaires desc,
                                     t.rares desc, t.pseudo)::integer,
         t.communes, t.legendaires, t.rares, t.departements, t.points
    from (
      select p.joueur_id,
             j.pseudo,
             count(*)::integer as communes,
             count(*) filter (where c.tier = 'legendaire')::integer as legendaires,
             count(*) filter (where c.tier = 'rare')::integer as rares,
             count(distinct c.departement)::integer as departements,
             coalesce(j.solde, 0)::integer as points
        from possessions p
        join communes c on c.code = p.commune_code
        left join joueurs j on j.id = p.joueur_id
       group by p.joueur_id, j.pseudo, j.solde
    ) t
  on conflict (saison, joueur_id) do nothing;
  get diagnostics v_lignes = row_count;

  -- --- c) completer les favoris a 5, une legendaire au plus ---------------
  -- La completion applique exactement la meme regle que marquer_gardee :
  -- au plus une legendaire parmi les cinq. Un joueur qui ne possederait
  -- que des legendaires n'en garderait donc qu'une — cas impossible en
  -- pratique, on tire des communs en permanence, mais la coherence entre
  -- les deux points d'application compte plus que ce cas limite.
  --
  -- D'abord, on retablit l'invariant : au plus UNE legendaire favorite par
  -- joueur. marquer_gardee interdit deja d'en marquer deux, donc cet etat
  -- ne peut venir que d'une modification directe ou d'un bug. Mais la
  -- cloture est le moment de verite : si elle se contente de ne pas
  -- aggraver un etat impossible, la regle n'est qu'un espoir. On garde la
  -- plus peuplee et on libere les autres, qui retournent au pot.
  with trop as (
    select p.commune_code
      from (
        select p.commune_code, p.joueur_id,
               row_number() over (partition by p.joueur_id
                                  order by c.population desc nulls last,
                                           p.commune_code) as rn
          from possessions p
          join communes c on c.code = p.commune_code
         where p.gardee and c.tier = 'legendaire'
      ) p
     where p.rn > 1
  )
  update possessions set gardee = false
   where commune_code in (select commune_code from trop);

  -- Ensuite la completion. Trois etapes lisibles plutot qu'un tri
  -- astucieux : les candidates, la seule legendaire autorisee, puis le
  -- classement final.
  with places as (
    select p.joueur_id,
           5 - count(*) filter (where p.gardee) as libres,
           count(*) filter (where p.gardee and c.tier = 'legendaire') as leg_deja
      from possessions p
      join communes c on c.code = p.commune_code
     group by p.joueur_id
    having count(*) filter (where p.gardee) < 5
  ),
  libres_cand as (
    select p.commune_code, p.joueur_id, c.tier, c.population, pl.leg_deja
      from possessions p
      join communes c on c.code = p.commune_code
      join places pl on pl.joueur_id = p.joueur_id
     where not p.gardee
  ),
  -- la meilleure legendaire, et seulement si le joueur n'en garde pas deja
  leg_ok as (
    select commune_code, joueur_id from (
      select lc.commune_code, lc.joueur_id,
             row_number() over (partition by lc.joueur_id
                                order by lc.population desc nulls last,
                                         lc.commune_code) as rn
        from libres_cand lc
       where lc.tier = 'legendaire' and lc.leg_deja = 0
    ) t where rn = 1
  ),
  candidates as (
    select lc.commune_code, lc.joueur_id,
           row_number() over (
             partition by lc.joueur_id
             order by case lc.tier when 'legendaire' then 1 when 'rare' then 2
                                   when 'peucommun' then 3 else 4 end,
                      lc.population desc nulls last,
                      lc.commune_code) as rang
      from libres_cand lc
     where lc.tier <> 'legendaire'
        or exists (select 1 from leg_ok lo
                    where lo.commune_code = lc.commune_code
                      and lo.joueur_id = lc.joueur_id)
  )
  update possessions p
     set gardee = true
    from candidates ca
    join places pl on pl.joueur_id = ca.joueur_id
   where p.commune_code = ca.commune_code
     and p.joueur_id = ca.joueur_id
     and ca.rang <= pl.libres;

  select count(*) into v_gardees from possessions where gardee;
  select count(*) into v_legendaires_gardees
    from possessions p join communes c on c.code = p.commune_code
   where p.gardee and c.tier = 'legendaire';
  v_rendues := v_possessions - v_gardees;

  -- --- d) fermer l'historique des communes rendues ------------------------
  -- On ferme TOUTE ligne ouverte qui ne correspond pas a une possession
  -- gardee : les communes rendues, et les lignes ouvertes dont la
  -- possession n'existe deja plus (29 cas mesures le 28 septembre, un
  -- ecart petit mais stable). Sans ce balayage elles resteraient ouvertes
  -- pour toujours.
  update historique h
     set released_at = now()
   where h.released_at is null
     and not exists (select 1 from possessions p
                      where p.commune_code = h.commune_code
                        and p.joueur_id = h.joueur_id
                        and p.gardee);
  get diagnostics v_hist = row_count;

  -- --- e) rendre les communes au pot --------------------------------------
  delete from possessions where not gardee;

  -- --- f) les gardees repartent propres -----------------------------------
  -- acquired_at reste : la possession n'a pas ete interrompue.
  update possessions
     set saison = p_nouvelle_id,
         gardee = false,
         bouclier_debut = null,
         bouclier_jusqua = null,
         conquise_le = null;

  -- --- g) purge ------------------------------------------------------------
  delete from sieges;
  delete from annonces;
  delete from echanges;

  -- --- h) les points repartent de zero ------------------------------------
  update joueurs
     set solde = p_solde_depart,
         paquets_achetes_jour = 0,
         paquets_achetes_date = current_date;

  -- --- i) fermer, puis ouvrir ---------------------------------------------
  update saisons
     set etat = 'terminee', fin_reelle = now()
   where id = p_saison;

  insert into saisons (id, nom, debut, etat)
  values (p_nouvelle_id, p_nouveau_nom, now(), 'en_cours');

  execute format('alter table public.possessions alter column saison set default %L',
                 p_nouvelle_id);

  return query
    select 'CLOTURE EFFECTUEE'::text, p_saison || ' -> ' || p_nouvelle_id
    union all select 'joueurs archives', v_lignes::text
    union all select 'communes gardees', v_gardees::text
    union all select 'dont legendaires', v_legendaires_gardees::text
    union all select 'communes rendues au pot', v_rendues::text
    union all select 'lignes d''historique fermees', v_hist::text
    union all select 'sieges purges', v_sieges::text
    union all select 'annonces purgees', v_annonces::text
    union all select 'echanges purges', v_echanges::text
    union all select 'soldes remis a', p_solde_depart::text;
end;
$function$;

revoke all on function
  public.cloturer_saison(text, text, text, boolean, integer)
  from public, anon, authenticated;
