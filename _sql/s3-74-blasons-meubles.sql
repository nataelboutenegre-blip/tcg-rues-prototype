-- s3-74 (25/11/2026, Arkhannou) : 7 meubles de blason en plus.
-- Pour tous : chateau, trefle, cloche, epees. Rares, gagnés par l'or de l'objectif de clan de la semaine
-- (1re semaine d'or : rose, 2e : aigle2, 3e : couronne2), gardés pour toujours par le clan.
do $m$
declare d text; n text;
begin
  d := pg_get_functiondef('public.blason_propre(jsonb)'::regprocedure);
  n := replace(d, $a$'coeur','coquille','hermine','aigle','soleil','epis'])$a$,
                  $b$'coeur','coquille','hermine','aigle','soleil','epis',
                                        'chateau','trefle','cloche','epees','rose','aigle2','couronne2'])$b$);
  if n = d then raise exception 's3-74 : blason_propre introuvable'; end if;
  execute n;
end $m$;

-- semaines d'or ramassées par au moins un membre du clan
create or replace function public.clan_meubles_rares_n(p_clan uuid)
 returns integer language sql stable security definer set search_path to 'public'
as $f$ select count(distinct g.semaine)::integer from clan_objectif_gains g where g.clan_id = p_clan and g.palier = 3; $f$;

create or replace function public.clan_meubles_rares()
 returns integer language sql stable security definer set search_path to 'public'
as $f$ select coalesce(clan_meubles_rares_n(clan_de(auth.uid())), 0); $f$;
revoke all on function public.clan_meubles_rares_n(uuid) from anon, authenticated;
revoke all on function public.clan_meubles_rares() from anon;
grant execute on function public.clan_meubles_rares() to authenticated;

do $m$
declare d text; n text;
begin
  d := pg_get_functiondef('public.clan_modifier(text,text,text,jsonb)'::regprocedure);
  n := replace(d, $a$    if v_blason is null then raise exception 'Blason invalide'; end if;
  end if;$a$, $b$    if v_blason is null then raise exception 'Blason invalide'; end if;
    if array_position(array['rose','aigle2','couronne2'], v_blason->>'meuble') > clan_meubles_rares_n(v_clan.id)   -- s3-74
       and (v_blason->>'meuble') is distinct from (v_clan.blason->>'meuble') then
      raise exception 'Ce meuble se gagne avec l''or de l''objectif de clan de la semaine';
    end if;
  end if;$b$);
  if n = d then raise exception 's3-74 : clan_modifier introuvable'; end if;
  execute n;
end $m$;
