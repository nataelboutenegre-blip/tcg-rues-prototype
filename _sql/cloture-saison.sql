-- ===========================================================================
--  TerraFront — cloture de saison
--
--  CE FICHIER DEFINIT une fonction qui supprime des donnees, mais ne
--  supprime rien a l'execution : la derniere instruction est une
--  SIMULATION, qui ne modifie aucune ligne.
--
--  Deux choses :
--
--    1. un correctif de saison_courante() — sans lui la saison 2 ne se
--       terminerait jamais
--    2. cloturer_saison(), qui ferme une saison et en ouvre une autre
--
--  Le correctif ne detruit rien et peut partir tout de suite.
--  La cloture ne doit PAS etre lancee avec p_confirmer => true sur la
--  saison reelle avant d'avoir ete vue tourner sur une saison factice,
--  sauvegarde Supabase prise.
--
--  --------------------------------------------------------------------
--  GARDE-FOU : cloturer_saison(..., p_confirmer => false) ne modifie
--  RIEN. Elle renvoie ce qu'elle ferait : combien de communes seraient
--  rendues, combien gardees, combien de joueurs. C'est le mode par
--  defaut. Il faut p_confirmer => true pour qu'elle agisse.
--  --------------------------------------------------------------------
--
--  NOTE — draw_commune n'est volontairement PAS modifiee ici. Elle recoit
--  la saison et ne l'ecrit pas dans possessions, ce qui est une petite
--  incoherence ; mais la reecrire voudrait dire remplacer integralement la
--  fonction la plus sollicitee du jeu pour une seule ligne, avec le risque
--  de transcription que ca comporte. cloturer_saison() deplace le DEFAUT
--  de la colonne saison a chaque ouverture, ce qui produit le meme
--  resultat sans toucher au tirage.
-- ===========================================================================


-- ---------------------------------------------------------------------------
--  1. saison_courante() — compter les communes prises comme draw_commune
--     les compte
--
--  Avant, le compte filtrait sur la saison courante. C'est faux pour deux
--  raisons.
--
--  D'abord draw_commune insere sans preciser la saison et s'en remet au
--  defaut de la colonne, fige a 'saison-1'. En saison 2 le compte serait
--  tombe a zero, le nombre de communes libres aurait valu 34 739, et le
--  seuil n'aurait jamais ete franchi : la saison 2 n'aurait jamais pris
--  fin.
--
--  Ensuite, meme avec l'etiquetage corrige, les communes gardees d'une
--  saison precedente occupent le terrain sans porter la saison courante :
--  elles auraient ete comptees comme libres alors qu'elles ont un
--  proprietaire.
--
--  La seule definition qui vaille est celle de draw_commune : une commune
--  est libre si elle n'a aucune ligne dans possessions. Une seule
--  definition, dans les deux fonctions.
-- ---------------------------------------------------------------------------
create or replace function public.saison_courante()
returns table(id text, nom text, etat text, fin_prevue timestamptz,
              libres integer, total integer, seuil integer, sans_bouclier boolean)
language plpgsql
security definer
set search_path to 'public'
as $function$
declare
  v_id text; v_nom text; v_etat text; v_fin timestamptz;
  v_seuil integer; v_jours integer; v_libres integer; v_total integer;
  v_prises integer;
begin
  select sa.id, sa.nom, sa.etat, sa.fin_prevue, sa.seuil_communes, sa.jours_rebours
    into v_id, v_nom, v_etat, v_fin, v_seuil, v_jours
    from saisons sa
   where sa.etat <> 'terminee'
   order by sa.debut desc
   limit 1;

  if v_id is null then
    return;                                   -- aucune saison ouverte
  end if;

  select count(*) into v_total  from communes c;
  select count(*) into v_prises from possessions p;   -- plus de filtre saison
  v_libres := v_total - v_prises;

  -- franchissement du seuil : on arme le compte a rebours, une seule fois
  if v_etat = 'en_cours' and v_libres <= v_seuil then
    update saisons sa
       set etat = 'compte_a_rebours',
           fin_prevue = now() + (v_jours || ' days')::interval
     where sa.id = v_id and sa.etat = 'en_cours'
    returning sa.etat, sa.fin_prevue into v_etat, v_fin;
  end if;

  return query select
    v_id, v_nom, v_etat, v_fin,
    v_libres, v_total, v_seuil,
    -- les dernieres 24 h se jouent sans aucune protection
    (v_etat = 'compte_a_rebours' and v_fin is not null
     and now() >= v_fin - interval '24 hours');
end;
$function$;

grant execute on function public.saison_courante() to authenticated;


-- ---------------------------------------------------------------------------
--  2. cloturer_saison()
--
--  Tout se passe dans une seule transaction : une fonction plpgsql est
--  atomique. Si une etape echoue, aucune ne s'applique. Une cloture a
--  moitie faite serait pire qu'une cloture absente — des joueurs sans
--  communes et un classement non archive, sans moyen de revenir en arriere.
--
--  L'ordre compte :
--   a) verrouiller la saison, refuser si elle est deja terminee
--   b) archiver le classement AVANT de supprimer quoi que ce soit
--   c) completer les favoris a 5 pour ceux qui en ont moins
--   d) fermer les lignes d'historique des communes rendues
--   e) supprimer les possessions non gardees
--   f) remettre les gardees a zero : nouvelle saison, plus de favori,
--      plus de bouclier
--   g) purger sieges, annonces, echanges
--   h) remettre les soldes a p_solde_depart
--   i) fermer la saison, ouvrir la suivante, deplacer le defaut de colonne
--
--  Ce qui n'est PAS touche, deliberement :
--   - acquired_at des communes gardees. Le joueur les detient sans
--     interruption, remettre la date a zero effacerait une information
--     vraie pour rien.
--   - historique des communes gardees. La possession continue, elle ne
--     recommence pas.
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
  v_sieges integer;
  v_annonces integer;
  v_echanges integer;
  v_hist integer;
  v_lignes integer;
  v_gardees_apres integer;
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

  -- combien de joueurs ont moins de 5 favoris et seront completes d'office
  select count(*) into v_sans_favori from (
    select joueur_id
      from possessions
     group by joueur_id
    having count(*) filter (where gardee) < least(5, count(*))
  ) t;

  -- Combien seront gardees apres completion. Pas « 5 par joueur » : un
  -- joueur qui possede moins de 5 communes garde tout ce qu'il a. La
  -- premiere version de cette simulation annoncait 15 la ou la cloture
  -- en gardait 13, et une simulation qui se trompe est une simulation
  -- qu'on cesse de lire.
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
  -- Le plateau se vide, pas le palmares.
  -- Rang : par nombre de communes, puis legendaires, puis rares. A VERIFIER
  -- contre le classement affiche dans le jeu avant la premiere vraie
  -- cloture — si les deux different, les joueurs le verront.
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

  -- --- c) completer les favoris a 5 --------------------------------------
  -- Personne n'est puni d'avoir moins de 5 favoris : on complete avec ses
  -- meilleures communes, par rarete puis population. Le choix reste au
  -- joueur, l'absence de choix ne lui coute rien.
  with places as (
    select p.joueur_id,
           5 - count(*) filter (where p.gardee) as libres
      from possessions p
     group by p.joueur_id
    having count(*) filter (where p.gardee) < 5
  ),
  candidates as (
    select p.commune_code, p.joueur_id,
           row_number() over (
             partition by p.joueur_id
             order by case c.tier when 'legendaire' then 1 when 'rare' then 2
                                  when 'peucommun' then 3 else 4 end,
                      c.population desc nulls last,
                      p.commune_code) as rang
      from possessions p
      join communes c on c.code = p.commune_code
      join places pl on pl.joueur_id = p.joueur_id
     where not p.gardee
  )
  update possessions p
     set gardee = true
    from candidates ca
    join places pl on pl.joueur_id = ca.joueur_id
   where p.commune_code = ca.commune_code
     and p.joueur_id = ca.joueur_id
     and ca.rang <= pl.libres;

  select count(*) into v_gardees from possessions where gardee;
  v_rendues := v_possessions - v_gardees;

  -- --- d) fermer l'historique des communes rendues ------------------------
  -- On ferme TOUTE ligne ouverte qui ne correspond pas a une possession
  -- gardee. Cela couvre deux cas :
  --
  --   - les communes rendues au pot, ce qui est l'objet de l'etape ;
  --   - les lignes ouvertes dont la possession n'existe deja plus. Mesure
  --     du 28 septembre : 29 lignes dans ce cas, un ecart petit mais
  --     stable, donc pas du bruit. Une vente ou un transfert a oublie de
  --     renseigner released_at. Sans ce balayage elles resteraient
  --     ouvertes pour toujours et fausseraient toute lecture de
  --     l'historique saison apres saison.
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

  -- Le defaut de la colonne suit la nouvelle saison. C'est ce qui remplace
  -- la modification de draw_commune : les tirages suivants seront etiquetes
  -- correctement sans avoir touche au tirage lui-meme.
  execute format('alter table public.possessions alter column saison set default %L',
                 p_nouvelle_id);

  return query
    select 'CLOTURE EFFECTUEE'::text, p_saison || ' -> ' || p_nouvelle_id
    union all select 'joueurs archives', v_lignes::text
    union all select 'communes gardees', v_gardees::text
    union all select 'communes rendues au pot', v_rendues::text
    union all select 'lignes d''historique fermees', v_hist::text
    union all select 'sieges purges', v_sieges::text
    union all select 'annonces purgees', v_annonces::text
    union all select 'echanges purges', v_echanges::text
    union all select 'soldes remis a', p_solde_depart::text;
end;
$function$;

-- Fonction d'administration : personne ne l'appelle depuis le jeu.
revoke all on function
  public.cloturer_saison(text, text, text, boolean, integer)
  from public, anon, authenticated;


-- ---------------------------------------------------------------------------
--  Derniere instruction : la SIMULATION. Elle ne modifie rien.
-- ---------------------------------------------------------------------------
select * from cloturer_saison('saison-1', 'saison-2', 'Saison 2');
