-- ===========================================================================
--  s2-67 — Libérer des communes du Front contre de l'énergie (30/10)
--  Idée de Maroli. Aperçu validé le 30/10, avec patch273.
--
--  Règles :
--   - énergie par commune selon sa rareté : commune 0,05 (1/20), peu commune
--     0,1 (1/10), rare 1, épique 3, légendaire 6 ; les fractions s'additionnent
--     (l'énergie du Front est déjà un nombre décimal en base) ;
--   - au plus 20 d'énergie par jour (heure de Paris) venue des libérations ;
--     le réservoir reste plafonné à 60 ; au-delà, l'énergie est perdue
--     (l'écran le dit avant de valider) ;
--   - la commune quitte la collection exactement comme une vente au jeu :
--     elle redevient libre et retourne dans les paquets du Front ;
--   - celui qui l'a libérée ne peut pas la retirer pendant 7 jours
--     (draw_commune les écarte pour lui seulement) ;
--   - refusée si la commune a une garnison, un bâtiment, ou si elle est
--     assiégée (commune_assiegee, comme la vente au jeu).
--
--  Tous les chiffres sont dans config_jeu 'liberation' : on peut les changer
--  sans patch (voir l'exemple tout en bas). « ouvert » à false referme tout.
--
--  Fonctions pour le jeu (authenticated) :
--    front_liberation_etat()      les réglages et l'énergie déjà gagnée aujourd'hui
--    front_liberer(codes[])       libère ce qui peut l'être, dit ce qui a été refusé
--
--  draw_commune est modifiée à partir de sa définition en base : si le texte
--  attendu manque, le fichier s'arrête et RIEN ne change (tout est dans une
--  transaction).
--  Rejouable. Contrôle attendu : true | true | true | 2
-- ===========================================================================
begin;

-- 1. Les réglages --------------------------------------------------------------
insert into public.config_jeu (cle, valeur)
values ('liberation', '{"ouvert": true, "taux": {"commun": 0.05, "peucommun": 0.1, "rare": 1, "epique": 3, "legendaire": 6}, "plafond": 20, "reservoir": 60, "jours": 7}')
on conflict (cle) do nothing;

create or replace function public.front_liberation_config()
 returns jsonb language sql stable security definer set search_path to 'public'
as $f$
  select '{"ouvert": false, "taux": {"commun": 0.05, "peucommun": 0.1, "rare": 1, "epique": 3, "legendaire": 6}, "plafond": 20, "reservoir": 60, "jours": 7}'::jsonb
         || coalesce((select c.valeur::jsonb from config_jeu c where c.cle = 'liberation'), '{}'::jsonb);
$f$;

-- 2. Le journal des libérations (sert au plafond du jour et aux 7 jours) -------
create table if not exists public.front_liberations(
  id           bigserial primary key,
  joueur_id    uuid not null references public.joueurs(id) on delete cascade,
  commune_code text not null,
  tier         text not null,
  energie      numeric not null default 0,     -- ce qui a vraiment été compté
  brute        numeric not null default 0,     -- ce que valait la commune
  jour         date not null,                  -- jour de Paris
  le           timestamptz not null default now(),
  jusqua       timestamptz not null            -- ne retombe pas à ce joueur avant
);
create index if not exists front_liberations_jour on public.front_liberations(joueur_id, jour);
create index if not exists front_liberations_retour on public.front_liberations(commune_code, joueur_id, jusqua);
alter table public.front_liberations enable row level security;
revoke all on public.front_liberations from public, anon, authenticated;
revoke all on sequence public.front_liberations_id_seq from public, anon, authenticated;

-- 3. L'état, pour l'écran -------------------------------------------------------
create or replace function public.front_liberation_etat()
 returns jsonb language plpgsql stable security definer set search_path to 'public'
as $f$
declare
  v_uid uuid := auth.uid();
  c jsonb := front_liberation_config();
begin
  if v_uid is null or not saison2_active() or not coalesce((c->>'ouvert')::boolean, false) then
    return jsonb_build_object('ouvert', false);
  end if;
  return jsonb_build_object(
    'ouvert', true, 'taux', c->'taux', 'plafond', (c->>'plafond')::numeric,
    'reservoir', (c->>'reservoir')::numeric, 'jours', (c->>'jours')::integer,
    'aujourdhui', (select coalesce(sum(l.energie), 0) from front_liberations l
                    where l.joueur_id = v_uid and l.jour = (now() at time zone 'Europe/Paris')::date));
end;
$f$;

-- 4. Libérer --------------------------------------------------------------------
create or replace function public.front_liberer(p_codes text[])
 returns jsonb language plpgsql security definer set search_path to 'public'
as $f$
declare
  v_uid uuid := auth.uid();
  c jsonb := front_liberation_config();
  v_jour date := (now() at time zone 'Europe/Paris')::date;
  v_plafond numeric := (c->>'plafond')::numeric;
  v_reservoir numeric := (c->>'reservoir')::numeric;
  v_jours integer := (c->>'jours')::integer;
  v numeric;            -- énergie du joueur
  v_deja numeric;       -- déjà gagné aujourd'hui en libérant
  v_gagne numeric := 0;
  v_perdue numeric := 0;
  v_brute numeric;
  v_e numeric;
  v_faites text[] := '{}';
  v_refus jsonb := '[]'::jsonb;
  r record;
begin
  if v_uid is null then raise exception 'Non connecte'; end if;
  if not saison2_active() or not coalesce((c->>'ouvert')::boolean, false) then
    raise exception 'La liberation n''est pas encore ouverte';
  end if;
  if p_codes is null or cardinality(p_codes) = 0 then raise exception 'Aucune commune a liberer'; end if;
  if cardinality(p_codes) > 2000 then raise exception 'Trop de communes d''un coup (2 000 au plus)'; end if;

  -- un seul appel à la fois par joueur : le plafond du jour reste juste
  select front_energie_lire(j.front_energie, j.front_energie_maj) into v from joueurs j where j.id = v_uid for update;
  select coalesce(sum(l.energie), 0) into v_deja from front_liberations l where l.joueur_id = v_uid and l.jour = v_jour;

  -- les plus précieuses d'abord : si le plafond coupe, il coupe les petites
  for r in
    select x.code, cm.tier
      from (select distinct unnest(p_codes) as code) x
      left join communes cm on cm.code = x.code
     order by array_position(array['legendaire','epique','rare','peucommun','commun'], cm.tier) nulls last, x.code
  loop
    perform 1 from possessions p where p.commune_code = r.code and p.joueur_id = v_uid for update;
    if not found then
      v_refus := v_refus || jsonb_build_object('code', r.code, 'raison', 'elle n''est plus à toi');
      continue;
    end if;
    if exists (select 1 from front_garnisons g where g.commune_code = r.code and g.joueur_id = v_uid) then
      v_refus := v_refus || jsonb_build_object('code', r.code, 'raison', 'garnison');
      continue;
    end if;
    if exists (select 1 from batiments b where b.commune_code = r.code) then
      v_refus := v_refus || jsonb_build_object('code', r.code, 'raison', 'bâtiment');
      continue;
    end if;
    if commune_assiegee(r.code) then
      v_refus := v_refus || jsonb_build_object('code', r.code, 'raison', 'attaquée');
      continue;
    end if;

    v_brute := coalesce((c->'taux'->>r.tier)::numeric, 0);
    v_e := greatest(0, least(v_brute, v_plafond - v_deja - v_gagne, v_reservoir - v - v_gagne));
    v_gagne := v_gagne + v_e;
    v_perdue := v_perdue + (v_brute - v_e);

    -- comme vendre_au_jeu : la commune redevient libre
    delete from possessions where commune_code = r.code and joueur_id = v_uid;
    delete from annonces where commune_code = r.code;
    update historique set released_at = now()
     where commune_code = r.code and joueur_id = v_uid and released_at is null;
    insert into front_liberations(joueur_id, commune_code, tier, energie, brute, jour, jusqua)
    values (v_uid, r.code, r.tier, v_e, v_brute, v_jour, now() + make_interval(days => v_jours));
    v_faites := v_faites || r.code;
  end loop;

  if v_gagne > 0 then
    update joueurs set front_energie = least(v_reservoir, v + v_gagne), front_energie_maj = now() where id = v_uid;
  end if;

  return jsonb_build_object('liberees', to_jsonb(v_faites), 'energie_gagnee', v_gagne, 'perdue', v_perdue,
                            'refusees', v_refus, 'energie', floor(least(v_reservoir, v + v_gagne)),
                            'etat', front_liberation_etat());
end;
$f$;

revoke all on function public.front_liberation_config() from public, anon, authenticated;
revoke all on function public.front_liberation_etat(), public.front_liberer(text[]) from public, anon;
grant execute on function public.front_liberation_etat(), public.front_liberer(text[]) to authenticated;

-- 5. draw_commune : une commune libérée ne retombe pas à son ancien joueur pendant 7 jours
do $$
declare
  d text := pg_get_functiondef('public.draw_commune(text)'::regprocedure);
  a1 text := 'where length(c.departement) <> 2 and p.commune_code is null';
  a2 text := 'where c.tier = v_tier and p.commune_code is null and length(c.departement) = 2';
  ex text := ' and not exists (select 1 from front_liberations fl where fl.commune_code = c.code and fl.joueur_id = v_joueur_id and fl.jusqua > now())';
begin
  if position('front_liberations' in d) > 0 then raise notice 'draw_commune : déjà fait'; return; end if;
  if (length(d) - length(replace(d, a1, ''))) / length(a1) <> 1
     or (length(d) - length(replace(d, a2, ''))) / length(a2) <> 1 then
    raise exception 'draw_commune : texte attendu introuvable, rien n''a changé';
  end if;
  execute replace(replace(d, a1, a1 || ex), a2, a2 || ex);
end $$;

commit;

-- contrôle : réglages | front_liberer | draw_commune modifiée | 2 conditions dans draw_commune
select (select (front_liberation_config()->>'ouvert')::boolean)                                            as ouvert,
       to_regprocedure('public.front_liberer(text[])') is not null                                       as fonction,
       position('front_liberations' in pg_get_functiondef('public.draw_commune(text)'::regprocedure)) > 0 as tirage,
       (length(pg_get_functiondef('public.draw_commune(text)'::regprocedure))
        - length(replace(pg_get_functiondef('public.draw_commune(text)'::regprocedure), 'front_liberations', ''))) / length('front_liberations') as conditions;

-- Pour changer les chiffres plus tard (exemple, à ne pas lancer tel quel) :
-- update public.config_jeu set valeur = (valeur::jsonb || '{"plafond": 25}'::jsonb)::text where cle = 'liberation';
-- update public.config_jeu set valeur = jsonb_set(valeur::jsonb, '{taux,legendaire}', '5')::text where cle = 'liberation';
-- Pour tout refermer : update public.config_jeu set valeur = (valeur::jsonb || '{"ouvert": false}'::jsonb)::text where cle = 'liberation';
