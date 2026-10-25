-- ===========================================================================
--  TerraFront — « Plus ou moins », le jeu du jour (25 octobre 2026)
--  Aperçu jouable validé (« parfait », avec les photos).
--
--  Chaque jour (jour de Paris) : 10 duels, les mêmes pour tous, du plus
--  facile (une commune 5 fois plus peuplée que l'autre) au plus serré
--  (3 % d'écart). « Laquelle a le plus d'habitants ? »
--  Une erreur n'arrête pas la partie : note sur 10.
--  5 points Terra par bonne réponse (50 par jour au plus), étiquetés 'pom'.
--  Quêtes : « Joue à Plus ou moins » entre dans la réserve Terra à partir
--  du 26 octobre (les quêtes d'aujourd'hui ne bougent pas) et dans les
--  quêtes Front dès aujourd'hui (+5 énergie, plafond inchangé).
--
--  Le serveur choisit les duels et vérifie chaque réponse ; la population
--  d'un duel n'est envoyée qu'une fois qu'on y a répondu.
--  Rejouable. Tout dans une transaction. Finit par un contrôle (une ligne) :
--  attendu true / true / true / 10 / true.
-- ===========================================================================
begin;

create table if not exists public.pom_jours(
  jour    date primary key,
  numero  integer not null,
  duels   jsonb not null            -- [{"a": code, "b": code}, ...] dans l'ordre d'affichage
);
create table if not exists public.pom_parties(
  joueur_id uuid not null references public.joueurs(id) on delete cascade,
  jour      date not null,
  reponses  smallint[] not null default '{}',   -- 0 = gauche, 1 = droite
  justes    integer not null default 0,
  gain      integer not null default 0,
  fini      boolean not null default false,
  le        timestamptz not null default now(),
  primary key (joueur_id, jour)
);
alter table public.pom_jours   enable row level security;
alter table public.pom_parties enable row level security;
revoke all on public.pom_jours, public.pom_parties from public, anon, authenticated;

-- les 10 duels d'un jour ---------------------------------------------------
create or replace function public.pom_generer()
 returns jsonb language plpgsql volatile security definer set search_path to 'public'
as $f$
declare
  ratios    numeric[] := array[5, 3, 2.3, 1.9, 1.6, 1.4, 1.25, 1.15, 1.08, 1.03];
  planchers integer[] := array[5000, 4000, 3000, 2000, 1500, 1000, 800, 500, 400, 300];
  res jsonb := '[]'::jsonb;
  deja text[] := '{}';
  a record; b record; r numeric; k int; essai int;
begin
  for k in 1..10 loop
    r := ratios[k];
    for essai in 1..40 loop
      select c.code, c.population, c.departement into a from communes c
       where c.photo is not null and c.population >= planchers[k] and c.code <> all (deja)
       order by random() limit 1;
      select c.code into b from communes c
       where c.photo is not null and c.code <> all (deja) and c.code <> a.code
         and c.departement <> a.departement
         and c.population < a.population
         and c.population > a.population / (r * 1.03)
         and c.population < a.population / (r * 0.97)
       order by random() limit 1;
      exit when b.code is not null;
    end loop;
    if b.code is null then   -- filet : n'importe quelle commune plus petite
      select c.code into b from communes c
       where c.photo is not null and c.code <> all (deja) and c.code <> a.code and c.population < a.population
       order by random() limit 1;
    end if;
    deja := deja || a.code::text || b.code::text;
    -- la plus peuplée n'est pas toujours à gauche
    res := res || case when random() < 0.5 then jsonb_build_array(jsonb_build_object('a', a.code, 'b', b.code))
                                           else jsonb_build_array(jsonb_build_object('a', b.code, 'b', a.code)) end;
  end loop;
  return res;
end; $f$;

create or replace function public.pom_assurer(p_jour date)
 returns void language plpgsql volatile security definer set search_path to 'public'
as $f$
begin
  if exists (select 1 from pom_jours where jour = p_jour) then return; end if;
  perform pg_advisory_xact_lock(hashtext('pom_jours'));
  if exists (select 1 from pom_jours where jour = p_jour) then return; end if;
  insert into pom_jours(jour, numero, duels)
  values (p_jour, (select coalesce(max(numero), 0) + 1 from pom_jours), pom_generer());
end; $f$;

-- une commune, sa population seulement si le duel est joué
create or replace function public.pom_carte(p_code text, p_reveler boolean)
 returns jsonb language sql stable security definer set search_path to 'public'
as $f$
  select jsonb_build_object('code', c.code, 'nom', c.nom, 'departement', c.departement,
           'photo', c.photo, 'auteur', c.photo_auteur, 'licence', c.photo_licence, 'source', c.photo_source,
           'population', case when p_reveler then c.population end)
    from communes c where c.code = p_code
$f$;

create or replace function public.pom_partie()
 returns jsonb language plpgsql volatile security definer set search_path to 'public'
as $f$
declare
  v_uid uuid := auth.uid();
  v_jour date := quete_jour();
  d pom_jours%rowtype;
  p pom_parties%rowtype;
  n int;
begin
  if v_uid is null then raise exception 'Non connecte'; end if;
  perform pom_assurer(v_jour);
  select * into d from pom_jours where jour = v_jour;
  select * into p from pom_parties where joueur_id = v_uid and jour = v_jour;
  n := coalesce(array_length(p.reponses, 1), 0);
  return jsonb_build_object(
    'numero', d.numero, 'jour', v_jour,
    'reponses', coalesce(to_jsonb(p.reponses), '[]'::jsonb),
    'justes', coalesce(p.justes, 0), 'gain', coalesce(p.gain, 0), 'fini', coalesce(p.fini, false),
    'duels', (select jsonb_agg(jsonb_build_object('i', e.i - 1,
                       'a', pom_carte(e.x ->> 'a', e.i - 1 < n),
                       'b', pom_carte(e.x ->> 'b', e.i - 1 < n)) order by e.i)
                from jsonb_array_elements(d.duels) with ordinality e(x, i)));
end; $f$;

create or replace function public.pom_repondre(p_i integer, p_choix integer)
 returns jsonb language plpgsql volatile security definer set search_path to 'public'
as $f$
declare
  v_uid uuid := auth.uid();
  v_jour date := quete_jour();
  d pom_jours%rowtype;
  p pom_parties%rowtype;
  n int; pa int; pb int; v_juste boolean;
begin
  if v_uid is null then raise exception 'Non connecte'; end if;
  if p_choix is null or p_choix not in (0, 1) then raise exception 'Choix inconnu'; end if;
  perform pom_assurer(v_jour);
  select * into d from pom_jours where jour = v_jour;
  insert into pom_parties(joueur_id, jour) values (v_uid, v_jour) on conflict do nothing;
  select * into p from pom_parties where joueur_id = v_uid and jour = v_jour for update;
  if p.fini then raise exception 'Tu as déjà joué aujourd''hui : reviens demain'; end if;
  n := coalesce(array_length(p.reponses, 1), 0);
  if p_i is distinct from n then raise exception 'Ce duel est déjà joué'; end if;
  select population into pa from communes where code = d.duels -> n ->> 'a';
  select population into pb from communes where code = d.duels -> n ->> 'b';
  v_juste := (p_choix = 0 and pa > pb) or (p_choix = 1 and pb > pa);
  update pom_parties set reponses = reponses || p_choix::smallint,
                         justes = justes + case when v_juste then 1 else 0 end,
                         gain = gain + case when v_juste then 5 else 0 end,
                         fini = (n + 1 >= jsonb_array_length(d.duels)),
                         le = now()
   where joueur_id = v_uid and jour = v_jour
   returning * into p;
  if v_juste then
    perform set_config('terrafront.motif', 'pom', true);
    update joueurs set solde = coalesce(solde, 0) + 5 where id = v_uid;
  end if;
  return jsonb_build_object('juste', v_juste, 'pop_a', pa, 'pop_b', pb,
                            'fini', p.fini, 'justes', p.justes, 'gain', p.gain);
end; $f$;

revoke all on function public.pom_generer()                 from public, anon, authenticated;
revoke all on function public.pom_assurer(date)             from public, anon, authenticated;
revoke all on function public.pom_carte(text, boolean)      from public, anon, authenticated;
revoke all on function public.pom_partie()                  from public, anon;
revoke all on function public.pom_repondre(integer, integer) from public, anon;
grant execute on function public.pom_partie()                  to authenticated;
grant execute on function public.pom_repondre(integer, integer) to authenticated;

-- les quêtes : modifiées à partir de leur définition en base ----------------
do $$
declare
  d text := pg_get_functiondef('public.quetes_liste(uuid)'::regprocedure);
  r record;
begin
  if position('t_pom' in d) > 0 then raise notice 'quetes_liste : déjà fait'; return; end if;
  for r in select * from (values
    ($a$v_radar int; v_rafale int;$a$,
     $a$v_radar int; v_rafale int; v_pom int;$a$),
    ($a$  select count(*) into v_cdj from cdj_gains g where g.joueur_id = p_uid and g.jour = v_jour;$a$,
     $a$  select count(*) into v_cdj from cdj_gains g where g.joueur_id = p_uid and g.jour = v_jour;
  select count(*) into v_pom from pom_parties pp where pp.joueur_id = p_uid and pp.jour = v_jour and pp.fini;$a$),
    ($a$c_radar_v + c_rafale_v, 1)),$a$,
     $a$c_radar_v + c_rafale_v, 1),
    ('t_pom',       'Joue à Plus ou moins',             'Les 10 duels, dans le QG',             v_pom,                 1)),$a$),
    ($a$select r.* from reserve r order by md5(r.id || v_jour::text) limit 5)$a$,
     $a$select r.* from reserve r where r.id <> 't_pom' or v_jour >= date '2026-10-26' order by md5(r.id || v_jour::text) limit 5)$a$),
    ($a$v_cdj,      1,    0, 5),$a$,
     $a$v_cdj,      1,    0, 5),
    ('f_pom',       'front', 'jour',   'Joue à Plus ou moins',           'Les 10 duels, dans le QG',               v_pom,      1,    0, 5),$a$)
  ) as t(avant, apres) loop
    if (length(d) - length(replace(d, r.avant, ''))) / length(r.avant) <> 1 then
      raise exception 'quetes_liste : texte attendu introuvable (ou en double) : %', left(r.avant, 60);
    end if;
    d := replace(d, r.avant, r.apres);
  end loop;
  execute d;
  raise notice 'quetes_liste : Plus ou moins ajouté';
end $$;

commit;

select to_regclass('public.pom_jours') is not null                       as tables_ok,
       to_regprocedure('public.pom_partie()') is not null                 as partie_ok,
       to_regprocedure('public.pom_repondre(integer, integer)') is not null as repondre_ok,
       jsonb_array_length(public.pom_generer())                            as duels_essai,
       position('f_pom' in pg_get_functiondef('public.quetes_liste(uuid)'::regprocedure)) > 0 as quetes_ok;
