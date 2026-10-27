-- ===========================================================================
--  TerraFront — choisir ses notifications (27 octobre 2026)
--  (aperçu « Mes notifications » validé par Nataël : « très bien »)
--
--  Un réglage PAR COMPTE (tous les appareils), stocké en jsonb :
--    jeu      : ce qui apparaît dans la cloche (centre de notifications)
--               attaque, perdue, defense, echange, alerte, quete, recolte,
--               clan, paquet — tout activé par défaut sauf « paquet ».
--    tel      : notifications du téléphone (les deux qui existent) :
--               attaque (« X est en danger »), paquet (« paquet gratuit »).
--    seuil    : rareté minimale pour être prévenu d'une attaque
--               (commun = toutes, par défaut).
--    sourdine : communes pour lesquelles on ne veut plus être prévenu
--               d'une attaque (200 au plus).
--  Le seuil et la sourdine valent pour la cloche ET le téléphone.
--
--  Remplace le projet mis de côté le 9 octobre (_en-attente/notif-preferences.sql,
--  jamais passé). Les notifications du téléphone : une ligne ajoutée au
--  début de notifier_joueur, à partir de sa définition EN BASE. Si le texte
--  attendu n'y est pas exactement une fois, cette étape est SAUTÉE (message
--  « NOTICE »), le reste passe quand même : le contrôle final le dit
--  (filtre_telephone false). La fonction d'envoi et son secret ne sont pas
--  touchés. Rejouable.
-- ===========================================================================

create table if not exists public.notif_preferences(
  joueur_id uuid primary key references public.joueurs(id) on delete cascade,
  maj       timestamptz not null default now()
);
alter table public.notif_preferences add column if not exists prefs jsonb not null default '{}'::jsonb;
alter table public.notif_preferences enable row level security;
revoke all on public.notif_preferences from public, anon, authenticated;

-- les valeurs par défaut
create or replace function public.notif_defaut()
 returns jsonb language sql immutable set search_path to 'public'
as $f$
  select '{"jeu": {"attaque": true, "perdue": true, "defense": true, "echange": true, "alerte": true,
                   "quete": true, "recolte": true, "clan": true, "paquet": false},
           "tel": {"attaque": true, "paquet": true},
           "seuil": "commun",
           "sourdine": []}'::jsonb;
$f$;

-- les préférences d'un joueur, valeurs par défaut comprises
create or replace function public.notif_prefs_de(p_joueur uuid)
 returns jsonb language sql stable security definer set search_path to 'public'
as $f$
  select jsonb_build_object(
    'jeu',      (notif_defaut() -> 'jeu') || coalesce(np.prefs -> 'jeu', '{}'::jsonb),
    'tel',      (notif_defaut() -> 'tel') || coalesce(np.prefs -> 'tel', '{}'::jsonb),
    'seuil',    coalesce(np.prefs -> 'seuil', notif_defaut() -> 'seuil'),
    'sourdine', coalesce(np.prefs -> 'sourdine', '[]'::jsonb))
  from (select p_joueur as id) moi
  left join notif_preferences np on np.joueur_id = moi.id;
$f$;

create or replace function public.mes_notif_preferences()
 returns jsonb language plpgsql stable security definer set search_path to 'public'
as $f$
begin
  if auth.uid() is null then raise exception 'Non connecte'; end if;
  return notif_prefs_de(auth.uid());
end;
$f$;

-- un type on/off, pour la cloche (jeu) ou le téléphone (tel)
create or replace function public.regler_notif(p_canal text, p_type text, p_actif boolean)
 returns jsonb language plpgsql security definer set search_path to 'public'
as $f$
declare v_uid uuid := auth.uid();
begin
  if v_uid is null then raise exception 'Non connecte'; end if;
  if p_actif is null
     or not ((p_canal = 'jeu' and p_type in ('attaque','perdue','defense','echange','alerte','quete','recolte','clan','paquet'))
          or (p_canal = 'tel' and p_type in ('attaque','paquet'))) then
    raise exception 'Réglage inconnu';
  end if;
  insert into notif_preferences(joueur_id) values (v_uid) on conflict do nothing;
  update notif_preferences
     set prefs = jsonb_set(prefs, array[p_canal], coalesce(prefs -> p_canal, '{}'::jsonb) || jsonb_build_object(p_type, p_actif)),
         maj = now()
   where joueur_id = v_uid;
  return notif_prefs_de(v_uid);
end;
$f$;

-- la rareté minimale pour être prévenu d'une attaque
create or replace function public.regler_notif_seuil(p_tier text)
 returns jsonb language plpgsql security definer set search_path to 'public'
as $f$
declare v_uid uuid := auth.uid();
begin
  if v_uid is null then raise exception 'Non connecte'; end if;
  if p_tier is null or p_tier not in ('commun','peucommun','rare','epique','legendaire') then raise exception 'Réglage inconnu'; end if;
  insert into notif_preferences(joueur_id) values (v_uid) on conflict do nothing;
  update notif_preferences set prefs = prefs || jsonb_build_object('seuil', p_tier), maj = now() where joueur_id = v_uid;
  return notif_prefs_de(v_uid);
end;
$f$;

-- mettre une commune en sourdine (ou l'en sortir)
create or replace function public.notif_sourdine(p_code text, p_on boolean)
 returns jsonb language plpgsql security definer set search_path to 'public'
as $f$
declare v_uid uuid := auth.uid(); v_liste jsonb;
begin
  if v_uid is null then raise exception 'Non connecte'; end if;
  if p_on is null or not exists (select 1 from communes c where c.code = p_code) then raise exception 'Commune inconnue'; end if;
  insert into notif_preferences(joueur_id) values (v_uid) on conflict do nothing;
  select coalesce(prefs -> 'sourdine', '[]'::jsonb) into v_liste from notif_preferences where joueur_id = v_uid for update;
  v_liste := coalesce((select jsonb_agg(x) from jsonb_array_elements_text(v_liste) x where x <> p_code), '[]'::jsonb);
  if p_on then
    if jsonb_array_length(v_liste) >= 200 then raise exception '200 communes en sourdine au maximum'; end if;
    v_liste := v_liste || to_jsonb(p_code);
  end if;
  update notif_preferences set prefs = prefs || jsonb_build_object('sourdine', v_liste), maj = now() where joueur_id = v_uid;
  return notif_prefs_de(v_uid);
end;
$f$;

-- vrai si le joueur ne veut pas de cette notification sur son téléphone
create or replace function public.notif_coupee(p_joueur uuid, p_tag text)
 returns boolean language plpgsql stable security definer set search_path to 'public'
as $f$
declare v_p jsonb; v_code text; v_tier text;
  v_ordre text[] := array['commun','peucommun','rare','epique','legendaire'];
begin
  if not exists (select 1 from notif_preferences np where np.joueur_id = p_joueur) then return false; end if;
  v_p := notif_prefs_de(p_joueur);
  if p_tag = 'paquet' then return not coalesce((v_p #>> '{tel,paquet}')::boolean, true); end if;
  if p_tag like 'danger-%' then
    if not coalesce((v_p #>> '{tel,attaque}')::boolean, true) then return true; end if;
    v_code := substr(p_tag, 8);
    if (v_p -> 'sourdine') ? v_code then return true; end if;
    select c.tier into v_tier from communes c where c.code = v_code;
    if v_tier is not null and array_position(v_ordre, v_tier) < array_position(v_ordre, coalesce(v_p ->> 'seuil', 'commun')) then
      return true;
    end if;
  end if;
  return false;
end;
$f$;

revoke all on function public.notif_defaut() from public, anon, authenticated;
revoke all on function public.notif_prefs_de(uuid) from public, anon, authenticated;
revoke all on function public.notif_coupee(uuid, text) from public, anon, authenticated;
revoke all on function public.mes_notif_preferences() from public, anon;
revoke all on function public.regler_notif(text, text, boolean) from public, anon;
revoke all on function public.regler_notif_seuil(text) from public, anon;
revoke all on function public.notif_sourdine(text, boolean) from public, anon;
grant execute on function public.mes_notif_preferences() to authenticated;
grant execute on function public.regler_notif(text, text, boolean) to authenticated;
grant execute on function public.regler_notif_seuil(text) to authenticated;
grant execute on function public.notif_sourdine(text, boolean) to authenticated;

-- le téléphone respecte les réglages : une ligne au début de notifier_joueur
do $g$
declare
  v_def text;
  v_avant text := $a$declare n integer;
begin
$a$;
  v_apres text := $a$declare n integer;
begin
  -- s2-38 : le joueur a coupé ce type de notification (ou cette commune)
  if notif_coupee(p_joueur, p_tag) then return 0; end if;
$a$;
  n integer;
begin
  if to_regprocedure('public.notifier_joueur(uuid,text,text,text,text)') is null then
    raise notice 's2-38 : notifier_joueur absente, étape du téléphone sautée';
    return;
  end if;
  v_def := pg_get_functiondef('public.notifier_joueur(uuid,text,text,text,text)'::regprocedure);
  if position('notif_coupee(p_joueur, p_tag)' in v_def) > 0 then
    raise notice 's2-38 : filtre du téléphone déjà en place';
    return;
  end if;
  n := (length(v_def) - length(replace(v_def, v_avant, ''))) / length(v_avant);
  if n <> 1 then
    raise notice 's2-38 : texte attendu trouvé % fois dans notifier_joueur : étape du téléphone SAUTÉE (le reste est en place)', n;
    return;
  end if;
  execute replace(v_def, v_avant, v_apres);
end
$g$;

-- Contrôle : tout doit être true (filtre_telephone false = étape sautée, le dire à Claude)
select
  to_regclass('public.notif_preferences') is not null                                        as table_ok,
  (public.notif_defaut() #>> '{jeu,paquet}') = 'false'                                       as defauts_ok,
  has_function_privilege('authenticated', 'public.regler_notif(text,text,boolean)', 'execute') as joueurs_ok,
  not has_function_privilege('anon', 'public.regler_notif(text,text,boolean)', 'execute')      as anon_ferme,
  not has_function_privilege('authenticated', 'public.notif_coupee(uuid,text)', 'execute')     as interne_ferme,
  coalesce(position('notif_coupee(p_joueur, p_tag)' in
    pg_get_functiondef(to_regprocedure('public.notifier_joueur(uuid,text,text,text,text)'))) > 0, false) as filtre_telephone;
