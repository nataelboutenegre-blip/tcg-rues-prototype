-- s3-28 : trois utilités de plus pour les clans (décisions de Nataël, 18/11/2026, 18 h 40)
--   1. Défense alliée : un membre du clan renforce la commune assiégée d'un coéquipier, × 1 (sans le bonus
--      défenseur × 1,2), 60 énergie au plus par allié et par siège ; l'alerte « en danger » prévient aussi le clan.
--   2. Classement des clans : somme des communes des 5 meilleurs membres actifs (au lieu de la moyenne).
--   3. Objectif de clan de la semaine : communes prises par le clan du lundi au dimanche, 3 paliers selon le
--      nombre d'actifs ; chaque membre qui a participé (une commune prise ou un renfort d'allié) ramasse.
-- Tout derrière des interrupteurs (config_jeu 'clans_s3'), ÉTEINTS ici. Lignes pour allumer à la fin.

begin;

create or replace function pg_temp.retoucher(p_sig text, p_marque text, p_ancien text, p_nouveau text)
returns void language plpgsql as $f$
declare d text; n integer;
begin
  d := pg_get_functiondef(p_sig::regprocedure);
  if position(p_marque in d) > 0 then return; end if;
  n := (length(d) - length(replace(d, p_ancien, ''))) / length(p_ancien);
  if n <> 1 then raise exception 's3-28 : % a changé (« % » trouvé % fois)', p_sig, left(p_ancien, 70), n; end if;
  if position(p_marque in p_nouveau) = 0 then raise exception 's3-28 : marque % absente du nouveau texte', p_marque; end if;
  execute replace(d, p_ancien, p_nouveau);
end $f$;

insert into public.config_jeu (cle, valeur)
values ('clans_s3', '{"defense_allie": 0, "allie_max": 60, "allie_mult": 1, "classement_top5": 0, "objectif": 0,
  "paliers": [2, 4, 7], "actifs_min": 3,
  "gains": [{"lingots": 5, "energie": 0}, {"lingots": 10, "energie": 10}, {"lingots": 20, "energie": 20}]}')
on conflict (cle) do nothing;

create or replace function public.clan_cfg(p_cle text)
returns jsonb language sql stable security definer set search_path to 'public' as $$
  select (select c.valeur::jsonb -> p_cle from config_jeu c where c.cle = 'clans_s3');
$$;
create or replace function public.clan_cfg_n(p_cle text)
returns numeric language sql stable security definer set search_path to 'public' as $$
  select (select (c.valeur::jsonb ->> p_cle)::numeric from config_jeu c where c.cle = 'clans_s3');
$$;

-- ───────────── 1. Défense alliée ─────────────
create or replace function public.defense_allie_ouverte()
returns boolean language sql stable security definer set search_path to 'public' as $$
  select clans_ouverts() and siege_actif() and coalesce(clan_cfg_n('defense_allie'), 0) >= 1;
$$;

create table if not exists public.siege_renforts_allies (
  siege_id bigint not null references public.front_sieges(id) on delete cascade,
  joueur_id uuid not null,
  proprio uuid,
  energie integer not null default 0,
  le timestamptz not null default now(),
  primary key (siege_id, joueur_id));
create index if not exists siege_renforts_allies_joueur on public.siege_renforts_allies (joueur_id, le desc);
alter table public.siege_renforts_allies enable row level security;
revoke all on public.siege_renforts_allies from anon, authenticated;

select pg_temp.retoucher('public.siege_renforcer(text, uuid, integer)', 's3-28a',
  $a$declare v_uid uuid := auth.uid(); s front_sieges; v_pts numeric := siege_n('points_par_energie'); v_recul numeric := 0; i integer;$a$,
  $b$declare v_uid uuid := auth.uid(); s front_sieges; v_pts numeric := siege_n('points_par_energie'); v_recul numeric := 0; i integer;
  v_allie boolean := false; v_proprio uuid; v_deja integer := 0; v_max integer := coalesce(clan_cfg_n('allie_max'), 60)::integer;   -- s3-28a$b$);
select pg_temp.retoucher('public.siege_renforcer(text, uuid, integer)', 's3-28b',
  $a$  if not exists (select 1 from possessions where commune_code = p_code and joueur_id = v_uid) then raise exception 'Cette commune ne t''appartient pas'; end if;$a$,
  $b$  select joueur_id into v_proprio from possessions where commune_code = p_code;   -- s3-28b : un allié du clan peut renforcer
  if v_proprio is distinct from v_uid then
    if v_proprio is null or not defense_allie_ouverte() or not meme_clan(v_uid, v_proprio) then raise exception 'Cette commune ne t''appartient pas'; end if;
    v_allie := true;
  end if;$b$);
select pg_temp.retoucher('public.siege_renforcer(text, uuid, integer)', 's3-28c',
  $a$  if not front_energie_depenser(v_uid, p_energie) then raise exception 'Énergie insuffisante (% requise)', p_energie; end if;
  for i in 1..p_energie loop v_recul := v_recul + v_pts * siege_n('defense_bonus') *$a$,
  $b$  if v_allie then   -- s3-28c : au plus 60 par allié et par siège, × 1
    if s.attaquant = v_uid then raise exception 'Tu ne peux pas défendre contre toi-même'; end if;
    select coalesce(energie, 0) into v_deja from siege_renforts_allies where siege_id = s.id and joueur_id = v_uid;
    v_deja := coalesce(v_deja, 0);
    if v_deja + p_energie > v_max then
      raise exception 'Un allié met au plus % énergie par siège (encore % pour toi)', v_max, greatest(0, v_max - v_deja);
    end if;
  end if;
  if not front_energie_depenser(v_uid, p_energie) then raise exception 'Énergie insuffisante (% requise)', p_energie; end if;
  for i in 1..p_energie loop v_recul := v_recul + v_pts * (case when v_allie then coalesce(clan_cfg_n('allie_mult'), 1) else siege_n('defense_bonus') end) *$b$);
select pg_temp.retoucher('public.siege_renforcer(text, uuid, integer)', 's3-28d',
  $a$defenseur = v_uid,$a$,
  $b$defenseur = case when v_allie then coalesce(defenseur, v_proprio) else v_uid end,   -- s3-28d : la défense reste au propriétaire
        $b$);
select pg_temp.retoucher('public.siege_renforcer(text, uuid, integer)', 's3-28e',
  $a$  perform quete_noter(v_uid, 'renfort', 1);   -- s3-22$a$,
  $b$  perform quete_noter(v_uid, 'renfort', 1);   -- s3-22
  if v_allie then   -- s3-28e : on note l'aide et on prévient le propriétaire
    insert into siege_renforts_allies (siege_id, joueur_id, proprio, energie) values (s.id, v_uid, v_proprio, p_energie)
    on conflict (siege_id, joueur_id) do update set energie = siege_renforts_allies.energie + excluded.energie, le = now();
    perform notifier_joueur(v_proprio, '🛡️ ' || coalesce((select pseudo from joueurs where id = v_uid), 'Un allié') || ' défend ' || coalesce((select nom from communes where code = p_code), 'ta commune'),
      'Ton allié a mis ' || p_energie || ' énergie pour repousser le siège.', './?onglet=defense', 'aide-recue-' || p_code);
  end if;$b$);

create or replace function public.clan_appel_aide(p_proprio uuid, p_code text, p_nom text, p_attaquant text)
returns void language plpgsql security definer set search_path to 'public' as $$
declare m record; v_p text;
begin
  if not defense_allie_ouverte() then return; end if;
  select pseudo into v_p from joueurs where id = p_proprio;
  for m in select b.joueur_id from clan_membres a join clan_membres b on b.clan_id = a.clan_id
            where a.joueur_id = p_proprio and b.joueur_id <> p_proprio loop
    perform notifier_joueur(m.joueur_id, '🛡️ ' || coalesce(v_p, 'Un allié') || ' a besoin d''aide',
      coalesce(p_nom, 'Sa commune') || ' va tomber : ' || coalesce(p_attaquant, 'un joueur') || ' a rempli les deux tiers de son siège. Tu peux la renforcer.',
      './?onglet=defense', 'aide-' || p_code);
  end loop;
end;
$$;
select pg_temp.retoucher('public.siege_appliquer(bigint, integer)', 's3-28f',
  $a$'./?onglet=defense', 'danger-' || s.commune_code);$a$,
  $b$'./?onglet=defense', 'danger-' || s.commune_code);
    perform clan_appel_aide(v_proprio, s.commune_code, v_nom, v_pseudo);   -- s3-28f : le clan aussi$b$);

create or replace function public.clan_sieges_allies()
returns jsonb language sql stable security definer set search_path to 'public' as $$
  select case when not defense_allie_ouverte() or clan_de(auth.uid()) is null then '[]'::jsonb else
    coalesce(jsonb_agg(siege_vue(s.id) || jsonb_build_object('nom', c.nom, 'dept', c.departement, 'garnison', siege_garnison(s.commune_code),
                         'proprio', po.joueur_id, 'proprio_pseudo', j.pseudo,
                         'mon_renfort', coalesce((select r.energie from siege_renforts_allies r where r.siege_id = s.id and r.joueur_id = auth.uid()), 0),
                         'allie_max', coalesce(clan_cfg_n('allie_max'), 60)::integer,
                         'allies', coalesce((select sum(r.energie) from siege_renforts_allies r where r.siege_id = s.id), 0))
                  order by s.degats / greatest(1, siege_resistance(s.commune_code, s.attaquant)) desc), '[]'::jsonb) end
    from front_sieges s
    join possessions po on po.commune_code = s.commune_code
    join clan_membres m on m.joueur_id = po.joueur_id and m.clan_id = clan_de(auth.uid())
    join communes c on c.code = s.commune_code
    left join joueurs j on j.id = po.joueur_id
   where s.fini_le is null and po.joueur_id <> auth.uid() and s.attaquant <> auth.uid();
$$;

-- ───────────── 2. Classement : somme des 5 meilleurs ─────────────
drop function if exists public.clans_classement();
create function public.clans_classement()
 returns table(clan_id uuid, nom text, tag text, couleur text, membres integer, communes integer, moyenne integer, actifs integer, mode text)
 language plpgsql stable security definer set search_path to 'public'
as $function$
declare v_depuis date := quete_jour() - 6; v_top5 boolean := coalesce(clan_cfg_n('classement_top5'), 0) >= 1;   -- s3-28
begin
  if auth.uid() is null then raise exception 'Non connecte'; end if;
  if not clans_ouverts() then raise exception 'Les clans ouvrent bientot'; end if;
  return query
  select c.id, c.nom, c.tag, c.couleur, x.n::integer, x.total::integer,
         case when v_top5 then x.top5::integer   -- « moyenne » garde son nom : c'est le score du clan
              when x.actifs > 0 then round(x.total_actifs::numeric / x.actifs)::integer else 0 end,
         x.actifs::integer,
         case when v_top5 then 'top5' else 'moyenne' end
    from clans c
    join lateral (
      select count(*) n,
             count(*) filter (where a.actif) actifs,
             coalesce(sum(a.communes), 0) total,
             coalesce(sum(a.communes) filter (where a.actif), 0) total_actifs,
             coalesce((select sum(t.communes) from (select a2.communes from clan_membres m2
                         cross join lateral (select (select count(*) from possessions p where p.joueur_id = m2.joueur_id) communes) a2
                        where m2.clan_id = c.id and exists (select 1 from jours_joues d where d.joueur_id = m2.joueur_id and d.jour >= v_depuis)
                        order by a2.communes desc limit 5) t), 0) top5
        from clan_membres m
        cross join lateral (
          select (select count(*) from possessions p where p.joueur_id = m.joueur_id) communes,
                 exists (select 1 from jours_joues d where d.joueur_id = m.joueur_id and d.jour >= v_depuis) actif) a
       where m.clan_id = c.id) x on true
   where x.n >= 3
   order by 7 desc, c.nom;
end;
$function$;
revoke all on function public.clans_classement() from public, anon;
grant execute on function public.clans_classement() to authenticated;

-- ───────────── 3. Objectif de clan de la semaine ─────────────
create or replace function public.objectif_ouvert()
returns boolean language sql stable security definer set search_path to 'public' as $$
  select clans_ouverts() and siege_actif() and coalesce(clan_cfg_n('objectif'), 0) >= 1;
$$;
create table if not exists public.clan_semaines (
  clan_id uuid not null references public.clans(id) on delete cascade,
  semaine date not null,
  actifs integer not null,
  primary key (clan_id, semaine));
create table if not exists public.clan_objectif_gains (
  joueur_id uuid not null,
  semaine date not null,
  palier integer not null,
  clan_id uuid,
  lingots integer not null default 0,
  energie integer not null default 0,
  le timestamptz not null default now(),
  primary key (joueur_id, semaine, palier));
alter table public.clan_semaines enable row level security;
alter table public.clan_objectif_gains enable row level security;
revoke all on public.clan_semaines, public.clan_objectif_gains from anon, authenticated;

create or replace function public.semaine_debut(p_semaine date)
returns timestamptz language sql immutable set search_path to 'public' as $$
  select (p_semaine::timestamp at time zone 'Europe/Paris');
$$;
-- les communes prises par chaque membre pendant la semaine (en étant déjà dans le clan), et ses renforts d'alliés
create or replace function public.clan_objectif_membres(p_clan uuid, p_semaine date)
returns table(joueur_id uuid, pseudo text, prises integer, renforts integer)
language sql stable security definer set search_path to 'public' as $$
  select m.joueur_id, j.pseudo,
         (select count(*) from front_sieges s where s.attaquant = m.joueur_id and s.resultat = 'conquise'
             and s.fini_le >= semaine_debut(p_semaine) and s.fini_le < semaine_debut(p_semaine + 7) and s.fini_le >= m.depuis)::integer,
         (select coalesce(sum(r.energie), 0) from siege_renforts_allies r where r.joueur_id = m.joueur_id
             and r.le >= semaine_debut(p_semaine) and r.le < semaine_debut(p_semaine + 7) and r.le >= m.depuis)::integer
    from clan_membres m left join joueurs j on j.id = m.joueur_id
   where m.clan_id = p_clan;
$$;
create or replace function public.clan_semaine_actifs(p_clan uuid, p_semaine date)
returns integer language plpgsql security definer set search_path to 'public' as $$
declare v integer;
begin
  select actifs into v from clan_semaines where clan_id = p_clan and semaine = p_semaine;
  if v is null then
    if p_semaine < date_trunc('week', quete_jour())::date then return null; end if;   -- semaine passée jamais ouverte
    v := greatest(clan_actifs(p_clan), coalesce(clan_cfg_n('actifs_min'), 3)::integer);
    insert into clan_semaines (clan_id, semaine, actifs) values (p_clan, p_semaine, v) on conflict do nothing;
    select actifs into v from clan_semaines where clan_id = p_clan and semaine = p_semaine;
  end if;
  return v;
end;
$$;
create or replace function public.clan_objectif_semaine(p_uid uuid, p_clan uuid, p_semaine date)
returns jsonb language plpgsql security definer set search_path to 'public' as $$
declare v_actifs integer := clan_semaine_actifs(p_clan, p_semaine); v_prises integer; v_moi record; v_pal jsonb := '[]'::jsonb; i integer;
  v_seuils jsonb := coalesce(clan_cfg('paliers'), '[2, 4, 7]'::jsonb); v_gains jsonb := coalesce(clan_cfg('gains'), '[]'::jsonb);
begin
  if v_actifs is null then return null; end if;
  select coalesce(sum(x.prises), 0)::integer into v_prises from clan_objectif_membres(p_clan, p_semaine) x;
  select * into v_moi from clan_objectif_membres(p_clan, p_semaine) x where x.joueur_id = p_uid;
  for i in 0 .. jsonb_array_length(v_seuils) - 1 loop
    v_pal := v_pal || jsonb_build_object('n', i + 1, 'seuil', ceil((v_seuils ->> i)::numeric * v_actifs)::integer,
               'lingots', coalesce((v_gains -> i ->> 'lingots')::integer, 0), 'energie', coalesce((v_gains -> i ->> 'energie')::integer, 0),
               'atteint', v_prises >= ceil((v_seuils ->> i)::numeric * v_actifs),
               'ramasse', exists (select 1 from clan_objectif_gains g where g.joueur_id = p_uid and g.semaine = p_semaine and g.palier = i + 1));
  end loop;
  return jsonb_build_object('semaine', p_semaine, 'fin', semaine_debut(p_semaine + 7), 'actifs', v_actifs, 'prises', v_prises,
    'participe', coalesce(v_moi.prises, 0) > 0 or coalesce(v_moi.renforts, 0) > 0,
    'mes_prises', coalesce(v_moi.prises, 0), 'mes_renforts', coalesce(v_moi.renforts, 0), 'paliers', v_pal,
    'membres', coalesce((select jsonb_agg(jsonb_build_object('pseudo', x.pseudo, 'prises', x.prises, 'renforts', x.renforts, 'moi', x.joueur_id = p_uid)
                                   order by x.prises desc, x.renforts desc, x.pseudo)
                           from clan_objectif_membres(p_clan, p_semaine) x), '[]'::jsonb));
end;
$$;

create or replace function public.clan_objectif_etat()
returns jsonb language plpgsql security definer set search_path to 'public' as $$
declare v_uid uuid := auth.uid(); v_clan uuid; v_sem date := date_trunc('week', quete_jour())::date;
begin
  if v_uid is null then raise exception 'Non connecte'; end if;
  v_clan := clan_de(v_uid);
  if v_clan is null or not objectif_ouvert() then return jsonb_build_object('ouvert', objectif_ouvert(), 'clan', v_clan is not null); end if;
  return jsonb_build_object('ouvert', true, 'clan', true,
    'cette', clan_objectif_semaine(v_uid, v_clan, v_sem),
    'derniere', clan_objectif_semaine(v_uid, v_clan, v_sem - 7));
end;
$$;

create or replace function public.clan_objectif_ramasser(p_semaine date)
returns jsonb language plpgsql security definer set search_path to 'public' as $$
declare v_uid uuid := auth.uid(); v_clan uuid; v_sem date := date_trunc('week', quete_jour())::date; o jsonb; p jsonb;
  v_l integer := 0; v_e integer := 0; v numeric; v_reel integer := 0;
begin
  if v_uid is null then raise exception 'Non connecte'; end if;
  if not objectif_ouvert() then raise exception 'L''objectif de clan n''est pas encore ouvert'; end if;
  v_clan := clan_de(v_uid);
  if v_clan is null then raise exception 'Il faut être dans un clan'; end if;
  if p_semaine is distinct from v_sem and p_semaine is distinct from v_sem - 7 then raise exception 'Cette semaine est trop ancienne'; end if;
  perform 1 from joueurs where id = v_uid for update;
  o := clan_objectif_semaine(v_uid, v_clan, p_semaine);
  if o is null then raise exception 'Rien à ramasser'; end if;
  if not (o ->> 'participe')::boolean then raise exception 'Prends une commune ou renforce un allié cette semaine pour avoir ta part'; end if;
  for p in select * from jsonb_array_elements(o -> 'paliers') loop
    if (p ->> 'atteint')::boolean and not (p ->> 'ramasse')::boolean then
      insert into clan_objectif_gains (joueur_id, semaine, palier, clan_id, lingots, energie)
      values (v_uid, p_semaine, (p ->> 'n')::integer, v_clan, (p ->> 'lingots')::integer, (p ->> 'energie')::integer);
      v_l := v_l + (p ->> 'lingots')::integer; v_e := v_e + (p ->> 'energie')::integer;
    end if;
  end loop;
  if v_l = 0 and v_e = 0 then raise exception 'Rien à ramasser pour l''instant'; end if;
  if v_l > 0 then perform lingots_figer(v_uid); update joueurs set lingots = lingots + v_l where id = v_uid; end if;
  if v_e > 0 then
    select front_energie_lire(j.front_energie, j.front_energie_maj) into v from joueurs j where j.id = v_uid;
    v_reel := greatest(0, least(front_energie_reglage('plafond'), floor(v + v_e)) - floor(v))::integer;
    update joueurs set front_energie = least(front_energie_reglage('plafond'), v + v_e), front_energie_maj = now() where id = v_uid;
  end if;
  return clan_objectif_etat() || jsonb_build_object('gagne_lingots', v_l, 'gagne_energie', v_reel, 'energie_prevue', v_e);
end;
$$;

revoke all on function public.clan_cfg(text), public.clan_cfg_n(text), public.clan_appel_aide(uuid, text, text, text),
  public.semaine_debut(date), public.clan_objectif_membres(uuid, date), public.clan_semaine_actifs(uuid, date),
  public.clan_objectif_semaine(uuid, uuid, date) from public, anon, authenticated;
revoke all on function public.defense_allie_ouverte(), public.clan_sieges_allies(), public.objectif_ouvert(),
  public.clan_objectif_etat(), public.clan_objectif_ramasser(date) from public, anon;
grant execute on function public.defense_allie_ouverte(), public.clan_sieges_allies(), public.objectif_ouvert(),
  public.clan_objectif_etat(), public.clan_objectif_ramasser(date) to authenticated;

commit;

-- Contrôle : false | false | false | 6 retouches
select defense_allie_ouverte() as defense_allie, objectif_ouvert() as objectif, coalesce(clan_cfg_n('classement_top5'), 0) >= 1 as top5,
  (select count(*) from unnest(array[
     position('s3-28a' in pg_get_functiondef('public.siege_renforcer(text, uuid, integer)'::regprocedure)),
     position('s3-28b' in pg_get_functiondef('public.siege_renforcer(text, uuid, integer)'::regprocedure)),
     position('s3-28c' in pg_get_functiondef('public.siege_renforcer(text, uuid, integer)'::regprocedure)),
     position('s3-28d' in pg_get_functiondef('public.siege_renforcer(text, uuid, integer)'::regprocedure)),
     position('s3-28e' in pg_get_functiondef('public.siege_renforcer(text, uuid, integer)'::regprocedure)),
     position('s3-28f' in pg_get_functiondef('public.siege_appliquer(bigint, integer)'::regprocedure))]) x where x > 0) as retouches;

-- Pour allumer (une ligne par système) :
-- update public.config_jeu set valeur = ((valeur::jsonb) || '{"defense_allie": 1}'::jsonb)::text where cle = 'clans_s3';
-- update public.config_jeu set valeur = ((valeur::jsonb) || '{"classement_top5": 1}'::jsonb)::text where cle = 'clans_s3';
-- update public.config_jeu set valeur = ((valeur::jsonb) || '{"objectif": 1}'::jsonb)::text where cle = 'clans_s3';
