-- ===========================================================================
--  TerraFront — s2-100 : les lenteurs du soir (relevé le 5/11)
--
--  Le 4/11 vers 21 h, la base a coupé 210 requêtes en une heure (délai de 8 s
--  dépassé), contre ~5 d'habitude. Ce qui lui coûte le plus depuis le 25/10 :
--    quêtes            103 000 appels × 0,4 s
--    classement         27 000 appels × 1,3 s
--    profil             23 000 appels × 1,05 s
--    détail des scores  24 000 appels × 0,7 s
--  Le classement et le détail des scores recalculaient TOUT (35 000 communes,
--  tous les départements) à chaque ouverture de l'onglet Communauté ; le
--  profil aussi, rien que pour donner le rang.
--
--  1. Le classement est recalculé une fois par minute (pg_cron) dans une
--     petite table, et le jeu lit cette table. Si elle a plus de 5 minutes
--     (tâche arrêtée), on recalcule comme avant : jamais de classement figé.
--     Depuis l'éditeur SQL (clôture de saison…), toujours le calcul direct.
--     « Ce mois-ci » reste calculé à la demande.
--  2. Le profil calcule les chiffres du joueur seul ; le rang vient du même
--     calcul que le classement.
--  3. Quêtes : « Complète un département » ne parcourt plus les 35 000
--     communes à chaque ouverture (une fois réclamée, plus de calcul du tout).
--  4. historique : un index par joueur (le profil le relisait en entier,
--     deux fois par ouverture).
--  5. points_rarete : sans « set search_path », Postgres remplace l'appel par
--     son CASE au lieu de l'appeler 32 000 fois (0,24 s de moins par calcul).
--     Le conseiller de sécurité Supabase signalera « search_path mutable » sur
--     cette fonction : sans danger ici (aucune table, que des constantes).
--
--  Ce que les joueurs verront : le classement peut avoir jusqu'à une minute
--  de retard sur une conquête. Rien d'autre ne change.
--
--  Vérifié sur la production (lecture seule, le 5/11) : le nouveau classement
--  donne exactement les mêmes lignes que l'ancien (131/131), le rang du profil
--  est le même pour les 132 joueurs, les départements complets aussi (109/109).
--  Indépendant du lot du 8/11 : aucun de ses fichiers ne touche ces
--  fonctions (s2-lot-8 modifie quetes_liste ailleurs, testé ensemble).
--  Rejouable. Peut passer tout de suite.
--
--  Contrôle attendu : ~132 | true | 1 | 0 | true | true | true | true
--  Retour arrière du point 1 si besoin : select cron.unschedule('classement_cache');
--  (la table vieillit, et au bout de 5 minutes tout repasse en calcul direct)
-- ===========================================================================
begin;

create or replace function pg_temp.remp(d text, avant text, apres text, nb int, quoi text)
 returns text language plpgsql as $f$
begin
  if (length(d) - length(replace(d, avant, ''))) / length(avant) <> nb then
    raise exception '% : texte attendu % fois, trouvé % fois — rien n''a changé : %',
      quoi, nb, (length(d) - length(replace(d, avant, ''))) / length(avant), avant;
  end if;
  return replace(d, avant, apres);
end;
$f$;

-- 4. historique : par joueur ---------------------------------------------------
create index if not exists historique_joueur on public.historique (joueur_id, acquired_at);

-- 5. points_rarete remplacée par son CASE ---------------------------------------
alter function public.points_rarete(text) reset search_path;

-- 1. le classement, une fois par minute ------------------------------------------
create table if not exists public.classement_cache (
  joueur_id      uuid primary key,
  cartes         integer not null,
  combats        integer not null,
  territoires    integer not null,
  victoires      integer not null,
  deps_domines   integer not null,
  deps_controles integer not null,
  regions        integer not null,
  communes       integer not null,
  habitants      bigint  not null,
  legendaires    integer not null,
  rares          integer not null,
  maj_le         timestamptz not null default now()
);
alter table public.classement_cache enable row level security;
revoke all on public.classement_cache from public, anon, authenticated;

-- le calcul complet : front_scores() + les totaux de chaque joueur
create or replace function public.classement_calcul()
 returns table(joueur_id uuid, cartes integer, combats integer, territoires integer, victoires integer,
               deps_domines integer, deps_controles integer, regions integer,
               communes integer, habitants bigint, legendaires integer, rares integer)
 language sql stable security definer set search_path = public
as $f$
  with tot as (
    select p.joueur_id,
           count(*)::integer                                      as communes,
           sum(coalesce(c.population, 0))::bigint                 as habitants,
           count(*) filter (where c.tier = 'legendaire')::integer as legendaires,
           count(*) filter (where c.tier = 'rare')::integer       as rares
      from possessions p join communes c on c.code = p.commune_code
     group by p.joueur_id
  )
  select f.joueur_id, f.cartes, f.combats, f.territoires, f.victoires,
         f.deps_domines, f.deps_controles, f.regions,
         coalesce(t.communes, 0), coalesce(t.habitants, 0)::bigint,
         coalesce(t.legendaires, 0), coalesce(t.rares, 0)
    from front_scores() f
    left join tot t on t.joueur_id = f.joueur_id;
$f$;
revoke all on function public.classement_calcul() from public, anon, authenticated;

create or replace function public.classement_cache_maj()
 returns integer language plpgsql security definer set search_path = public
as $f$
declare
  n integer;
begin
  -- un seul calcul à la fois (tâche de la minute + appel à la main)
  if not pg_try_advisory_xact_lock(hashtext('classement_cache_maj')) then return -1; end if;
  delete from classement_cache;
  insert into classement_cache (joueur_id, cartes, combats, territoires, victoires, deps_domines,
                                deps_controles, regions, communes, habitants, legendaires, rares, maj_le)
  select l.joueur_id, l.cartes, l.combats, l.territoires, l.victoires, l.deps_domines,
         l.deps_controles, l.regions, l.communes, l.habitants, l.legendaires, l.rares, now()
    from classement_calcul() l;
  get diagnostics n = row_count;
  return n;
end;
$f$;
revoke all on function public.classement_cache_maj() from public, anon, authenticated;

create or replace function public.classement_cache_frais()
 returns boolean language sql stable security definer set search_path = public
as $f$
  select coalesce(max(k.maj_le) > now() - interval '5 minutes', false) from classement_cache k;
$f$;
revoke all on function public.classement_cache_frais() from public, anon, authenticated;

-- ce que lisent classement, score_detail et profil_joueur
create or replace function public.classement_lignes()
 returns table(joueur_id uuid, cartes integer, combats integer, territoires integer, victoires integer,
               deps_domines integer, deps_controles integer, regions integer,
               communes integer, habitants bigint, legendaires integer, rares integer)
 language plpgsql stable security definer set search_path = public
as $f$
begin
  -- depuis le jeu : la copie de la minute ; depuis l'éditeur SQL, ou si la
  -- copie a vieilli (tâche arrêtée) : le calcul direct
  if coalesce(current_setting('request.jwt.claims', true), '') <> '' and classement_cache_frais() then
    return query
      select k.joueur_id, k.cartes, k.combats, k.territoires, k.victoires, k.deps_domines,
             k.deps_controles, k.regions, k.communes, k.habitants, k.legendaires, k.rares
        from classement_cache k;
  else
    return query select * from classement_calcul();
  end if;
end;
$f$;
revoke all on function public.classement_lignes() from public, anon, authenticated;

-- le classement : mêmes lignes qu'avant (vérifié), lues dans la copie
create or replace function public.classement(p_mode text default 'general'::text, p_limite integer default 20)
 returns table(rang integer, joueur_id uuid, pseudo text, score integer, communes integer, habitants bigint,
               legendaires integer, rares integer, est_moi boolean)
 language sql stable security definer set search_path to 'public'
as $function$
  with mois as (
    -- ce mois-ci : communes acquises depuis le 1er du mois et encore possedees
    select h.joueur_id,
           sum(points_rarete(c.tier))::integer                    as score,
           count(*)::integer                                      as communes,
           sum(coalesce(c.population, 0))::bigint                 as habitants,
           count(*) filter (where c.tier = 'legendaire')::integer as legendaires,
           count(*) filter (where c.tier = 'rare')::integer       as rares
      from historique h
      join communes c on c.code = h.commune_code
      join possessions p on p.commune_code = h.commune_code and p.joueur_id = h.joueur_id
     where p_mode = 'mois'
       and h.released_at is null
       and h.acquired_at >= date_trunc('month', now())
     group by h.joueur_id
  ),
  tous as (
    -- la saison : cartes + combats + territoires (s2-100 : lus dans la copie de la minute)
    select l.joueur_id,
           l.cartes + case when score_bonus_actif() then l.combats + l.territoires else 0 end as score,
           l.communes, l.habitants, l.legendaires, l.rares
      from classement_lignes() l
     where p_mode <> 'mois'
    union all
    select m.joueur_id, m.score, m.communes, m.habitants, m.legendaires, m.rares
      from mois m
  ),
  classe as (
    select row_number() over (order by x.score desc, x.communes desc, x.habitants desc)::integer as rang,
           x.*, coalesce(j.pseudo, 'Joueur')::text as pseudo
    from tous x join joueurs j on j.id = x.joueur_id
    where x.score > 0 and not est_exclu_classement(j.pseudo)
  )
  -- les meilleurs, plus ma propre ligne meme si je suis loin derriere
  select c.rang, c.joueur_id, c.pseudo, c.score::integer, c.communes, c.habitants,
         c.legendaires, c.rares, (c.joueur_id = auth.uid()) as est_moi
  from classe c
  where c.rang <= greatest(p_limite, 3) or c.joueur_id = auth.uid()
  order by c.rang;
$function$;

-- le détail des scores (la légende sous le classement)
create or replace function public.score_detail(p_joueurs uuid[])
 returns table(joueur_id uuid, cartes integer, combats integer, territoires integer, victoires integer,
               deps_domines integer, deps_controles integer, regions integer)
 language sql stable security definer set search_path to 'public'
as $function$
  select l.joueur_id, l.cartes, l.combats, l.territoires, l.victoires,
         l.deps_domines, l.deps_controles, l.regions
    from classement_lignes() l   -- s2-100
   where auth.uid() is not null and l.joueur_id = any(p_joueurs[1:60]);
$function$;

-- 2. le profil : les chiffres du joueur seul, le rang depuis le classement --------
create or replace function public.profil_joueur(p_joueur uuid)
 returns jsonb
 language sql
 stable security definer
 set search_path to 'public'
as $function$
  with moi as (
    -- s2-100 : le joueur seul (avant : tous les joueurs, pour en garder un)
    select count(*)::integer                                      as communes,
           coalesce(sum(points_rarete(c.tier)), 0)::integer       as score,
           coalesce(sum(coalesce(c.population, 0)), 0)::bigint    as habitants,
           count(*) filter (where c.tier = 'legendaire')::integer as legendaires,
           count(*) filter (where c.tier = 'rare')::integer       as rares,
           count(distinct c.departement)::integer                 as departements
      from possessions p
      join communes c on c.code = p.commune_code
     where p.joueur_id = p_joueur
  ),
  rang as (
    -- même ordre qu'avant : cartes, puis communes, puis habitants
    select case when m.communes = 0 then 0
                else 1 + (select count(*) from classement_lignes() l
                           where l.communes > 0 and l.joueur_id <> p_joueur
                             and (l.cartes, l.communes, l.habitants) > (m.score, m.communes, m.habitants))::integer
           end as n
      from moi m
  ),
  phares as (
    select jsonb_agg(x order by x.pop desc) as liste
      from (
        select c.nom, c.departement as dep, c.population as pop, c.tier
          from possessions p
          join communes c on c.code = p.commune_code
         where p.joueur_id = p_joueur
         order by c.population desc nulls last
         limit 5
      ) x
  ),
  deps as (
    select jsonb_agg(jsonb_build_object('dep', d.departement, 'n', d.n)) as liste
      from (
        select c.departement, count(*)::integer as n
          from possessions p
          join communes c on c.code = p.commune_code
         where p.joueur_id = p_joueur
         group by c.departement
      ) d
  )
  select jsonb_build_object(
    'id',            j.id,
    'pseudo',        coalesce(j.pseudo, 'Joueur'),
    'avatar',        j.avatar,
    'depuis',        j.created_at,
    'est_moi',       (j.id = auth.uid()),
    'rang',          coalesce((select n from rang), 0),
    'score',         m.score,
    'communes',      m.communes,
    'habitants',     m.habitants,
    'legendaires',   m.legendaires,
    'rares',         m.rares,
    'epiques',       (select count(*)::integer from possessions pe join communes ce on ce.code = pe.commune_code
                       where pe.joueur_id = p_joueur and ce.tier = 'epique'),
    'departements',  m.departements,
    'phares',        coalesce((select liste from phares), '[]'::jsonb),
    'deps',          coalesce((select liste from deps), '[]'::jsonb)
  ) || compteurs_joueur(p_joueur)
  from joueurs j
  cross join moi m
  where j.id = p_joueur;
$function$;

-- 3. quêtes : « Complète un département » -----------------------------------------
do $$
declare d text := pg_get_functiondef('public.quetes_liste(uuid)'::regprocedure);
begin
  if position('s2-100' in d) > 0 then raise notice 'quetes_liste : déjà à jour'; return; end if;
  d := pg_temp.remp(d,
'  select count(*) into v_dept from (
    select c.departement
      from communes c
      left join terra_collection t on t.commune_code = c.code and t.joueur_id = p_uid and t.exemplaires > 0
     where est_metropole(c.departement)
     group by c.departement
    having count(*) = count(t.commune_code)) x;',
'  -- s2-100 : une fois la quête réclamée, plus rien à compter ; sinon on part
  -- de la collection du joueur (avant : les 35 000 communes à chaque ouverture)
  if exists (select 1 from quetes_reclamees r where r.joueur_id = p_uid and r.quete = ''u_tdept'') then
    v_dept := 1;
  else
    select count(*) into v_dept
      from (select c.departement, count(*) as n
              from terra_collection t join communes c on c.code = t.commune_code
             where t.joueur_id = p_uid and t.exemplaires > 0 and est_metropole(c.departement)
             group by c.departement) m
      join (select c2.departement, count(*) as n from communes c2 group by c2.departement) tot
        on tot.departement = m.departement and tot.n = m.n;
  end if;',
    1, 'quetes_liste (départements complets)');
  execute d;
end $$;

-- la copie, tout de suite, puis chaque minute
select public.classement_cache_maj();
select cron.schedule('classement_cache', '* * * * *', 'select public.classement_cache_maj()');

commit;

-- Contrôle : ~132 | true | 1 | 0 | true | true | true | true
select (select count(*) from public.classement_cache)                                        as joueurs,
       public.classement_cache_frais()                                                        as frais,
       (select count(*) from cron.job where jobname = 'classement_cache' and active)           as tache,
       (select count(*) from (select * from public.classement_calcul()
                              except
                              select joueur_id, cartes, combats, territoires, victoires, deps_domines,
                                     deps_controles, regions, communes, habitants, legendaires, rares
                                from public.classement_cache) x)                               as ecarts,
       position('s2-100' in pg_get_functiondef('public.quetes_liste(uuid)'::regprocedure)) > 0 as quetes_ok,
       (select proconfig is null from pg_proc where oid = 'public.points_rarete(text)'::regprocedure) as points_ok,
       has_function_privilege('authenticated', 'public.classement(text, integer)', 'execute')
       and has_function_privilege('authenticated', 'public.profil_joueur(uuid)', 'execute')
       and has_function_privilege('authenticated', 'public.score_detail(uuid[])', 'execute')  as droits_ok,
       not has_function_privilege('authenticated', 'public.classement_cache_maj()', 'execute')
       and not has_function_privilege('authenticated', 'public.classement_lignes()', 'execute')
       and not has_function_privilege('anon', 'public.classement_calcul()', 'execute')         as prive_ok;
