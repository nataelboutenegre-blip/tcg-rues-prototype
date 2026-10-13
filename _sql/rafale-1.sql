-- =====================================================================
--  TerraFront — Rafale : duel en différé, classé à l'Elo (13 octobre 2026)
--
--  Une lettre, 30 secondes : le plus de communes de France qui commencent
--  par cette lettre. Une commune = 1 point. Idée d'Oshannir.
--
--  LE DUEL (calqué sur le Radar)
--  - « Lancer » cherche une partie terminée par un autre joueur, d'Elo
--    proche, pas encore affrontée : on joue SA lettre, et le duel se règle
--    à la fin du chrono. Sinon on joue une lettre neuve et la partie
--    attend le prochain joueur.
--  - Défi amical : un joueur en défie un autre, sans Elo ni points, 7 jours
--    pour le relever, 5 défis en attente au plus.
--  - Victoire en duel classé : 20 pts, 5 victoires payées par jour (comme
--    le Radar). Rien pour une défaite, une égalité ou un défi.
--  - Quête du jour (saison 2) : « rafale_victoire » notée à chaque victoire
--    classée, si quete_noter existe.
--
--  CONTRE LA TRICHE
--  - La lettre n'est donnée qu'au départ du chrono (rafale_partir) ; le
--    chrono est celui du serveur (30 s + 2 s de marge pour le réseau).
--  - Chaque nom est vérifié ici (rafale_dire) : bonne lettre, vraie
--    commune, pas déjà dite, et au moins 0,5 s depuis le nom précédent
--    accepté (un copier-coller de liste ne passe pas). 300 envois au plus.
--  - Quitter en pleine partie n'arrête pas le chrono : la partie se ferme
--    avec ce qui a été dit.
--
--  Tables neuves (rafale_*), aucune table existante modifiée. Les seules
--  fonctions existantes appelées : quete_noter (si elle existe).
--  Rejouable. Finit par un contrôle.
-- =====================================================================

create table if not exists public.rafale_joueurs(
  joueur_id  uuid primary key references public.joueurs(id) on delete cascade,
  elo        integer not null default 1000,
  parties    integer not null default 0,
  victoires  integer not null default 0,
  maj        timestamptz not null default now()
);

-- les noms acceptés : un nom normalisé -> la plus peuplée des communes de ce nom
create table if not exists public.rafale_noms(
  cle   text primary key,
  code  text not null,
  nom   text not null,
  dept  text not null,
  pop   integer not null default 0
);

create table if not exists public.rafale_parties(
  id             bigserial primary key,
  joueur_id      uuid not null references public.joueurs(id) on delete cascade,
  lettre         text not null,
  source_id      bigint references public.rafale_parties(id) on delete set null,  -- la partie affrontée
  cible_id       uuid references public.joueurs(id) on delete set null,          -- défi : le joueur défié
  amical         boolean not null default false,
  debut          timestamptz,                                  -- départ du chrono
  mots           jsonb not null default '[]'::jsonb,           -- [{k, n, d, t}] : clé, nom, département, ms depuis le départ
  essais         integer not null default 0,
  dernier_mot    timestamptz,
  score          integer,
  fini           boolean not null default false,
  utilisee       boolean not null default false,
  elo_avant      integer,
  elo_apres      integer,
  resultat       text,                                         -- victoire / defaite / egalite / refuse / expire
  vu             boolean not null default true,
  gain           integer,
  gain_le        timestamptz,
  jour           date not null default (now() at time zone 'Europe/Paris')::date,
  cree_le        timestamptz not null default now(),
  fin_le         timestamptz
);
create index if not exists rafale_parties_joueur on public.rafale_parties(joueur_id, jour);
create index if not exists rafale_parties_dispo  on public.rafale_parties(fini, utilisee) where source_id is null;
create index if not exists rafale_parties_source on public.rafale_parties(source_id) where source_id is not null;
create index if not exists rafale_parties_cible  on public.rafale_parties(cible_id) where cible_id is not null;

alter table public.rafale_joueurs enable row level security;
alter table public.rafale_noms    enable row level security;
alter table public.rafale_parties enable row level security;
revoke all on public.rafale_joueurs, public.rafale_noms, public.rafale_parties from public, anon, authenticated;
revoke all on sequence public.rafale_parties_id_seq from public, anon, authenticated;

-- ---------------------------------------------------------------------
-- Réglages, rangs, normalisation
-- ---------------------------------------------------------------------
create or replace function public.rafale_reglage(p text)
returns integer language sql immutable set search_path to 'public'
as $$
  select case p
    when 'secondes'   then 30
    when 'marge'      then 2
    when 'k'          then 24
    when 'ecart_ms'   then 500     -- entre deux noms acceptés
    when 'envois'     then 300     -- envois au plus par partie
    when 'gain'       then 20
    when 'gains_jour' then 5
  end;
$$;

-- les lettres jouables : assez de communes pour 30 secondes
create or replace function public.rafale_lettres()
returns text language sql immutable set search_path to 'public'
as $$ select 'ABCDEFGHJLMNOPRSTV'; $$;

create or replace function public.rafale_rang(p_elo integer)
returns text language sql immutable set search_path to 'public'
as $$
  select case when p_elo >= 1200 then 'Pilote'
              when p_elo >= 1100 then 'Routier'
              when p_elo >= 1000 then 'Motard'
              when p_elo >= 900  then 'Cycliste'
              else 'Piéton' end;
$$;

-- « Saint-Étienne », « st etienne », « ST-ÉTIENNE » -> SAINTETIENNE
create or replace function public.rafale_norm(p text)
returns text language plpgsql immutable set search_path to 'public'
as $$
declare s text;
begin
  s := coalesce(p, '');
  s := replace(replace(replace(replace(s, 'œ', 'oe'), 'Œ', 'OE'), 'æ', 'ae'), 'Æ', 'AE');
  s := translate(s, 'àâäáãåçéèêëíìîïñóòôöõúùûüýÿÀÂÄÁÃÅÇÉÈÊËÍÌÎÏÑÓÒÔÖÕÚÙÛÜÝŸ',
                    'aaaaaaceeeeiiiinooooouuuuyyAAAAAACEEEEIIIINOOOOOUUUUYY');
  s := upper(s);
  s := regexp_replace(s, '(^|[^A-Z])STE([^A-Z]|$)', '\1SAINTE\2', 'g');
  s := regexp_replace(s, '(^|[^A-Z])ST([^A-Z]|$)',  '\1SAINT\2',  'g');
  return regexp_replace(s, '[^A-Z]', '', 'g');
end;
$$;

-- la liste des noms, refaite à chaque lancement du fichier
truncate public.rafale_noms;
insert into public.rafale_noms(cle, code, nom, dept, pop)
select distinct on (rafale_norm(c.nom)) rafale_norm(c.nom), c.code, c.nom, c.departement, coalesce(c.population, 0)
  from public.communes c
 where c.nom not ilike '%arrondissement%'
   and rafale_norm(c.nom) <> ''
 order by rafale_norm(c.nom), c.population desc nulls last, c.code;

-- ---------------------------------------------------------------------
-- Interne : les points d'une victoire classée
-- ---------------------------------------------------------------------
create or replace function public.rafale_gagner(p_partie bigint)
returns void language plpgsql security definer set search_path to 'public'
as $$
declare
  v_joueur uuid;
  v_deja integer;
  v_minuit timestamptz := date_trunc('day', now() at time zone 'Europe/Paris') at time zone 'Europe/Paris';
begin
  select joueur_id into v_joueur from rafale_parties where id = p_partie and gain is null;
  if v_joueur is null then return; end if;
  select count(*) into v_deja from rafale_parties
   where joueur_id = v_joueur and gain > 0 and gain_le >= v_minuit;
  if v_deja >= rafale_reglage('gains_jour') then return; end if;
  update rafale_parties set gain = rafale_reglage('gain'), gain_le = now() where id = p_partie;
  perform set_config('terrafront.motif', 'rafale', true);
  update joueurs set solde = coalesce(solde, 0) + rafale_reglage('gain') where id = v_joueur;
end;
$$;

-- Interne : la quête du jour, seulement si la saison 2 l'a installée
create or replace function public.rafale_noter_quete(p_uid uuid)
returns void language plpgsql security definer set search_path to 'public'
as $$
begin
  if to_regprocedure('public.quete_noter(uuid,text,integer)') is not null then
    execute 'select public.quete_noter($1, $2, 1)' using p_uid, 'rafale_victoire';
  end if;
end;
$$;

-- ---------------------------------------------------------------------
-- Interne : fermer une partie, et régler le duel s'il y a un adversaire
-- ---------------------------------------------------------------------
create or replace function public.rafale_clore(p_id bigint)
returns void language plpgsql security definer set search_path to 'public'
as $$
declare
  p rafale_parties;
  s rafale_parties;
  v_score int;
  ea int; eb int; va int; vb int;
  v_att numeric; v_res numeric;
  v_k int := rafale_reglage('k');
begin
  select * into p from rafale_parties where id = p_id for update;
  if p.fini then return; end if;
  v_score := jsonb_array_length(p.mots);
  update rafale_parties set fini = true, score = v_score, fin_le = now(),
         debut = coalesce(debut, now()) where id = p_id;

  if p.source_id is null then return; end if;   -- partie neuve ou défi lancé : elle attend

  select * into s from rafale_parties where id = p.source_id for update;
  if s.id is null then return; end if;
  v_res := case when v_score > s.score then 1 when v_score < s.score then 0 else 0.5 end;

  if p.amical or s.amical then
    update rafale_parties set vu = true,
           resultat = case v_res when 1 then 'victoire' when 0 then 'defaite' else 'egalite' end where id = p.id;
    update rafale_parties set vu = false,
           resultat = case v_res when 0 then 'victoire' when 1 then 'defaite' else 'egalite' end where id = s.id;
    return;
  end if;

  insert into rafale_joueurs(joueur_id) values (p.joueur_id), (s.joueur_id) on conflict do nothing;
  select elo into ea from rafale_joueurs where joueur_id = p.joueur_id for update;
  select elo into eb from rafale_joueurs where joueur_id = s.joueur_id for update;
  v_att := 1 / (1 + power(10, (eb - ea) / 400.0));
  va := ea + round(v_k * (v_res - v_att));
  vb := eb + round(v_k * ((1 - v_res) - (1 - v_att)));
  update rafale_joueurs set elo = va, parties = parties + 1,
         victoires = victoires + (v_res = 1)::int, maj = now() where joueur_id = p.joueur_id;
  update rafale_joueurs set elo = vb, parties = parties + 1,
         victoires = victoires + (v_res = 0)::int, maj = now() where joueur_id = s.joueur_id;
  update rafale_parties set elo_avant = ea, elo_apres = va, vu = true,
         resultat = case v_res when 1 then 'victoire' when 0 then 'defaite' else 'egalite' end where id = p.id;
  update rafale_parties set elo_avant = eb, elo_apres = vb, vu = false,
         resultat = case v_res when 0 then 'victoire' when 1 then 'defaite' else 'egalite' end where id = s.id;

  if v_res = 1 then perform rafale_gagner(p.id); perform rafale_noter_quete(p.joueur_id);
  elsif v_res = 0 then perform rafale_gagner(s.id); perform rafale_noter_quete(s.joueur_id); end if;
end;
$$;

-- Interne : fermer une partie dont le chrono est dépassé
create or replace function public.rafale_rattraper(p_id bigint)
returns void language plpgsql security definer set search_path to 'public'
as $$
begin
  if exists (select 1 from rafale_parties where id = p_id and not fini and debut is not null
               and now() > debut + make_interval(secs => rafale_reglage('secondes') + rafale_reglage('marge'))) then
    perform rafale_clore(p_id);
  end if;
end;
$$;

-- ---------------------------------------------------------------------
-- Interne : ce que le joueur voit d'une partie
-- (l'adversaire : celui qu'on affronte, ou celui qui a rejoué notre partie)
-- ---------------------------------------------------------------------
create or replace function public.rafale_vue(p_id bigint)
returns jsonb language plpgsql security definer set search_path to 'public'
as $$
declare
  p rafale_parties;
  s rafale_parties;
  v_adv jsonb := null;
  v_mots jsonb;
begin
  select * into p from rafale_parties where id = p_id;
  if p.source_id is not null then
    select * into s from rafale_parties where id = p.source_id;
  elsif p.fini then
    select * into s from rafale_parties where source_id = p.id and fini limit 1;
  end if;

  select coalesce(jsonb_agg(jsonb_build_object('n', m->>'n', 'd', m->>'d') order by o), '[]'::jsonb)
    into v_mots from jsonb_array_elements(p.mots) with ordinality as x(m, o);

  if s.id is not null then
    v_adv := jsonb_build_object(
      'pseudo', (select coalesce(pseudo, 'Joueur') from joueurs where id = s.joueur_id),
      'elo', (select elo from rafale_joueurs where joueur_id = s.joueur_id),
      'joue_le', s.fin_le,
      -- son score et ses mots, seulement quand ma partie est finie
      'score', case when p.fini and s.fini then s.score end,
      'mots', case when p.fini and s.fini then
        (select coalesce(jsonb_agg(jsonb_build_object('n', m->>'n', 'd', m->>'d') order by o), '[]'::jsonb)
           from jsonb_array_elements(s.mots) with ordinality as x(m, o)) end);
  end if;

  return jsonb_build_object(
    'id', p.id,
    'jeu', 'rafale',
    'lettre', case when p.debut is not null or p.fini then p.lettre end,
    'secondes', rafale_reglage('secondes'),
    'parti', p.debut is not null,
    'reste_ms', case when not p.fini and p.debut is not null then
        greatest(0, round(extract(epoch from (p.debut + make_interval(secs => rafale_reglage('secondes')) - now())) * 1000)) end,
    'mots', v_mots,
    'score', coalesce(p.score, jsonb_array_length(p.mots)),
    'fini', p.fini,
    'adversaire', v_adv,
    'en_attente', p.fini and p.source_id is null and p.resultat is null and s.id is null,
    'resultat', p.resultat,
    'elo_avant', p.elo_avant,
    'elo_apres', p.elo_apres,
    'amical', p.amical,
    'gain', p.gain,
    'regle_le', case when p.source_id is not null then p.fin_le else s.fin_le end,
    'cible', case when p.cible_id is not null
                  then (select coalesce(pseudo, 'un joueur') from joueurs where id = p.cible_id) end);
end;
$$;

-- ---------------------------------------------------------------------
-- Ce que le jeu appelle
-- ---------------------------------------------------------------------

-- Lancer un duel classé, ou reprendre la partie en cours
create or replace function public.rafale_lancer()
returns jsonb language plpgsql security definer set search_path to 'public'
as $$
declare
  v_uid uuid := auth.uid();
  v_id bigint;
  v_elo int;
  s rafale_parties;
  v_lettre text;
begin
  if v_uid is null then raise exception 'Connecte-toi pour jouer à Rafale.'; end if;
  perform pg_advisory_xact_lock(hashtextextended('rafale' || v_uid::text, 7));

  select id into v_id from rafale_parties where joueur_id = v_uid and not fini order by id desc limit 1;
  if v_id is not null then
    perform rafale_rattraper(v_id);
    if not (select fini from rafale_parties where id = v_id) then return rafale_vue(v_id); end if;
  end if;

  insert into rafale_joueurs(joueur_id) values (v_uid) on conflict do nothing;
  select elo into v_elo from rafale_joueurs where joueur_id = v_uid;

  -- un adversaire : partie classée finie, pas encore affrontée, d'un autre
  -- joueur ; de préférence pas affronté depuis 24 h, puis Elo proche, puis
  -- la plus ancienne
  select p.* into s
    from rafale_parties p
    left join rafale_joueurs r on r.joueur_id = p.joueur_id
   where p.source_id is null and p.fini and not p.utilisee
     and p.joueur_id <> v_uid and p.cible_id is null and not p.amical
   order by exists (select 1 from rafale_parties m
                      join rafale_parties ms on ms.id = m.source_id
                     where m.joueur_id = v_uid and ms.joueur_id = p.joueur_id
                       and m.cree_le > now() - interval '24 hours'),
            abs(coalesce(r.elo, 1000) - v_elo), p.fin_le
   limit 1
   for update of p skip locked;

  if s.id is not null then
    update rafale_parties set utilisee = true where id = s.id;
    v_lettre := s.lettre;
  else
    v_lettre := substr(rafale_lettres(), 1 + floor(random() * length(rafale_lettres()))::int, 1);
  end if;

  insert into rafale_parties(joueur_id, lettre, source_id) values (v_uid, v_lettre, s.id)
  returning id into v_id;
  return rafale_vue(v_id);
end;
$$;

-- Départ du chrono : c'est ici que la lettre est donnée
create or replace function public.rafale_partir(p_id bigint)
returns jsonb language plpgsql security definer set search_path to 'public'
as $$
declare v_uid uuid := auth.uid();
begin
  if v_uid is null then raise exception 'Connecte-toi pour jouer à Rafale.'; end if;
  perform rafale_rattraper(p_id);
  update rafale_parties set debut = now()
   where id = p_id and joueur_id = v_uid and not fini and debut is null;
  if not exists (select 1 from rafale_parties where id = p_id and joueur_id = v_uid) then
    raise exception 'Partie introuvable.';
  end if;
  return rafale_vue(p_id);
end;
$$;

-- Dire un nom. Réponse : ok, raison (lettre / inconnue / deja / vite / vide / trop / fini), le nom reconnu
create or replace function public.rafale_dire(p_id bigint, p_nom text)
returns jsonb language plpgsql security definer set search_path to 'public'
as $$
declare
  v_uid uuid := auth.uid();
  p rafale_parties;
  v_cle text;
  n rafale_noms;
  v_limite timestamptz;
begin
  if v_uid is null then raise exception 'Connecte-toi pour jouer à Rafale.'; end if;
  select * into p from rafale_parties where id = p_id and joueur_id = v_uid for update;
  if not found then raise exception 'Partie introuvable.'; end if;
  if p.fini then return jsonb_build_object('ok', false, 'raison', 'fini', 'score', p.score); end if;
  if p.debut is null then raise exception 'Le chrono n''est pas parti.'; end if;
  v_limite := p.debut + make_interval(secs => rafale_reglage('secondes') + rafale_reglage('marge'));
  if now() > v_limite then
    perform rafale_clore(p_id);
    return jsonb_build_object('ok', false, 'raison', 'fini', 'score', jsonb_array_length(p.mots));
  end if;
  if p.essais >= rafale_reglage('envois') then
    return jsonb_build_object('ok', false, 'raison', 'trop', 'score', jsonb_array_length(p.mots));
  end if;
  update rafale_parties set essais = essais + 1 where id = p_id;

  v_cle := rafale_norm(left(p_nom, 80));
  if v_cle = '' then return jsonb_build_object('ok', false, 'raison', 'vide', 'score', jsonb_array_length(p.mots)); end if;
  if left(v_cle, 1) <> p.lettre then
    return jsonb_build_object('ok', false, 'raison', 'lettre', 'score', jsonb_array_length(p.mots));
  end if;
  select * into n from rafale_noms where cle = v_cle;
  if not found then return jsonb_build_object('ok', false, 'raison', 'inconnue', 'score', jsonb_array_length(p.mots)); end if;
  if p.mots @> jsonb_build_array(jsonb_build_object('k', v_cle)) then
    return jsonb_build_object('ok', false, 'raison', 'deja', 'nom', n.nom, 'score', jsonb_array_length(p.mots));
  end if;
  if p.dernier_mot is not null and now() < p.dernier_mot + make_interval(secs => rafale_reglage('ecart_ms') / 1000.0) then
    return jsonb_build_object('ok', false, 'raison', 'vite', 'score', jsonb_array_length(p.mots));
  end if;

  update rafale_parties
     set mots = mots || jsonb_build_array(jsonb_build_object('k', v_cle, 'n', n.nom, 'd', n.dept,
                  't', round(extract(epoch from (now() - p.debut)) * 1000)::int)),
         dernier_mot = now()
   where id = p_id;
  return jsonb_build_object('ok', true, 'nom', n.nom, 'dept', n.dept, 'score', jsonb_array_length(p.mots) + 1);
end;
$$;

-- Fin de partie (chrono écoulé côté jeu, ou le joueur s'arrête)
create or replace function public.rafale_terminer(p_id bigint)
returns jsonb language plpgsql security definer set search_path to 'public'
as $$
declare v_uid uuid := auth.uid();
begin
  if v_uid is null then raise exception 'Connecte-toi pour jouer à Rafale.'; end if;
  if not exists (select 1 from rafale_parties where id = p_id and joueur_id = v_uid and debut is not null) then
    raise exception 'Partie introuvable.';
  end if;
  perform rafale_clore(p_id);
  return rafale_vue(p_id);
end;
$$;

-- Le résumé d'une de mes parties finies
create or replace function public.rafale_resume(p_id bigint)
returns jsonb language plpgsql security definer set search_path to 'public'
as $$
declare v_uid uuid := auth.uid();
begin
  if v_uid is null then raise exception 'Connecte-toi pour jouer à Rafale.'; end if;
  if not exists (select 1 from rafale_parties where id = p_id and joueur_id = v_uid and fini) then
    raise exception 'Partie introuvable.';
  end if;
  return rafale_vue(p_id);
end;
$$;

-- Défier un joueur (amical)
create or replace function public.rafale_defier(p_cible uuid)
returns jsonb language plpgsql security definer set search_path to 'public'
as $$
declare
  v_uid uuid := auth.uid();
  v_id bigint;
  v_pseudo text;
  v_bloque boolean := false;
begin
  if v_uid is null then raise exception 'Connecte-toi pour jouer à Rafale.'; end if;
  if p_cible is null or p_cible = v_uid then raise exception 'Choisis un autre joueur à défier.'; end if;
  select pseudo into v_pseudo from joueurs where id = p_cible;
  if not found then raise exception 'Ce joueur n''existe plus.'; end if;
  if to_regclass('public.amis') is not null then
    execute 'select exists (select 1 from amis where joueur_id = $1 and ami_id = $2 and etat = ''bloque'')'
       into v_bloque using p_cible, v_uid;
    if v_bloque then raise exception 'Ce joueur ne peut pas être défié pour le moment.'; end if;
  end if;
  perform pg_advisory_xact_lock(hashtextextended('rafale' || v_uid::text, 7));
  select id into v_id from rafale_parties where joueur_id = v_uid and not fini limit 1;
  if v_id is not null then perform rafale_rattraper(v_id); end if;
  if exists (select 1 from rafale_parties where joueur_id = v_uid and not fini) then
    raise exception 'Termine d''abord ta partie en cours.';
  end if;
  if exists (select 1 from rafale_parties where joueur_id = v_uid and cible_id = p_cible
                and resultat is null and not utilisee and cree_le > now() - interval '7 days') then
    raise exception 'Tu as déjà un défi en attente avec %.', coalesce(v_pseudo, 'ce joueur');
  end if;
  if (select count(*) from rafale_parties where joueur_id = v_uid and cible_id is not null
        and resultat is null and not utilisee and cree_le > now() - interval '7 days') >= 5 then
    raise exception 'Tu as déjà 5 défis en attente. Attends qu''ils soient relevés.';
  end if;
  insert into rafale_parties(joueur_id, lettre, cible_id, amical)
  values (v_uid, substr(rafale_lettres(), 1 + floor(random() * length(rafale_lettres()))::int, 1), p_cible, true)
  returning id into v_id;
  return rafale_vue(v_id);
end;
$$;

-- Relever un défi : même lettre
create or replace function public.rafale_relever(p_id bigint)
returns jsonb language plpgsql security definer set search_path to 'public'
as $$
declare
  v_uid uuid := auth.uid();
  d rafale_parties;
  v_id bigint;
begin
  if v_uid is null then raise exception 'Connecte-toi pour jouer à Rafale.'; end if;
  perform pg_advisory_xact_lock(hashtextextended('rafale' || v_uid::text, 7));
  select * into d from rafale_parties
   where id = p_id and cible_id = v_uid and fini and not utilisee and resultat is null
     and cree_le > now() - interval '7 days'
   for update;
  if not found then raise exception 'Ce défi n''est plus disponible.'; end if;
  select id into v_id from rafale_parties where joueur_id = v_uid and not fini limit 1;
  if v_id is not null then perform rafale_rattraper(v_id); end if;
  if exists (select 1 from rafale_parties where joueur_id = v_uid and not fini) then
    raise exception 'Termine d''abord ta partie en cours.';
  end if;
  update rafale_parties set utilisee = true where id = d.id;
  insert into rafale_parties(joueur_id, lettre, source_id, amical) values (v_uid, d.lettre, d.id, true)
  returning id into v_id;
  return rafale_vue(v_id);
end;
$$;

-- Décliner un défi
create or replace function public.rafale_refuser(p_id bigint)
returns void language plpgsql security definer set search_path to 'public'
as $$
begin
  if auth.uid() is null then raise exception 'Connecte-toi pour jouer à Rafale.'; end if;
  update rafale_parties set utilisee = true, resultat = 'refuse', vu = false
   where id = p_id and cible_id = auth.uid() and fini and not utilisee and resultat is null;
  if not found then raise exception 'Ce défi n''est plus disponible.'; end if;
end;
$$;

-- Les résultats affichés sont vus (pastille du QG)
create or replace function public.rafale_vu()
returns void language sql security definer set search_path to 'public'
as $$ update rafale_parties set vu = true where joueur_id = auth.uid() and not vu; $$;

-- L'état du QG : mêmes clés que radar_etat
create or replace function public.rafale_etat()
returns jsonb language plpgsql security definer set search_path to 'public'
as $$
declare
  v_uid uuid := auth.uid();
  v_elo int;
  v_parties int;
  v_premier uuid;
  v_en_cours bigint;
begin
  if v_uid is null then raise exception 'Connecte-toi pour jouer à Rafale.'; end if;
  select elo, parties into v_elo, v_parties from rafale_joueurs where joueur_id = v_uid;
  v_elo := coalesce(v_elo, 1000);
  select joueur_id into v_premier from rafale_joueurs
   where parties >= 5 and elo > 1000 order by elo desc, maj limit 1;

  select id into v_en_cours from rafale_parties where joueur_id = v_uid and not fini order by id desc limit 1;
  if v_en_cours is not null then perform rafale_rattraper(v_en_cours); end if;

  update rafale_parties set utilisee = true, resultat = 'expire', vu = false
   where cible_id is not null and fini and not utilisee and resultat is null
     and cree_le <= now() - interval '7 days'
     and (joueur_id = v_uid or cible_id = v_uid);

  return jsonb_build_object(
    'elo', v_elo,
    'parties', coalesce(v_parties, 0),
    'rang', case when v_premier = v_uid then 'As du volant' else rafale_rang(v_elo) end,
    'restants', null,
    'en_cours', (select id from rafale_parties where joueur_id = v_uid and not fini order by id desc limit 1),
    'non_vus', (select count(*) from rafale_parties where joueur_id = v_uid and not vu),
    'en_attente', (select count(*) from rafale_parties
                    where joueur_id = v_uid and fini and source_id is null and resultat is null and cible_id is null),
    'attente_liste', (select coalesce(jsonb_agg(x order by x.fin desc), '[]'::jsonb) from (
        select p.id, p.score, p.lettre, p.fin_le as fin
          from rafale_parties p
         where p.joueur_id = v_uid and p.fini and p.source_id is null and p.resultat is null and p.cible_id is null
         order by p.fin_le desc limit 5) x),
    'defis_recus', (select coalesce(jsonb_agg(x order by x.fin desc), '[]'::jsonb) from (
        select p.id, coalesce(j.pseudo, 'un joueur') as pseudo, p.joueur_id, p.fin_le as fin,
               p.cree_le + interval '7 days' as expire_le
          from rafale_parties p left join joueurs j on j.id = p.joueur_id
         where p.cible_id = v_uid and p.fini and not p.utilisee and p.resultat is null
         order by p.fin_le desc limit 10) x),
    'defis_envoyes', (select coalesce(jsonb_agg(x order by x.fin desc), '[]'::jsonb) from (
        select p.id, coalesce(j.pseudo, 'un joueur') as pseudo, p.score, p.lettre, p.fin_le as fin
          from rafale_parties p left join joueurs j on j.id = p.cible_id
         where p.joueur_id = v_uid and p.cible_id is not null and p.fini and p.resultat is null
         order by p.fin_le desc limit 5) x),
    'derniers', (select coalesce(jsonb_agg(x order by x.fin desc), '[]'::jsonb) from (
        select p.id, p.resultat, p.score, p.lettre, p.elo_avant, p.elo_apres, p.vu, p.amical,
               coalesce(p2.fin_le, p.fin_le) as fin,
               (select coalesce(pseudo, 'Joueur') from joueurs
                 where id = coalesce(p2.joueur_id, s.joueur_id, p.cible_id)) as adversaire,
               coalesce(p2.score, s.score) as adversaire_score
          from rafale_parties p
          left join rafale_parties s  on s.id = p.source_id
          left join rafale_parties p2 on p2.source_id = p.id and p2.fini
         where p.joueur_id = v_uid and p.resultat is not null
         order by coalesce(p2.fin_le, p.fin_le) desc limit 8) x),
    'classement', (select coalesce(jsonb_agg(x order by x.elo desc), '[]'::jsonb) from (
        select r.joueur_id as id, coalesce(j.pseudo, 'Joueur') as pseudo, r.elo, r.parties,
               case when r.joueur_id = v_premier then 'As du volant' else rafale_rang(r.elo) end as rang,
               r.joueur_id = v_uid as moi
          from rafale_joueurs r join joueurs j on j.id = r.joueur_id
         where r.parties > 0
         order by r.elo desc limit 20) x));
end;
$$;

-- ---------------------------------------------------------------------
-- Droits
-- ---------------------------------------------------------------------
revoke all on function public.rafale_reglage(text)          from public, anon, authenticated;
revoke all on function public.rafale_lettres()              from public, anon, authenticated;
revoke all on function public.rafale_rang(integer)          from public, anon, authenticated;
revoke all on function public.rafale_norm(text)             from public, anon, authenticated;
revoke all on function public.rafale_gagner(bigint)         from public, anon, authenticated;
revoke all on function public.rafale_noter_quete(uuid)      from public, anon, authenticated;
revoke all on function public.rafale_clore(bigint)          from public, anon, authenticated;
revoke all on function public.rafale_rattraper(bigint)      from public, anon, authenticated;
revoke all on function public.rafale_vue(bigint)            from public, anon, authenticated;
revoke all on function public.rafale_lancer()               from public, anon;
revoke all on function public.rafale_partir(bigint)         from public, anon;
revoke all on function public.rafale_dire(bigint, text)     from public, anon;
revoke all on function public.rafale_terminer(bigint)       from public, anon;
revoke all on function public.rafale_resume(bigint)         from public, anon;
revoke all on function public.rafale_defier(uuid)           from public, anon;
revoke all on function public.rafale_relever(bigint)        from public, anon;
revoke all on function public.rafale_refuser(bigint)        from public, anon;
revoke all on function public.rafale_vu()                   from public, anon;
revoke all on function public.rafale_etat()                 from public, anon;
grant execute on function public.rafale_lancer()            to authenticated;
grant execute on function public.rafale_partir(bigint)      to authenticated;
grant execute on function public.rafale_dire(bigint, text)  to authenticated;
grant execute on function public.rafale_terminer(bigint)    to authenticated;
grant execute on function public.rafale_resume(bigint)      to authenticated;
grant execute on function public.rafale_defier(uuid)        to authenticated;
grant execute on function public.rafale_relever(bigint)     to authenticated;
grant execute on function public.rafale_refuser(bigint)     to authenticated;
grant execute on function public.rafale_vu()                to authenticated;
grant execute on function public.rafale_etat()              to authenticated;

-- ---------------------------------------------------------------------
-- Contrôle
-- ---------------------------------------------------------------------
select (select count(*) from public.rafale_noms) as noms_acceptes_environ_32000,
       public.rafale_norm('st-Étienne') = 'SAINTETIENNE' and public.rafale_norm('Ste Maxime') = 'SAINTEMAXIME'
         and public.rafale_norm('L''Haÿ-les-Roses') = 'LHAYLESROSES' as normalisation_ok,
       has_function_privilege('authenticated', 'public.rafale_dire(bigint,text)', 'execute') as dire_ouvert_doit_etre_true,
       has_function_privilege('anon', 'public.rafale_dire(bigint,text)', 'execute') as dire_anon_doit_etre_false,
       has_function_privilege('authenticated', 'public.rafale_clore(bigint)', 'execute') as clore_doit_etre_false;
