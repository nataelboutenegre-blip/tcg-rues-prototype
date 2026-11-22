-- s3-43 : l'attaquant apprend qu'on l'a défendu (idée d'ASMFCB, aperçu validé par Nataël le 22/11 à 10 h 46).
-- 1. siege_renforcer note chaque défense contre un siège ; à la première, l'attaquant reçoit une notification
--    (une seule par siège, pour ne pas le noyer si le défenseur renforce 10 fois).
-- 2. siege_fermer note le siège tombé faute de vague (24 h) et prévient l'attaquant.
-- 3. mes_alertes_siege() : la cloche du jeu (7 jours), une ligne par siège et par type.
-- Va avec patch485. Retour arrière : relancer les deux fonctions sans les lignes « -- s3-43 ».

create table if not exists public.front_siege_alertes (
  id            bigserial primary key,
  attaquant     uuid not null,
  siege_id      bigint not null,
  commune_code  text not null,
  type          text not null check (type in ('defendu', 'tombee')),
  defenseur     uuid,
  recul         integer not null default 0,
  degats_apres  integer,
  resistance    integer,
  devient_long  boolean not null default false,
  energie_rendue integer not null default 0,
  le            timestamptz not null default now()
);
create index if not exists front_siege_alertes_att on public.front_siege_alertes (attaquant, le desc);
create index if not exists front_siege_alertes_siege on public.front_siege_alertes (siege_id, type);
alter table public.front_siege_alertes enable row level security;   -- pas de politique : on passe par les fonctions

do $$
declare d text; n text;
begin
  -- 1. la défense
  d := pg_get_functiondef('public.siege_renforcer(text,uuid,integer)'::regprocedure);
  n := replace(d, 'v_max integer := coalesce(clan_cfg_n(''allie_max''), 60)::integer;   -- s3-28a',
                  'v_max integer := coalesce(clan_cfg_n(''allie_max''), 60)::integer;   -- s3-28a
  v_premier boolean;   -- s3-43');
  n := replace(n, '  perform quete_noter(v_uid, ''renfort'', 1);   -- s3-22',
'  -- s3-43 : l''attaquant apprend la défense (une notification par siège, la cloche garde tout)
  v_premier := not exists (select 1 from front_siege_alertes where siege_id = s.id and type = ''defendu'');
  insert into front_siege_alertes (attaquant, siege_id, commune_code, type, defenseur, recul, degats_apres, resistance, devient_long)
  values (s.attaquant, s.id, p_code, ''defendu'', v_uid, round(v_recul), round(greatest(0, s.degats - v_recul)),
          round(siege_resistance(p_code, p_attaquant)), s.long_depuis is null);
  if v_premier then
    perform notifier_joueur(s.attaquant,
      ''🛡️ '' || coalesce((select pseudo from joueurs where id = v_uid), ''Le défenseur'') || '' défend '' || coalesce((select nom from communes where code = p_code), ''ta cible''),
      ''−'' || round(v_recul) || '' sur ta jauge'' || case when s.long_depuis is null then '' · le siège devient long'' else '''' end,
      ''./?onglet=combat'', ''defendu-'' || s.id);
  end if;
  perform quete_noter(v_uid, ''renfort'', 1);   -- s3-22');
  if n = d or position('s3-43' in n) = 0 or position('v_premier :=' in n) = 0 then raise exception 's3-43 : siege_renforcer a changé, rien n''est fait'; end if;
  execute n;

  -- 2. le siège tombé
  d := pg_get_functiondef('public.siege_fermer(bigint,text)'::regprocedure);
  n := replace(d, '  perform siege_rendre_energie(s.attaquant, s.attente);',
'  perform siege_rendre_energie(s.attaquant, s.attente);
  if p_resultat = ''tombee'' then   -- s3-43 : l''attaquant est prévenu
    insert into front_siege_alertes (attaquant, siege_id, commune_code, type, energie_rendue)
    values (s.attaquant, s.id, s.commune_code, ''tombee'', coalesce(s.attente, 0));
    perform notifier_joueur(s.attaquant,
      ''⌛ Ton siège de '' || coalesce((select nom from communes where code = s.commune_code), ''ta cible'') || '' est tombé'',
      siege_n(''expiration_h'')::int || '' h sans vague'' || case when coalesce(s.attente, 0) > 0 then '' · '' || s.attente || '' énergie rendue'' else '''' end,
      ''./?onglet=combat'', ''tombee-'' || s.id);
  end if;');
  if n = d then raise exception 's3-43 : siege_fermer a changé, rien n''est fait'; end if;
  execute n;
end $$;

-- 3. la cloche
create or replace function public.mes_alertes_siege()
returns jsonb
language sql stable security definer set search_path to 'public' as $$
  select coalesce(jsonb_agg(to_jsonb(x) order by x.le desc), '[]'::jsonb) from (
    select a.siege_id, a.type, a.commune_code, c.nom, c.departement as dept,
           max(a.le) as le, count(*) as n, sum(a.recul)::int as recul,
           (array_agg(j.pseudo order by a.le desc))[1] as defenseur_pseudo,
           (array_agg(a.degats_apres order by a.le desc))[1] as degats,
           (array_agg(a.resistance order by a.le desc))[1] as resistance,
           bool_or(a.devient_long) as devient_long, max(a.energie_rendue) as energie_rendue,
           (s.fini_le is null) as ouvert
      from front_siege_alertes a
      join communes c on c.code = a.commune_code
      left join joueurs j on j.id = a.defenseur
      left join front_sieges s on s.id = a.siege_id
     where a.attaquant = auth.uid() and a.le > now() - interval '7 days'
     group by a.siege_id, a.type, a.commune_code, c.nom, c.departement, s.fini_le
     order by max(a.le) desc
     limit 30) x;
$$;
revoke all on function public.mes_alertes_siege() from public, anon;
grant execute on function public.mes_alertes_siege() to authenticated;

-- contrôle : true · true · true
select position('s3-43' in pg_get_functiondef('public.siege_renforcer(text,uuid,integer)'::regprocedure)) > 0 as renforcer_ok,
       position('s3-43' in pg_get_functiondef('public.siege_fermer(bigint,text)'::regprocedure)) > 0 as fermer_ok,
       to_regprocedure('public.mes_alertes_siege()') is not null as cloche_ok;
