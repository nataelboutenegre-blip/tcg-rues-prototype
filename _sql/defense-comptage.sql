-- ===========================================================================
--  TerraFront — La défense qui annule un siège n'était pas comptée
--
--  SIGNALÉ PAR BOULE2PAIN LE 1er OCTOBRE
--    « Quand notre commune est à deux attaques, si on réussit une défense à
--      une attaque, cela n'est pas comptabilisé. »
--
--  CE QUI SE PASSAIT VRAIMENT, ET C'EST PIRE
--    defendre() finit par :
--        defense_utilisee = (v_restantes > 0)
--    et les deux déclencheurs reconnaissaient une défense à :
--        les victoires baissent ET defense_utilisee vient de passer à vrai
--
--    Quand l'assaillant n'avait qu'UNE victoire, la défense le ramène à
--    zéro, defense_utilisee repasse donc à FAUX, et la condition n'est
--    jamais remplie. Ni compteur, ni ligne de journal.
--
--    Autrement dit : la meilleure défense possible, celle qui annule
--    complètement le siège, était la seule à ne pas compter. Le nombre
--    d'assaillants n'y est pour rien — c'est le nombre de victoires de
--    celui qu'on repousse.
--
--  POURQUOI CETTE CONDITION EXISTAIT
--    Il fallait distinguer une défense réussie d'un assaillant qui perd son
--    round : les deux font baisser victoires_consecutives. La devinette
--    était légitime, elle était juste fausse dans un cas sur deux.
--
--  LA CORRECTION
--    On arrête de deviner. defendre() sait de source sûre ce qui vient de
--    se passer : c'est elle qui écrit le journal et incrémente le compteur.
--    Les déclencheurs ne gardent que ce qu'ils savent faire sans ambiguïté,
--    c'est-à-dire le côté attaque.
--
--  CE QUI N'EST PAS RATTRAPABLE
--    Les défenses perdues n'ont laissé aucune trace, nulle part. On ne peut
--    pas les reconstituer. total_defenses reste sous-évalué pour tout le
--    monde, et le comptage ne redevient juste qu'à partir de maintenant.
--
--  AU PASSAGE
--    L'objectif « Possède une légendaire » annonçait encore « Plus de
--    100 000 habitants ». Depuis le rééquilibrage du 29 septembre c'est
--    50 000. Le texte mentait aux joueurs ; corrigé ici, le reste de la
--    fonction est reproduit à l'identique.
-- ===========================================================================


-- ---------------------------------------------------------------------------
--  1. defendre() : elle compte et elle journalise elle-même
--
--  Seule la fin change. Tout ce qui précède est repris mot pour mot.
-- ---------------------------------------------------------------------------
create or replace function public.defendre(
  p_commune_code text, p_attaquant uuid, p_intensite text default 'normale'::text)
returns table(reussie boolean, victoires_restantes integer, cout integer, chances integer)
language plpgsql
security definer
set search_path to 'public'
as $function$
#variable_conflict use_column
declare
  v_uid uuid := auth.uid();
  v_tier text;
  v_proprio uuid;
  v_bouclier timestamptz;
  v_victoires integer;
  v_deja boolean;
  v_cout integer;
  v_solde integer;
  v_reussie boolean;
  v_restantes integer;
  v_chance numeric;
begin
  if v_uid is null then raise exception 'Non connecté'; end if;

  select c.tier, p.joueur_id, p.bouclier_jusqua into v_tier, v_proprio, v_bouclier
    from possessions p join communes c on c.code = p.commune_code
    where p.commune_code = p_commune_code
    for update of p;
  if v_proprio is null or v_proprio <> v_uid then
    raise exception 'Cette commune ne t''appartient pas';
  end if;
  if v_bouclier is not null and v_bouclier > now() then
    raise exception 'Ta commune est déjà protégée par un bouclier';
  end if;

  select s.victoires_consecutives, s.defense_utilisee into v_victoires, v_deja
    from sieges s
    where s.commune_code = p_commune_code and s.attacker_id = p_attaquant
    for update of s;
  if v_victoires is null or v_victoires = 0 then
    raise exception 'Cet attaquant n''a aucune victoire en cours sur ta commune';
  end if;
  if v_deja then
    raise exception 'Tu as déjà utilisé ta défense contre cette attaque';
  end if;

  v_chance := chance_intensite(p_intensite);
  if v_chance is null then raise exception 'Intensité inconnue'; end if;
  v_cout := greatest(1, round(cout_attaque(v_tier) * cout_intensite(p_intensite)))::integer;
  select solde into v_solde from joueurs where id = v_uid for update;
  if v_solde < v_cout then
    raise exception 'Solde insuffisant pour défendre (% points requis)', v_cout;
  end if;
  update joueurs set solde = solde - v_cout where id = v_uid;

  v_reussie := random() < v_chance;
  if v_reussie then
    v_restantes := v_victoires - 1;
  else
    v_restantes := v_victoires;
  end if;

  -- si l'attaquant retombe a zero, son attaque est terminee : la defense sera de nouveau disponible
  update sieges
    set victoires_consecutives = v_restantes,
        defense_utilisee = (v_restantes > 0)
    where commune_code = p_commune_code and attacker_id = p_attaquant;

  -- NOUVEAU : le comptage et le journal se font ici, pas dans un declencheur.
  -- Ici on SAIT qu'une defense vient d'avoir lieu et si elle a reussi ; un
  -- declencheur, lui, ne voit qu'un compteur qui bouge et doit deviner.
  if v_reussie then
    perform ajouter_compteur(v_uid, 'defenses', 1);
    perform noter_journal('defense', v_uid, p_attaquant, p_commune_code, v_tier);
  end if;

  return query select v_reussie, v_restantes, v_cout, round(v_chance * 100)::integer;
end;
$function$;


-- ---------------------------------------------------------------------------
--  2. suivi_combat() : on retire la branche défense
--
--  Sans ça, une défense contre un assaillant à 2 victoires serait comptée
--  deux fois — une par le déclencheur, une par defendre().
--  Le côté attaque ne change pas d'une virgule.
-- ---------------------------------------------------------------------------
create or replace function public.suivi_combat()
returns trigger
language plpgsql
security definer
set search_path to 'public'
as $function$
declare v_avant integer := coalesce(old.victoires_consecutives, 0);
begin
  if new.victoires_consecutives > v_avant then
    perform ajouter_compteur(new.attacker_id, 'rounds_gagnes', 1);
    if new.victoires_consecutives >= 3 then
      perform ajouter_compteur(new.attacker_id, 'conquetes', 1);
    end if;
  end if;
  -- La baisse n'est plus traitee ici : elle peut venir d'une defense reussie
  -- comme d'un assaillant qui perd son round, et rien dans la ligne ne permet
  -- de les distinguer. defendre() s'en charge, elle sait.
  return new;
end;
$function$;


-- ---------------------------------------------------------------------------
--  3. Le déclencheur de journal des défenses disparaît
--
--  Même raison : il portait exactement la même devinette. defendre() écrit
--  désormais la ligne.
-- ---------------------------------------------------------------------------
drop trigger if exists trg_journal_defense on public.sieges;
drop function if exists public.journal_defense();


-- ---------------------------------------------------------------------------
--  4. Le texte de l'objectif « Possède une légendaire »
--
--  Reproduction fidèle de la fonction, un seul mot change : le seuil de
--  population, 100 000 -> 50 000.
-- ---------------------------------------------------------------------------
create or replace function public.objectifs()
returns table(id text, categorie text, titre text, detail text, avancement integer,
              cible integer, recompense text, valeur integer, reclamable boolean, reclame boolean)
language plpgsql
stable security definer
set search_path to 'public'
as $function$
declare
  u uuid := auth.uid();
  d_paquets integer := 0; d_cartes integer := 0; d_rounds integer := 0;
  d_conquetes integer := 0; d_defenses integer := 0;
  t_conquetes integer := 0; t_defenses integer := 0;
  nb_communes integer; nb_rares integer; nb_leg integer;
  nb_depts integer; max_meme_dept integer; solde integer;
begin
  if u is null then raise exception 'Non connecté'; end if;

  -- compteurs du jour : ceux d'hier ne comptent pas, les totaux restent
  select case when jour = current_date then paquets else 0 end,
         case when jour = current_date then cartes else 0 end,
         case when jour = current_date then rounds_gagnes else 0 end,
         case when jour = current_date then conquetes else 0 end,
         case when jour = current_date then defenses else 0 end,
         total_conquetes, total_defenses
    into d_paquets, d_cartes, d_rounds, d_conquetes, d_defenses, t_conquetes, t_defenses
    from objectifs_compteurs where joueur_id = u;

  select count(*), count(*) filter (where cm.tier = 'rare'), count(*) filter (where cm.tier = 'legendaire'),
         count(distinct cm.departement)
    into nb_communes, nb_rares, nb_leg, nb_depts
    from possessions p join communes cm on cm.code = p.commune_code where p.joueur_id = u;
  select coalesce(max(n), 0) into max_meme_dept from (
    select count(*) n from possessions p join communes cm on cm.code = p.commune_code
    where p.joueur_id = u group by cm.departement) x;
  select j.solde into solde from joueurs j where j.id = u;

  return query
  with liste(id, categorie, titre, detail, avancement, cible, recompense, valeur) as (values
    -- quotidiens (remis a zero chaque jour)
    ('j_paquets', 'jour', 'Ouvre 3 paquets', 'Gratuits ou achetés', coalesce(d_paquets, 0), 3, 'points', 60),
    ('j_cartes', 'jour', 'Tire 15 cartes', 'Toutes raretés confondues', coalesce(d_cartes, 0), 15, 'points', 80),
    ('j_rounds', 'jour', 'Gagne 5 rounds', 'En attaque', coalesce(d_rounds, 0), 5, 'paquet', 1),
    ('j_conquete', 'jour', 'Conquiers une commune', 'Trois victoires d''affilée', coalesce(d_conquetes, 0), 1, 'points', 150),
    ('j_defense', 'jour', 'Réussis une défense', 'Contre un attaquant', coalesce(d_defenses, 0), 1, 'points', 120),
    -- une seule fois
    ('u_25', 'unique', 'Collectionne 25 communes', 'Ta collection s''étoffe', nb_communes, 25, 'paquet', 1),
    ('u_100', 'unique', 'Collectionne 100 communes', 'Un vrai territoire', nb_communes, 100, 'paquet', 3),
    ('u_250', 'unique', 'Collectionne 250 communes', 'Une collection sérieuse', nb_communes, 250, 'points', 1500),
    ('u_rare', 'unique', 'Possède 5 communes rares', 'De quoi être attaqué', nb_rares, 5, 'points', 200),
    ('u_leg', 'unique', 'Possède une légendaire', 'Plus de 50 000 habitants', nb_leg, 1, 'paquet', 2),
    ('u_dept5', 'unique', 'Domine un département', '5 communes dans le même département', max_meme_dept, 5, 'points', 300),
    ('u_dept10', 'unique', 'Présent dans 10 départements', 'Étends-toi sur la carte', nb_depts, 10, 'paquet', 2),
    ('u_conq5', 'unique', 'Réussis 5 conquêtes', 'Depuis le début', coalesce(t_conquetes, 0), 5, 'points', 400),
    ('u_def3', 'unique', 'Réussis 3 défenses', 'Depuis le début', coalesce(t_defenses, 0), 3, 'points', 300),
    ('u_solde', 'unique', 'Atteins 5 000 points', 'Un joueur fortuné', coalesce(solde, 0), 5000, 'paquet', 3)
  )
  select l.id::text, l.categorie::text, l.titre::text, l.detail::text,
         least(l.avancement, l.cible)::integer, l.cible::integer,
         l.recompense::text, l.valeur::integer,
         (l.avancement >= l.cible and r.objectif is null) as reclamable,
         (r.objectif is not null) as reclame
  from liste l
  left join objectifs_reclames r
    on r.joueur_id = u and r.objectif = l.id
   and r.jour = case when l.categorie = 'jour' then current_date else date '2000-01-01' end
  order by l.categorie desc, (l.avancement >= l.cible and r.objectif is null) desc, l.id;
end;
$function$;


-- ---------------------------------------------------------------------------
--  Vérification
-- ---------------------------------------------------------------------------
select 'A. defendre compte' as controle,
       case when pg_get_functiondef(p.oid) like '%ajouter_compteur(v_uid, ''defenses'', 1)%'
            then 'oui' else 'NON' end as valeur
  from pg_proc p join pg_namespace n on n.oid = p.pronamespace
 where n.nspname = 'public' and p.proname = 'defendre'
union all
select 'B. suivi_combat sans defense',
       case when pg_get_functiondef(p.oid) like '%''defenses''%' then 'ENCORE LA' else 'retiree' end
  from pg_proc p join pg_namespace n on n.oid = p.pronamespace
 where n.nspname = 'public' and p.proname = 'suivi_combat'
union all
select 'C. trg_journal_defense',
       coalesce((select 'ENCORE LA' from pg_trigger where tgname = 'trg_journal_defense'), 'supprime')
union all
select 'D. seuil legendaire dans objectifs',
       case when pg_get_functiondef(p.oid) like '%Plus de 50 000 habitants%'
            then '50 000' else 'PAS CORRIGE' end
  from pg_proc p join pg_namespace n on n.oid = p.pronamespace
 where n.nspname = 'public' and p.proname = 'objectifs'
order by 1;
