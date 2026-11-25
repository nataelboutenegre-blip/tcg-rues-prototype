-- s3-73 (25/11/2026, idée d'Arkhannou) : changer une quête du jour, 1 fois par jour en Terra et 1 en Front.
-- Pas les quêtes fixes (Commune du jour, Conquiers une commune, bonus) ni une quête finie ou récupérée.
-- La remplaçante est la suivante dans le même tirage du jour (même famille pour le Front).
create table if not exists public.quetes_relances (
  joueur_id uuid not null references public.joueurs(id) on delete cascade,
  jour date not null,
  mode text not null check (mode in ('terra', 'front')),
  quete text not null,
  le timestamptz not null default now(),
  primary key (joueur_id, jour, mode)
);
alter table public.quetes_relances enable row level security;
revoke all on public.quetes_relances from anon, authenticated;

do $m$
declare d text; n text;
begin
  d := pg_get_functiondef('public.quetes_liste(uuid)'::regprocedure);
  n := replace(d, $a$select r.* from reserve r order by md5(r.id || v_jour::text) limit n_terra),$a$,
    $b$select r.* from reserve r where r.id not in (select x.quete from quetes_relances x where x.joueur_id = p_uid and x.jour = v_jour)   -- s3-73
     order by md5(r.id || v_jour::text) limit n_terra),$b$);
  n := replace(n, $a$from front f where f.jouable and f.famille <> 'fixe'),$a$,
    $b$from front f where f.jouable and f.famille <> 'fixe'
       and f.id not in (select x.quete from quetes_relances x where x.joueur_id = p_uid and x.jour = v_jour)),   -- s3-73$b$);
  if (length(n) - length(replace(n, 's3-73', ''))) / 5 < 2 then raise exception 's3-73 : remplacements incomplets'; end if;
  execute n;
end $m$;

create or replace function public.quetes_relance_etat()
 returns jsonb language sql stable security definer set search_path to 'public'
as $f$
  select jsonb_build_object(
    'terra', not exists (select 1 from quetes_relances x where x.joueur_id = auth.uid() and x.jour = quete_jour() and x.mode = 'terra'),
    'front', not exists (select 1 from quetes_relances x where x.joueur_id = auth.uid() and x.jour = quete_jour() and x.mode = 'front'));
$f$;

create or replace function public.quete_relancer(p_quete text)
 returns jsonb language plpgsql security definer set search_path to 'public'
as $f$
declare v_uid uuid := auth.uid(); v_jour date := quete_jour(); q record;
begin
  if v_uid is null then raise exception 'Non connecte'; end if;
  if p_quete in ('f_cdj', 'f_conquete', 't_bonus', 'f_bonus') then raise exception 'Les quêtes fixes ne se changent pas'; end if;
  perform 1 from joueurs where id = v_uid for update;
  select * into q from quetes() x where x.id = p_quete;
  if q.id is null or q.categorie <> 'jour' then raise exception 'Cette quête ne se change pas'; end if;
  if q.reclame or q.avancement >= q.cible then raise exception 'Cette quête est déjà terminée'; end if;
  if exists (select 1 from quetes_relances x where x.joueur_id = v_uid and x.jour = v_jour and x.mode = q.mode) then
    raise exception 'Tu as déjà changé une quête % aujourd''hui : reviens demain', case when q.mode = 'terra' then 'Terra' else 'du Front' end;
  end if;
  insert into quetes_relances(joueur_id, jour, mode, quete) values (v_uid, v_jour, q.mode, p_quete);
  return quetes_relance_etat();
end; $f$;
revoke all on function public.quete_relancer(text) from anon;
revoke all on function public.quetes_relance_etat() from anon;
grant execute on function public.quete_relancer(text) to authenticated;
grant execute on function public.quetes_relance_etat() to authenticated;
