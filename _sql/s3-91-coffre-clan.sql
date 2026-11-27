-- s3-91 (27/11/2026) : le coffre du clan (idée de Bonjean). Règles validées par Nataël le 27/11 :
-- 150 lingots au plus ; tout membre dépose ; retrait après 48 h dans le clan, 15 lingots par jour (Paris),
-- sans dépasser son propre plafond de lingots ; journal visible par le clan ; le chef bloque les retraits ;
-- pas d'intérêts ; ce qui est déposé reste au clan. Le coffre repart à zéro avec la saison.
-- Réglages : config_jeu 'clans_s3' -> coffre (1/0), coffre_max, coffre_retrait_jour, coffre_anciennete_h.
create table if not exists public.clan_coffres(
  clan_id uuid primary key references public.clans(id) on delete cascade,
  contenu integer not null default 0 check (contenu >= 0),
  saison text,
  retraits_bloques boolean not null default false,
  maj timestamptz not null default now());
create table if not exists public.clan_coffre_journal(
  id bigserial primary key,
  clan_id uuid not null references public.clans(id) on delete cascade,
  joueur_id uuid,
  sens text not null check (sens in ('depot', 'retrait', 'blocage', 'deblocage')),
  lingots integer not null default 0,
  le timestamptz not null default now());
create index if not exists clan_coffre_journal_clan on public.clan_coffre_journal(clan_id, le desc);
alter table public.clan_coffres enable row level security;
alter table public.clan_coffre_journal enable row level security;

create or replace function public.coffre_n(p_cle text, p_defaut numeric)
 returns numeric language sql stable set search_path to 'public'
as $f$ select coalesce((select (valeur::jsonb ->> p_cle)::numeric from config_jeu where cle = 'clans_s3'), p_defaut); $f$;

-- la ligne du coffre, créée et remise à zéro à la nouvelle saison ; verrouillée
create or replace function public.coffre_prendre(p_clan uuid)
 returns clan_coffres language plpgsql security definer set search_path to 'public'
as $f$
declare c clan_coffres; s text := saison_en_cours_id();
begin
  insert into clan_coffres(clan_id, saison) values (p_clan, s) on conflict (clan_id) do nothing;
  select * into c from clan_coffres where clan_id = p_clan for update;
  if c.saison is distinct from s then
    update clan_coffres set contenu = 0, saison = s, maj = now() where clan_id = p_clan returning * into c;
  end if;
  return c;
end; $f$;

create or replace function public.coffre_retire_aujourdhui(p_clan uuid, p_joueur uuid)
 returns integer language sql stable set search_path to 'public'
as $f$
  select coalesce(sum(lingots), 0)::integer from clan_coffre_journal
   where clan_id = p_clan and joueur_id = p_joueur and sens = 'retrait'
     and le >= ((now() at time zone 'Europe/Paris')::date)::timestamp at time zone 'Europe/Paris';
$f$;

create or replace function public.clan_coffre_etat()
 returns jsonb language plpgsql security definer set search_path to 'public'
as $f$
declare moi uuid := auth.uid(); v_clan uuid; v_chef uuid; c clan_coffres; v_depuis timestamptz;
        v_anc numeric := coffre_n('coffre_anciennete_h', 48); v_jour integer := coffre_n('coffre_retrait_jour', 15)::integer;
        v_deja integer; v_l numeric; v_max numeric; v_journal jsonb;
begin
  if moi is null then raise exception 'Non connecte'; end if;
  if coffre_n('coffre', 0) <> 1 then return jsonb_build_object('ouvert', false); end if;
  v_clan := clan_de(moi);
  if v_clan is null then return jsonb_build_object('ouvert', true, 'clan', false); end if;
  select chef into v_chef from clans where id = v_clan;
  select depuis into v_depuis from clan_membres where joueur_id = moi and clan_id = v_clan;
  c := coffre_prendre(v_clan);
  v_deja := coffre_retire_aujourdhui(v_clan, moi);
  v_l := coalesce(lingots_lire(moi), 0); v_max := lingots_max_fonderies(moi);
  select coalesce(jsonb_agg(jsonb_build_object('pseudo', j.pseudo, 'moi', x.joueur_id = moi, 'sens', x.sens, 'lingots', x.lingots, 'le', x.le) order by x.le desc), '[]'::jsonb)
    into v_journal
    from (select * from clan_coffre_journal where clan_id = v_clan order by le desc limit 30) x left join joueurs j on j.id = x.joueur_id;
  return jsonb_build_object('ouvert', true, 'clan', true, 'contenu', c.contenu, 'max', coffre_n('coffre_max', 150)::integer,
    'bloque', c.retraits_bloques, 'chef', v_chef = moi, 'retrait_jour', v_jour, 'retire_aujourdhui', v_deja,
    'anciennete_h', v_anc::integer,
    'retrait_des', case when v_depuis + make_interval(hours => v_anc::integer) > now() then v_depuis + make_interval(hours => v_anc::integer) end,
    'mes_lingots', floor(v_l)::integer, 'mon_max', floor(v_max)::integer, 'journal', v_journal);
end; $f$;

create or replace function public.clan_coffre_deposer(p_lingots integer)
 returns jsonb language plpgsql security definer set search_path to 'public'
as $f$
declare moi uuid := auth.uid(); v_clan uuid; c clan_coffres; v numeric; v_max integer := coffre_n('coffre_max', 150)::integer;
begin
  if moi is null then raise exception 'Non connecte'; end if;
  if coffre_n('coffre', 0) <> 1 then raise exception 'Le coffre du clan n''est pas ouvert'; end if;
  if p_lingots is null or p_lingots < 1 then raise exception 'Montant invalide'; end if;
  v_clan := clan_de(moi);
  if v_clan is null then raise exception 'Tu n''es pas dans un clan'; end if;
  c := coffre_prendre(v_clan);
  if c.contenu + p_lingots > v_max then
    raise exception 'Le coffre garde % lingots au plus : tu peux encore en déposer %', v_max, greatest(0, v_max - c.contenu);
  end if;
  perform 1 from joueurs where id = moi for update;
  v := lingots_figer(moi);
  if v < p_lingots then raise exception 'Il te faut % lingots (tu en as %)', p_lingots, floor(v)::integer; end if;
  update joueurs set lingots = lingots - p_lingots where id = moi;
  update clan_coffres set contenu = contenu + p_lingots, maj = now() where clan_id = v_clan;
  insert into clan_coffre_journal(clan_id, joueur_id, sens, lingots) values (v_clan, moi, 'depot', p_lingots);
  return clan_coffre_etat();
end; $f$;

create or replace function public.clan_coffre_retirer(p_lingots integer)
 returns jsonb language plpgsql security definer set search_path to 'public'
as $f$
declare moi uuid := auth.uid(); v_clan uuid; c clan_coffres; v numeric; v_depuis timestamptz; v_deja integer; v_max numeric;
        v_anc integer := coffre_n('coffre_anciennete_h', 48)::integer; v_jour integer := coffre_n('coffre_retrait_jour', 15)::integer;
begin
  if moi is null then raise exception 'Non connecte'; end if;
  if coffre_n('coffre', 0) <> 1 then raise exception 'Le coffre du clan n''est pas ouvert'; end if;
  if p_lingots is null or p_lingots < 1 then raise exception 'Montant invalide'; end if;
  v_clan := clan_de(moi);
  if v_clan is null then raise exception 'Tu n''es pas dans un clan'; end if;
  c := coffre_prendre(v_clan);
  if c.retraits_bloques then raise exception 'Le chef a bloqué les retraits du coffre'; end if;
  select depuis into v_depuis from clan_membres where joueur_id = moi and clan_id = v_clan;
  if v_depuis + make_interval(hours => v_anc) > now() then
    raise exception 'Tu pourras retirer du coffre % h après ton arrivée dans le clan (le %)', v_anc,
      to_char((v_depuis + make_interval(hours => v_anc)) at time zone 'Europe/Paris', 'DD/MM à HH24:MI');
  end if;
  v_deja := coffre_retire_aujourdhui(v_clan, moi);
  if v_deja + p_lingots > v_jour then
    raise exception 'Tu peux retirer % lingots par jour : il t''en reste % aujourd''hui', v_jour, greatest(0, v_jour - v_deja);
  end if;
  if c.contenu < p_lingots then raise exception 'Le coffre ne contient que % lingots', c.contenu; end if;
  perform 1 from joueurs where id = moi for update;
  v := lingots_figer(moi);
  v_max := lingots_max_fonderies(moi);
  if floor(v) + p_lingots > v_max then
    raise exception 'Tu peux garder % lingots au plus : tu peux en retirer % maintenant', floor(v_max)::integer, greatest(0, floor(v_max - v))::integer;
  end if;
  update clan_coffres set contenu = contenu - p_lingots, maj = now() where clan_id = v_clan;
  update joueurs set lingots = lingots + p_lingots where id = moi;
  insert into clan_coffre_journal(clan_id, joueur_id, sens, lingots) values (v_clan, moi, 'retrait', p_lingots);
  return clan_coffre_etat();
end; $f$;

create or replace function public.clan_coffre_bloquer(p_bloque boolean)
 returns jsonb language plpgsql security definer set search_path to 'public'
as $f$
declare moi uuid := auth.uid(); v_clan uuid; c clan_coffres;
begin
  if moi is null then raise exception 'Non connecte'; end if;
  if coffre_n('coffre', 0) <> 1 then raise exception 'Le coffre du clan n''est pas ouvert'; end if;
  select id into v_clan from clans where chef = moi;
  if v_clan is null then raise exception 'Seul le chef peut bloquer les retraits'; end if;
  c := coffre_prendre(v_clan);
  if c.retraits_bloques is distinct from coalesce(p_bloque, false) then
    update clan_coffres set retraits_bloques = coalesce(p_bloque, false), maj = now() where clan_id = v_clan;
    insert into clan_coffre_journal(clan_id, joueur_id, sens) values (v_clan, moi, case when p_bloque then 'blocage' else 'deblocage' end);
  end if;
  return clan_coffre_etat();
end; $f$;

revoke all on function public.coffre_prendre(uuid) from public, anon, authenticated;
revoke all on function public.coffre_n(text, numeric) from public, anon;
revoke all on function public.coffre_retire_aujourdhui(uuid, uuid) from public, anon, authenticated;
revoke all on function public.clan_coffre_etat() from public, anon;
revoke all on function public.clan_coffre_deposer(integer) from public, anon;
revoke all on function public.clan_coffre_retirer(integer) from public, anon;
revoke all on function public.clan_coffre_bloquer(boolean) from public, anon;
grant execute on function public.clan_coffre_etat() to authenticated;
grant execute on function public.clan_coffre_deposer(integer) to authenticated;
grant execute on function public.clan_coffre_retirer(integer) to authenticated;
grant execute on function public.clan_coffre_bloquer(boolean) to authenticated;
update public.config_jeu set valeur = ((valeur::jsonb) || '{"coffre": 0, "coffre_max": 150, "coffre_retrait_jour": 15, "coffre_anciennete_h": 48}'::jsonb)::text where cle = 'clans_s3';
-- allumer : update public.config_jeu set valeur = ((valeur::jsonb) || '{"coffre": 1}'::jsonb)::text where cle = 'clans_s3';
