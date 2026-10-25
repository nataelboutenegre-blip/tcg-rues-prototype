-- ===========================================================================
--  TerraFront — Plus ou moins : entraînement et duels classés (25 octobre 2026)
--  Aperçu validé : minuteur de 8 s, gains comme le Radar (20 pts par
--  victoire, 5 victoires payées par jour), rangs Arpenteur, Cartographe,
--  Géomètre, Recenseur, Préfet.
--
--  ENTRAÎNEMENT : pom_entrainement() donne 10 duels tirés au hasard, avec
--  les populations (rien n'est enregistré, rien ne se gagne).
--
--  DUEL CLASSÉ (calqué sur la Rafale)
--  - « Lancer » cherche une partie classée finie d'un autre joueur, d'Elo
--    proche, pas encore affrontée : on joue SES 10 duels, et le duel se
--    règle à la fin. Sinon 10 duels neufs, et la partie attend.
--  - Score : bonnes réponses ; à égalité, le moins de temps au total.
--  - Contre la triche : la paire n'est donnée qu'au moment de la question
--    (pom_d_question), le minuteur est celui du serveur (8 s + 1,5 s de
--    marge) ; trop tard = faux. Redemander la question ne relance pas le
--    minuteur. La population n'arrive qu'avec la réponse.
--  Pas de défi entre amis pour l'instant.
--  Tables neuves (pom_joueurs, pom_duels). Rejouable. Contrôle à la fin.
-- ===========================================================================
begin;

create table if not exists public.pom_joueurs(
  joueur_id  uuid primary key references public.joueurs(id) on delete cascade,
  elo        integer not null default 1000,
  parties    integer not null default 0,
  victoires  integer not null default 0,
  maj        timestamptz not null default now()
);
create table if not exists public.pom_duels(
  id          bigserial primary key,
  joueur_id   uuid not null references public.joueurs(id) on delete cascade,
  duels       jsonb not null,                     -- [{"a": code, "b": code}] x 10
  source_id   bigint references public.pom_duels(id) on delete set null,
  question_le timestamptz,                        -- quand la question en cours a été donnée
  reponses    smallint[] not null default '{}',   -- 0 / 1, ou -1 = trop tard
  temps       integer[] not null default '{}',    -- ms par réponse
  justes      integer not null default 0,
  temps_total integer not null default 0,
  fini        boolean not null default false,
  utilisee    boolean not null default false,
  elo_avant   integer,
  elo_apres   integer,
  resultat    text,                               -- victoire / defaite / egalite
  vu          boolean not null default true,
  gain        integer,
  gain_le     timestamptz,
  cree_le     timestamptz not null default now(),
  fin_le      timestamptz
);
create index if not exists pom_duels_joueur on public.pom_duels(joueur_id, cree_le desc);
create index if not exists pom_duels_dispo  on public.pom_duels(fini, utilisee) where source_id is null;
create index if not exists pom_duels_source on public.pom_duels(source_id) where source_id is not null;
alter table public.pom_joueurs enable row level security;
alter table public.pom_duels   enable row level security;
revoke all on public.pom_joueurs, public.pom_duels from public, anon, authenticated;
revoke all on sequence public.pom_duels_id_seq from public, anon, authenticated;

create or replace function public.pom_reglage(p text)
returns integer language sql immutable set search_path to 'public'
as $$ select case p when 'ms' then 8000 when 'marge_ms' then 1500 when 'k' then 24
                    when 'gain' then 20 when 'gains_jour' then 5 end; $$;

create or replace function public.pom_rang(p_elo integer)
returns text language sql immutable set search_path to 'public'
as $$ select case when p_elo >= 1300 then 'Préfet' when p_elo >= 1200 then 'Recenseur'
                  when p_elo >= 1100 then 'Géomètre' when p_elo >= 1000 then 'Cartographe'
                  else 'Arpenteur' end; $$;

-- ---------------------------------------------------------------- entraînement
create or replace function public.pom_entrainement()
returns jsonb language plpgsql volatile security definer set search_path to 'public'
as $$
begin
  if auth.uid() is null then raise exception 'Connecte-toi pour jouer.'; end if;
  return (select jsonb_agg(jsonb_build_object('i', e.i - 1,
                   'a', pom_carte(e.x ->> 'a', true), 'b', pom_carte(e.x ->> 'b', true)) order by e.i)
            from jsonb_array_elements(pom_generer()) with ordinality e(x, i));
end; $$;

-- ---------------------------------------------------------------- internes
create or replace function public.pom_d_gagner(p_id bigint)
returns void language plpgsql security definer set search_path to 'public'
as $$
declare v_joueur uuid; v_deja int;
        v_minuit timestamptz := date_trunc('day', now() at time zone 'Europe/Paris') at time zone 'Europe/Paris';
begin
  select joueur_id into v_joueur from pom_duels where id = p_id and gain is null;
  if v_joueur is null then return; end if;
  select count(*) into v_deja from pom_duels where joueur_id = v_joueur and gain > 0 and gain_le >= v_minuit;
  if v_deja >= pom_reglage('gains_jour') then return; end if;
  update pom_duels set gain = pom_reglage('gain'), gain_le = now() where id = p_id;
  perform set_config('terrafront.motif', 'pom_duel', true);
  update joueurs set solde = coalesce(solde, 0) + pom_reglage('gain') where id = v_joueur;
end; $$;

create or replace function public.pom_d_clore(p_id bigint)
returns void language plpgsql security definer set search_path to 'public'
as $$
declare p pom_duels; s pom_duels; v_res numeric; ea int; eb int; va int; vb int; v_att numeric;
        v_k int := pom_reglage('k');
begin
  select * into p from pom_duels where id = p_id for update;
  if p.fini then return; end if;
  update pom_duels set fini = true, fin_le = now(), question_le = null where id = p_id;
  if p.source_id is null then return; end if;
  select * into s from pom_duels where id = p.source_id for update;
  if s.id is null then return; end if;
  v_res := case when p.justes > s.justes then 1 when p.justes < s.justes then 0
                when p.temps_total < s.temps_total then 1 when p.temps_total > s.temps_total then 0 else 0.5 end;
  insert into pom_joueurs(joueur_id) values (p.joueur_id), (s.joueur_id) on conflict do nothing;
  select elo into ea from pom_joueurs where joueur_id = p.joueur_id for update;
  select elo into eb from pom_joueurs where joueur_id = s.joueur_id for update;
  v_att := 1 / (1 + power(10, (eb - ea) / 400.0));
  va := ea + round(v_k * (v_res - v_att));
  vb := eb + round(v_k * ((1 - v_res) - (1 - v_att)));
  update pom_joueurs set elo = va, parties = parties + 1, victoires = victoires + (v_res = 1)::int, maj = now() where joueur_id = p.joueur_id;
  update pom_joueurs set elo = vb, parties = parties + 1, victoires = victoires + (v_res = 0)::int, maj = now() where joueur_id = s.joueur_id;
  update pom_duels set elo_avant = ea, elo_apres = va, vu = true,
         resultat = case v_res when 1 then 'victoire' when 0 then 'defaite' else 'egalite' end where id = p.id;
  update pom_duels set elo_avant = eb, elo_apres = vb, vu = false,
         resultat = case v_res when 0 then 'victoire' when 1 then 'defaite' else 'egalite' end where id = s.id;
  if v_res = 1 then perform pom_d_gagner(p.id); elsif v_res = 0 then perform pom_d_gagner(s.id); end if;
end; $$;

-- une question restée sans réponse au-delà du minuteur compte faux
create or replace function public.pom_d_rattraper(p_id bigint)
returns void language plpgsql security definer set search_path to 'public'
as $$
declare p pom_duels; n int;
begin
  select * into p from pom_duels where id = p_id for update;
  if p.id is null or p.fini or p.question_le is null then return; end if;
  if now() <= p.question_le + make_interval(secs => (pom_reglage('ms') + pom_reglage('marge_ms')) / 1000.0) then return; end if;
  n := coalesce(array_length(p.reponses, 1), 0);
  update pom_duels set reponses = reponses || (-1)::smallint, temps = temps || pom_reglage('ms'),
         temps_total = temps_total + pom_reglage('ms'), question_le = null where id = p_id;
  if n + 1 >= jsonb_array_length(p.duels) then perform pom_d_clore(p_id); end if;
end; $$;

create or replace function public.pom_d_vue(p_id bigint)
returns jsonb language plpgsql security definer set search_path to 'public'
as $$
declare p pom_duels; s pom_duels; n int; v_adv jsonb := null;
begin
  select * into p from pom_duels where id = p_id;
  if p.source_id is not null then select * into s from pom_duels where id = p.source_id;
  elsif p.fini then select * into s from pom_duels where source_id = p.id and fini limit 1; end if;
  n := coalesce(array_length(p.reponses, 1), 0);
  if s.id is not null then
    v_adv := jsonb_build_object(
      'pseudo', (select coalesce(pseudo, 'Joueur') from joueurs where id = s.joueur_id),
      'elo', (select elo from pom_joueurs where joueur_id = s.joueur_id),
      'justes', case when p.fini and s.fini then s.justes end,
      'temps_total', case when p.fini and s.fini then s.temps_total end);
  end if;
  return jsonb_build_object(
    'id', p.id, 'n', n, 'total', jsonb_array_length(p.duels), 'ms', pom_reglage('ms'),
    'reponses', to_jsonb(p.reponses), 'justes', p.justes, 'temps_total', p.temps_total, 'fini', p.fini,
    -- les duels déjà joués, avec les populations
    'joues', (select coalesce(jsonb_agg(jsonb_build_object('a', pom_carte(e.x ->> 'a', true), 'b', pom_carte(e.x ->> 'b', true)) order by e.i), '[]'::jsonb)
                from jsonb_array_elements(p.duels) with ordinality e(x, i) where e.i <= n),
    'adversaire', v_adv,
    'en_attente', p.fini and p.source_id is null and p.resultat is null,
    'resultat', p.resultat, 'elo_avant', p.elo_avant, 'elo_apres', p.elo_apres, 'gain', p.gain);
end; $$;

-- ---------------------------------------------------------------- ce que le jeu appelle
create or replace function public.pom_d_lancer()
returns jsonb language plpgsql security definer set search_path to 'public'
as $$
declare v_uid uuid := auth.uid(); v_id bigint; v_elo int; s pom_duels;
begin
  if v_uid is null then raise exception 'Connecte-toi pour jouer.'; end if;
  perform pg_advisory_xact_lock(hashtextextended('pom' || v_uid::text, 7));
  select id into v_id from pom_duels where joueur_id = v_uid and not fini order by id desc limit 1;
  if v_id is not null then
    perform pom_d_rattraper(v_id);
    if not (select fini from pom_duels where id = v_id) then return pom_d_vue(v_id); end if;
  end if;
  insert into pom_joueurs(joueur_id) values (v_uid) on conflict do nothing;
  select elo into v_elo from pom_joueurs where joueur_id = v_uid;
  select p.* into s from pom_duels p left join pom_joueurs r on r.joueur_id = p.joueur_id
   where p.source_id is null and p.fini and not p.utilisee and p.joueur_id <> v_uid
   order by exists (select 1 from pom_duels m join pom_duels ms on ms.id = m.source_id
                     where m.joueur_id = v_uid and ms.joueur_id = p.joueur_id and m.cree_le > now() - interval '24 hours'),
            abs(coalesce(r.elo, 1000) - v_elo), p.fin_le
   limit 1 for update of p skip locked;
  if s.id is not null then
    update pom_duels set utilisee = true where id = s.id;
    insert into pom_duels(joueur_id, duels, source_id) values (v_uid, s.duels, s.id) returning id into v_id;
  else
    insert into pom_duels(joueur_id, duels) values (v_uid, pom_generer()) returning id into v_id;
  end if;
  return pom_d_vue(v_id);
end; $$;

-- la question en cours : la paire, sans les populations ; le minuteur part ici
create or replace function public.pom_d_question(p_id bigint)
returns jsonb language plpgsql security definer set search_path to 'public'
as $$
declare v_uid uuid := auth.uid(); p pom_duels; n int;
begin
  if v_uid is null then raise exception 'Connecte-toi pour jouer.'; end if;
  perform pom_d_rattraper(p_id);
  select * into p from pom_duels where id = p_id and joueur_id = v_uid for update;
  if not found then raise exception 'Partie introuvable.'; end if;
  if p.fini then return jsonb_build_object('fini', true, 'vue', pom_d_vue(p_id)); end if;
  n := coalesce(array_length(p.reponses, 1), 0);
  if p.question_le is null then update pom_duels set question_le = now() where id = p_id returning * into p; end if;
  return jsonb_build_object('fini', false, 'i', n, 'total', jsonb_array_length(p.duels),
    'reste_ms', greatest(0, round(pom_reglage('ms') - extract(epoch from (now() - p.question_le)) * 1000)),
    'a', pom_carte(p.duels -> n ->> 'a', false), 'b', pom_carte(p.duels -> n ->> 'b', false));
end; $$;

create or replace function public.pom_d_repondre(p_id bigint, p_i integer, p_choix integer)
returns jsonb language plpgsql security definer set search_path to 'public'
as $$
declare v_uid uuid := auth.uid(); p pom_duels; n int; pa int; pb int; v_ms int; v_juste boolean; v_tard boolean;
begin
  if v_uid is null then raise exception 'Connecte-toi pour jouer.'; end if;
  if p_choix is null or p_choix not in (0, 1) then raise exception 'Choix inconnu'; end if;
  select * into p from pom_duels where id = p_id and joueur_id = v_uid for update;
  if not found then raise exception 'Partie introuvable.'; end if;
  if p.fini then raise exception 'Cette partie est finie.'; end if;
  n := coalesce(array_length(p.reponses, 1), 0);
  if p_i is distinct from n or p.question_le is null then raise exception 'Ce duel est déjà joué'; end if;
  v_ms := round(extract(epoch from (now() - p.question_le)) * 1000);
  v_tard := v_ms > pom_reglage('ms') + pom_reglage('marge_ms');
  select population into pa from communes where code = p.duels -> n ->> 'a';
  select population into pb from communes where code = p.duels -> n ->> 'b';
  v_juste := not v_tard and ((p_choix = 0 and pa > pb) or (p_choix = 1 and pb > pa));
  update pom_duels set reponses = reponses || (case when v_tard then -1 else p_choix end)::smallint,
         temps = temps || least(v_ms, pom_reglage('ms')),
         temps_total = temps_total + least(v_ms, pom_reglage('ms')),
         justes = justes + v_juste::int, question_le = null
   where id = p_id;
  if n + 1 >= jsonb_array_length(p.duels) then perform pom_d_clore(p_id); end if;
  return jsonb_build_object('juste', v_juste, 'tard', v_tard, 'pop_a', pa, 'pop_b', pb, 'ms', least(v_ms, pom_reglage('ms')),
                            'fin', n + 1 >= jsonb_array_length(p.duels), 'vue', pom_d_vue(p_id));
end; $$;

create or replace function public.pom_d_etat()
returns jsonb language plpgsql security definer set search_path to 'public'
as $$
declare v_uid uuid := auth.uid(); v_elo int; v_parties int; v_en_cours bigint;
        v_minuit timestamptz := date_trunc('day', now() at time zone 'Europe/Paris') at time zone 'Europe/Paris';
begin
  if v_uid is null then raise exception 'Connecte-toi pour jouer.'; end if;
  select elo, parties into v_elo, v_parties from pom_joueurs where joueur_id = v_uid;
  v_elo := coalesce(v_elo, 1000);
  select id into v_en_cours from pom_duels where joueur_id = v_uid and not fini order by id desc limit 1;
  if v_en_cours is not null then perform pom_d_rattraper(v_en_cours); end if;
  update pom_duels set vu = true where joueur_id = v_uid and not vu;
  return jsonb_build_object(
    'elo', v_elo, 'parties', coalesce(v_parties, 0), 'rang', pom_rang(v_elo),
    'en_cours', (select id from pom_duels where joueur_id = v_uid and not fini order by id desc limit 1),
    'gains_jour', (select count(*) from pom_duels where joueur_id = v_uid and gain > 0 and gain_le >= v_minuit),
    'gains_max', pom_reglage('gains_jour'),
    'en_attente', (select count(*) from pom_duels where joueur_id = v_uid and fini and source_id is null and resultat is null),
    'derniers', (select coalesce(jsonb_agg(x order by x.fin desc), '[]'::jsonb) from (
        select p.resultat, p.justes, p.elo_avant, p.elo_apres, coalesce(p2.fin_le, p.fin_le) as fin,
               (select coalesce(pseudo, 'Joueur') from joueurs where id = coalesce(p2.joueur_id, s.joueur_id)) as adversaire,
               coalesce(p2.justes, s.justes) as adversaire_justes
          from pom_duels p
          left join pom_duels s on s.id = p.source_id
          left join pom_duels p2 on p2.source_id = p.id and p2.fini
         where p.joueur_id = v_uid and p.resultat is not null
         order by coalesce(p2.fin_le, p.fin_le) desc limit 5) x),
    'classement', (select coalesce(jsonb_agg(x order by x.elo desc), '[]'::jsonb) from (
        select coalesce(j.pseudo, 'Joueur') as pseudo, r.elo, pom_rang(r.elo) as rang, r.joueur_id = v_uid as moi
          from pom_joueurs r join joueurs j on j.id = r.joueur_id
         where r.parties > 0 order by r.elo desc limit 10) x));
end; $$;

revoke all on function public.pom_reglage(text)        from public, anon, authenticated;
revoke all on function public.pom_rang(integer)        from public, anon, authenticated;
revoke all on function public.pom_d_gagner(bigint)     from public, anon, authenticated;
revoke all on function public.pom_d_clore(bigint)      from public, anon, authenticated;
revoke all on function public.pom_d_rattraper(bigint)  from public, anon, authenticated;
revoke all on function public.pom_d_vue(bigint)        from public, anon, authenticated;
revoke all on function public.pom_entrainement()       from public, anon;
revoke all on function public.pom_d_lancer()           from public, anon;
revoke all on function public.pom_d_question(bigint)   from public, anon;
revoke all on function public.pom_d_repondre(bigint, integer, integer) from public, anon;
revoke all on function public.pom_d_etat()             from public, anon;
grant execute on function public.pom_entrainement()    to authenticated;
grant execute on function public.pom_d_lancer()        to authenticated;
grant execute on function public.pom_d_question(bigint) to authenticated;
grant execute on function public.pom_d_repondre(bigint, integer, integer) to authenticated;
grant execute on function public.pom_d_etat()          to authenticated;

commit;

select to_regclass('public.pom_duels') is not null                     as tables_ok,
       to_regprocedure('public.pom_d_lancer()') is not null             as duel_ok,
       to_regprocedure('public.pom_entrainement()') is not null         as entrainement_ok,
       public.pom_rang(1000)                                           as rang_depart;
