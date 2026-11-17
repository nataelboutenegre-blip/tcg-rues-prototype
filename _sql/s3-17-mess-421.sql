-- ===========================================================================
--  s3-17 (17/11/2026) — Le Mess : le 421 (troisième jeu)
--  3 dés tirés par le serveur ; après le premier lancer, le joueur peut relancer
--  deux fois les dés qu'il ne garde pas, ou s'arrêter. Seule la dernière
--  combinaison compte. 2 tickets la partie.
--  Lots (config_jeu 'mess'.des, modifiables) :
--    421 du premier coup (1 chance sur 36) : 1 paquet Terra + 5 énergie
--    421 en relançant 3 énergie · trois as 6 énergie · autre brelan 3 énergie
--    suite 15 TP · paire, nénette (2-2-1), rien : rien
--  L'énergie passe par la ration du Mess (mess_donner : 25 par jour, au-delà en TP).
--  Calcul (jeu optimal, programmation dynamique) : ≈ 16 TP-équivalent par partie,
--  ≈ 8 TP par ticket, comme la Machine à chiffrer.
--  Contrôle attendu (dernière ligne) : true | true | true
-- ===========================================================================

update public.config_jeu
   set valeur = (valeur::jsonb || jsonb_build_object('des', jsonb_build_object(
         'prix', 2,
         'lots', jsonb_build_object(
           '421sec', jsonb_build_object('terra', 1, 'energie', 5),
           '421',    jsonb_build_object('energie', 3),
           'as',     jsonb_build_object('energie', 6),
           'brelan', jsonb_build_object('energie', 3),
           'suite',  jsonb_build_object('tp', 15)))))::text
 where cle = 'mess' and not (valeur::jsonb ? 'des');

create table if not exists public.mess_421_parties (
  id bigserial primary key,
  joueur_id uuid not null references public.joueurs(id) on delete cascade,
  le timestamptz not null default now(),
  jour date not null,
  mise integer not null,
  des integer[] not null,
  lancer integer not null default 1,
  historique jsonb not null default '[]'::jsonb,
  en_cours boolean not null default true,
  resultat text,
  gain jsonb,
  fini_le timestamptz
);
create unique index if not exists mess_421_une_en_cours on public.mess_421_parties (joueur_id) where en_cours;
alter table public.mess_421_parties enable row level security;   -- seulement par les fonctions

-- la combinaison de trois dés (« 421sec » est décidé par l'appelant)
create or replace function public.mess_421_combi(p_des integer[])
 returns text language sql immutable set search_path to 'public'
as $f$
  with s as (select array_agg(d order by d) a from unnest(p_des) d)
  select case
    when a = array[1,2,4] then '421'
    when a = array[1,1,1] then 'as'
    when a[1] = a[3] then 'brelan'
    when a in (array[1,2,3], array[2,3,4], array[3,4,5], array[4,5,6]) then 'suite'
    when a = array[1,2,2] then 'nenette'
    when a[1] = a[2] or a[2] = a[3] then 'paire'
    else 'rien' end
  from s;
$f$;

create or replace function public.mess_421_vue(p_id bigint)
 returns jsonb language sql stable security definer set search_path to 'public'
as $f$
  select jsonb_build_object('id', p.id, 'en_cours', p.en_cours, 'lancer', p.lancer, 'des', to_jsonb(p.des),
           'resultat', p.resultat, 'gain', coalesce(p.gain, '{}'::jsonb),
           'tickets', coalesce((select m.tickets from mess_joueurs m where m.joueur_id = p.joueur_id), 0))
    from mess_421_parties p where p.id = p_id;
$f$;

-- la fin d'une partie : la combinaison, le lot, la ration
create or replace function public.mess_421_finir(p_id bigint)
 returns void language plpgsql security definer set search_path to 'public'
as $f$
declare
  p record; c jsonb := mess_cfg() -> 'des';
  v_res text; l jsonb; v_tp integer := 0; v_terra integer := 0; v_ration jsonb;
begin
  select * into p from mess_421_parties where id = p_id and en_cours for update;
  if p.id is null then return; end if;
  v_res := mess_421_combi(p.des);
  if v_res = '421' and p.lancer = 1 then v_res := '421sec'; end if;
  l := c -> 'lots' -> v_res;
  if l is not null then
    v_tp := greatest(0, coalesce((l ->> 'tp')::int, 0));
    v_terra := greatest(0, coalesce((l ->> 'terra')::int, 0));
  end if;
  if v_tp > 0 then
    perform set_config('terrafront.motif', 'mess', true);
    update joueurs set solde = coalesce(solde, 0) + v_tp where id = p.joueur_id;
  end if;
  if v_terra > 0 then
    update joueurs set terra_jetons = terra_jetons_lire(terra_jetons, terra_jetons_maj) + v_terra, terra_jetons_maj = now() where id = p.joueur_id;
  end if;
  v_ration := case when l is not null then mess_donner(p.joueur_id, coalesce((l ->> 'energie')::int, 0), coalesce((l ->> 'lingots')::int, 0)) else '{}'::jsonb end;
  update mess_421_parties
     set en_cours = false, fini_le = now(), resultat = v_res,
         gain = jsonb_strip_nulls(jsonb_build_object('tp', nullif(v_tp + coalesce((v_ration ->> 'tp_repli')::int, 0), 0), 'terra', nullif(v_terra, 0),
                  'energie', (v_ration -> 'energie'), 'lingots', (v_ration -> 'lingots')))
   where id = p_id;
end $f$;

create or replace function public.mess_421_lancer()
 returns jsonb language plpgsql security definer set search_path to 'public'
as $f$
declare
  v_uid uuid := auth.uid(); c jsonb := mess_cfg() -> 'des';
  v_prix integer := greatest(1, coalesce((c ->> 'prix')::int, 2));
  v_id bigint; v_tk integer; v_des integer[];
begin
  if v_uid is null then raise exception 'Non connecté'; end if;
  if not mess_ouvert(v_uid) then raise exception 'Le Mess ouvre avec la saison 3'; end if;
  if c is null then raise exception 'Le 421 n''est pas réglé'; end if;
  perform 1 from joueurs where id = v_uid for update;
  select id into v_id from mess_421_parties where joueur_id = v_uid and en_cours;
  if v_id is not null then return mess_421_vue(v_id); end if;   -- une partie en cours reprend, sans ticket
  select tickets into v_tk from mess_joueurs where joueur_id = v_uid for update;
  if coalesce(v_tk, 0) < v_prix then
    raise exception 'Il te faut % tickets : ils se gagnent en duel classé (Radar, Rafale, Plus ou moins)', v_prix;
  end if;
  v_des := array[1 + floor(random() * 6)::int, 1 + floor(random() * 6)::int, 1 + floor(random() * 6)::int];
  update mess_joueurs set tickets = tickets - v_prix, joues = joues + 1, maj = now() where joueur_id = v_uid;
  insert into mess_421_parties (joueur_id, jour, mise, des, historique)
  values (v_uid, (now() at time zone 'Europe/Paris')::date, v_prix, v_des, jsonb_build_array(to_jsonb(v_des)))
  returning id into v_id;
  -- 421 du premier coup : la partie s'arrête là, rien à relancer
  if mess_421_combi(v_des) = '421' then perform mess_421_finir(v_id); end if;
  return mess_421_vue(v_id);
end $f$;

create or replace function public.mess_421_relancer(p_garder boolean[])
 returns jsonb language plpgsql security definer set search_path to 'public'
as $f$
declare v_uid uuid := auth.uid(); p record; v_des integer[]; i integer;
begin
  if v_uid is null then raise exception 'Non connecté'; end if;
  select * into p from mess_421_parties where joueur_id = v_uid and en_cours for update;
  if p.id is null then raise exception 'Aucune partie en cours : lance les dés'; end if;
  if p.lancer >= 3 then perform mess_421_finir(p.id); return mess_421_vue(p.id); end if;
  if coalesce(array_length(p_garder, 1), 0) <> 3 then raise exception 'Choisis les dés à garder'; end if;
  if p_garder[1] and p_garder[2] and p_garder[3] then raise exception 'Garde au plus deux dés pour relancer'; end if;
  v_des := p.des;
  for i in 1..3 loop
    if not coalesce(p_garder[i], false) then v_des[i] := 1 + floor(random() * 6)::int; end if;
  end loop;
  update mess_421_parties set des = v_des, lancer = lancer + 1, historique = historique || jsonb_build_array(to_jsonb(v_des))
   where id = p.id;
  if p.lancer + 1 >= 3 then perform mess_421_finir(p.id); end if;   -- troisième lancer : fin
  return mess_421_vue(p.id);
end $f$;

create or replace function public.mess_421_arreter()
 returns jsonb language plpgsql security definer set search_path to 'public'
as $f$
declare v_uid uuid := auth.uid(); v_id bigint;
begin
  if v_uid is null then raise exception 'Non connecté'; end if;
  select id into v_id from mess_421_parties where joueur_id = v_uid and en_cours;
  if v_id is null then raise exception 'Aucune partie en cours'; end if;
  perform mess_421_finir(v_id);
  return mess_421_vue(v_id);
end $f$;

revoke all on function public.mess_421_combi(integer[]) from public, anon;
revoke all on function public.mess_421_vue(bigint) from public, anon, authenticated;
revoke all on function public.mess_421_finir(bigint) from public, anon, authenticated;
revoke all on function public.mess_421_lancer() from public, anon;
revoke all on function public.mess_421_relancer(boolean[]) from public, anon;
revoke all on function public.mess_421_arreter() from public, anon;
grant execute on function public.mess_421_lancer() to authenticated;
grant execute on function public.mess_421_relancer(boolean[]) to authenticated;
grant execute on function public.mess_421_arreter() to authenticated;

-- mess_etat : + le réglage du 421 et la partie en cours
do $do$
declare d text; a text;
begin
  d := pg_get_functiondef('public.mess_etat()'::regprocedure);
  if position('s3-17' in d) = 0 then
    a := $a$    'rec', (select mess_rec_vue(p.id) from mess_rec_parties p where p.joueur_id = auth.uid() and p.en_cours),$a$;
    if (length(d) - length(replace(d, a, ''))) / length(a) <> 1 then raise exception 's3-17 : mess_etat a changé, repère introuvable'; end if;
    d := replace(d, a, a || $b$
    'des', mess_cfg() -> 'des',   -- s3-17
    'de421', (select mess_421_vue(p.id) from mess_421_parties p where p.joueur_id = auth.uid() and p.en_cours),$b$);
    execute d;
  end if;
end $do$;

select exists (select 1 from pg_proc where proname = 'mess_421_lancer') as fonctions,
       (select valeur::jsonb ? 'des' from config_jeu where cle = 'mess') as reglage,
       position('s3-17' in pg_get_functiondef('public.mess_etat()'::regprocedure)) > 0 as mess_etat;
