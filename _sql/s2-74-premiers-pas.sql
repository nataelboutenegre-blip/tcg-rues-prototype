-- ===========================================================================
--  TerraFront — s2-74 : « Premiers pas » pour les nouveaux joueurs (2/11/2026)
--  Décidé avec Nataël le 2/11 (aperçu « Premiers pas et candidatures » validé).
--
--  Pourquoi : sur les nouveaux des 14 derniers jours, ceux qui combattent le
--  1er jour reviennent à 75 %, les autres à 25 % (et 10 % pour ceux qui ne
--  combattent jamais). La carte les mène à leur première attaque.
--
--  4 étapes, cochées par le serveur (jamais décochées) :
--    paquet   : a au moins une commune au Front ou une carte Terra
--    attaque  : a gagné un round (siège à 1 victoire ou plus) ou conquis une commune
--    clan     : est dans un clan (rejoint ou créé)
--    fonderie : a construit (ou commencé) sa Fonderie
--  Récompense, une seule fois, quand les 4 sont faites : 1 paquet Terra en
--  plus (il peut dépasser la réserve de 3, comme le cadeau du parrainage) et
--  10 lingots.
--
--  Qui la voit : les comptes créés il y a moins de 14 jours (et ceux qui l'ont
--  déjà vue, jusqu'à ce qu'ils récupèrent la récompense).
--
--  premiers_pas()           : l'état (et met les étapes à jour).
--  premiers_pas_reclamer()  : la récompense.
--  Rejouable. Finit par un contrôle (une ligne).
-- ===========================================================================
begin;

create table if not exists public.premiers_pas(
  joueur_id  uuid primary key references public.joueurs(id) on delete cascade,
  paquet     boolean not null default false,
  attaque    boolean not null default false,
  clan       boolean not null default false,
  fonderie   boolean not null default false,
  cree_le    timestamptz not null default now(),
  maj        timestamptz not null default now(),
  reclame_le timestamptz
);
alter table public.premiers_pas enable row level security;
revoke all on public.premiers_pas from public, anon, authenticated;

create or replace function public.premiers_pas()
 returns jsonb language plpgsql security definer set search_path to 'public' as $f$
declare
  v_uid uuid := auth.uid();
  v_cree timestamptz;
  p premiers_pas%rowtype;
begin
  if v_uid is null then raise exception 'Non connecte'; end if;
  select * into p from premiers_pas where joueur_id = v_uid;
  if p.joueur_id is null then
    select u.created_at into v_cree from auth.users u where u.id = v_uid;
    if v_cree is null or v_cree < now() - interval '14 days' then
      return jsonb_build_object('eligible', false);
    end if;
    insert into premiers_pas(joueur_id) values (v_uid) on conflict do nothing;
  end if;
  if p.reclame_le is not null then
    return jsonb_build_object('eligible', false, 'reclame', true);
  end if;

  update premiers_pas set
    paquet   = paquet
               or exists (select 1 from possessions x where x.joueur_id = v_uid)
               or exists (select 1 from terra_collection t where t.joueur_id = v_uid and t.exemplaires > 0),
    attaque  = attaque
               or exists (select 1 from sieges s where s.attacker_id = v_uid and coalesce(s.victoires_consecutives, 0) > 0)
               or exists (select 1 from front_victoires v where v.joueur_id = v_uid and v.type = 'conquete'),
    clan     = clan or exists (select 1 from clan_membres m where m.joueur_id = v_uid),
    fonderie = fonderie or exists (select 1 from batiments b where b.joueur_id = v_uid and b.type = 'fonderie'),
    maj      = now()
   where joueur_id = v_uid
  returning * into p;

  return jsonb_build_object('eligible', true,
    'paquet', p.paquet, 'attaque', p.attaque, 'clan', p.clan, 'fonderie', p.fonderie,
    'recompense', jsonb_build_object('paquets', 1, 'lingots', 10));
end; $f$;
revoke all on function public.premiers_pas() from public, anon;
grant execute on function public.premiers_pas() to authenticated;

create or replace function public.premiers_pas_reclamer()
 returns jsonb language plpgsql security definer set search_path to 'public' as $f$
declare
  v_uid uuid := auth.uid();
  e jsonb;
  j record;
  v numeric;
begin
  if v_uid is null then raise exception 'Non connecte'; end if;
  perform 1 from joueurs where id = v_uid for update;
  e := premiers_pas();   -- remet les étapes à jour
  if exists (select 1 from premiers_pas where joueur_id = v_uid and reclame_le is not null) then
    raise exception 'Récompense déjà récupérée';
  end if;
  if not coalesce((e->>'eligible')::boolean, false) then raise exception 'Pas de premiers pas pour ce compte'; end if;
  if not ((e->>'paquet')::boolean and (e->>'attaque')::boolean and (e->>'clan')::boolean and (e->>'fonderie')::boolean) then
    raise exception 'Il reste des étapes à faire';
  end if;

  -- 1 paquet Terra en plus (la réserve peut dépasser 3)
  select terra_jetons, terra_jetons_maj into j from joueurs where id = v_uid;
  update joueurs set terra_jetons = terra_jetons_lire(coalesce(j.terra_jetons, 0), coalesce(j.terra_jetons_maj, now())) + 1,
                     terra_jetons_maj = now()
   where id = v_uid;
  -- 10 lingots
  v := lingots_figer(v_uid);
  update joueurs set lingots = coalesce(lingots, 0) + 10 where id = v_uid;

  update premiers_pas set reclame_le = now() where joueur_id = v_uid;
  return jsonb_build_object('paquets', 1, 'lingots', 10);
end; $f$;
revoke all on function public.premiers_pas_reclamer() from public, anon;
grant execute on function public.premiers_pas_reclamer() to authenticated;

commit;

-- Contrôle : true | true | true | (nombre de comptes qui la verront)
select to_regclass('public.premiers_pas') is not null                                         as table_ok,
       has_function_privilege('authenticated', 'public.premiers_pas()', 'execute')           as lecture_ok,
       has_function_privilege('authenticated', 'public.premiers_pas_reclamer()', 'execute')  as recompense_ok,
       (select count(*) from auth.users where created_at >= now() - interval '14 days')       as comptes_concernes;
