-- s3-11 (13/11/2026) : Le Mess, deuxième jeu : le Recensement (« Parfait oui ! », 19 h 52 UTC).
-- 2 tickets. Le Préfet recense d'abord (noms, populations et total visibles), entre 30 000 et 50 000 habitants.
-- Le joueur tire des communes une à une : nom et département visibles, population cachée (gardée au serveur).
-- « Clore » : on révèle. Gagné si son total dépasse celui du Préfet sans franchir 50 000 : 50 TP ;
-- entre 47 500 et 50 000 : « Recensement parfait », 1 paquet Terra. Au-delà de 50 000, la partie s'arrête seule.
-- Communes de 3 000 à 60 000 habitants, tirées par tranche (même chance pour chaque tranche).
-- Simulation : environ 15 % de victoires en tirant au hasard, 41 % en connaissant toutes les populations.

update config_jeu set valeur = jsonb_set(valeur::jsonb, '{recensement}', $j${
  "prix": 2,
  "plafond": 50000,
  "prefet_min": 30000,
  "parfait": 47500,
  "max_communes": 8,
  "tranches": [[3000, 5000], [5000, 10000], [10000, 20000], [20000, 35000], [35000, 60000]],
  "lots": {
    "gagne":   { "nom": "Recensé !",           "tp": 50 },
    "parfait": { "nom": "Recensement parfait", "terra": 1 }
  }
}$j$::jsonb)::text
 where cle = 'mess' and not (valeur::jsonb ? 'recensement');

create table if not exists public.mess_rec_parties (
  id bigserial primary key,
  joueur_id uuid not null references public.joueurs(id) on delete cascade,
  le timestamptz not null default now(),
  jour date not null,
  mise integer not null,
  prefet jsonb not null,
  joueur jsonb not null default '[]'::jsonb,
  en_cours boolean not null default true,
  resultat text,
  gain jsonb not null default '{}'::jsonb,
  fini_le timestamptz
);
create unique index if not exists mess_rec_une_en_cours on public.mess_rec_parties (joueur_id) where en_cours;
create index if not exists mess_rec_joueur on public.mess_rec_parties (joueur_id, le desc);
alter table public.mess_rec_parties enable row level security;
revoke all on public.mess_rec_parties from anon, authenticated;

-- une commune au hasard : une tranche au hasard, puis une commune de la tranche (sans celles déjà tirées)
create or replace function public.mess_rec_commune(p_sauf text[])
 returns jsonb language plpgsql volatile security definer set search_path to 'public'
as $f$
declare
  t jsonb := (mess_cfg() -> 'recensement' -> 'tranches');
  k integer;
  r record;
begin
  k := floor(random() * jsonb_array_length(t))::int;
  select c.code, c.nom, c.departement, c.population into r
    from communes c
   where c.population >= (t -> k ->> 0)::int and c.population < (t -> k ->> 1)::int
     and not (c.code = any(coalesce(p_sauf, '{}')))
   order by random() limit 1;
  return jsonb_build_object('code', r.code, 'nom', r.nom, 'dept', r.departement, 'pop', r.population);
end;
$f$;

-- ce que voit le joueur : les populations de son registre seulement une fois la partie finie
create or replace function public.mess_rec_vue(p_id bigint)
 returns jsonb language sql stable security definer set search_path to 'public'
as $f$
  select jsonb_build_object(
    'id', p.id, 'en_cours', p.en_cours, 'resultat', p.resultat, 'gain', p.gain, 'mise', p.mise,
    'prefet', p.prefet,
    'prefet_total', (select coalesce(sum((x ->> 'pop')::int), 0) from jsonb_array_elements(p.prefet) x),
    'joueur', (select coalesce(jsonb_agg(case when p.en_cours then x - 'pop' - 'code' else x end order by o), '[]'::jsonb)
                 from jsonb_array_elements(p.joueur) with ordinality as e(x, o)),
    'joueur_total', case when p.en_cours then null else (select coalesce(sum((x ->> 'pop')::int), 0) from jsonb_array_elements(p.joueur) x) end,
    'tickets', coalesce((select m.tickets from mess_joueurs m where m.joueur_id = p.joueur_id), 0))
  from mess_rec_parties p where p.id = p_id;
$f$;

-- la fin d'une partie : compter, payer, révéler
create or replace function public.mess_rec_finir(p_id bigint)
 returns void language plpgsql security definer set search_path to 'public'
as $f$
declare
  p record;
  c jsonb := mess_cfg() -> 'recensement';
  tp integer; tj integer; v_res text; l jsonb; v_tp integer := 0; v_terra integer := 0;
begin
  select * into p from mess_rec_parties where id = p_id and en_cours for update;
  if p.id is null then return; end if;
  select coalesce(sum((x ->> 'pop')::int), 0) into tp from jsonb_array_elements(p.prefet) x;
  select coalesce(sum((x ->> 'pop')::int), 0) into tj from jsonb_array_elements(p.joueur) x;
  v_res := case when tj > (c ->> 'plafond')::int then 'depasse'
                when tj <= tp then 'perdu'
                when tj >= (c ->> 'parfait')::int then 'parfait'
                else 'gagne' end;
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
  update mess_rec_parties
     set en_cours = false, fini_le = now(), resultat = v_res,
         gain = jsonb_strip_nulls(jsonb_build_object('tp', nullif(v_tp, 0), 'terra', nullif(v_terra, 0)))
   where id = p_id;
end;
$f$;

-- lancer une partie (ou reprendre celle en cours)
create or replace function public.mess_rec_lancer()
 returns jsonb language plpgsql security definer set search_path to 'public'
as $f$
declare
  v_uid uuid := auth.uid();
  c jsonb := mess_cfg() -> 'recensement';
  v_prix integer := greatest(1, coalesce((c ->> 'prix')::int, 2));
  v_id bigint; v_tk integer;
  pr jsonb; s integer; essai integer := 0; x jsonb; codes text[];
begin
  if v_uid is null then raise exception 'Non connecté'; end if;
  if not mess_ouvert(v_uid) then raise exception 'Le Mess ouvre avec la saison 3'; end if;
  if c is null then raise exception 'Le Recensement n''est pas réglé'; end if;
  perform 1 from joueurs where id = v_uid for update;
  select id into v_id from mess_rec_parties where joueur_id = v_uid and en_cours;
  if v_id is not null then return mess_rec_vue(v_id); end if;   -- on reprend la partie laissée en cours
  select tickets into v_tk from mess_joueurs where joueur_id = v_uid for update;
  if coalesce(v_tk, 0) < v_prix then
    raise exception 'Il te faut % tickets : ils se gagnent en duel classé (Radar, Rafale, Plus ou moins)', v_prix;
  end if;
  -- le Préfet : jusqu'à au moins prefet_min, sans dépasser le plafond (sinon il recommence)
  loop
    essai := essai + 1; pr := '[]'::jsonb; s := 0; codes := '{}';
    while s < (c ->> 'prefet_min')::int loop
      x := mess_rec_commune(codes);
      pr := pr || jsonb_build_array(x); s := s + (x ->> 'pop')::int; codes := codes || (x ->> 'code');
    end loop;
    exit when s <= (c ->> 'plafond')::int or essai >= 30;
  end loop;
  x := mess_rec_commune(codes);
  update mess_joueurs set tickets = tickets - v_prix, joues = joues + 1, maj = now() where joueur_id = v_uid;
  insert into mess_rec_parties (joueur_id, jour, mise, prefet, joueur)
  values (v_uid, (now() at time zone 'Europe/Paris')::date, v_prix, pr, jsonb_build_array(x))
  returning id into v_id;
  return mess_rec_vue(v_id);
end;
$f$;

-- « Recenser » : une commune de plus (la partie s'arrête seule au-delà du plafond)
create or replace function public.mess_rec_tirer()
 returns jsonb language plpgsql security definer set search_path to 'public'
as $f$
declare
  v_uid uuid := auth.uid();
  c jsonb := mess_cfg() -> 'recensement';
  p record; x jsonb; codes text[]; s integer;
begin
  if v_uid is null then raise exception 'Non connecté'; end if;
  select * into p from mess_rec_parties where joueur_id = v_uid and en_cours for update;
  if p.id is null then raise exception 'Pas de recensement en cours'; end if;
  if jsonb_array_length(p.joueur) >= coalesce((c ->> 'max_communes')::int, 8) then
    raise exception 'Ton registre est plein : clos-le';
  end if;
  select array_agg(e ->> 'code') into codes from (select jsonb_array_elements(p.prefet || p.joueur) e) z;
  x := mess_rec_commune(codes);
  update mess_rec_parties set joueur = joueur || jsonb_build_array(x) where id = p.id;
  select coalesce(sum((e ->> 'pop')::int), 0) into s from jsonb_array_elements(p.joueur || jsonb_build_array(x)) e;
  if s > (c ->> 'plafond')::int then perform mess_rec_finir(p.id); end if;
  return mess_rec_vue(p.id);
end;
$f$;

-- « Clore »
create or replace function public.mess_rec_clore()
 returns jsonb language plpgsql security definer set search_path to 'public'
as $f$
declare v_uid uuid := auth.uid(); v_id bigint;
begin
  if v_uid is null then raise exception 'Non connecté'; end if;
  select id into v_id from mess_rec_parties where joueur_id = v_uid and en_cours for update;
  if v_id is null then raise exception 'Pas de recensement en cours'; end if;
  perform mess_rec_finir(v_id);
  return mess_rec_vue(v_id);
end;
$f$;

-- mess_etat : + le Recensement (réglages et partie en cours)
create or replace function public.mess_etat()
 returns jsonb language sql stable security definer set search_path to 'public'
as $f$
  select case when auth.uid() is null then null else jsonb_build_object(
    'actif',   coalesce((mess_cfg() ->> 'actif')::int, 0) = 1,
    'ouvert',  mess_ouvert(auth.uid()),
    'tickets', coalesce((select m.tickets from mess_joueurs m where m.joueur_id = auth.uid()), 0),
    'jour',    coalesce((select sum(g.tickets) from mess_gains g where g.joueur_id = auth.uid()
                          and g.jour = (now() at time zone 'Europe/Paris')::date), 0),
    'regles',  mess_cfg() -> 'tickets',
    'machine', mess_cfg() -> 'machine',
    'recensement', (mess_cfg() -> 'recensement') - 'tranches',
    'rec', (select mess_rec_vue(p.id) from mess_rec_parties p where p.joueur_id = auth.uid() and p.en_cours),
    'as',      exists (select 1 from mess_tirages x where x.joueur_id = auth.uid() and x.gain ->> 'titre' = 'mess-as'),
    'energie_jour', exists (select 1 from mess_tirages x where x.joueur_id = auth.uid()
                             and x.jour = (now() at time zone 'Europe/Paris')::date and (x.gain ->> 'energie')::int > 0),
    'derniers', coalesce((select jsonb_agg(jsonb_build_object('le', x.le, 'rotors', x.rotors, 'lot', x.lot, 'gain', x.gain) order by x.le desc)
                            from (select * from mess_tirages x where x.joueur_id = auth.uid() order by x.le desc limit 8) x), '[]'::jsonb)) end;
$f$;

revoke all on function public.mess_rec_commune(text[]), public.mess_rec_vue(bigint), public.mess_rec_finir(bigint),
  public.mess_rec_lancer(), public.mess_rec_tirer(), public.mess_rec_clore(), public.mess_etat() from public, anon, authenticated;
grant execute on function public.mess_etat(), public.mess_rec_lancer(), public.mess_rec_tirer(), public.mess_rec_clore() to authenticated;
notify pgrst, 'reload schema';
