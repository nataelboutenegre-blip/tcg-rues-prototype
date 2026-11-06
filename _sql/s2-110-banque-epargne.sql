-- s2-110 (6/11/2026) : la Banque devient une épargne (décision de Nataël, 22 h 06).
-- Constat : la Banque ne recevait que le surplus des Fonderies ; un joueur qui
-- dépense au fur et à mesure n'y avait jamais rien (6 Banques prêtes, 0 lingot
-- dedans).
-- Désormais :
--   - on DÉPOSE soi-même des lingots dans sa Banque (60 au plus) ;
--   - ils rapportent 10 % par nuit (sans dépasser 60), versés vers 4 h 20 ;
--   - on les RETIRE quand on veut (même au-delà de la réserve des Fonderies :
--     la production s'arrête alors, comme une réserve pleine) ;
--   - à l'abri du pillage des Fonderies ; si on prend la commune de la Banque,
--     le contenu est perdu et l'attaquant en pille la moitié ; une bombe en
--     détruit 20 / 30 / 40 % ; toujours secrète.
-- La réserve des Fonderies ne gagne plus +60 avec la Banque.
-- Prérequis : s2-104. Testé sur la prod dans un bloc annulé.

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

alter table public.batiments add column if not exists contenu numeric not null default 0;

update public.config_jeu
   set valeur = (valeur::jsonb || '{"banque_interet": 0.10}'::jsonb)::text
 where cle = 'batiments' and not (valeur::jsonb ? 'banque_interet');

-- la réserve : seulement les Fonderies
create or replace function public.lingots_max(p_uid uuid)
 returns numeric language sql stable security definer set search_path to 'public' as $f$
  select lingots_max_fonderies(p_uid);   -- s2-110 : la Banque est une épargne à part
$f$;

create or replace function public.banque_deposer(p_lingots integer)
 returns jsonb language plpgsql security definer set search_path to 'public' as $f$
-- s2-110
declare
  v_uid uuid := auth.uid();
  b batiments;
  v numeric;
  v_max integer := coalesce(batiment_reglage('banque_reserve'), 60)::integer;
begin
  if v_uid is null then raise exception 'Non connecte'; end if;
  if p_lingots is null or p_lingots < 1 then raise exception 'Montant invalide'; end if;
  perform 1 from joueurs where id = v_uid for update;
  select * into b from batiments where joueur_id = v_uid and type = 'banque' for update;
  if b.id is null then raise exception 'Tu n''as pas de Banque'; end if;
  if b.pret_le > now() then raise exception 'Ta Banque n''est pas encore construite'; end if;
  if floor(b.contenu) + p_lingots > v_max then
    raise exception 'Ta Banque garde % lingots au plus : tu peux encore en déposer %', v_max, greatest(0, v_max - floor(b.contenu))::integer;
  end if;
  v := lingots_figer(v_uid);
  if v < p_lingots then raise exception 'Il te faut % lingots (tu en as %)', p_lingots, floor(v)::integer; end if;
  update joueurs set lingots = lingots - p_lingots where id = v_uid;
  update batiments set contenu = contenu + p_lingots where id = b.id;
  return jsonb_build_object('contenu', floor(b.contenu + p_lingots)::integer, 'lingots', floor(v - p_lingots)::integer);
end;
$f$;

create or replace function public.banque_retirer(p_lingots integer)
 returns jsonb language plpgsql security definer set search_path to 'public' as $f$
-- s2-110
declare
  v_uid uuid := auth.uid();
  b batiments;
  v numeric;
begin
  if v_uid is null then raise exception 'Non connecte'; end if;
  if p_lingots is null or p_lingots < 1 then raise exception 'Montant invalide'; end if;
  perform 1 from joueurs where id = v_uid for update;
  select * into b from batiments where joueur_id = v_uid and type = 'banque' for update;
  if b.id is null then raise exception 'Tu n''as pas de Banque'; end if;
  if floor(b.contenu) < p_lingots then raise exception 'Ta Banque ne contient que % lingots', floor(b.contenu)::integer; end if;
  v := lingots_figer(v_uid);
  update batiments set contenu = contenu - p_lingots where id = b.id;
  update joueurs set lingots = lingots + p_lingots where id = v_uid;
  return jsonb_build_object('contenu', floor(b.contenu - p_lingots)::integer, 'lingots', floor(v + p_lingots)::integer);
end;
$f$;

revoke all on function public.banque_deposer(integer), public.banque_retirer(integer) from public, anon;
grant execute on function public.banque_deposer(integer), public.banque_retirer(integer) to authenticated, service_role;

-- les intérêts, une fois par jour
create or replace function public.banque_interets()
 returns integer language plpgsql security definer set search_path to 'public' as $f$
-- s2-110 : +10 % par nuit, sans dépasser la capacité ; une seule passe par jour
declare
  v_jour date := (now() at time zone 'Europe/Paris')::date;
  n integer;
begin
  if exists (select 1 from config_jeu where cle = 'banque_interets' and valeur::jsonb ->> 'jour' = v_jour::text) then return 0; end if;
  insert into config_jeu(cle, valeur) values ('banque_interets', jsonb_build_object('jour', v_jour)::text)
  on conflict (cle) do update set valeur = excluded.valeur;
  update batiments
     set contenu = least(coalesce(batiment_reglage('banque_reserve'), 60), contenu * (1 + coalesce(batiment_reglage('banque_interet'), 0.10)))
   where type = 'banque' and pret_le <= now() and contenu > 0;
  get diagnostics n = row_count;
  return n;
end;
$f$;
revoke all on function public.banque_interets() from public, anon, authenticated;

do $$
begin
  if exists (select 1 from pg_extension where extname = 'pg_cron') then
    perform cron.unschedule(jobid) from cron.job where jobname = 'banque-interets';
    perform cron.schedule('banque-interets', '20 3 * * *', 'select public.banque_interets()');
  end if;
end $$;

-- la commune de la Banque prise : son contenu est perdu, l'attaquant en pille la moitié
do $$
declare d text := pg_get_functiondef('public.batiments_changement_proprio()'::regprocedure);
begin
  if position('s2-110' in d) > 0 then raise notice 'batiments_changement_proprio : déjà à jour'; return; end if;
  d := pg_temp.remp(d,
'elsif b.type = ''banque'' then   -- s2-104
      v := lingots_figer(b.joueur_id);
      v_banque := greatest(0, v - lingots_max_fonderies(b.joueur_id));
      delete from batiments where id = b.id;
      if v_banque > 0 then
        update joueurs set lingots = greatest(0, lingots - v_banque) where id = b.joueur_id;
        if v_conquete then',
'elsif b.type = ''banque'' then   -- s2-104, s2-110 : le contenu déposé
      v_banque := floor(coalesce(b.contenu, 0));
      delete from batiments where id = b.id;
      if v_banque > 0 then
        if v_conquete then', 1, 'banque prise');
  execute d;
end $$;

-- la bombe : 20 / 30 / 40 % du contenu déposé
do $$
declare d text := pg_get_functiondef('public.bombe_lacher(text)'::regprocedure);
begin
  if position('s2-110' in d) > 0 then raise notice 'bombe_lacher : déjà à jour'; return; end if;
  d := pg_temp.remp(d,
'    select b.joueur_id from batiments b join communes k on k.code = b.commune_code',
'    select b.id, b.joueur_id, b.contenu from batiments b join communes k on k.code = b.commune_code', 1, 'bombe (liste)');
  d := pg_temp.remp(d,
'    v_bv := lingots_figer(v_bq.joueur_id);
    v_bperte := floor(greatest(0, v_bv - lingots_max_fonderies(v_bq.joueur_id))
                      * coalesce(batiment_reglage(''banque_bombe'' || v_n), 0.2))::integer;
    if v_bperte > 0 then
      update joueurs set lingots = greatest(0, lingots - v_bperte) where id = v_bq.joueur_id;',
'    v_bperte := floor(coalesce(v_bq.contenu, 0) * coalesce(batiment_reglage(''banque_bombe'' || v_n), 0.2))::integer;   -- s2-110
    if v_bperte > 0 then
      update batiments set contenu = greatest(0, contenu - v_bperte) where id = v_bq.id;', 1, 'bombe (perte)');
  execute d;
end $$;

-- ce que le jeu affiche
do $$
declare d text := pg_get_functiondef('public.mes_batiments()'::regprocedure);
begin
  if position('s2-110' in d) > 0 then raise notice 'mes_batiments : déjà à jour'; return; end if;
  d := pg_temp.remp(d,
'''contenu'', case when b.pret_le <= now() then greatest(0, floor(v) - lingots_max_fonderies(v_uid))::integer else 0 end)',
'''contenu'', floor(b.contenu)::integer)   -- s2-110', 1, 'contenu');
  d := pg_temp.remp(d,
'''pillage'', round(batiment_reglage(''banque_pillage'') * 100)::integer,',
'''pillage'', round(batiment_reglage(''banque_pillage'') * 100)::integer,
                      ''interet'', round(coalesce(batiment_reglage(''banque_interet''), 0.10) * 100)::integer,   -- s2-110
                      ''epargne'', true,', 1, 'réglages');
  execute d;
end $$;

commit;

-- Contrôle attendu : t | t | t | t | t | t
select position('s2-110' in pg_get_functiondef('public.batiments_changement_proprio()'::regprocedure)) > 0 as prise_ok,
       position('s2-110' in pg_get_functiondef('public.bombe_lacher(text)'::regprocedure)) > 0                as bombe_ok,
       position('s2-110' in pg_get_functiondef('public.mes_batiments()'::regprocedure)) > 0                    as affichage_ok,
       has_function_privilege('authenticated', 'public.banque_deposer(integer)', 'execute')
       and has_function_privilege('authenticated', 'public.banque_retirer(integer)', 'execute')             as droits_ok,
       not has_function_privilege('authenticated', 'public.banque_interets()', 'execute')                    as interets_prives,
       case when not exists (select 1 from pg_extension where extname = 'pg_cron') then true
            else query_to_xml('select 1 from cron.job where jobname = ''banque-interets''', false, false, '')::text like '%<row>%' end as tache_ok;
