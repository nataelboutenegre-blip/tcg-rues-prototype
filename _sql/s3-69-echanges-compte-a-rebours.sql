-- s3-69 (24/11/2026, H34VEN et Saaslil) : les échanges disent QUAND ils redeviennent possibles.
-- clan_ech_dans(t) : « dans 5 h » / « dans 40 min » ; clan_ech_etat : pret_le par membre + demain_le ;
-- clan_ech_raison : « échangeable dans N h » ; messages d'erreur avec l'heure (coéquipier ou joueur arrivé < 48 h).
create or replace function public.clan_ech_dans(p_t timestamptz)
 returns text language sql stable set search_path to 'public'
as $f$
  select case when p_t <= now() then 'maintenant'
              when p_t - now() < interval '1 hour' then 'dans ' || greatest(1, ceil(extract(epoch from p_t - now()) / 60))::int || ' min'
              else 'dans ' || ceil(extract(epoch from p_t - now()) / 3600)::int || ' h' end;
$f$;

do $m$
declare d text; n text;
begin
  -- 1. clan_ech_etat
  d := pg_get_functiondef('public.clan_ech_etat()'::regprocedure);
  n := replace(d, $a$'membres', coalesce((select jsonb_agg(jsonb_build_object('id', j.id, 'pseudo', j.pseudo, 'faits', clan_ech_du_jour_avec(v_uid, j.id)) order by j.pseudo)$a$,
                  $b$'demain_le', (quete_jour() + 1)::timestamp at time zone 'Europe/Paris',   -- s3-69
    'membres', coalesce((select jsonb_agg(jsonb_build_object('id', j.id, 'pseudo', j.pseudo, 'faits', clan_ech_du_jour_avec(v_uid, j.id),
                     'pret_le', case when m.depuis > now() - interval '48 hours' then m.depuis + interval '48 hours' end) order by j.pseudo)$b$);
  if n = d then raise exception 's3-69 : clan_ech_etat introuvable'; end if;
  execute n;

  -- 2. clan_ech_raison
  d := pg_get_functiondef('public.clan_ech_raison(text, uuid)'::regprocedure);
  n := replace(d, $a$    h := greatest(1, floor(extract(epoch from now() - p.conquise_le) / 3600)::int);
    return 'prise il y a ' || h || ' h';$a$, $b$    return 'échangeable ' || clan_ech_dans(p.conquise_le + interval '24 hours');   -- s3-69$b$);
  n := replace(n, $a$    return 'échangée récemment';$a$,
    $b$    return 'échangeable ' || clan_ech_dans((select max(e.repondu_le) from clan_echanges e where e.etat = 'accepte'
                                            and p_code in (e.commune_proposant, e.commune_destinataire)) + interval '48 hours');   -- s3-69$b$);
  if n = d or n !~ 'clan_ech_dans\(\(select' then raise exception 's3-69 : clan_ech_raison introuvable'; end if;
  execute n;

  -- 3. clan_ech_proposer
  d := pg_get_functiondef('public.clan_ech_proposer(uuid, text, text)'::regprocedure);
  n := replace(d, $a$    raise exception 'Ce joueur n''est pas dans ton clan, ou il y est depuis moins de 48 h.';$a$,
    $b$    if exists (select 1 from clan_membres m where m.joueur_id = p_cible and m.clan_id = (select m2.clan_id from clan_membres m2 where m2.joueur_id = v_uid)) then   -- s3-69
      raise exception 'Ce coéquipier est arrivé il y a moins de 48 h : échange possible %.',
        (select clan_ech_dans(m.depuis + interval '48 hours') from clan_membres m where m.joueur_id = p_cible);
    end if;
    raise exception 'Ce joueur n''est pas dans ton clan.';$b$);
  if n = d then raise exception 's3-69 : clan_ech_proposer introuvable'; end if;
  execute n;

  -- 4. clan_ech_inter_proposer
  d := pg_get_functiondef('public.clan_ech_inter_proposer(uuid, text, text)'::regprocedure);
  n := replace(d, $a$  if v_clan2 is null then raise exception 'Ce joueur n''est pas dans un clan (ou depuis moins de 48 h).'; end if;$a$,
    $b$  if v_clan2 is null then   -- s3-69 : avec l'heure
    select m.depuis into d from clan_membres m where m.joueur_id = p_cible;
    if d is not null then
      raise exception 'Ce joueur est arrivé dans son clan il y a peu : échange possible le %.', to_char((d + interval '48 hours') at time zone 'Europe/Paris', 'DD/MM à HH24" h "MI');
    end if;
    raise exception 'Ce joueur n''est pas dans un clan.';
  end if;$b$);
  if n = d then raise exception 's3-69 : clan_ech_inter_proposer introuvable'; end if;
  execute n;
end $m$;
