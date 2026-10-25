-- ===========================================================================
--  s2-26-clans-activite.sql — l'activité du jour dans l'onglet Clan, et un
--  classement qui ne compte que les membres actifs (idées de Maroli, 25 oct.).
--  Rejouable.
--
--  1. front_energie_depenser note désormais l'énergie dépensée (compteur
--     « energie » des quêtes). Elle ne se compte qu'à partir de maintenant :
--     le 25 octobre, le chiffre du jour est donc incomplet.
--  2. clan_activite() : pour MON clan seulement, ce que chaque membre a fait
--     depuis minuit (heure de Paris) : cartes obtenues (tirages, contrats),
--     communes conquises, défenses, énergie dépensée, et son dernier jour joué.
--  3. clans_classement() : la moyenne ne compte plus que les membres ACTIFS
--     (le jeu ouvert dans les 7 derniers jours). Un inactif ne tire plus le
--     clan vers le bas. Il faut toujours 3 membres pour être classé.
--  Contrôle attendu : true | true | true | false
-- ===========================================================================

begin;

-- 1. l'énergie dépensée -------------------------------------------------------
do $d$
declare
  v_def text := pg_get_functiondef('public.front_energie_depenser(uuid, integer)'::regprocedure);
  v_avant text := 'update joueurs set front_energie = v - p_n, front_energie_maj = now() where id = p_uid;';
  v_apres text := v_avant || E'\n  perform quete_noter(p_uid, ''energie'', p_n);   -- s2-26 : l''activité du clan';
begin
  if position('s2-26' in v_def) > 0 then
    raise notice 'front_energie_depenser : déjà fait';
  elsif (length(v_def) - length(replace(v_def, v_avant, ''))) / length(v_avant) <> 1 then
    raise exception 'front_energie_depenser ne ressemble pas à ce qui est attendu : rien n''est changé';
  else
    execute replace(v_def, v_avant, v_apres);
  end if;
end $d$;

-- 2. l'activité du jour de mon clan ---------------------------------------------
create or replace function public.clan_activite()
 returns table(joueur_id uuid, pseudo text, cartes integer, conquetes integer, defenses integer,
               energie integer, dernier_jour date)
 language plpgsql
 stable security definer
 set search_path to 'public'
as $f$
declare
  v_uid uuid := auth.uid();
  v_clan uuid;
  v_jour date := quete_jour();
  v_minuit timestamptz := quete_jour()::timestamp at time zone 'Europe/Paris';
begin
  if v_uid is null then raise exception 'Non connecte'; end if;
  select m.clan_id into v_clan from clan_membres m where m.joueur_id = v_uid;
  if v_clan is null then return; end if;
  return query
  select j.id, j.pseudo::text,
         -- les communes arrivées aujourd'hui, sauf celles prises à un joueur
         (select count(*) from historique h
           where h.joueur_id = j.id and h.acquired_at >= v_minuit
             and not exists (select 1 from front_prises f
                              where f.attaquant = j.id and f.commune_code = h.commune_code and f.le >= v_minuit))::integer,
         (select count(*) from front_prises f where f.attaquant = j.id and f.le >= v_minuit)::integer,
         coalesce((select q.n from quetes_compteurs q where q.joueur_id = j.id and q.jour = v_jour and q.cle = 'defense'), 0)::integer,
         coalesce((select q.n from quetes_compteurs q where q.joueur_id = j.id and q.jour = v_jour and q.cle = 'energie'), 0)::integer,
         (select max(d.jour) from jours_joues d where d.joueur_id = j.id)
    from clan_membres m join joueurs j on j.id = m.joueur_id
   where m.clan_id = v_clan;
end;
$f$;

-- 3. le classement aux membres actifs -------------------------------------------
-- (le retour change : une colonne « actifs » en plus)
drop function if exists public.clans_classement();
create function public.clans_classement()
 returns table(clan_id uuid, nom text, tag text, couleur text, membres integer, communes integer,
               moyenne integer, actifs integer)
 language plpgsql stable security definer set search_path to 'public'
as $f$
declare v_depuis date := quete_jour() - 6;
begin
  if auth.uid() is null then raise exception 'Non connecte'; end if;
  if not clans_ouverts() then raise exception 'Les clans ouvrent bientot'; end if;
  return query
  select c.id, c.nom, c.tag, c.couleur, x.n::integer, x.total::integer,
         case when x.actifs > 0 then round(x.total_actifs::numeric / x.actifs)::integer else 0 end,
         x.actifs::integer
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
$f$;

revoke all on function public.clan_activite()      from public, anon;
revoke all on function public.clans_classement()   from public, anon;
grant execute on function public.clan_activite()    to authenticated;
grant execute on function public.clans_classement() to authenticated;

commit;

-- contrôle : true | true | true | false
select position('s2-26' in pg_get_functiondef('public.front_energie_depenser(uuid, integer)'::regprocedure)) > 0 as energie_notee,
       has_function_privilege('authenticated', 'public.clan_activite()', 'execute')    as activite_ok,
       has_function_privilege('authenticated', 'public.clans_classement()', 'execute') as classement_ok,
       has_function_privilege('anon', 'public.clan_activite()', 'execute')             as anon_doit_etre_false;
