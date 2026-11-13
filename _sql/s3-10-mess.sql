-- s3-10 (13/11/2026) : Le Mess, l'espace de jeux de l'Arcade (saison 3). Premier jeu : la Machine à chiffrer.
-- Décisions de Nataël (10/11 et 13/11) : tickets gagnés seulement en duel classé (victoire > défaite),
-- pas de mises en énergie ni en lingots, DA à la Balatro, nom « Le Mess », sortie avec la saison 3 (22/11).
-- Éteint (actif 0) jusqu'au jour J ; les modérateurs (discussion_moderateurs) peuvent déjà gagner des
-- tickets et jouer, pour la répétition.
--
-- Tickets : duel classé (Radar, Rafale, Plus ou moins) gagné 3, égalité 2, perdu 1 ; 30 par jour au plus
-- (jour de Paris) ; 2 duels qui rapportent par jour contre le même adversaire. Pas d'amical (pas d'Elo).
-- Les tickets ne s'achètent pas, la machine n'en rend jamais.
--
-- Machine à chiffrer (1 ticket) : 3 rotors, 6 symboles également probables (réglables : poids).
--   3 identiques : le lot du symbole ; 2 couronnes : 25 TP ; une autre paire : 10 TP ; sinon rien.
--   Simulation (poids égaux, paquet Terra compté 100 TP) : 44 % de tirages gagnants, environ 7,7 TP par ticket ;
--   un triple 1 fois sur 216 pour chaque symbole.

insert into config_jeu (cle, valeur) values ('mess', $j${
  "actif": 0,
  "tickets": { "victoire": 3, "egalite": 2, "defaite": 1, "par_jour": 30, "meme_adversaire": 2 },
  "machine": {
    "prix": 1,
    "symboles": ["couronne", "bombe", "forteresse", "fonderie", "lingot", "blason"],
    "poids": { "couronne": 1, "bombe": 1, "forteresse": 1, "fonderie": 1, "lingot": 1, "blason": 1 },
    "lots": {
      "couronne":       { "nom": "Trois couronnes",   "terra": 1, "titre": "mess-as" },
      "bombe":          { "nom": "Trois bombes",      "terra": 1 },
      "forteresse":     { "nom": "Trois Forteresses", "tp": 150 },
      "fonderie":       { "nom": "Trois Fonderies",   "tp": 100 },
      "lingot":         { "nom": "Trois lingots",     "energie": 3, "repli_tp": 30 },
      "blason":         { "nom": "Trois blasons",     "tp": 60 },
      "paire_couronne": { "nom": "Deux couronnes",    "tp": 25 },
      "paire":          { "nom": "Une paire",         "tp": 10 }
    }
  }
}$j$)
on conflict (cle) do nothing;

create table if not exists public.mess_joueurs (
  joueur_id uuid primary key references public.joueurs(id) on delete cascade,
  tickets integer not null default 0 check (tickets >= 0),
  gagnes integer not null default 0,
  joues integer not null default 0,
  maj timestamptz not null default now()
);
create table if not exists public.mess_gains (
  id bigserial primary key,
  joueur_id uuid not null references public.joueurs(id) on delete cascade,
  jour date not null,
  jeu text not null,
  partie_id bigint not null,
  adversaire uuid,
  resultat text,
  tickets integer not null default 0,
  le timestamptz not null default now(),
  unique (jeu, partie_id)
);
create index if not exists mess_gains_jour on public.mess_gains (joueur_id, jour);
create table if not exists public.mess_tirages (
  id bigserial primary key,
  joueur_id uuid not null references public.joueurs(id) on delete cascade,
  jeu text not null default 'machine',
  le timestamptz not null default now(),
  jour date not null,
  mise integer not null,
  rotors text[] not null,
  lot text,
  gain jsonb not null default '{}'::jsonb
);
create index if not exists mess_tirages_joueur on public.mess_tirages (joueur_id, le desc);
alter table public.mess_joueurs enable row level security;
alter table public.mess_gains enable row level security;
alter table public.mess_tirages enable row level security;
revoke all on public.mess_joueurs, public.mess_gains, public.mess_tirages from anon, authenticated;

create or replace function public.mess_cfg()
 returns jsonb language sql stable security definer set search_path to 'public'
as $f$ select coalesce((select c.valeur::jsonb from config_jeu c where c.cle = 'mess'), '{}'::jsonb); $f$;

create or replace function public.mess_ouvert(p_uid uuid)
 returns boolean language sql stable security definer set search_path to 'public'
as $f$ select coalesce((mess_cfg() ->> 'actif')::int, 0) = 1 or discussion_est_moderateur(p_uid); $f$;

-- les tickets d'un duel classé terminé (appelée par le déclencheur des trois jeux)
create or replace function public.mess_tickets_gagner(p_uid uuid, p_jeu text, p_partie bigint, p_adv uuid, p_resultat text)
 returns integer language plpgsql security definer set search_path to 'public'
as $f$
declare
  t jsonb := mess_cfg() -> 'tickets';
  v_jour date := (now() at time zone 'Europe/Paris')::date;
  v_n integer;
  v_deja integer;
  v_meme integer;
  v_id bigint;
begin
  if p_uid is null or not mess_ouvert(p_uid) then return 0; end if;
  v_n := coalesce((t ->> p_resultat)::int, 0);
  if v_n <= 0 then return 0; end if;
  perform 1 from joueurs where id = p_uid for update;
  select coalesce(sum(g.tickets), 0) into v_deja from mess_gains g where g.joueur_id = p_uid and g.jour = v_jour;
  select count(*) into v_meme from mess_gains g
   where g.joueur_id = p_uid and g.jour = v_jour and g.adversaire = p_adv and g.tickets > 0;
  if p_adv is not null and v_meme >= coalesce((t ->> 'meme_adversaire')::int, 2) then v_n := 0; end if;
  v_n := greatest(0, least(v_n, coalesce((t ->> 'par_jour')::int, 30) - v_deja));
  insert into mess_gains (joueur_id, jour, jeu, partie_id, adversaire, resultat, tickets)
  values (p_uid, v_jour, p_jeu, p_partie, p_adv, p_resultat, v_n)
  on conflict (jeu, partie_id) do nothing
  returning id into v_id;
  if v_id is null or v_n = 0 then return 0; end if;
  insert into mess_joueurs (joueur_id, tickets, gagnes) values (p_uid, v_n, v_n)
  on conflict (joueur_id) do update set tickets = mess_joueurs.tickets + v_n, gagnes = mess_joueurs.gagnes + v_n, maj = now();
  return v_n;
end;
$f$;

-- déclencheur commun à radar_parties, rafale_parties, pom_duels : quand le résultat d'un duel CLASSÉ tombe
create or replace function public.mess_trg_duel()
 returns trigger language plpgsql security definer set search_path to 'public'
as $f$
declare
  v_adv uuid;
  v_jeu text := case tg_table_name when 'radar_parties' then 'radar' when 'rafale_parties' then 'rafale' else 'pom' end;
begin
  if new.resultat is null or old.resultat is not null or new.elo_apres is null then return null; end if;
  if new.resultat not in ('victoire', 'egalite', 'defaite') then return null; end if;
  begin
    execute format('select joueur_id from %I where id = $1', tg_table_name) into v_adv using new.source_id;
    if v_adv is null then
      execute format('select joueur_id from %I where source_id = $1 limit 1', tg_table_name) into v_adv using new.id;
    end if;
    perform mess_tickets_gagner(new.joueur_id, v_jeu, new.id, v_adv, new.resultat);
  exception when others then
    raise warning 'mess_trg_duel : %', sqlerrm;   -- un souci du Mess ne casse jamais un duel
  end;
  return null;
end;
$f$;
drop trigger if exists mess_radar on public.radar_parties;
create trigger mess_radar after update of resultat on public.radar_parties for each row execute function public.mess_trg_duel();
drop trigger if exists mess_rafale on public.rafale_parties;
create trigger mess_rafale after update of resultat on public.rafale_parties for each row execute function public.mess_trg_duel();
drop trigger if exists mess_pom on public.pom_duels;
create trigger mess_pom after update of resultat on public.pom_duels for each row execute function public.mess_trg_duel();

-- l'état du Mess pour le joueur connecté
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
    'as',      exists (select 1 from mess_tirages x where x.joueur_id = auth.uid() and x.gain ->> 'titre' = 'mess-as'),
    'energie_jour', exists (select 1 from mess_tirages x where x.joueur_id = auth.uid()
                             and x.jour = (now() at time zone 'Europe/Paris')::date and (x.gain ->> 'energie')::int > 0),
    'derniers', coalesce((select jsonb_agg(jsonb_build_object('le', x.le, 'rotors', x.rotors, 'lot', x.lot, 'gain', x.gain) order by x.le desc)
                            from (select * from mess_tirages x where x.joueur_id = auth.uid() order by x.le desc limit 8) x), '[]'::jsonb)) end;
$f$;

-- la Machine à chiffrer : un ticket, trois rotors, le tirage au serveur
create or replace function public.mess_chiffrer()
 returns jsonb language plpgsql security definer set search_path to 'public'
as $f$
declare
  v_uid uuid := auth.uid();
  m jsonb := mess_cfg() -> 'machine';
  v_prix integer := greatest(1, coalesce((m ->> 'prix')::int, 1));
  v_jour date := (now() at time zone 'Europe/Paris')::date;
  v_sym text[];
  v_total numeric := 0;
  v_rot text[] := '{}';
  v_tir numeric; v_acc numeric; s text; i integer;
  v_lot text; v_l jsonb;
  v_tp integer := 0; v_terra integer := 0; v_en integer := 0; v_titre text;
  v_tickets integer;
  e numeric; e2 numeric; j record;
  v_gain jsonb;
begin
  if v_uid is null then raise exception 'Non connecté'; end if;
  if not mess_ouvert(v_uid) then raise exception 'Le Mess ouvre avec la saison 3'; end if;
  perform 1 from joueurs where id = v_uid for update;
  select tickets into v_tickets from mess_joueurs where joueur_id = v_uid for update;
  if coalesce(v_tickets, 0) < v_prix then
    raise exception 'Pas assez de tickets : ils se gagnent en duel classé (Radar, Rafale, Plus ou moins)';
  end if;

  select array_agg(x order by o) into v_sym from jsonb_array_elements_text(m -> 'symboles') with ordinality as t(x, o);
  if v_sym is null or array_length(v_sym, 1) < 2 then raise exception 'La machine n''est pas réglée'; end if;
  foreach s in array v_sym loop v_total := v_total + greatest(0, coalesce((m -> 'poids' ->> s)::numeric, 1)); end loop;
  for i in 1..3 loop
    v_tir := random() * v_total; v_acc := 0;
    foreach s in array v_sym loop
      v_acc := v_acc + greatest(0, coalesce((m -> 'poids' ->> s)::numeric, 1));
      exit when v_tir < v_acc;
    end loop;
    v_rot := v_rot || s;
  end loop;

  if v_rot[1] = v_rot[2] and v_rot[2] = v_rot[3] then v_lot := v_rot[1];
  elsif (v_rot[1] = 'couronne')::int + (v_rot[2] = 'couronne')::int + (v_rot[3] = 'couronne')::int = 2 then v_lot := 'paire_couronne';
  elsif v_rot[1] = v_rot[2] or v_rot[2] = v_rot[3] or v_rot[1] = v_rot[3] then v_lot := 'paire';
  end if;
  v_l := case when v_lot is not null then m -> 'lots' -> v_lot end;

  if v_l is not null then
    v_tp := greatest(0, coalesce((v_l ->> 'tp')::int, 0));
    v_terra := greatest(0, coalesce((v_l ->> 'terra')::int, 0));
    -- l'énergie : une fois par jour, sinon son équivalent en TP ; jamais au-dessus du plafond des bonus
    if coalesce((v_l ->> 'energie')::int, 0) > 0 then
      if exists (select 1 from mess_tirages x where x.joueur_id = v_uid and x.jour = v_jour and (x.gain ->> 'energie')::int > 0) then
        v_tp := v_tp + greatest(0, coalesce((v_l ->> 'repli_tp')::int, 0));
      else
        select front_energie, front_energie_maj into j from joueurs where id = v_uid;
        e := front_energie_lire(j.front_energie, j.front_energie_maj);
        e2 := greatest(e, least(front_energie_reglage('plafond'), e + (v_l ->> 'energie')::int));
        v_en := greatest(0, floor(e2) - floor(e))::integer;
        update joueurs set front_energie = e2, front_energie_maj = now() where id = v_uid;
        if v_en = 0 then v_tp := v_tp + greatest(0, coalesce((v_l ->> 'repli_tp')::int, 0)); end if;
      end if;
    end if;
    -- le titre : une seule fois
    if v_l ->> 'titre' is not null and not exists (select 1 from mess_tirages x where x.joueur_id = v_uid and x.gain ->> 'titre' = v_l ->> 'titre') then
      v_titre := v_l ->> 'titre';
    end if;
  end if;

  if v_tp > 0 then
    perform set_config('terrafront.motif', 'mess', true);
    update joueurs set solde = coalesce(solde, 0) + v_tp where id = v_uid;
  end if;
  if v_terra > 0 then
    update joueurs set terra_jetons = terra_jetons_lire(terra_jetons, terra_jetons_maj) + v_terra, terra_jetons_maj = now() where id = v_uid;
  end if;
  update mess_joueurs set tickets = tickets - v_prix, joues = joues + 1, maj = now() where joueur_id = v_uid
  returning tickets into v_tickets;

  v_gain := jsonb_strip_nulls(jsonb_build_object('tp', nullif(v_tp, 0), 'terra', nullif(v_terra, 0), 'energie', nullif(v_en, 0), 'titre', v_titre));
  insert into mess_tirages (joueur_id, jeu, jour, mise, rotors, lot, gain) values (v_uid, 'machine', v_jour, v_prix, v_rot, v_lot, v_gain);

  return jsonb_build_object('rotors', to_jsonb(v_rot), 'lot', v_lot, 'nom', v_l ->> 'nom', 'gain', v_gain, 'tickets', v_tickets,
    'solde', (select coalesce(solde, 0) from joueurs where id = v_uid));
end;
$f$;

-- le titre « As du Mess » (trois couronnes) parmi les titres choisissables
create or replace function public.titres_possibles(p_joueur uuid)
 returns text[] language sql stable security definer set search_path to 'public'
as $function$
  select coalesce(array_agg(x.titre order by x.titre), '{}')
    from (select t.titre
            from (values ('parrain', 'parrain')) as t(titre, badge)
           where exists (select 1 from joueur_badges b where b.joueur_id = p_joueur and b.badge = t.badge)
          union
          -- s2-53 : les titres gagnés dans un pass de saison
          select r.valeur
            from pass_reclames c join pass_recompenses r on r.saison = c.saison and r.niveau = c.niveau
           where c.joueur_id = p_joueur and r.type = 'titre'
          union
          -- s2-68 : la quête d'Halloween (Terra ou Front)
          select coalesce(halloween_hantees_cfg() ->> 'titre', 'halloween-2026')
            from halloween_quete q
           where q.joueur_id = p_joueur and (q.reclame_le is not null or q.front_reclame_le is not null)
          union
          -- s3-10 : le Mess (trois couronnes à la Machine à chiffrer)
          select distinct x.gain ->> 'titre' from mess_tirages x where x.joueur_id = p_joueur and x.gain ? 'titre') x;
$function$;

revoke all on function public.mess_cfg(), public.mess_ouvert(uuid), public.mess_tickets_gagner(uuid, text, bigint, uuid, text),
  public.mess_trg_duel(), public.mess_etat(), public.mess_chiffrer() from public, anon, authenticated;   -- les droits par défaut les donnent à tous
grant execute on function public.mess_etat(), public.mess_chiffrer() to authenticated;
notify pgrst, 'reload schema';
