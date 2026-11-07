-- s2-111 (7/11/2026) : le bonus de débutant (« piste 1 », accord de Nataël le 6/11 à 13 h 57).
-- Constat : une conquête dans les 24 premières heures donne 86 % de retour le
-- lendemain, contre 17 % sans ; seuls 3 nouveaux sur 7 ont gagné la conquête
-- guidée. Et le pot est vide : un nouveau sans commune ne peut entrer au Front
-- qu'en conquérant.
-- Désormais, pour un compte de moins de 7 jours qui n'a encore rien conquis :
--   - chaque assaut a au moins 85 % de chances, quel que soit l'engagement,
--     et même loin de ses communes (la pénalité de distance ne joue plus) ;
--   - une Forteresse garde son effet (85 − 15 = 70 %), une zone bombardée aussi
--     (90 % au plus, comme pour tous) ;
--   - AUCUN bonus contre une commune en garnison (demande de Nataël : ce ne
--     doit pas être plus simple d'attaquer une garnison) ;
--   - toujours 3 victoires pour prendre une commune ;
--   - le bonus s'arrête à la première conquête, ou au bout de 7 jours.
-- Premiers pas : l'étape 1 se coche aussi en tournant la roue du Front (quand
-- le pot est vide, aucun paquet ne peut s'ouvrir : l'étape restait bloquée).
-- Réglages : config_jeu 'debutant' (actif, jours, chances). Pour couper le
-- bonus : {"actif": false}.
-- Testé sur la prod dans un bloc annulé.

create or replace function pg_temp.remp(d text, avant text, apres text, nb int, quoi text)
 returns text language plpgsql as $f$
begin
  if (length(d) - length(replace(d, avant, ''))) / length(avant) <> nb then
    raise exception '% : texte attendu % fois, trouvé % fois — rien n''a changé : %',
      quoi, nb, (length(d) - length(replace(d, avant, ''))) / length(avant), avant;
  end if;
  return replace(d, avant, apres);
end;
$f$;

begin;

insert into public.config_jeu (cle, valeur)
values ('debutant', '{"actif": true, "jours": 7, "chances": 0.85}')
on conflict (cle) do nothing;

-- une garnison active sur la commune (même règle que apercu_attaque, s2-82)
create or replace function public.garnison_active(p_code text)
 returns boolean language sql stable security definer set search_path to 'public' as $f$
  select exists (select 1 from front_garnisons g
                   join possessions po on po.commune_code = g.commune_code and po.joueur_id = g.joueur_id
                  where g.commune_code = p_code and g.energie > 0);
$f$;

-- le joueur a-t-il encore son bonus ?
create or replace function public.debutant_actif(p_uid uuid)
 returns boolean language sql stable security definer set search_path to 'public' as $f$
  with cfg as (select coalesce((select c.valeur::jsonb from config_jeu c where c.cle = 'debutant'), '{}'::jsonb) as v)
  select p_uid is not null and saison2_active()
     and coalesce((cfg.v->>'actif')::boolean, true)
     and exists (select 1 from auth.users u
                  where u.id = p_uid
                    and u.created_at > now() - make_interval(days => coalesce((cfg.v->>'jours')::int, 7)))
     and not exists (select 1 from front_victoires v where v.joueur_id = p_uid and v.type = 'conquete')
    from cfg;
$f$;

-- la chance avec le bonus : au moins 85 % (+ bâtiments), jamais contre une garnison
create or replace function public.chance_debutant(p_actif boolean, p_uid uuid, p_code text, p_chance numeric)
 returns numeric language sql stable security definer set search_path to 'public' as $f$
  select case
    when coalesce(p_actif, false) and not garnison_active(p_code)
      then least(0.90, greatest(p_chance,
             coalesce((select (c.valeur::jsonb->>'chances')::numeric from config_jeu c where c.cle = 'debutant'), 0.85)
             + bonus_batiments(p_uid, p_code)))
    else p_chance end;
$f$;

-- ce que le jeu affiche : le bonus et sa fin
create or replace function public.debutant_etat()
 returns jsonb language sql stable security definer set search_path to 'public' as $f$
  with cfg as (select coalesce((select c.valeur::jsonb from config_jeu c where c.cle = 'debutant'), '{}'::jsonb) as v)
  select jsonb_build_object(
           'actif', debutant_actif(auth.uid()),
           'fin_le', (select u.created_at + make_interval(days => coalesce((cfg.v->>'jours')::int, 7))
                        from auth.users u where u.id = auth.uid()),
           'chances', round(coalesce((cfg.v->>'chances')::numeric, 0.85) * 100)::integer)
    from cfg;
$f$;

revoke execute on function public.garnison_active(text) from public, anon, authenticated;
revoke execute on function public.debutant_actif(uuid) from public, anon, authenticated;
revoke execute on function public.chance_debutant(boolean, uuid, text, numeric) from public, anon, authenticated;
revoke execute on function public.debutant_etat() from public, anon;
grant execute on function public.debutant_etat() to authenticated;

-- l'aperçu d'une attaque
do $$
declare d text := pg_get_functiondef('public.apercu_attaque(text, text)'::regprocedure);
begin
  if position('s2-111' in d) > 0 then raise notice 'apercu_attaque : déjà à jour'; return; end if;
  d := pg_temp.remp(d,
'  v_chance := greatest(0.10, least(0.90, v_chance + bonus_proximite(v_proches) + bonus_batiments(v_uid, p_commune_code)));',
'  v_chance := greatest(0.10, least(0.90, v_chance + bonus_proximite(v_proches) + bonus_batiments(v_uid, p_commune_code)));
  v_chance := chance_debutant(debutant_actif(v_uid), v_uid, p_commune_code, v_chance);   -- s2-111 : bonus de débutant', 1, 'apercu_attaque');
  execute d;
end $$;

-- l'aperçu de la liste des cibles
do $$
declare d text := pg_get_functiondef('public.apercu_attaques(text[], text)'::regprocedure);
begin
  if position('s2-111' in d) > 0 then raise notice 'apercu_attaques : déjà à jour'; return; end if;
  d := pg_temp.remp(d,
'  v_base numeric;
begin',
'  v_base numeric;
  v_deb boolean;   -- s2-111
begin', 1, 'apercu_attaques (déclaration)');
  d := pg_temp.remp(d,
'  v_base := chance_intensite(p_intensite);',
'  v_base := chance_intensite(p_intensite);
  v_deb := debutant_actif(v_uid);   -- s2-111 : bonus de débutant', 1, 'apercu_attaques (bonus)');
  d := pg_temp.remp(d,
'round(greatest(0.10, least(0.90, v_base + bonus_proximite(p.nb) + bonus_batiments(v_uid, c.code)))',
'round(chance_debutant(v_deb, v_uid, c.code, greatest(0.10, least(0.90, v_base + bonus_proximite(p.nb) + bonus_batiments(v_uid, c.code))))', 1, 'apercu_attaques (chance)');
  execute d;
end $$;

-- l'assaut
do $$
declare d text := pg_get_functiondef('public.attaquer(text, text)'::regprocedure);
begin
  if position('s2-111' in d) > 0 then raise notice 'attaquer : déjà à jour'; return; end if;
  d := pg_temp.remp(d,
'  v_chance := greatest(0.10, least(0.90, v_chance + bonus_proximite(v_proches) + bonus_batiments(v_attaquant_id, p_commune_code)));',
'  v_chance := greatest(0.10, least(0.90, v_chance + bonus_proximite(v_proches) + bonus_batiments(v_attaquant_id, p_commune_code)));
  v_chance := chance_debutant(debutant_actif(v_attaquant_id), v_attaquant_id, p_commune_code, v_chance);   -- s2-111 : bonus de débutant', 1, 'attaquer');
  execute d;
end $$;

-- Premiers pas : la roue coche l'étape 1 quand le pot est vide
do $$
declare d text := pg_get_functiondef('public.premiers_pas()'::regprocedure);
begin
  if position('s2-111' in d) > 0 then raise notice 'premiers_pas : déjà à jour'; return; end if;
  d := pg_temp.remp(d,
'               or exists (select 1 from front_liberations fl where fl.joueur_id = v_uid),',
'               or exists (select 1 from front_liberations fl where fl.joueur_id = v_uid)
               or exists (select 1 from roue_front_tours rt where rt.joueur_id = v_uid),   -- s2-111 : la roue, quand le pot est vide', 1, 'premiers_pas');
  execute d;
end $$;

commit;

-- Contrôle attendu : t | t | t | t | t | t | t
select position('s2-111' in pg_get_functiondef('public.apercu_attaque(text, text)'::regprocedure)) > 0    as apercu_ok,
       position('s2-111' in pg_get_functiondef('public.apercu_attaques(text[], text)'::regprocedure)) > 0 as liste_ok,
       position('s2-111' in pg_get_functiondef('public.attaquer(text, text)'::regprocedure)) > 0          as assaut_ok,
       position('s2-111' in pg_get_functiondef('public.premiers_pas()'::regprocedure)) > 0                as premiers_pas_ok,
       has_function_privilege('authenticated', 'public.debutant_etat()', 'execute')                      as etat_ok,
       not has_function_privilege('authenticated', 'public.chance_debutant(boolean, uuid, text, numeric)', 'execute')
       and not has_function_privilege('authenticated', 'public.debutant_actif(uuid)', 'execute')        as aides_privees,
       exists (select 1 from public.config_jeu where cle = 'debutant')                                   as reglages_ok;
