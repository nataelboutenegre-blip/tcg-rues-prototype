-- ===========================================================================
--  TerraFront — saison 2 : les quêtes (10 octobre 2026)
--  Décisions de Nataël du 10 octobre (montants validés).
--
--  SANS EFFET EN SAISON 1 : quetes() et reclamer_quete() refusent tant que
--  saison2_active() est faux, et quete_noter() ne compte rien. Les missions
--  de la saison 1 (objectifs, reclamer_objectif) ne sont pas touchées.
--  À lancer APRÈS s2-11-garnison-recharge.sql et mini-jeux-gains.sql.
--
--  Quotidiennes (jour de Paris) :
--   Terra (points)  : 2 paquets Terra 30 · 3 nouvelles communes 40 ·
--                     1 doublon vendu ou échangé 30            (100 / jour)
--   Front (énergie) : défense réussie +5 · garnison posée/rechargée +5 ·
--                     paquet Terra ouvert +5 · Commune du jour trouvée +5 ·
--                     duel Radar classé gagné +5 · conquête 50 pts + 3
--                     L'énergie des quêtes est plafonnée à 20 par jour ; elle
--                     peut faire dépasser le réservoir (40) jusqu'à 60.
--  Uniques (Terra, points) : 100 communes 200 · 500 communes 400 ·
--                     2 000 communes 600 · un département complet 300 ·
--                     une première épique 200.
--
--  Compteurs : table quetes_compteurs, alimentée par quete_noter(), appelée
--  depuis terra_ouvrir_paquet, terra_vendre, terra_vendre_doublons,
--  terra_acheter (vendeur), terra_accepter_echange (les deux), defendre,
--  attaquer (conquête), garnison_poser, radar_clore_si_fini (victoire classée).
--  Les « nouvelles communes » se lisent dans terra_collection.premiere_le, la
--  Commune du jour dans cdj_gains. Chaque fonction est modifiée à partir de sa
--  définition en production, seulement si le texte attendu y est exactement
--  une fois (sinon rien n'est modifié). Rejouable. Finit par un contrôle.
-- ===========================================================================

create table if not exists public.quetes_compteurs(
  joueur_id uuid not null references public.joueurs(id) on delete cascade,
  jour      date not null,
  cle       text not null,
  n         integer not null default 0,
  primary key (joueur_id, jour, cle)
);
create table if not exists public.quetes_reclamees(
  joueur_id uuid not null references public.joueurs(id) on delete cascade,
  quete     text not null,
  jour      date not null,             -- 2000-01-01 pour une quête unique
  points    integer not null default 0,
  energie   integer not null default 0,
  le        timestamptz not null default now(),
  primary key (joueur_id, quete, jour)
);
alter table public.quetes_compteurs enable row level security;
alter table public.quetes_reclamees enable row level security;
revoke all on public.quetes_compteurs, public.quetes_reclamees from public, anon, authenticated;

create or replace function public.quete_jour()
 returns date language sql stable set search_path to 'public'
as $f$ select (now() at time zone 'Europe/Paris')::date; $f$;

create or replace function public.quete_noter(p_uid uuid, p_cle text, p_n integer default 1)
 returns void language plpgsql security definer set search_path to 'public'
as $f$
begin
  if p_uid is null or not saison2_active() then return; end if;
  insert into quetes_compteurs(joueur_id, jour, cle, n) values (p_uid, quete_jour(), p_cle, coalesce(p_n, 1))
  on conflict (joueur_id, jour, cle) do update set n = quetes_compteurs.n + excluded.n;
end;
$f$;

-- la liste des quêtes d'un joueur, avec son avancement (interne)
create or replace function public.quetes_liste(p_uid uuid)
 returns table(id text, mode text, categorie text, titre text, detail text,
               avancement integer, cible integer, points integer, energie integer)
 language plpgsql stable security definer set search_path to 'public'
as $f$
declare
  v_jour date := quete_jour();
  v_minuit timestamptz := v_jour::timestamp at time zone 'Europe/Paris';
  c_paquet int; c_doublon int; c_defense int; c_garnison int; c_radar int; c_conquete int;
  v_nouvelles int; v_cdj int; v_communes int; v_epiques int; v_dept int;
begin
  select coalesce(sum(n) filter (where q.cle = 'terra_paquet'), 0),
         coalesce(sum(n) filter (where q.cle = 'doublon'), 0),
         coalesce(sum(n) filter (where q.cle = 'defense'), 0),
         coalesce(sum(n) filter (where q.cle = 'garnison'), 0),
         coalesce(sum(n) filter (where q.cle = 'radar_victoire'), 0),
         coalesce(sum(n) filter (where q.cle = 'conquete'), 0)
    into c_paquet, c_doublon, c_defense, c_garnison, c_radar, c_conquete
    from quetes_compteurs q where q.joueur_id = p_uid and q.jour = v_jour;
  select count(*) into v_nouvelles from terra_collection t
   where t.joueur_id = p_uid and t.premiere_le >= v_minuit and t.exemplaires > 0;
  select count(*) into v_cdj from cdj_gains g where g.joueur_id = p_uid and g.jour = v_jour;
  select count(*), count(*) filter (where c.tier = 'epique')
    into v_communes, v_epiques
    from terra_collection t join communes c on c.code = t.commune_code
   where t.joueur_id = p_uid and t.exemplaires > 0;
  -- un departement complet : toutes ses communes dans la collection
  select count(*) into v_dept from (
    select c.departement
      from communes c
      left join terra_collection t on t.commune_code = c.code and t.joueur_id = p_uid and t.exemplaires > 0
     group by c.departement
    having count(*) = count(t.commune_code)) x;

  return query select * from (values
    ('t_paquets',   'terra', 'jour',   'Ouvre 2 paquets Terra',          'Gratuits ou achetés',                    c_paquet,   2,    30, 0),
    ('t_nouvelles', 'terra', 'jour',   'Ajoute 3 nouvelles communes',    'Des communes que tu n''avais pas',       v_nouvelles, 3,   40, 0),
    ('t_doublon',   'terra', 'jour',   'Vends ou échange un doublon',    'Au jeu, à la Bourse ou en échange',      c_doublon,  1,    30, 0),
    ('f_defense',   'front', 'jour',   'Réussis une défense',            'Défends toi-même une commune attaquée',  c_defense,  1,    0, 5),
    ('f_garnison',  'front', 'jour',   'Mets une commune en garnison',   'Ou recharge une garnison',               c_garnison, 1,    0, 5),
    ('f_paquet',    'front', 'jour',   'Ouvre un paquet Terra',          'Le lien entre les deux modes',           c_paquet,   1,    0, 5),
    ('f_cdj',       'front', 'jour',   'Trouve la Commune du jour',      'Dans le QG',                             v_cdj,      1,    0, 5),
    ('f_radar',     'front', 'jour',   'Gagne un duel Radar',            'Duel classé, dans le QG',                c_radar,    1,    0, 5),
    ('f_conquete',  'front', 'jour',   'Conquiers une commune',          'Trois victoires d''affilée',             c_conquete, 1,    50, 3),
    ('u_t100',      'terra', 'unique', 'Collectionne 100 communes',      'Communes différentes',                   v_communes, 100,  200, 0),
    ('u_t500',      'terra', 'unique', 'Collectionne 500 communes',      'Communes différentes',                   v_communes, 500,  400, 0),
    ('u_t2000',     'terra', 'unique', 'Collectionne 2 000 communes',    'Communes différentes',                   v_communes, 2000, 600, 0),
    ('u_tdept',     'terra', 'unique', 'Complète un département',        'Toutes ses communes dans ta collection', v_dept,     1,    300, 0),
    ('u_tepique',   'terra', 'unique', 'Obtiens une épique',             'Dans un paquet ou par un contrat',       v_epiques,  1,    200, 0)
  ) as l(id, mode, categorie, titre, detail, avancement, cible, points, energie);
end;
$f$;

create or replace function public.quetes()
 returns table(id text, mode text, categorie text, titre text, detail text,
               avancement integer, cible integer, points integer, energie integer,
               reclamable boolean, reclame boolean, energie_jour integer)
 language plpgsql stable security definer set search_path to 'public'
as $f$
declare
  v_uid uuid := auth.uid();
  v_jour date := quete_jour();
  v_ej integer;
begin
  if v_uid is null then raise exception 'Non connecte'; end if;
  if not saison2_active() then raise exception 'Les quêtes arrivent avec la saison 2'; end if;
  select coalesce(sum(r.energie), 0)::integer into v_ej from quetes_reclamees r
   where r.joueur_id = v_uid and r.jour = v_jour;
  return query
  select l.id, l.mode, l.categorie, l.titre, l.detail,
         least(l.avancement, l.cible), l.cible, l.points, l.energie,
         (l.avancement >= l.cible and r.quete is null),
         (r.quete is not null),
         v_ej
    from quetes_liste(v_uid) l
    left join quetes_reclamees r on r.joueur_id = v_uid and r.quete = l.id
     and r.jour = case when l.categorie = 'jour' then v_jour else date '2000-01-01' end;
end;
$f$;

create or replace function public.reclamer_quete(p_id text)
 returns table(message text, points integer, energie integer)
 language plpgsql security definer set search_path to 'public'
as $f$
declare
  v_uid uuid := auth.uid();
  v_jour date := quete_jour();
  q record;
  v_deja integer;
  v_e integer := 0;
  v numeric;
begin
  if v_uid is null then raise exception 'Non connecte'; end if;
  if not saison2_active() then raise exception 'Les quêtes arrivent avec la saison 2'; end if;
  perform 1 from joueurs where id = v_uid for update;
  select * into q from quetes_liste(v_uid) l where l.id = p_id;
  if q.id is null then raise exception 'Quête inconnue'; end if;
  if q.avancement < q.cible then raise exception 'Quête pas encore terminée'; end if;
  if exists (select 1 from quetes_reclamees r where r.joueur_id = v_uid and r.quete = p_id
               and r.jour = case when q.categorie = 'jour' then v_jour else date '2000-01-01' end) then
    raise exception 'Récompense déjà récupérée';
  end if;

  if q.energie > 0 then
    select coalesce(sum(r.energie), 0) into v_deja from quetes_reclamees r
     where r.joueur_id = v_uid and r.jour = v_jour;
    v_e := least(q.energie, greatest(0, 20 - v_deja));
    if v_e > 0 then
      select front_energie_lire(j.front_energie, j.front_energie_maj) into v from joueurs j where j.id = v_uid;
      update joueurs set front_energie = least(60, v + v_e), front_energie_maj = now() where id = v_uid;
    end if;
  end if;
  if q.points > 0 then
    perform set_config('terrafront.motif', 'quete', true);
    update joueurs set solde = coalesce(solde, 0) + q.points where id = v_uid;
  end if;
  insert into quetes_reclamees(joueur_id, quete, jour, points, energie)
  values (v_uid, p_id, case when q.categorie = 'jour' then v_jour else date '2000-01-01' end, q.points, v_e);

  return query select
    (q.titre || ' : '
      || concat_ws(' et ',
           case when q.points > 0 then q.points || ' pts' end,
           case when v_e > 0 then '+' || v_e || ' énergie' end,
           case when q.energie > 0 and v_e = 0 then 'plus d''énergie de quête aujourd''hui (20 / 20)' end))::text,
    q.points, v_e;
end;
$f$;

revoke all on function public.quete_jour() from public, anon, authenticated;
revoke all on function public.quete_noter(uuid, text, integer) from public, anon, authenticated;
revoke all on function public.quetes_liste(uuid) from public, anon, authenticated;
revoke all on function public.quetes() from public, anon;
revoke all on function public.reclamer_quete(text) from public, anon;
grant execute on function public.quetes() to authenticated;
grant execute on function public.reclamer_quete(text) to authenticated;

-- Les compteurs, dans les fonctions du jeu ------------------------------------------------
do $g$
declare
  r record;
  v_def text;
  n integer;
begin
  for r in select * from (values
  ('public.terra_ouvrir_paquet(boolean)', 1,
   $a$  return query
  with tirage as ($a$,
   $a$  perform quete_noter(v_uid, 'terra_paquet', 1);
  return query
  with tirage as ($a$),
  ('public.terra_vendre(text,integer)', 1,
   $a$  perform set_config('terrafront.motif', 'terra_revente', true);$a$,
   $a$  perform set_config('terrafront.motif', 'terra_revente', true);
  perform quete_noter(v_uid, 'doublon', 1);$a$),
  ('public.terra_vendre_doublons(text[])', 1,
   $a$    perform set_config('terrafront.motif', 'terra_revente', true);$a$,
   $a$    perform set_config('terrafront.motif', 'terra_revente', true);
    perform quete_noter(v_uid, 'doublon', 1);$a$),
  ('public.terra_acheter(bigint)', 1,
   $a$  perform set_config('terrafront.motif', 'terra_bourse', true);$a$,
   $a$  perform set_config('terrafront.motif', 'terra_bourse', true);
  perform quete_noter(a.vendeur, 'doublon', 1);$a$),
  ('public.terra_accepter_echange(bigint)', 1,
   $a$  perform set_config('terrafront.motif', 'terra_echange', true);$a$,
   $a$  perform set_config('terrafront.motif', 'terra_echange', true);
  perform quete_noter(e.proposant, 'doublon', 1);
  perform quete_noter(v_uid, 'doublon', 1);$a$),
  ('public.defendre(text,uuid,text)', 1,
   $a$    perform ajouter_compteur(v_uid, 'defenses', 1);$a$,
   $a$    perform ajouter_compteur(v_uid, 'defenses', 1);
    perform quete_noter(v_uid, 'defense', 1);$a$),
  ('public.attaquer(text,text)', 1,
   $a$    delete from front_garnisons where commune_code = p_commune_code;$a$,
   $a$    delete from front_garnisons where commune_code = p_commune_code;
    perform quete_noter(v_attaquant_id, 'conquete', 1);$a$),
  ('public.garnison_poser(text,integer)', 1,
   $a$  on conflict (commune_code) do update set energie = g.energie + v_ajout;$a$,
   $a$  on conflict (commune_code) do update set energie = g.energie + v_ajout;
  perform quete_noter(v_uid, 'garnison', 1);$a$),
  ('public.radar_clore_si_fini(bigint)', 1,
   $a$  perform radar_gagner(s.id, 1 - v_score);$a$,
   $a$  perform radar_gagner(s.id, 1 - v_score);
  if v_score = 1 then perform quete_noter(p.joueur_id, 'radar_victoire', 1);
  elsif v_score = 0 then perform quete_noter(s.joueur_id, 'radar_victoire', 1); end if;$a$)
  ) t(fonction, etape, avant, apres)
  order by fonction, etape
  loop
    v_def := pg_get_functiondef(r.fonction::regprocedure);
    if position(r.apres in v_def) > 0 then
      raise notice '% : deja en place', r.fonction;
      continue;
    end if;
    n := (length(v_def) - length(replace(v_def, r.avant, ''))) / length(r.avant);
    if n <> 1 then
      raise exception '% : texte a remplacer present % fois au lieu de 1. Rien n''a ete modifie.', r.fonction, n;
    end if;
    execute replace(v_def, r.avant, r.apres);
  end loop;
end
$g$;

-- Contrôle ---------------------------------------------------------------------------------
select saison2_active() as saison2_active_doit_etre_false,
       (select count(*) from pg_proc p where p.proname in
          ('terra_ouvrir_paquet','terra_vendre','terra_vendre_doublons','terra_acheter','terra_accepter_echange',
           'defendre','attaquer','garnison_poser','radar_clore_si_fini')
          and pg_get_functiondef(p.oid) like '%quete_noter%') as fonctions_branchees_doit_etre_9,
       has_function_privilege('authenticated', 'public.quete_noter(uuid,text,integer)', 'execute') as noter_ouvert_doit_etre_false;
