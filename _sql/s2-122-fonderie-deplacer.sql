-- s2-122 (8/11/2026) : déplacer une Fonderie (Maroli, Discord 8/11 18 h 26 ; règles validées par Nataël à 19 h 09).
--
-- Comme les forteresses (s2-116) :
--   - fonderie_deplacer_prix lingots (10) ;
--   - 6 h de chantier à la nouvelle adresse (construction_h) ; pendant ce temps elle ne
--     produit rien (lingots_lire ne compte que les Fonderies prêtes) ; lingots_figer avant le
--     déplacement crédite tout ce qu'elle a produit jusque-là ;
--   - la réserve maximale (30, 45 avec deux Fonderies) ne change pas ;
--   - refusé pendant un assaut sur sa commune, ou s'il y a déjà une Fonderie à l'arrivée ;
--   - même bâtiment (mise à jour de la ligne) : compté une seule fois au score ;
--   - un déplacement ne s'annule pas ;
--   - pendant le chantier elle reste pillable si on prend sa nouvelle commune (comme avant).

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

-- 1. Réglage
update public.config_jeu
   set valeur = (valeur::jsonb || '{"fonderie_deplacer_prix": 10}'::jsonb)::text
 where cle = 'batiments';

-- 2. Déplacer
create or replace function public.fonderie_deplacer(p_depuis text, p_vers text)
 returns jsonb language plpgsql security definer set search_path to 'public' as $f$
-- s2-122 : une Fonderie prête va sur une autre de ses communes ; 10 lingots, 6 h sans production
declare
  v_uid uuid := auth.uid();
  b record;
  v numeric;
  v_prix numeric := coalesce(batiment_reglage('fonderie_deplacer_prix'), 10);
  v_tier text;
begin
  if v_uid is null then raise exception 'Non connecte'; end if;
  if not batiments_ouverts() then raise exception 'Les bâtiments ne sont pas encore ouverts'; end if;
  perform 1 from joueurs where id = v_uid for update;   -- deux clics ne paient pas deux fois
  select * into b from batiments where joueur_id = v_uid and type = 'fonderie' and commune_code = p_depuis;
  if b.id is null then raise exception 'Cette Fonderie n''existe pas (ou plus)'; end if;
  if b.pret_le > now() then raise exception 'Cette Fonderie est encore en chantier : attends qu''elle soit prête pour la déplacer'; end if;
  if p_vers = p_depuis then raise exception 'Ta Fonderie est déjà ici'; end if;
  if not exists (select 1 from possessions p where p.commune_code = p_vers and p.joueur_id = v_uid) then
    raise exception 'Cette commune ne t''appartient pas';
  end if;
  if exists (select 1 from batiments x where x.commune_code = p_vers and x.type = 'fonderie') then
    raise exception 'Il y a déjà une Fonderie ici';
  end if;
  if exists (select 1 from sieges s where s.commune_code = p_depuis and coalesce(s.victoires_consecutives, 0) > 0) then
    raise exception 'Cette Fonderie est attaquée : impossible de la déplacer pendant l''assaut';
  end if;
  v := lingots_figer(v_uid);   -- avant le déplacement : sa production jusqu'ici est comptée
  if v < v_prix then raise exception 'Il te faut % lingots (tu en as %)', v_prix::integer, floor(v)::integer; end if;
  update batiments
     set commune_code = p_vers,
         pret_le = now() + make_interval(hours => batiment_reglage('construction_h')::integer),
         deplacee_le = now()
   where id = b.id;
  if v_prix > 0 then update joueurs set lingots = lingots - v_prix where id = v_uid; end if;
  select c.tier into v_tier from communes c where c.code = p_vers;
  perform noter_journal('fonderie', v_uid, null, p_vers, v_tier);
  return mes_batiments();
end;
$f$;
revoke execute on function public.fonderie_deplacer(text, text) from public, anon;
grant execute on function public.fonderie_deplacer(text, text) to authenticated;

-- 3. Un déplacement ne s'annule pas ; mes_batiments dit si une Fonderie est en route
do $$
declare d text;
begin
  d := pg_get_functiondef('public.batiment_annuler(text, text)'::regprocedure);
  d := pg_temp.remp(d,
$a$  if b.type in ('forteresse', 'banque') and b.deplacee_le is not null then   -- s2-116, s2-117$a$,
$a$  if b.type in ('forteresse', 'banque', 'fonderie') and b.deplacee_le is not null then   -- s2-116, s2-117, s2-122$a$, 1, 'batiment_annuler');
  execute d;

  d := pg_get_functiondef('public.mes_batiments()'::regprocedure);
  d := pg_temp.remp(d,
$a$'fonderies', coalesce((select jsonb_agg(jsonb_build_object($a$,
$a$'fonderies', coalesce((select jsonb_agg(jsonb_build_object('deplacee', b.deplacee_le is not null and b.pret_le > now(),   -- s2-122
        $a$, 1, 'mes_batiments (fonderies)');
  d := pg_temp.remp(d,
$a$'forteresse_deplacer_prix', coalesce(batiment_reglage('forteresse_deplacer_prix'), 10)::integer,   -- s2-116$a$,
$a$'forteresse_deplacer_prix', coalesce(batiment_reglage('forteresse_deplacer_prix'), 10)::integer,   -- s2-116
        'fonderie_deplacer_prix', coalesce(batiment_reglage('fonderie_deplacer_prix'), 10)::integer,   -- s2-122$a$, 1, 'mes_batiments (réglages)');
  execute d;
end $$;

commit;

-- Contrôle : t | t | t | 10
select has_function_privilege('authenticated', 'public.fonderie_deplacer(text, text)', 'execute')
         and not has_function_privilege('anon', 'public.fonderie_deplacer(text, text)', 'execute') as droits_ok,
       position('s2-122' in pg_get_functiondef('public.batiment_annuler(text, text)'::regprocedure)) > 0 as annuler_ok,
       position('s2-122' in pg_get_functiondef('public.mes_batiments()'::regprocedure)) > 0 as mes_ok,
       public.batiment_reglage('fonderie_deplacer_prix') as prix;
