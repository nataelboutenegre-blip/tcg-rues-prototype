-- s3-41 : ce qui a été lu (cloche, alertes de bombe) est retenu sur le compte, et plus seulement
-- sur l'appareil (bug d'Oshannir : les mêmes alertes revenaient sur le téléphone après les avoir vues
-- sur le PC, surtout les bombes). Va avec patch482.
-- Une clé par chose lue (« nc:… » pour la cloche, « bo:… » pour les bombes), gardée 30 jours.
-- Retour arrière : drop function vus_marquer(text[]); drop function vus_lire(timestamptz); drop table joueur_vus;

create table if not exists public.joueur_vus (
  joueur_id uuid not null references public.joueurs(id) on delete cascade,
  cle       text not null check (length(cle) between 1 and 200),
  le        timestamptz not null default now(),
  primary key (joueur_id, cle)
);
create index if not exists joueur_vus_le on public.joueur_vus (joueur_id, le);
alter table public.joueur_vus enable row level security;   -- pas de politique : on passe par les fonctions

create or replace function public.vus_lire(p_depuis timestamptz default null)
returns table (cle text, le timestamptz)
language sql stable security definer set search_path to 'public' as $$
  select v.cle, v.le from joueur_vus v
   where v.joueur_id = auth.uid()
     and v.le > coalesce(p_depuis, now() - interval '30 days')
   order by v.le desc
   limit 3000;
$$;

create or replace function public.vus_marquer(p_cles text[])
returns integer
language plpgsql security definer set search_path to 'public' as $$
declare v_uid uuid := auth.uid(); v_n integer;
begin
  if v_uid is null then raise exception 'Non connecte'; end if;
  insert into joueur_vus (joueur_id, cle)
  select distinct v_uid, c from unnest((p_cles)[1:300]) c
   where c is not null and length(c) between 1 and 200
  on conflict (joueur_id, cle) do nothing;
  get diagnostics v_n = row_count;
  delete from joueur_vus where joueur_id = v_uid and le < now() - interval '30 days';
  return v_n;
end $$;

revoke all on function public.vus_lire(timestamptz) from public, anon;
revoke all on function public.vus_marquer(text[]) from public, anon;
grant execute on function public.vus_lire(timestamptz) to authenticated;
grant execute on function public.vus_marquer(text[]) to authenticated;

-- contrôle : true · true · true
select to_regclass('public.joueur_vus') is not null as table_ok,
       to_regprocedure('public.vus_lire(timestamptz)') is not null as lire_ok,
       to_regprocedure('public.vus_marquer(text[])') is not null as marquer_ok;
