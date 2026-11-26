-- s3-81 (Arkhannou, Maroli) : échanges entre clans
--  - la limite repart à minuit (heure de Paris), au lieu de 24 h glissantes ;
--  - un échange par jour AVEC CHAQUE CLAN, au lieu d'un seul échange par jour tous clans confondus.
-- clan_echanges.clan2 : le clan du destinataire au moment de la proposition (les anciennes lignes : son clan actuel).
-- clan_ech_inter_dispo ne bloque plus rien (null) ; clan_ech_etat renvoie « inter_faits » : les sigles des clans
-- avec qui tu as déjà échangé aujourd'hui.

alter table clan_echanges add column if not exists clan2 uuid;
update clan_echanges e set clan2 = m.clan_id from clan_membres m
 where e.inter and e.clan2 is null and m.joueur_id = e.destinataire;

-- l'autre clan d'un échange entre clans, vu de p_joueur
create or replace function clan_ech_inter_autre(e clan_echanges, p_joueur uuid) returns uuid
language sql stable security definer set search_path to 'public' as $$
  select case when e.proposant = p_joueur then coalesce(e.clan2, (select m.clan_id from clan_membres m where m.joueur_id = e.destinataire))
              else e.clan_id end;
$$;
-- p_joueur a-t-il déjà conclu aujourd'hui un échange avec le clan p_clan ?
create or replace function clan_ech_inter_avec(p_joueur uuid, p_clan uuid) returns boolean
language sql stable security definer set search_path to 'public' as $$
  select exists (select 1 from clan_echanges e
                  where e.inter and e.etat = 'accepte' and p_joueur in (e.proposant, e.destinataire)
                    and e.repondu_le >= (quete_jour()::timestamp at time zone 'Europe/Paris')
                    and clan_ech_inter_autre(e, p_joueur) = p_clan);
$$;
revoke all on function clan_ech_inter_autre(clan_echanges, uuid) from public, anon, authenticated;
revoke all on function clan_ech_inter_avec(uuid, uuid) from public, anon, authenticated;

create or replace function clan_ech_inter_dispo(p_joueur uuid) returns timestamptz
language sql stable security definer set search_path to 'public' as $$
  select null::timestamptz;   -- s3-81 : plus de limite globale (un échange par jour avec chaque clan)
$$;

do $do$
declare d text; avant text;
begin
  ---------- proposer ----------
  d := pg_get_functiondef('clan_ech_inter_proposer(uuid,text,text)'::regprocedure); avant := d;
  d := regexp_replace(d, $r$  d := clan_ech_inter_dispo\(v_uid\);.*?du jour\.'; end if;$r$,
$b$  -- s3-81 : un échange par jour avec chaque clan, remis à zéro à minuit
  if clan_ech_inter_avec(v_uid, v_clan2) then
    raise exception 'Un échange par jour avec chaque clan : déjà fait avec ce clan aujourd''hui, à nouveau possible %.',
      clan_ech_dans((quete_jour() + 1)::timestamp at time zone 'Europe/Paris');
  end if;
  if clan_ech_inter_avec(p_cible, v_clan) then
    raise exception 'Ce joueur a déjà fait son échange du jour avec ton clan.';
  end if;$b$);
  d := replace(d, $a$values (v_clan, v_uid, p_cible, p_ma, p_sa, t1, true);$a$,
                  $b$values (v_clan, v_uid, p_cible, p_ma, p_sa, t1, true, v_clan2);$b$);
  d := replace(d, $a$tier, inter)$a$, $b$tier, inter, clan2)$b$);
  if position('clan_ech_inter_avec(v_uid, v_clan2)' in d) = 0 or position('clan_ech_inter_dispo' in d) > 0
     or position('t1, true, v_clan2)' in d) = 0 then
    raise exception 's3-81 : proposer mal modifiée';
  end if;
  execute d;

  ---------- répondre ----------
  d := pg_get_functiondef('clan_ech_repondre(bigint,boolean)'::regprocedure); avant := d;
  d := regexp_replace(d, $r$  if e\.inter and clan_ech_inter_dispo\(v_uid\) is not null then.*?du jour\.';\n  end if;$r$,
$b$  -- s3-81 : un échange par jour avec chaque clan, remis à zéro à minuit
  if e.inter and clan_ech_inter_avec(v_uid, e.clan_id) then
    raise exception 'Un échange par jour avec chaque clan : déjà fait avec ce clan aujourd''hui, à nouveau possible %.',
      clan_ech_dans((quete_jour() + 1)::timestamp at time zone 'Europe/Paris');
  end if;
  if e.inter and clan_ech_inter_avec(e.proposant, clan_ech_clan(v_uid)) then
    update clan_echanges set etat = 'annule', repondu_le = now() where id = p_id;
    raise exception 'Ce joueur a déjà fait son échange du jour avec ton clan.';
  end if;$b$);
  if position('clan_ech_inter_avec(v_uid, e.clan_id)' in d) = 0 or position('clan_ech_inter_dispo' in d) > 0 then
    raise exception 's3-81 : repondre mal modifiée';
  end if;
  execute d;

  ---------- état : les clans déjà faits aujourd'hui ----------
  d := pg_get_functiondef('clan_ech_etat()'::regprocedure); avant := d;
  d := replace(d, $a$'inter_dispo_le', clan_ech_inter_dispo(v_uid),$a$,
$b$'inter_dispo_le', clan_ech_inter_dispo(v_uid),
    'inter_faits', coalesce((select jsonb_agg(distinct c.tag) from clan_echanges e join clans c on c.id = clan_ech_inter_autre(e, v_uid)
                               where e.inter and e.etat = 'accepte' and v_uid in (e.proposant, e.destinataire)
                                 and e.repondu_le >= (quete_jour()::timestamp at time zone 'Europe/Paris')), '[]'::jsonb),   -- s3-81$b$);
  if d = avant then raise exception 's3-81 : etat non modifiée'; end if;
  execute d;
end $do$;
