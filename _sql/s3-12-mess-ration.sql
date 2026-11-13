-- s3-12 (13/11/2026) : le Mess compte pour le classement (Oshannir : « on joue le classement »).
-- Décision de Nataël (20 h 23 UTC) : de l'énergie, 25 par jour au plus, « et des lingots aussi ».
-- Ration du Mess (par jour de Paris) : 25 énergies et 6 lingots au plus ; au-delà (ou au-dessus du plafond
-- d'énergie, ou de la réserve de lingots), 10 TP par énergie et 15 TP par lingot.
-- Lots modifiés :
--   Machine : 3 lingots +3 énergie (plus de « 1 fois par jour », la ration suffit) ; 3 bombes paquet Terra + 5 énergie ;
--             3 Fonderies 100 TP + 2 lingots ; 3 Forteresses 150 TP + 2 lingots.
--   Recensement : gagné 30 TP + 3 énergie + 1 lingot ; parfait paquet Terra + 6 énergie + 2 lingots.

update config_jeu set valeur = (
  jsonb_set(jsonb_set(jsonb_set(jsonb_set(jsonb_set(jsonb_set(jsonb_set(valeur::jsonb,
    '{ration}', '{"energie": 25, "lingots": 6, "tp_par_energie": 10, "tp_par_lingot": 15}'),
    '{machine,lots,lingot}', '{"nom": "Trois lingots", "energie": 3}'),
    '{machine,lots,bombe}', '{"nom": "Trois bombes", "terra": 1, "energie": 5}'),
    '{machine,lots,fonderie}', '{"nom": "Trois Fonderies", "tp": 100, "lingots": 2}'),
    '{machine,lots,forteresse}', '{"nom": "Trois Forteresses", "tp": 150, "lingots": 2}'),
    '{recensement,lots,gagne}', '{"nom": "Recensé !", "tp": 30, "energie": 3, "lingots": 1}'),
    '{recensement,lots,parfait}', '{"nom": "Recensement parfait", "terra": 1, "energie": 6, "lingots": 2}'))::text
 where cle = 'mess' and not (valeur::jsonb ? 'ration');

create table if not exists public.mess_rations (
  joueur_id uuid not null references public.joueurs(id) on delete cascade,
  jour date not null,
  energie integer not null default 0,
  lingots integer not null default 0,
  primary key (joueur_id, jour)
);
alter table public.mess_rations enable row level security;
revoke all on public.mess_rations from anon, authenticated;

-- donner de l'énergie et des lingots dans la ration du jour ; le reste en TP. Rend ce qui a été donné.
create or replace function public.mess_donner(p_uid uuid, p_energie integer, p_lingots integer)
 returns jsonb language plpgsql security definer set search_path to 'public'
as $f$
declare
  r jsonb := mess_cfg() -> 'ration';
  v_jour date := (now() at time zone 'Europe/Paris')::date;
  x record; j record;
  v_e integer := 0; v_l integer := 0; v_tp integer := 0;
  e numeric; e2 numeric; l numeric; l2 numeric;
begin
  p_energie := greatest(0, coalesce(p_energie, 0)); p_lingots := greatest(0, coalesce(p_lingots, 0));
  if p_energie = 0 and p_lingots = 0 then return '{}'::jsonb; end if;
  insert into mess_rations (joueur_id, jour) values (p_uid, v_jour) on conflict do nothing;
  select * into x from mess_rations where joueur_id = p_uid and jour = v_jour for update;
  if p_energie > 0 then
    v_e := least(p_energie, greatest(0, coalesce((r ->> 'energie')::int, 25) - x.energie));
    if v_e > 0 then
      select front_energie, front_energie_maj into j from joueurs where id = p_uid;
      e := front_energie_lire(j.front_energie, j.front_energie_maj);
      e2 := greatest(e, least(front_energie_reglage('plafond'), e + v_e));
      v_e := greatest(0, floor(e2) - floor(e))::integer;
      update joueurs set front_energie = e2, front_energie_maj = now() where id = p_uid;
    end if;
    v_tp := v_tp + (p_energie - v_e) * coalesce((r ->> 'tp_par_energie')::int, 10);
  end if;
  if p_lingots > 0 then
    v_l := least(p_lingots, greatest(0, coalesce((r ->> 'lingots')::int, 6) - x.lingots));
    if v_l > 0 then
      l := lingots_figer(p_uid);
      l2 := greatest(l, least(lingots_max(p_uid), l + v_l));
      v_l := greatest(0, floor(l2) - floor(l))::integer;
      update joueurs set lingots = l2 where id = p_uid;
    end if;
    v_tp := v_tp + (p_lingots - v_l) * coalesce((r ->> 'tp_par_lingot')::int, 15);
  end if;
  update mess_rations set energie = energie + v_e, lingots = lingots + v_l where joueur_id = p_uid and jour = v_jour;
  if v_tp > 0 then
    perform set_config('terrafront.motif', 'mess', true);
    update joueurs set solde = coalesce(solde, 0) + v_tp where id = p_uid;
  end if;
  return jsonb_strip_nulls(jsonb_build_object('energie', nullif(v_e, 0), 'lingots', nullif(v_l, 0), 'tp_repli', nullif(v_tp, 0)));
end;
$f$;

-- la Machine : l'énergie et les lingots passent par la ration
do $d$
declare def text; a text; b text;
begin
  select pg_get_functiondef('public.mess_chiffrer'::regproc) into def;
  a := $x$    if coalesce((v_l ->> 'energie')::int, 0) > 0 then
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
    end if;$x$;
  b := $x$    -- s3-12 : énergie et lingots dans la ration du jour
    v_ration := mess_donner(v_uid, coalesce((v_l ->> 'energie')::int, 0), coalesce((v_l ->> 'lingots')::int, 0));
    v_en := coalesce((v_ration ->> 'energie')::int, 0);$x$;
  if position(a in def) = 0 then raise exception 's3-12 : bloc énergie introuvable dans mess_chiffrer'; end if;
  def := replace(def, a, b);
  def := replace(def, 'v_gain jsonb;', 'v_gain jsonb;' || chr(10) || '  v_ration jsonb := ''{}''::jsonb;   -- s3-12');
  def := replace(def, $x$v_gain := jsonb_strip_nulls(jsonb_build_object('tp', nullif(v_tp, 0), 'terra', nullif(v_terra, 0), 'energie', nullif(v_en, 0), 'titre', v_titre));$x$,
    $x$v_gain := jsonb_strip_nulls(jsonb_build_object('tp', nullif(v_tp + coalesce((v_ration ->> 'tp_repli')::int, 0), 0), 'terra', nullif(v_terra, 0),
                 'energie', nullif(v_en, 0), 'lingots', nullif(coalesce((v_ration ->> 'lingots')::int, 0), 0), 'titre', v_titre));   -- s3-12$x$);
  if position('s3-12' in def) = 0 or position('v_ration jsonb' in def) = 0 then raise exception 's3-12 : mess_chiffrer pas modifiée'; end if;
  execute def;
end $d$;

-- le Recensement : idem
do $d$
declare def text; a text; b text;
begin
  select pg_get_functiondef('public.mess_rec_finir'::regproc) into def;
  a := $x$  update mess_rec_parties
     set en_cours = false, fini_le = now(), resultat = v_res,
         gain = jsonb_strip_nulls(jsonb_build_object('tp', nullif(v_tp, 0), 'terra', nullif(v_terra, 0)))$x$;
  b := $x$  v_ration := case when l is not null then mess_donner(p.joueur_id, coalesce((l ->> 'energie')::int, 0), coalesce((l ->> 'lingots')::int, 0)) else '{}'::jsonb end;   -- s3-12
  update mess_rec_parties
     set en_cours = false, fini_le = now(), resultat = v_res,
         gain = jsonb_strip_nulls(jsonb_build_object('tp', nullif(v_tp + coalesce((v_ration ->> 'tp_repli')::int, 0), 0), 'terra', nullif(v_terra, 0),
                  'energie', (v_ration -> 'energie'), 'lingots', (v_ration -> 'lingots')))$x$;
  if position(a in def) = 0 then raise exception 's3-12 : fin du Recensement introuvable'; end if;
  def := replace(def, a, b);
  def := replace(def, 'v_terra integer := 0;', 'v_terra integer := 0; v_ration jsonb;');
  if position('v_ration jsonb;' in def) = 0 then raise exception 's3-12 : déclaration introuvable'; end if;
  execute def;
end $d$;

-- mess_etat : + la ration du jour
do $d$
declare def text;
begin
  select pg_get_functiondef('public.mess_etat'::regproc) into def;
  def := replace(def, $x$'recensement', (mess_cfg() -> 'recensement') - 'tranches',$x$,
    $x$'recensement', (mess_cfg() -> 'recensement') - 'tranches',
    'ration', (mess_cfg() -> 'ration') || jsonb_build_object(
       'energie_jour', coalesce((select r.energie from mess_rations r where r.joueur_id = auth.uid() and r.jour = (now() at time zone 'Europe/Paris')::date), 0),
       'lingots_jour', coalesce((select r.lingots from mess_rations r where r.joueur_id = auth.uid() and r.jour = (now() at time zone 'Europe/Paris')::date), 0)),   -- s3-12$x$);
  if position('s3-12' in def) = 0 then raise exception 's3-12 : mess_etat pas modifiée'; end if;
  execute def;
end $d$;

revoke all on function public.mess_donner(uuid, integer, integer), public.mess_chiffrer(), public.mess_rec_finir(bigint), public.mess_etat() from public, anon, authenticated;
grant execute on function public.mess_etat(), public.mess_chiffrer() to authenticated;
notify pgrst, 'reload schema';
