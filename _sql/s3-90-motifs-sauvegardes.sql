-- s3-90 (27/11/2026) : sauvegardes de motifs, 6 places par joueur (idée d'Arkhannou).
-- Le motif sauvegardé passe par motif_net (mêmes filtres que motif_enregistrer). Le charger ne l'applique pas :
-- il revient dans l'éditeur, et « Enregistrer » repasse par motif_enregistrer.
create table if not exists public.motifs_sauvegardes(
  joueur_id uuid not null references public.joueurs(id) on delete cascade,
  place smallint not null check (place between 1 and 6),
  nom text not null check (char_length(nom) between 1 and 24),
  motif jsonb not null,
  le timestamptz not null default now(),
  primary key (joueur_id, place));
alter table public.motifs_sauvegardes enable row level security;   -- pas de règle : on passe par les fonctions

create or replace function public.motif_sauvegardes()
 returns jsonb language sql stable security definer set search_path to 'public'
as $f$
  select coalesce(jsonb_agg(jsonb_build_object('place', s.place, 'nom', s.nom, 'motif', s.motif) order by s.place), '[]'::jsonb)
    from motifs_sauvegardes s where s.joueur_id = auth.uid();
$f$;

create or replace function public.motif_sauver(p_place integer, p_nom text, p_motif jsonb)
 returns jsonb language plpgsql security definer set search_path to 'public'
as $f$
declare moi uuid := auth.uid(); net jsonb; v_nom text := left(btrim(regexp_replace(coalesce(p_nom, ''), '\s+', ' ', 'g')), 24);
begin
  if moi is null then raise exception 'Non connecte'; end if;
  if p_place is null or p_place < 1 or p_place > 6 then raise exception 'Place invalide'; end if;
  if v_nom = '' then v_nom := 'Motif ' || p_place; end if;
  if p_motif is null or octet_length(p_motif::text) > 20000 then raise exception 'Motif invalide'; end if;
  net := motif_net(p_motif, moi);
  if net is null or jsonb_array_length(coalesce(net->'calques', '[]'::jsonb)) = 0 then raise exception 'Ce motif est vide'; end if;
  insert into motifs_sauvegardes(joueur_id, place, nom, motif, le) values (moi, p_place, v_nom, net, now())
  on conflict (joueur_id, place) do update set nom = excluded.nom, motif = excluded.motif, le = now();
  return motif_sauvegardes();
end; $f$;

create or replace function public.motif_sauvegarde_retirer(p_place integer)
 returns jsonb language plpgsql security definer set search_path to 'public'
as $f$
begin
  if auth.uid() is null then raise exception 'Non connecte'; end if;
  delete from motifs_sauvegardes where joueur_id = auth.uid() and place = p_place;
  return motif_sauvegardes();
end; $f$;

revoke all on function public.motif_sauvegardes() from public, anon;
revoke all on function public.motif_sauver(integer, text, jsonb) from public, anon;
revoke all on function public.motif_sauvegarde_retirer(integer) from public, anon;
grant execute on function public.motif_sauvegardes() to authenticated;
grant execute on function public.motif_sauver(integer, text, jsonb) to authenticated;
grant execute on function public.motif_sauvegarde_retirer(integer) to authenticated;
-- retour arrière : drop function motif_sauvegardes(), motif_sauver(integer, text, jsonb), motif_sauvegarde_retirer(integer); drop table motifs_sauvegardes;
