-- ===========================================================================
--  TerraFront — s2-86 : « Premiers pas » mène au Front + mesure de l'accueil
--  (3/11/2026, avec patch324). Décidé avec Nataël le 3/11 (aperçu validé).
--
--  Pourquoi : sur les 70 nouveaux du 2/11, 15 n'ont jamais eu de commune au
--  Front (10 n'ont joué qu'en Terra, 5 n'ont rien ouvert). Or ceux qui
--  combattent et conquièrent le 1er jour reviennent nettement plus.
--
--  1. premiers_pas() : l'étape « paquet » ne se coche plus avec une carte
--     Terra, seulement avec une trace au Front (une commune aujourd'hui, une
--     commune prise par un autre, ou une commune libérée).
--  2. Une seule fois : l'étape « paquet » est décochée pour les comptes qui
--     n'ont pas encore récupéré la récompense et n'ont aucune trace au Front.
--  3. accueil_etapes + accueil_etape(etape, detail) : le jeu note la première
--     fois qu'un nouveau (compte de moins de 14 jours) passe chaque étape de
--     l'accueil (accueil vu, guide fini ou passé, premier paquet par mode…).
--     Une ligne par joueur et par étape, au plus 60 étapes par joueur.
--     Lecture : _sql/lecture-entonnoir-accueil.sql.
--
--  Rejouable. Finit par un contrôle (une ligne) :
--  true | true | true | true | (comptes dont l'étape 1 est à refaire)
-- ===========================================================================
begin;

-- ---------- 3. la mesure de l'accueil ----------
create table if not exists public.accueil_etapes(
  joueur_id uuid not null references public.joueurs(id) on delete cascade,
  etape     text not null,
  detail    text,
  le        timestamptz not null default now(),
  primary key (joueur_id, etape)
);
alter table public.accueil_etapes enable row level security;
revoke all on public.accueil_etapes from public, anon, authenticated;

create or replace function public.accueil_etape(p_etape text, p_detail text default null)
 returns void language plpgsql security definer set search_path to 'public' as $f$
declare
  v_uid uuid := auth.uid();
begin
  if v_uid is null or p_etape is null or p_etape !~ '^[a-z0-9_]{1,30}$' then return; end if;
  -- seulement les nouveaux comptes
  if not exists (select 1 from auth.users u where u.id = v_uid and u.created_at >= now() - interval '14 days') then return; end if;
  if not exists (select 1 from joueurs j where j.id = v_uid) then return; end if;
  if (select count(*) from accueil_etapes a where a.joueur_id = v_uid) >= 60 then return; end if;
  insert into accueil_etapes(joueur_id, etape, detail)
  values (v_uid, p_etape, left(nullif(p_detail, ''), 60))
  on conflict do nothing;
end; $f$;
revoke all on function public.accueil_etape(text, text) from public, anon;
grant execute on function public.accueil_etape(text, text) to authenticated;

-- ---------- 1. premiers_pas() : l'étape 1 se coche au Front seulement ----------
do $do$
declare
  d text;
  avant text := 'or exists (select 1 from terra_collection t where t.joueur_id = v_uid and t.exemplaires > 0)';
  apres text := 'or exists (select 1 from front_prises fp where fp.victime = v_uid)   -- s2-86 : au Front seulement
               or exists (select 1 from front_liberations fl where fl.joueur_id = v_uid)';
  n int;
begin
  d := pg_get_functiondef('public.premiers_pas()'::regprocedure);
  if position('s2-86' in d) > 0 then
    raise notice 's2-86 : premiers_pas() déjà modifiée';
  else
    n := (length(d) - length(replace(d, avant, ''))) / length(avant);
    if n <> 1 then raise exception 's2-86 : repère trouvé % fois dans premiers_pas() (1 attendu), rien n''est changé', n; end if;
    execute replace(d, avant, apres);
  end if;
end $do$;

-- ---------- 2. une fois : l'étape 1 à refaire pour ceux qui n'ont rien au Front ----------
update public.premiers_pas p
   set paquet = false, maj = now()
 where p.paquet
   and p.reclame_le is null
   and not exists (select 1 from public.possessions x       where x.joueur_id = p.joueur_id)
   and not exists (select 1 from public.front_prises fp     where fp.victime   = p.joueur_id)
   and not exists (select 1 from public.front_liberations fl where fl.joueur_id = p.joueur_id);

commit;

-- Contrôle : true | true | true | true | (comptes dont l'étape 1 est à refaire)
select to_regclass('public.accueil_etapes') is not null                                                as table_ok,
       has_function_privilege('authenticated', 'public.accueil_etape(text, text)', 'execute')          as mesure_ok,
       position('s2-86' in pg_get_functiondef('public.premiers_pas()'::regprocedure)) > 0              as premiers_pas_front,
       position('terra_collection' in pg_get_functiondef('public.premiers_pas()'::regprocedure)) = 0   as plus_de_terra,
       (select count(*) from public.premiers_pas where not paquet and reclame_le is null)               as etape_1_a_faire;
