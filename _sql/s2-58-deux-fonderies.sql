-- ===========================================================================
--  s2-58 — Bâtiments : une 2e Fonderie (28/10, décision de Nataël)
--  - 2 Fonderies au plus par joueur. La 1re reste gratuite ; la 2e coûte
--    30 lingots. Chacune produit 10 lingots par jour.
--  - Réserve partagée : 30 au plus avec une Fonderie, 45 avec deux.
--  - Prendre une Fonderie pille la part de cette Fonderie : 50 % de la
--    réserve divisés par le nombre de Fonderies du joueur (25 % s'il en a 2).
--  - Réglages dans config_jeu 'batiments' (fonderies_max, fonderie2_prix,
--    fonderie_max2), modifiables sans code.
--  Remplace lingots_lire, mes_batiments, batiment_construire,
--  batiments_changement_proprio (toutes de s2-48, mêmes signatures).
--  Rejouable. Contrôle attendu : false | 2 | 30 | 45
-- ===========================================================================
begin;

update public.config_jeu
   set valeur = (valeur::jsonb || '{"fonderies_max": 2, "fonderie2_prix": 30, "fonderie_max2": 45}'::jsonb)::text
 where cle = 'batiments';

create or replace function public.batiment_reglage(p_cle text)
 returns numeric language sql stable security definer set search_path to 'public'
as $f$
  select coalesce(
    (select (c.valeur::jsonb ->> p_cle)::numeric from config_jeu c where c.cle = 'batiments'),
    case p_cle when 'fonderie_production' then 10 when 'fonderie_max' then 30 when 'construction_h' then 24
               when 'forteresse_prix' then 20 when 'forteresse_max' then 3 when 'forteresse_defense' then 0.15
               when 'forteresse_appui' then 0.05 when 'forteresse_rayon_km' then 20 when 'pillage' then 0.5
               when 'fonderies_max' then 2 when 'fonderie2_prix' then 30 when 'fonderie_max2' then 45 end);
$f$;

drop index if exists public.batiments_une_fonderie;

-- la réserve maximale du joueur : 30 avec une Fonderie, 45 avec deux
create or replace function public.lingots_max(p_uid uuid)
 returns numeric language sql stable security definer set search_path to 'public'
as $f$
  select case when (select count(*) from batiments f where f.joueur_id = p_uid and f.type = 'fonderie') >= 2
              then batiment_reglage('fonderie_max2') else batiment_reglage('fonderie_max') end;
$f$;

-- réserve actuelle : chaque Fonderie prête produit depuis la dernière mise à jour (ou depuis qu'elle est prête)
create or replace function public.lingots_lire(p_uid uuid)
 returns numeric language sql stable security definer set search_path to 'public'
as $f$
  select case
    when x.base >= x.mx then x.base
    else least(x.mx, x.base + batiment_reglage('fonderie_production') * coalesce((
           select sum(greatest(0, extract(epoch from (now() - greatest(j.lingots_maj, f.pret_le)))))
             from batiments f where f.joueur_id = j.id and f.type = 'fonderie' and f.pret_le <= now()), 0) / 86400.0)
  end
  from joueurs j
  cross join lateral (select case when j.lingots_saison is not distinct from saison_en_cours_id()
                                  then j.lingots else 0 end as base,
                             lingots_max(j.id) as mx) x
  where j.id = p_uid;
$f$;

create or replace function public.mes_batiments()
 returns jsonb language plpgsql stable security definer set search_path to 'public'
as $f$
declare
  v_uid uuid := auth.uid();
  v numeric;
  v_prod numeric := batiment_reglage('fonderie_production');
  v_max numeric;
  v_pretes integer;
  v_tot numeric;
begin
  if v_uid is null then raise exception 'Non connecte'; end if;
  v := coalesce(lingots_lire(v_uid), 0);
  v_max := lingots_max(v_uid);
  select count(*) into v_pretes from batiments b where b.joueur_id = v_uid and b.type = 'fonderie' and b.pret_le <= now();
  v_tot := v_prod * v_pretes;
  return jsonb_build_object(
    'ouverts', batiments_ouverts(),
    'lingots', floor(v)::integer,
    'max', v_max::integer,
    'production', v_prod::integer,
    'production_totale', v_tot::integer,
    'prochain_dans', case when v_tot > 0 and v < v_max then ceil((1 - (v - floor(v))) * 86400.0 / v_tot)::integer end,
    -- la plus ancienne (pour les versions du jeu qui n'en connaissent qu'une)
    'fonderie', (select jsonb_build_object('code', b.commune_code, 'nom', c.nom, 'dept', c.departement,
                        'pret_le', b.pret_le, 'pret', b.pret_le <= now())
                   from batiments b join communes c on c.code = b.commune_code
                  where b.joueur_id = v_uid and b.type = 'fonderie' order by b.cree_le limit 1),
    'fonderies', coalesce((select jsonb_agg(jsonb_build_object(
        'code', b.commune_code, 'nom', c.nom, 'dept', c.departement,
        'pret_le', b.pret_le, 'pret', b.pret_le <= now()) order by b.cree_le)
        from batiments b join communes c on c.code = b.commune_code
       where b.joueur_id = v_uid and b.type = 'fonderie'), '[]'::jsonb),
    'forteresses', coalesce((select jsonb_agg(jsonb_build_object(
        'code', b.commune_code, 'nom', c.nom, 'dept', c.departement,
        'pret_le', b.pret_le, 'pret', b.pret_le <= now()) order by b.cree_le)
        from batiments b join communes c on c.code = b.commune_code
       where b.joueur_id = v_uid and b.type = 'forteresse'), '[]'::jsonb),
    'reglages', jsonb_build_object(
        'forteresse_prix', batiment_reglage('forteresse_prix')::integer,
        'forteresse_max', batiment_reglage('forteresse_max')::integer,
        'forteresse_defense', round(batiment_reglage('forteresse_defense') * 100)::integer,
        'forteresse_appui', round(batiment_reglage('forteresse_appui') * 100)::integer,
        'rayon_km', batiment_reglage('forteresse_rayon_km')::integer,
        'construction_h', batiment_reglage('construction_h')::integer,
        'pillage', round(batiment_reglage('pillage') * 100)::integer,
        'fonderies_max', batiment_reglage('fonderies_max')::integer,
        'fonderie2_prix', batiment_reglage('fonderie2_prix')::integer,
        'fonderie_max2', batiment_reglage('fonderie_max2')::integer));
end;
$f$;

create or replace function public.batiment_construire(p_code text, p_type text)
 returns jsonb language plpgsql security definer set search_path to 'public'
as $f$
declare
  v_uid uuid := auth.uid();
  v numeric;
  v_prix numeric;
  v_nf integer;
begin
  if v_uid is null then raise exception 'Non connecte'; end if;
  if not batiments_ouverts() then raise exception 'Les bâtiments ne sont pas encore ouverts'; end if;
  if p_type not in ('fonderie', 'forteresse') then raise exception 'Bâtiment inconnu'; end if;
  perform 1 from joueurs where id = v_uid for update;
  if not exists (select 1 from possessions p where p.commune_code = p_code and p.joueur_id = v_uid) then
    raise exception 'Cette commune ne t''appartient pas';
  end if;
  if exists (select 1 from batiments b where b.commune_code = p_code and b.type = p_type) then
    raise exception 'Il y a déjà ce bâtiment ici';
  end if;
  select count(*) into v_nf from batiments b where b.joueur_id = v_uid and b.type = 'fonderie';

  if p_type = 'fonderie' then
    if v_nf >= batiment_reglage('fonderies_max') then
      raise exception 'Tu as déjà % Fonderies', batiment_reglage('fonderies_max')::integer;
    end if;
    v := lingots_figer(v_uid);
    if v_nf >= 1 then   -- la 2e se paie
      v_prix := batiment_reglage('fonderie2_prix');
      if v < v_prix then raise exception 'Il te faut % lingots (tu en as %)', v_prix::integer, floor(v)::integer; end if;
      update joueurs set lingots = lingots - v_prix where id = v_uid;
    end if;
  else
    if v_nf = 0 then raise exception 'Il te faut d''abord une Fonderie'; end if;
    if (select count(*) from batiments b where b.joueur_id = v_uid and b.type = 'forteresse')
       >= batiment_reglage('forteresse_max') then
      raise exception 'Tu as déjà % forteresses', batiment_reglage('forteresse_max')::integer;
    end if;
    v_prix := batiment_reglage('forteresse_prix');
    v := lingots_figer(v_uid);
    if v < v_prix then
      raise exception 'Il te faut % lingots (tu en as %)', v_prix::integer, floor(v)::integer;
    end if;
    update joueurs set lingots = lingots - v_prix where id = v_uid;
  end if;

  insert into batiments(joueur_id, commune_code, type, pret_le)
  values (v_uid, p_code, p_type, now() + make_interval(hours => batiment_reglage('construction_h')::integer));
  return mes_batiments();
end;
$f$;

-- destruction (et pillage) : la part de la Fonderie prise
create or replace function public.batiments_changement_proprio()
 returns trigger language plpgsql security definer set search_path to 'public'
as $f$
declare
  b record;
  v numeric;
  v_nf integer;
  v_pille integer;
  v_conquete boolean;
begin
  if tg_op = 'UPDATE' and new.joueur_id is not distinct from old.joueur_id then return null; end if;
  v_conquete := tg_op = 'UPDATE' and new.joueur_id is not null
                and new.conquise_le is distinct from old.conquise_le and new.conquise_le is not null;
  for b in select * from batiments where commune_code = old.commune_code loop
    if b.type = 'fonderie' then
      v := lingots_figer(b.joueur_id);   -- avant la destruction : la production jusqu'ici est comptée
      select count(*) into v_nf from batiments f where f.joueur_id = b.joueur_id and f.type = 'fonderie';
      delete from batiments where id = b.id;
      if v_conquete and v > 0 then
        v_pille := floor(v * batiment_reglage('pillage') / greatest(v_nf, 1))::integer;
        update joueurs set lingots = lingots - v_pille where id = b.joueur_id;
        perform lingots_figer(new.joueur_id);
        update joueurs set lingots = lingots + v_pille where id = new.joueur_id;
      end if;
      -- la réserve ne dépasse plus le nouveau plafond (45 -> 30 si on perd la 2e)
      update joueurs set lingots = least(lingots, lingots_max(b.joueur_id)) where id = b.joueur_id;
    else
      delete from batiments where id = b.id;
    end if;
  end loop;
  return null;
exception when others then
  raise warning 'batiments_changement_proprio : %', sqlerrm;
  return null;
end;
$f$;

revoke all on function public.lingots_max(uuid), public.lingots_lire(uuid), public.batiments_changement_proprio() from public, anon, authenticated;
revoke all on function public.mes_batiments(), public.batiment_construire(text, text) from public, anon;
grant execute on function public.mes_batiments(), public.batiment_construire(text, text) to authenticated;

commit;

select exists (select 1 from pg_indexes where indexname = 'batiments_une_fonderie') as index_unique_encore_la,
       public.batiment_reglage('fonderies_max')::int as fonderies_max,
       public.batiment_reglage('fonderie2_prix')::int as prix_2e,
       public.batiment_reglage('fonderie_max2')::int as reserve_avec_2;
