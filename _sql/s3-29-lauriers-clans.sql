-- s3-29 : les lauriers du podium des clans (décision de Nataël, 18/11/2026, 19 h 20)
--   La clôture du 22/11 enregistre aussi le 2e et le 3e clan (rangs 2 et 3 dans clan_trophees, en plus du champion).
--   Laurier or / argent / bronze autour du blason, affiché par défaut ; le chef ou un bras droit (droit « modifier »)
--   peut le retirer. À lancer AVANT la clôture du 22.

begin;

create or replace function pg_temp.retoucher(p_sig text, p_marque text, p_ancien text, p_nouveau text)
returns void language plpgsql as $f$
declare d text; n integer;
begin
  d := pg_get_functiondef(p_sig::regprocedure);
  if position(p_marque in d) > 0 then return; end if;
  n := (length(d) - length(replace(d, p_ancien, ''))) / length(p_ancien);
  if n <> 1 then raise exception 's3-29 : % a changé (« % » trouvé % fois)', p_sig, left(p_ancien, 70), n; end if;
  if position(p_marque in p_nouveau) = 0 then raise exception 's3-29 : marque % absente du nouveau texte', p_marque; end if;
  execute replace(d, p_ancien, p_nouveau);
end $f$;

-- le podium des clans, même calcul que le champion (moyenne par membre actif, 3 membres au moins)
create or replace function public.clans_podium_s2()
returns table(clan_id uuid, rang integer, nom text, tag text, moyenne integer)
language sql stable security definer set search_path to 'public' as $$
  select x.id, (row_number() over (order by x.moyenne desc, x.nom))::integer, x.nom::text, x.tag::text, x.moyenne
    from (
      select c.id, c.nom, c.tag,
             case when count(*) filter (where a.actif) > 0
                  then round(coalesce(sum(a.communes) filter (where a.actif), 0)::numeric / count(*) filter (where a.actif))::integer
                  else 0 end as moyenne,
             count(*) as n
        from clans c
        join clan_membres m on m.clan_id = c.id
        cross join lateral (
          select (select count(*) from possessions p where p.joueur_id = m.joueur_id) communes,
                 exists (select 1 from jours_joues d where d.joueur_id = m.joueur_id and d.jour >= quete_jour() - 6) actif) a
       group by c.id, c.nom, c.tag) x
   where x.n >= 3
   order by x.moyenne desc, x.nom
   limit 3;
$$;
revoke all on function public.clans_podium_s2() from public, anon, authenticated;

select pg_temp.retoucher('public.recompenses_s2_attribuer(boolean)', 's3-29a',
  $a$    get diagnostics v_trophee = row_count;$a$,
  $b$    get diagnostics v_trophee = row_count;
    with ins as (   -- s3-29a : le 2e et le 3e clan (lauriers d'argent et de bronze)
      insert into clan_trophees(clan_id, saison, rang, nom, tag, moyenne)
      select p.clan_id, 'saison-2', p.rang, p.nom, p.tag, p.moyenne from clans_podium_s2() p where p.rang in (2, 3)
      on conflict do nothing
      returning 1)
    select v_trophee + count(*) into v_trophee from ins;$b$);
select pg_temp.retoucher('public.recompenses_s2_attribuer(boolean)', 's3-29b',
  $a$  return query select 'pionnier'::text,$a$,
  $b$  return query select 'clan-podium (lauriers)'::text,   -- s3-29b
    coalesce((select string_agg(p.rang || '. ' || p.tag || ' (' || p.moyenne || ')', ', ' order by p.rang) from clans_podium_s2() p), 'aucun');
  return query select 'pionnier'::text,$b$);

-- le laurier se retire (et se remet)
alter table public.clans add column if not exists laurier_masque boolean not null default false;

drop function if exists public.clans_blasons();
create function public.clans_blasons()
 returns table(tag text, blason jsonb, nom_libre_le timestamp with time zone, laurier_rang integer, laurier_saison text, laurier_masque boolean)
 language sql stable security definer set search_path to 'public'
as $$
  select c.tag::text, c.blason, c.nom_change_le + interval '7 days', t.rang, t.saison, c.laurier_masque   -- s3-29
    from clans c
    left join lateral (select x.rang, x.saison from clan_trophees x where x.clan_id = c.id and x.rang between 1 and 3
                        order by x.saison desc, x.rang limit 1) t on true
   where auth.uid() is not null and (c.blason is not null or c.nom_change_le is not null or t.rang is not null);
$$;
revoke all on function public.clans_blasons() from public, anon;
grant execute on function public.clans_blasons() to authenticated;

create or replace function public.clan_laurier_afficher(p_afficher boolean)
returns jsonb language plpgsql security definer set search_path to 'public' as $$
declare v_uid uuid := auth.uid(); v_clan uuid;
begin
  if v_uid is null then raise exception 'Non connecte'; end if;
  select id into v_clan from clans where chef = v_uid;
  if v_clan is null then
    select m.clan_id into v_clan from clan_membres m where m.joueur_id = v_uid and m.bras_droit and m.peut_modifier;
  end if;
  if v_clan is null then raise exception 'Seul le chef peut modifier le clan'; end if;
  if not exists (select 1 from clan_trophees t where t.clan_id = v_clan and t.rang between 1 and 3) then
    raise exception 'Ton clan n''a pas encore de laurier';
  end if;
  update clans set laurier_masque = not coalesce(p_afficher, true) where id = v_clan;
  return jsonb_build_object('laurier_masque', not coalesce(p_afficher, true));
end;
$$;
revoke all on function public.clan_laurier_afficher(boolean) from public, anon;
grant execute on function public.clan_laurier_afficher(boolean) to authenticated;

commit;

-- Contrôle : 2 retouches, et le podium d'aujourd'hui
select (select count(*) from unnest(array[
          position('s3-29a' in pg_get_functiondef('public.recompenses_s2_attribuer(boolean)'::regprocedure)),
          position('s3-29b' in pg_get_functiondef('public.recompenses_s2_attribuer(boolean)'::regprocedure))]) x where x > 0) as retouches,
       (select string_agg(p.rang || '. ' || p.tag || ' (' || p.moyenne || ')', ', ' order by p.rang) from clans_podium_s2() p) as podium;
