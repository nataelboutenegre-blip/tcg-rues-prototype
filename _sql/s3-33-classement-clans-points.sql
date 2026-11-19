-- ===========================================================================
--  TerraFront — s3-33 : classement des clans aux POINTS (idée d'Oshannir, 19/11)
--  Le mode « 5 meilleurs membres actifs » (s3-28, éteint) additionne maintenant
--  les POINTS du classement du Front de ces 5 joueurs (cartes + combats +
--  territoires + bâtiments, barème de la population compris), et plus leurs
--  communes. Le mode « moyenne » (celui de la saison 2) ne change pas.
--  Rien ne bouge tant que config_jeu 'clans_s3'.classement_top5 vaut 0 :
--  il s'allume le 22, APRÈS la clôture (_jour-j/s3-jj-4d-classement-clans.sql).
--  Contrôle attendu : true
-- ===========================================================================
create or replace function public.clans_classement()
 returns table(clan_id uuid, nom text, tag text, couleur text, membres integer, communes integer, moyenne integer, actifs integer, mode text)
 language plpgsql
 stable security definer
 set search_path to 'public'
as $function$
declare v_depuis date := quete_jour() - 6; v_top5 boolean := coalesce(clan_cfg_n('classement_top5'), 0) >= 1;   -- s3-28
begin
  if auth.uid() is null then raise exception 'Non connecte'; end if;
  if not clans_ouverts() then raise exception 'Les clans ouvrent bientot'; end if;
  if v_top5 then
    -- s3-33 : les points du classement du Front, une seule lecture pour tous les clans
    return query
    with pts as materialized (
      select l.joueur_id, (coalesce(l.cartes, 0) + coalesce(l.combats, 0) + coalesce(l.territoires, 0) + coalesce(l.batiments, 0))::bigint as points
        from classement_lignes() l),
    mb as (
      select m.clan_id, m.joueur_id,
             (select count(*) from possessions p where p.joueur_id = m.joueur_id) as nb,
             exists (select 1 from jours_joues d where d.joueur_id = m.joueur_id and d.jour >= v_depuis) as actif,
             coalesce((select x.points from pts x where x.joueur_id = m.joueur_id), 0) as points
        from clan_membres m),
    rg as (
      select mb.*, row_number() over (partition by mb.clan_id order by mb.points desc) as r
        from mb where mb.actif)
    select c.id, c.nom, c.tag, c.couleur,
           (select count(*) from mb where mb.clan_id = c.id)::integer,
           (select coalesce(sum(mb.nb), 0) from mb where mb.clan_id = c.id)::integer,
           (select coalesce(sum(rg.points), 0) from rg where rg.clan_id = c.id and rg.r <= 5)::integer,
           (select count(*) from mb where mb.clan_id = c.id and mb.actif)::integer,
           'top5'::text
      from clans c
     where (select count(*) from mb where mb.clan_id = c.id) >= 3
     order by 7 desc, c.nom;
    return;
  end if;
  return query
  select c.id, c.nom, c.tag, c.couleur, x.n::integer, x.total::integer,
         case when x.actifs > 0 then round(x.total_actifs::numeric / x.actifs)::integer else 0 end,
         x.actifs::integer,
         'moyenne'::text
    from clans c
    join lateral (
      select count(*) n,
             count(*) filter (where a.actif) actifs,
             coalesce(sum(a.communes), 0) total,
             coalesce(sum(a.communes) filter (where a.actif), 0) total_actifs
        from clan_membres m
        cross join lateral (
          select (select count(*) from possessions p where p.joueur_id = m.joueur_id) communes,
                 exists (select 1 from jours_joues d where d.joueur_id = m.joueur_id and d.jour >= v_depuis) actif) a
       where m.clan_id = c.id) x on true
   where x.n >= 3
   order by 7 desc, c.nom;
end;
$function$;

select position('s3-33' in pg_get_functiondef('public.clans_classement()'::regprocedure)) > 0 as s3_33_installe;
