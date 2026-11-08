-- s2-116 (8/11/2026) : déplacer une Forteresse (demande de Nataël, 8/11).
--
-- Une Forteresse active (chantier fini) peut aller sur une autre de ses communes :
--   - forteresse_deplacer_prix lingots (10 : la moitié de sa construction) ;
--   - 6 h de chantier à la nouvelle adresse (construction_h), sans aucun effet
--     pendant ce temps (bonus_batiments ne compte que les bâtiments prêts) ;
--   - refusé si sa commune est attaquée, ou s'il y a déjà une forteresse à l'arrivée ;
--   - c'est le même bâtiment (mise à jour de la ligne, pas de nouvelle) : il reste
--     compté une seule fois au score, et le reste même s'il est détruit pendant
--     le chantier (il était déjà acquis) ;
--   - un déplacement ne s'annule pas (sinon : déplacer pour 10, annuler et
--     récupérer 20) ;
--   - le journal note la forteresse à sa nouvelle adresse, comme une construction.

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

-- 1. Réglage et colonne
update public.config_jeu
   set valeur = (valeur::jsonb || '{"forteresse_deplacer_prix": 10}'::jsonb)::text
 where cle = 'batiments';
alter table public.batiments add column if not exists deplacee_le timestamptz;

-- 2. Déplacer
create or replace function public.forteresse_deplacer(p_depuis text, p_vers text)
 returns jsonb language plpgsql security definer set search_path to 'public' as $f$
-- s2-116 : une forteresse active va sur une autre de ses communes ; 10 lingots, 6 h sans effet
declare
  v_uid uuid := auth.uid();
  b record;
  v numeric;
  v_prix numeric := coalesce(batiment_reglage('forteresse_deplacer_prix'), 10);
  v_tier text;
begin
  if v_uid is null then raise exception 'Non connecte'; end if;
  if not batiments_ouverts() then raise exception 'Les bâtiments ne sont pas encore ouverts'; end if;
  perform 1 from joueurs where id = v_uid for update;   -- deux clics ne paient pas deux fois
  select * into b from batiments where joueur_id = v_uid and type = 'forteresse' and commune_code = p_depuis;
  if b.id is null then raise exception 'Cette forteresse n''existe pas (ou plus)'; end if;
  if b.pret_le > now() then raise exception 'Cette forteresse est encore en chantier : attends qu''elle soit prête pour la déplacer'; end if;
  if p_vers = p_depuis then raise exception 'Ta forteresse est déjà ici'; end if;
  if not exists (select 1 from possessions p where p.commune_code = p_vers and p.joueur_id = v_uid) then
    raise exception 'Cette commune ne t''appartient pas';
  end if;
  if exists (select 1 from batiments x where x.commune_code = p_vers and x.type = 'forteresse') then
    raise exception 'Il y a déjà une forteresse ici';
  end if;
  if exists (select 1 from sieges s where s.commune_code = p_depuis and coalesce(s.victoires_consecutives, 0) > 0) then
    raise exception 'Cette forteresse est attaquée : impossible de la déplacer pendant l''assaut';
  end if;
  v := lingots_figer(v_uid);
  if v < v_prix then raise exception 'Il te faut % lingots (tu en as %)', v_prix::integer, floor(v)::integer; end if;
  update batiments
     set commune_code = p_vers,
         pret_le = now() + make_interval(hours => batiment_reglage('construction_h')::integer),
         deplacee_le = now()
   where id = b.id;
  if v_prix > 0 then update joueurs set lingots = lingots - v_prix where id = v_uid; end if;
  select c.tier into v_tier from communes c where c.code = p_vers;
  perform noter_journal('forteresse', v_uid, null, p_vers, v_tier);
  return mes_batiments();
end;
$f$;
revoke execute on function public.forteresse_deplacer(text, text) from public, anon;
grant execute on function public.forteresse_deplacer(text, text) to authenticated;

-- 3. Un déplacement ne s'annule pas ; une forteresse déplacée reste acquise au score
do $$
declare d text;
begin
  d := pg_get_functiondef('public.batiment_annuler(text, text)'::regprocedure);
  d := pg_temp.remp(d,
$a$  if b.pret_le <= now() then raise exception 'Ce bâtiment est déjà construit : on ne peut plus l''annuler'; end if;$a$,
$a$  if b.pret_le <= now() then raise exception 'Ce bâtiment est déjà construit : on ne peut plus l''annuler'; end if;
  if b.type = 'forteresse' and b.deplacee_le is not null then   -- s2-116
    raise exception 'Une forteresse en déplacement ne s''annule pas';
  end if;$a$, 1, 'batiment_annuler');
  execute d;

  d := pg_get_functiondef('public.batiments_historique_noter()'::regprocedure);
  d := pg_temp.remp(d,
$a$  elsif old.pret_le > now() then$a$,
$a$  elsif old.pret_le > now() and old.deplacee_le is null then   -- s2-116 : une forteresse déplacée était déjà acquise$a$, 1, 'batiments_historique_noter');
  execute d;

  d := pg_get_functiondef('public.mes_batiments()'::regprocedure);
  d := pg_temp.remp(d,
$a$'forteresses', coalesce((select jsonb_agg(jsonb_build_object($a$,
$a$'forteresses', coalesce((select jsonb_agg(jsonb_build_object('deplacee', b.deplacee_le is not null and b.pret_le > now(), $a$, 1, 'mes_batiments (forteresses)');
  d := pg_temp.remp(d,
$a$'forteresse_max', batiment_reglage('forteresse_max')::integer,$a$,
$a$'forteresse_max', batiment_reglage('forteresse_max')::integer,
        'forteresse_deplacer_prix', coalesce(batiment_reglage('forteresse_deplacer_prix'), 10)::integer,   -- s2-116$a$, 1, 'mes_batiments (réglages)');
  execute d;
end $$;

commit;

-- Contrôle : t | t | t | t | t | 10
select exists (select 1 from information_schema.columns where table_schema = 'public' and table_name = 'batiments' and column_name = 'deplacee_le') as colonne_ok,
       has_function_privilege('authenticated', 'public.forteresse_deplacer(text, text)', 'execute')
         and not has_function_privilege('anon', 'public.forteresse_deplacer(text, text)', 'execute') as droits_ok,
       position('s2-116' in pg_get_functiondef('public.batiment_annuler(text, text)'::regprocedure)) > 0 as annuler_ok,
       position('s2-116' in pg_get_functiondef('public.batiments_historique_noter()'::regprocedure)) > 0 as historique_ok,
       position('s2-116' in pg_get_functiondef('public.mes_batiments()'::regprocedure)) > 0 as mes_ok,
       public.batiment_reglage('forteresse_deplacer_prix') as prix;
