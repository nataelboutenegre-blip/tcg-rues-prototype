-- s2-133 (10/11/2026) : échanges de communes entre joueurs de clans différents (idée de zintox, 9/11 ;
-- « Ok pour les échanges entre clans », Nataël, 9/11 23 h 39).
-- Même règles qu'entre coéquipiers (une contre une, même rareté, pas en garnison, pas prise il y a moins de 24 h,
-- pas échangée il y a moins de 48 h, 24 h pour répondre), mais :
--   * les deux joueurs sont chacun dans un clan depuis 48 h, deux clans différents ;
--   * UN échange entre clans par joueur tous les 7 jours (conclu) ; 2 propositions entre clans en attente au plus ;
--   * ces échanges ne comptent pas dans les 3 échanges du jour entre coéquipiers.
-- Même table clan_echanges (colonne inter), même acceptation (clan_ech_repondre), même liste (clan_ech_etat).

alter table clan_echanges add column if not exists inter boolean not null default false;

-- la date à laquelle le joueur pourra conclure son prochain échange entre clans (null : tout de suite)
create or replace function public.clan_ech_inter_dispo(p_joueur uuid)
returns timestamptz
language sql
stable security definer
set search_path to 'public'
as $f$
  select d from (select max(e.repondu_le) + interval '7 days' as d
                   from clan_echanges e
                  where e.inter and e.etat = 'accepte' and p_joueur in (e.proposant, e.destinataire)) x
   where d > now();
$f$;

create or replace function public.clan_ech_inter_proposer(p_cible uuid, p_ma text, p_sa text)
returns text
language plpgsql
security definer
set search_path to 'public'
as $f$
declare v_uid uuid := auth.uid(); v_clan uuid; v_clan2 uuid; t1 text; t2 text; r text; d timestamptz;
begin
  if v_uid is null then raise exception 'Non connecte'; end if;
  if not saison2_active() then raise exception 'Les échanges arrivent avec la saison 2.'; end if;
  if p_cible is null or p_cible = v_uid then raise exception 'Choisis un autre joueur.'; end if;
  v_clan := clan_ech_clan(v_uid);
  if v_clan is null then raise exception 'Il faut être dans un clan depuis 48 h pour échanger avec un autre clan.'; end if;
  v_clan2 := clan_ech_clan(p_cible);
  if v_clan2 is null then raise exception 'Ce joueur n''est pas dans un clan (ou depuis moins de 48 h).'; end if;
  if v_clan2 = v_clan then raise exception 'Ce joueur est dans ton clan : passe par les échanges du clan.'; end if;
  d := clan_ech_inter_dispo(v_uid);
  if d is not null then
    raise exception 'Un échange entre clans par semaine : ton prochain le %.', to_char(d at time zone 'Europe/Paris', 'DD/MM à HH24"h"MI');
  end if;
  d := clan_ech_inter_dispo(p_cible);
  if d is not null then raise exception 'Ce joueur a déjà fait son échange entre clans de la semaine.'; end if;
  if (select count(*) from clan_echanges where proposant = v_uid and inter and etat = 'en_attente' and expire_le > now()) >= 2 then
    raise exception 'Tu as déjà 2 propositions entre clans en attente.';
  end if;
  if not exists (select 1 from possessions where commune_code = p_ma and joueur_id = v_uid) then
    raise exception 'Cette commune n''est pas à toi.';
  end if;
  if not exists (select 1 from possessions where commune_code = p_sa and joueur_id = p_cible) then
    raise exception 'Cette commune n''est plus à ce joueur.';
  end if;
  r := clan_ech_raison(p_ma, v_uid);
  if r is not null then raise exception 'Ta commune ne peut pas être échangée (%).', r; end if;
  r := clan_ech_raison(p_sa, p_cible);
  if r is not null then raise exception 'Sa commune ne peut pas être échangée (%).', r; end if;
  select tier into t1 from communes where code = p_ma;
  select tier into t2 from communes where code = p_sa;
  if t1 is distinct from t2 then raise exception 'Les deux communes doivent être de même rareté.'; end if;
  if exists (select 1 from clan_echanges where etat = 'en_attente' and expire_le > now()
              and proposant = v_uid and commune_proposant = p_ma and commune_destinataire = p_sa) then
    raise exception 'Tu as déjà proposé cet échange.';
  end if;
  insert into clan_echanges(clan_id, proposant, destinataire, commune_proposant, commune_destinataire, tier, inter)
  values (v_clan, v_uid, p_cible, p_ma, p_sa, t1, true);
  return 'Proposition envoyée';
end; $f$;
revoke execute on function public.clan_ech_inter_proposer(uuid, text, text) from public, anon;
grant execute on function public.clan_ech_inter_proposer(uuid, text, text) to authenticated;
revoke execute on function public.clan_ech_inter_dispo(uuid) from public, anon;

-- les échanges entre clans ne comptent pas dans les 3 du jour entre coéquipiers
create or replace function public.clan_ech_du_jour(p_joueur uuid)
 returns integer language sql stable security definer set search_path to 'public'
as $f$
  select count(*)::integer from clan_echanges e
   where e.etat = 'accepte' and not e.inter and p_joueur in (e.proposant, e.destinataire)
     and e.repondu_le >= (quete_jour()::timestamp at time zone 'Europe/Paris');
$f$;
create or replace function public.clan_ech_du_jour_avec(p_a uuid, p_b uuid)
 returns integer language sql stable security definer set search_path to 'public'
as $f$
  select count(*)::integer from clan_echanges e
   where e.etat = 'accepte' and not e.inter
     and ((e.proposant = p_a and e.destinataire = p_b) or (e.proposant = p_b and e.destinataire = p_a))
     and e.repondu_le >= (quete_jour()::timestamp at time zone 'Europe/Paris');
$f$;

-- clan_ech_repondre et clan_ech_etat : modifiés sur place (voir le bloc DO ci-dessous)
create or replace function pg_temp.remp(d text, avant text, apres text, nb int, quoi text) returns text language plpgsql as $r$
declare n int := (length(d) - length(replace(d, avant, ''))) / greatest(length(avant), 1);
begin
  if n <> nb then raise exception '% : % occurrence(s) au lieu de %', quoi, n, nb; end if;
  return replace(d, avant, apres);
end $r$;

do $do$
declare d text;
begin
  d := pg_get_functiondef('public.clan_ech_repondre'::regproc);
  d := pg_temp.remp(d,
$a$  if clan_ech_clan(v_uid) is distinct from e.clan_id or clan_ech_clan(e.proposant) is distinct from e.clan_id then
    update clan_echanges set etat = 'annule', repondu_le = now() where id = p_id;
    raise exception 'Vous n''êtes plus dans le même clan.';
  end if;
  if clan_ech_du_jour_avec(v_uid, e.proposant) >= 3 then raise exception 'Vous avez déjà fait vos 3 échanges du jour ensemble.'; end if;$a$,
$b$  if not e.inter and (clan_ech_clan(v_uid) is distinct from e.clan_id or clan_ech_clan(e.proposant) is distinct from e.clan_id) then
    update clan_echanges set etat = 'annule', repondu_le = now() where id = p_id;
    raise exception 'Vous n''êtes plus dans le même clan.';
  end if;
  -- s2-133 : entre clans, deux clans différents depuis 48 h, un échange par semaine chacun
  if e.inter and (clan_ech_clan(v_uid) is null or clan_ech_clan(e.proposant) is null or clan_ech_clan(v_uid) = clan_ech_clan(e.proposant)) then
    update clan_echanges set etat = 'annule', repondu_le = now() where id = p_id;
    raise exception 'Cet échange entre clans n''est plus possible : il faut être dans deux clans différents depuis 48 h.';
  end if;
  if e.inter and clan_ech_inter_dispo(v_uid) is not null then
    raise exception 'Un échange entre clans par semaine : ton prochain le %.', to_char(clan_ech_inter_dispo(v_uid) at time zone 'Europe/Paris', 'DD/MM à HH24"h"MI');
  end if;
  if e.inter and clan_ech_inter_dispo(e.proposant) is not null then
    update clan_echanges set etat = 'annule', repondu_le = now() where id = p_id;
    raise exception 'Ce joueur a déjà fait son échange entre clans de la semaine.';
  end if;
  if not e.inter and clan_ech_du_jour_avec(v_uid, e.proposant) >= 3 then raise exception 'Vous avez déjà fait vos 3 échanges du jour ensemble.'; end if;$b$, 1, 'repondre');
  execute d;

  d := pg_get_functiondef('public.clan_ech_etat'::regproc);
  d := pg_temp.remp(d, $a$'faits', clan_ech_du_jour(v_uid), 'max', 3, 'par_membre', true,$a$,
                       $b$'faits', clan_ech_du_jour(v_uid), 'max', 3, 'par_membre', true, 'inter_dispo_le', clan_ech_inter_dispo(v_uid),$b$, 1, 'etat dispo');
  d := pg_temp.remp(d, $a$'expire_le', e.expire_le, 'tier', e.tier,$a$, $b$'expire_le', e.expire_le, 'tier', e.tier, 'inter', e.inter,$b$, 2, 'etat inter');
  execute d;
end $do$;

notify pgrst, 'reload schema';
