-- s3-75 (25/11/2026) : un clan qui change de sigle gardait son nom sur Discord sous l'ancien rôle et l'ancien
-- salon ; le bot en créait de nouveaux (Comtois rend toi ! [FC] → Les Troubadours du Chaos [TDC]).
-- On garde les anciens sigles, et discord_clans_donnees les envoie au bot.
create table if not exists public.clans_tags_anciens (
  clan_id uuid not null references public.clans(id) on delete cascade,
  tag text not null,
  jusqua timestamptz not null default now(),
  primary key (clan_id, tag)
);
alter table public.clans_tags_anciens enable row level security;
revoke all on public.clans_tags_anciens from anon, authenticated;

create or replace function public.clans_tag_change() returns trigger language plpgsql security definer set search_path to 'public'
as $f$ begin
  if new.tag is distinct from old.tag then
    insert into clans_tags_anciens(clan_id, tag) values (old.id, old.tag) on conflict (clan_id, tag) do update set jusqua = now();
  end if;
  return new;
end; $f$;
drop trigger if exists trg_clans_tag_change on public.clans;
create trigger trg_clans_tag_change after update of tag on public.clans for each row execute function public.clans_tag_change();

-- le cas d'aujourd'hui
insert into clans_tags_anciens(clan_id, tag) select id, 'FC' from clans where tag = 'TDC' on conflict do nothing;

do $m$
declare d text; n text;
begin
  d := pg_get_functiondef('public.discord_clans_donnees()'::regprocedure);
  n := replace(d, $a$        'tag', c.tag, 'nom', c.nom, 'couleur', c.couleur,$a$,
    $b$        'tag', c.tag, 'nom', c.nom, 'couleur', c.couleur,
        'anciens', coalesce((select jsonb_agg(t.tag order by t.jusqua desc) from clans_tags_anciens t where t.clan_id = c.id), '[]'::jsonb),   -- s3-75$b$);
  if n = d then raise exception 's3-75 : discord_clans_donnees introuvable'; end if;
  execute n;
end $m$;
