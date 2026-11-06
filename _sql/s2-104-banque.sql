-- ===========================================================================
--  TerraFront — s2-104 : la Banque (idée de Nataël, 5/11 ; aperçu validé le 6/11)
--
--  Un 4e bâtiment, secret comme le Centre de recherche :
--    - 20 lingots, prête en 6 h, une seule par joueur, il faut une Fonderie ;
--    - +60 lingots de réserve : ce qui dépasse la réserve des Fonderies
--      (30, ou 45 avec deux) est « dans la Banque » ;
--    - une Fonderie prise ne pille plus que la part des Fonderies ;
--    - commune de la Banque prise : Banque détruite, son contenu perdu, et
--      l'attaquant en pille la moitié ;
--    - bombe dont la zone couvre la Banque : elle perd 20 / 30 / 40 % de son
--      contenu selon le niveau (la Banque reste debout) ;
--    - invisible sur la carte pour les autres (batiments_visibles).
--  Réglages dans config_jeu 'batiments' (banques_ouvertes = interrupteur).
--
--  Les fonctions déjà touchées par le lot du 6/11 (mes_batiments) sont
--  modifiées en place, par remplacement de texte : à lancer APRÈS le lot.
--  Rejouable. Contrôle attendu : 20 | 60 | t | t | t | t | t | t | t
-- ===========================================================================
begin;

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

-- 1. réglages ---------------------------------------------------------------
update public.config_jeu
   set valeur = (valeur::jsonb || '{"banques_ouvertes": 1, "banque_prix": 20, "banque_reserve": 60, "banque_pillage": 0.5,
                                    "banque_bombe1": 0.2, "banque_bombe2": 0.3, "banque_bombe3": 0.4}'::jsonb)::text
 where cle = 'batiments' and not (valeur::jsonb ? 'banque_prix');

alter table public.batiments drop constraint if exists batiments_type_check;
alter table public.batiments add constraint batiments_type_check check (type in ('fonderie', 'forteresse', 'centre', 'banque'));

-- 2. la réserve -------------------------------------------------------------
-- la réserve des Fonderies seules (30 / 45), comme avant
create or replace function public.lingots_max_fonderies(p_uid uuid)
 returns numeric language sql stable security definer set search_path to 'public' as $f$
  select case when (select count(*) from batiments f where f.joueur_id = p_uid and f.type = 'fonderie') >= 2
              then batiment_reglage('fonderie_max2') else batiment_reglage('fonderie_max') end;
$f$;
-- s2-104 : + la Banque, une fois construite
create or replace function public.lingots_max(p_uid uuid)
 returns numeric language sql stable security definer set search_path to 'public' as $f$
  select lingots_max_fonderies(p_uid)
       + case when exists (select 1 from batiments b where b.joueur_id = p_uid and b.type = 'banque' and b.pret_le <= now())
              then coalesce(batiment_reglage('banque_reserve'), 60) else 0 end;
$f$;
revoke all on function public.lingots_max_fonderies(uuid) from public, anon, authenticated;

-- 3. construire / annuler ---------------------------------------------------
do $$
declare d text := pg_get_functiondef('public.batiment_construire(text, text)'::regprocedure);
begin
  if position('s2-104' in d) > 0 then raise notice 'batiment_construire : déjà à jour'; return; end if;
  d := pg_temp.remp(d, 'if p_type not in (''fonderie'', ''forteresse'', ''centre'') then raise exception ''Bâtiment inconnu''; end if;',
    'if p_type not in (''fonderie'', ''forteresse'', ''centre'', ''banque'') then raise exception ''Bâtiment inconnu''; end if;   -- s2-104', 1, 'batiment_construire (types)');
  d := pg_temp.remp(d, '  else
    if v_nf = 0 then raise exception ''Il te faut d''''abord une Fonderie''; end if;',
    '  elsif p_type = ''banque'' then   -- s2-104 : la Banque
    if coalesce(batiment_reglage(''banques_ouvertes''), 0) < 1 then raise exception ''La Banque n''''est pas encore ouverte''; end if;
    if v_nf = 0 then raise exception ''Il te faut d''''abord une Fonderie''; end if;
    if exists (select 1 from batiments b where b.joueur_id = v_uid and b.type = ''banque'') then
      raise exception ''Tu as déjà une Banque'';
    end if;
    v_prix := batiment_reglage(''banque_prix'');
    v := lingots_figer(v_uid);
    if v < v_prix then raise exception ''Il te faut % lingots (tu en as %)'', v_prix::integer, floor(v)::integer; end if;
    update joueurs set lingots = lingots - v_prix where id = v_uid;
  else
    if v_nf = 0 then raise exception ''Il te faut d''''abord une Fonderie''; end if;', 1, 'batiment_construire (banque)');
  execute d;
end $$;

do $$
declare d text := pg_get_functiondef('public.batiment_annuler(text, text)'::regprocedure);
begin
  if position('''banque''' in d) > 0 then raise notice 'batiment_annuler : déjà à jour'; return; end if;
  d := pg_temp.remp(d, '    when ''centre''     then batiment_reglage(''centre_prix'')',
    '    when ''centre''     then batiment_reglage(''centre_prix'')
    when ''banque''     then batiment_reglage(''banque_prix'')   -- s2-104', 1, 'batiment_annuler');
  execute d;
end $$;

-- 4. conquête : pillage de la Fonderie (hors Banque) et de la Banque ----------
do $$
declare d text := pg_get_functiondef('public.batiments_changement_proprio()'::regprocedure);
begin
  if position('s2-104' in d) > 0 then raise notice 'batiments_changement_proprio : déjà à jour'; return; end if;
  -- la Fonderie ne pille plus que la part des Fonderies
  d := pg_temp.remp(d, 'v_pille := floor(v * batiment_reglage(''pillage'') / greatest(v_nf, 1))::integer;',
    'v_pille := floor(least(v, lingots_max_fonderies(b.joueur_id)) * batiment_reglage(''pillage'') / greatest(v_nf, 1))::integer;   -- s2-104 : la Banque est à l''abri', 1, 'pillage Fonderie');
  -- la Banque : contenu perdu, l'attaquant en pille la moitié
  d := pg_temp.remp(d, '    elsif b.type = ''centre'' then',
    '    elsif b.type = ''banque'' then   -- s2-104
      v := lingots_figer(b.joueur_id);
      v_banque := greatest(0, v - lingots_max_fonderies(b.joueur_id));
      delete from batiments where id = b.id;
      if v_banque > 0 then
        update joueurs set lingots = greatest(0, lingots - v_banque) where id = b.joueur_id;
        if v_conquete then
          v_pille := floor(v_banque * coalesce(batiment_reglage(''banque_pillage''), 0.5))::integer;
          perform lingots_figer(new.joueur_id);
          update joueurs set lingots = lingots + v_pille where id = new.joueur_id;
        end if;
      end if;
    elsif b.type = ''centre'' then', 1, 'banque');
  d := pg_temp.remp(d, '  v_conquete boolean;', '  v_conquete boolean;
  v_banque numeric;', 1, 'déclaration');
  execute d;
end $$;

-- 5. la bombe : la Banque dans la zone perd une part de son contenu ------------
alter table public.bombes_degats add column if not exists banque_lingots integer not null default 0;
do $$
declare d text := pg_get_functiondef('public.bombe_lacher(text)'::regprocedure);
begin
  if position('s2-104' in d) > 0 then raise notice 'bombe_lacher : déjà à jour'; return; end if;
  d := pg_temp.remp(d, '  select coalesce(sum(garnisons), 0), coalesce(sum(forteresses), 0) into v_g, v_f from bombes_degats where bombe_id = v_id;',
    '  -- s2-104 : les Banques de la zone perdent 20 / 30 / 40 % de leur contenu (elles restent debout)
  for v_bq in
    select b.joueur_id from batiments b join communes k on k.code = b.commune_code
     where b.type = ''banque'' and b.pret_le <= now() and dist_km(k.latitude, k.longitude, v_c.lat, v_c.lon) <= v_r
  loop
    v_bv := lingots_figer(v_bq.joueur_id);
    v_bperte := floor(greatest(0, v_bv - lingots_max_fonderies(v_bq.joueur_id))
                      * coalesce(batiment_reglage(''banque_bombe'' || v_n), 0.2))::integer;
    if v_bperte > 0 then
      update joueurs set lingots = greatest(0, lingots - v_bperte) where id = v_bq.joueur_id;
      insert into bombes_degats(bombe_id, joueur_id, banque_lingots) values (v_id, v_bq.joueur_id, v_bperte)
      on conflict (bombe_id, joueur_id) do update set banque_lingots = excluded.banque_lingots;
    end if;
  end loop;
  select coalesce(sum(garnisons), 0), coalesce(sum(forteresses), 0) into v_g, v_f from bombes_degats where bombe_id = v_id;', 1, 'bombe_lacher');
  d := pg_temp.remp(d, '  v_g integer; v_f integer; v_nb integer;', '  v_g integer; v_f integer; v_nb integer;
  v_bq record; v_bv numeric; v_bperte integer;', 1, 'bombe_lacher (déclarations)');
  d := pg_temp.remp(d, '''forteresses_moi'', coalesce((select forteresses from bombes_degats where bombe_id = v_id and joueur_id = v_uid), 0),',
    '''forteresses_moi'', coalesce((select forteresses from bombes_degats where bombe_id = v_id and joueur_id = v_uid), 0),
    ''banque_moi'', coalesce((select banque_lingots from bombes_degats where bombe_id = v_id and joueur_id = v_uid), 0),', 1, 'bombe_lacher (retour)');
  execute d;
end $$;

-- la victime voit ce que sa Banque a perdu (colonne en plus à la fin : la fonction est recréée)
drop function if exists public.bombes_alertes(integer);
create function public.bombes_alertes(p_jours integer default 2)
 returns table(type text, id bigint, le timestamptz, dept text, cible_code text, cible_nom text, lanceur_pseudo text,
               rayon_km integer, garnisons integer, forteresses integer, mes_garnisons integer, mes_forteresses integer,
               moi boolean, etat text, mes_banque integer)
 language sql stable security definer set search_path to 'public' as $f$
  select * from (
    select 'preparation'::text, p.id, p.commence_le, p.dept, null::text, null::text, null::text,
           null::integer, null::integer, null::integer, null::integer, null::integer,
           p.joueur_id = auth.uid(), p.etat, null::integer
      from bombes_preparations p
     where p.commence_le > now() - make_interval(days => least(greatest(p_jours, 1), 14))
    union all
    select 'bombe', b.id, b.le, c.departement, b.cible_code, c.nom, j.pseudo,
           b.rayon_km::integer, b.garnisons, b.forteresses, coalesce(d.garnisons, 0), coalesce(d.forteresses, 0),
           b.lanceur = auth.uid(), case when b.fin > now() then 'active' else 'finie' end, coalesce(d.banque_lingots, 0)
      from bombes b join communes c on c.code = b.cible_code left join joueurs j on j.id = b.lanceur
      left join bombes_degats d on d.bombe_id = b.id and d.joueur_id = auth.uid()
     where b.le > now() - make_interval(days => least(greatest(p_jours, 1), 14))
  ) x
  where auth.uid() is not null
  order by 3 desc
  limit 40;
$f$;
revoke all on function public.bombes_alertes(integer) from public, anon;
grant execute on function public.bombes_alertes(integer) to authenticated, service_role;

-- 6. secrète : seul son propriétaire la voit sur la carte ----------------------
do $$
declare d text := pg_get_functiondef('public.batiments_visibles()'::regprocedure);
begin
  if position('banque' in d) > 0 then raise notice 'batiments_visibles : déjà à jour'; return; end if;
  d := pg_temp.remp(d, 'and (b.type <> ''centre'' or b.joueur_id = auth.uid() or centre_devoile(b.joueur_id, b.commune_code));',
    'and (b.type not in (''centre'', ''banque'') or b.joueur_id = auth.uid()
          or (b.type = ''centre'' and centre_devoile(b.joueur_id, b.commune_code)));   -- s2-104 : la Banque reste secrète', 1, 'batiments_visibles');
  execute d;
end $$;

-- 7. mes_batiments : la Banque, sa part de la réserve, ses réglages -------------
do $$
declare d text := pg_get_functiondef('public.mes_batiments()'::regprocedure);
begin
  if position('s2-104' in d) > 0 then raise notice 'mes_batiments : déjà à jour'; return; end if;
  d := pg_temp.remp(d, '''bombes_ouvertes'', bombes_ouvertes(),',
    '''bombes_ouvertes'', bombes_ouvertes(),
    -- s2-104 : la Banque
    ''banques_ouvertes'', coalesce(batiment_reglage(''banques_ouvertes''), 0) >= 1,
    ''max_fonderies'', lingots_max_fonderies(v_uid)::integer,
    ''banque'', (select jsonb_build_object(''code'', b.commune_code, ''nom'', c.nom, ''dept'', c.departement,
                      ''pret_le'', b.pret_le, ''pret'', b.pret_le <= now(),
                      ''contenu'', case when b.pret_le <= now() then greatest(0, floor(v) - lingots_max_fonderies(v_uid))::integer else 0 end)
                 from batiments b join communes c on c.code = b.commune_code
                where b.joueur_id = v_uid and b.type = ''banque''),
    ''banque_reglages'', jsonb_build_object(''prix'', batiment_reglage(''banque_prix'')::integer,
                      ''reserve'', batiment_reglage(''banque_reserve'')::integer,
                      ''pillage'', round(batiment_reglage(''banque_pillage'') * 100)::integer,
                      ''bombe'', jsonb_build_array(round(batiment_reglage(''banque_bombe1'') * 100)::integer,
                                                    round(batiment_reglage(''banque_bombe2'') * 100)::integer,
                                                    round(batiment_reglage(''banque_bombe3'') * 100)::integer)),', 1, 'mes_batiments');
  execute d;
end $$;

commit;

-- Contrôle : 20 | 60 | t | t | t | t | t | t | t
select batiment_reglage('banque_prix')::integer                                                         as prix,
       batiment_reglage('banque_reserve')::integer                                                      as reserve,
       position('s2-104' in pg_get_functiondef('public.batiment_construire(text, text)'::regprocedure)) > 0 as construire,
       position('banque' in pg_get_functiondef('public.batiment_annuler(text, text)'::regprocedure)) > 0    as annuler,
       position('s2-104' in pg_get_functiondef('public.batiments_changement_proprio()'::regprocedure)) > 0  as conquete,
       position('s2-104' in pg_get_functiondef('public.bombe_lacher(text)'::regprocedure)) > 0              as bombe,
       position('banque' in pg_get_functiondef('public.batiments_visibles()'::regprocedure)) > 0            as secrete,
       position('s2-104' in pg_get_functiondef('public.mes_batiments()'::regprocedure)) > 0                 as mes_batiments,
       has_function_privilege('authenticated', 'public.bombes_alertes(integer)', 'execute')                as alertes;
