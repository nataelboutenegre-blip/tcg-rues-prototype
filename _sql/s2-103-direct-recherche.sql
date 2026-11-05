-- ===========================================================================
--  TerraFront — s2-103 : la commune demandée en live (5/11/2026)
--  Aperçu validé par Nataël le 5/11 (apercu-recherche.png) : pendant un live
--  TikTok, un spectateur écrit sa commune dans le chat ; Nataël la cherche dans
--  la régie (terrafront.fr/direct/regie.html, sur son téléphone) et la scène
--  (direct/tiktok.html) zoome dessus 15 s avec une fiche « tenue par… / libre ».
--
--  - direct_affichage : une seule ligne, ce qui est à l'écran (RLS sans règle :
--    on n'y touche que par les deux fonctions ci-dessous).
--  - direct_montrer(code, demandeur, duree, ajouter) : réservé à la modération
--    (discussion_est_moderateur, s2-99) ; code null = retour à la France.
--  - direct_regie_ok() : la régie demande si le compte connecté y a droit.
--  - direct_affiche() : lu par la scène toutes les 2 s (anon) ; rend le n° de la
--    demande, la commune, le pseudo du demandeur et les secondes restantes
--    (calculées par la base : l'horloge de l'ordinateur du live ne compte pas).
--  Prérequis : s2-90 (direct_ouvert), s2-99 (discussion_est_moderateur).
--  Rejouable. Contrôle (une ligne) : true | false | true | 0 ou plus
-- ===========================================================================
do $$ begin
  if to_regprocedure('public.direct_ouvert()') is null or to_regprocedure('public.discussion_est_moderateur(uuid)') is null then
    raise exception 'Lance d''abord s2-90-carte-en-direct.sql et s2-99-discussion.sql';
  end if;
end $$;

begin;

create table if not exists public.direct_affichage (
  id smallint primary key default 1 check (id = 1),
  n bigint not null default 0,
  code text,
  demandeur text,
  fin timestamptz not null default now()
);
alter table public.direct_affichage enable row level security;
revoke all on table public.direct_affichage from public, anon, authenticated;
insert into public.direct_affichage (id) values (1) on conflict (id) do nothing;

create or replace function public.direct_montrer(p_code text, p_demandeur text default null, p_duree int default 15, p_ajouter boolean default false)
 returns json language plpgsql security definer set search_path to 'public' as $f$
declare v_code text := nullif(trim(coalesce(p_code, '')), '');
        v_dem text := nullif(left(regexp_replace(trim(coalesce(p_demandeur, '')), '[[:cntrl:]<>]', '', 'g'), 30), '');
        v_duree int := least(120, greatest(5, coalesce(p_duree, 15)));
        r direct_affichage;
begin
  if not discussion_est_moderateur(auth.uid()) then raise exception 'Réservé à la régie du direct'; end if;
  if v_code is not null and v_code !~ '^[0-9][0-9AB][0-9]{3}$' then raise exception 'Code de commune inconnu'; end if;
  if v_code is null then
    update direct_affichage set n = n + 1, code = null, demandeur = null, fin = now() where id = 1 returning * into r;
  elsif coalesce(p_ajouter, false) and exists (select 1 from direct_affichage a where a.id = 1 and a.code = v_code and a.fin > now()) then
    -- bouton « +15 s » : la même commune reste plus longtemps (2 min au plus devant soi)
    update direct_affichage set fin = least(now() + interval '120 seconds', fin + make_interval(secs => v_duree)) where id = 1 returning * into r;
  else
    update direct_affichage set n = n + 1, code = v_code, demandeur = v_dem, fin = now() + make_interval(secs => v_duree) where id = 1 returning * into r;
  end if;
  return json_build_object('n', r.n, 'code', r.code, 'demandeur', r.demandeur,
                           'reste', greatest(0, ceil(extract(epoch from r.fin - now())))::int);
end $f$;

create or replace function public.direct_regie_ok()
 returns boolean language sql stable security definer set search_path to 'public' as $f$
  select auth.uid() is not null and discussion_est_moderateur(auth.uid());
$f$;

create or replace function public.direct_affiche()
 returns json language sql stable security definer set search_path to 'public' as $f$
  select json_build_object('n', a.n,
           'code', case when a.fin > now() then a.code end,
           'demandeur', case when a.fin > now() then a.demandeur end,
           'reste', greatest(0, ceil(extract(epoch from a.fin - now())))::int)
    from direct_affichage a where a.id = 1 and direct_ouvert();
$f$;

revoke all on function public.direct_montrer(text, text, int, boolean), public.direct_affiche(), public.direct_regie_ok() from public, anon, authenticated;
grant execute on function public.direct_affiche() to anon, authenticated;
grant execute on function public.direct_montrer(text, text, int, boolean), public.direct_regie_ok() to authenticated;

commit;

-- Contrôle : true | false | true | 0 ou plus
select has_function_privilege('anon', 'public.direct_affiche()', 'execute')                       as affiche_ok,
       has_function_privilege('anon', 'public.direct_montrer(text, text, integer, boolean)', 'execute')    as montrer_anon,
       has_function_privilege('authenticated', 'public.direct_montrer(text, text, integer, boolean)', 'execute') as montrer_connecte,
       (public.direct_affiche() ->> 'n')::bigint                                                  as n;
