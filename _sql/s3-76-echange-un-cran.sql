-- s3-76 : échanges dans le clan avec un cran d'écart de rareté (légendaire <-> épique, épique <-> rare…)
-- Une fois par jour et par joueur (journée de quete_jour), seulement entre membres du même clan
-- (pas entre clans). Les échanges de même rareté ne changent pas.
-- clan_ech_etat renvoie aussi la rareté de chaque commune des propositions et l'état « écart utilisé ».

alter table clan_echanges add column if not exists ecart boolean not null default false;

create or replace function tier_rang(t text) returns integer
language sql immutable set search_path to 'public' as $$
  select array_position(array['commun','peucommun','rare','epique','legendaire'], t);
$$;

create or replace function clan_ech_ecart_fait(p_joueur uuid) returns boolean
language sql stable security definer set search_path to 'public' as $$
  select exists (select 1 from clan_echanges e
                  where e.etat = 'accepte' and not e.inter and e.ecart and p_joueur in (e.proposant, e.destinataire)
                    and e.repondu_le >= (quete_jour()::timestamp at time zone 'Europe/Paris'));
$$;
revoke all on function clan_ech_ecart_fait(uuid) from public, anon;

do $do$
declare d text; n text; avant text;
begin
  ---------- clan_ech_proposer ----------
  d := pg_get_functiondef('clan_ech_proposer(uuid,text,text)'::regprocedure); avant := d;
  d := replace(d,
$a$  if t1 is distinct from t2 then raise exception 'Les deux communes doivent être de même rareté.'; end if;$a$,
$b$  if t1 is distinct from t2 then   -- s3-76 : un cran d'écart, une fois par jour
    if abs(tier_rang(t1) - tier_rang(t2)) <> 1 then
      raise exception 'Un seul cran d''écart de rareté au plus (légendaire contre épique, épique contre rare…).';
    end if;
    if clan_ech_ecart_fait(v_uid) then
      raise exception 'Tu as déjà fait ton échange de rareté différente aujourd''hui : à nouveau possible %.',
        clan_ech_dans((quete_jour() + 1)::timestamp at time zone 'Europe/Paris');
    end if;
    if clan_ech_ecart_fait(p_cible) then
      raise exception 'Ton coéquipier a déjà fait son échange de rareté différente aujourd''hui.';
    end if;
  end if;$b$);
  if d = avant then raise exception 's3-76 : proposer non modifiée'; end if;
  execute d;

  ---------- clan_ech_repondre ----------
  d := pg_get_functiondef('clan_ech_repondre(bigint,boolean)'::regprocedure); avant := d;
  d := replace(d,
$a$  if t1 is distinct from t2 then
    update clan_echanges set etat = 'annule', repondu_le = now() where id = p_id;
    raise exception 'Les deux communes ne sont plus de même rareté.';
  end if;$a$,
$b$  if t1 is distinct from t2 and (e.inter or abs(tier_rang(t1) - tier_rang(t2)) <> 1) then   -- s3-76
    update clan_echanges set etat = 'annule', repondu_le = now() where id = p_id;
    raise exception 'Les deux communes ne sont plus de même rareté.';
  end if;
  if t1 is distinct from t2 and clan_ech_ecart_fait(v_uid) then
    raise exception 'Tu as déjà fait ton échange de rareté différente aujourd''hui : à nouveau possible %.',
      clan_ech_dans((quete_jour() + 1)::timestamp at time zone 'Europe/Paris');
  end if;
  if t1 is distinct from t2 and clan_ech_ecart_fait(e.proposant) then
    update clan_echanges set etat = 'annule', repondu_le = now() where id = p_id;
    raise exception 'Ce joueur a déjà fait son échange de rareté différente aujourd''hui.';
  end if;$b$);
  n := d;
  d := replace(d, $a$perform noter_journal('echange', e.proposant, v_uid, e.commune_destinataire, t1);$a$,
                  $b$perform noter_journal('echange', e.proposant, v_uid, e.commune_destinataire, t2);$b$);
  if d = n then raise exception 's3-76 : journal non modifié'; end if;
  n := d;
  d := replace(d, $a$update clan_echanges set etat = 'accepte', repondu_le = now() where id = p_id;$a$,
                  $b$update clan_echanges set etat = 'accepte', repondu_le = now(), ecart = (t1 is distinct from t2) where id = p_id;$b$);
  if d = n or position('tier_rang' in d) = 0 then raise exception 's3-76 : repondre non modifiée'; end if;
  execute d;

  ---------- clan_ech_etat ----------
  d := pg_get_functiondef('clan_ech_etat()'::regprocedure); avant := d;
  d := replace(d, $a$jsonb_build_object('code', c1.code, 'nom', c1.nom, 'dept', c1.departement)$a$,
                  $b$jsonb_build_object('code', c1.code, 'nom', c1.nom, 'dept', c1.departement, 'tier', c1.tier)$b$);
  d := replace(d, $a$jsonb_build_object('code', c2.code, 'nom', c2.nom, 'dept', c2.departement)$a$,
                  $b$jsonb_build_object('code', c2.code, 'nom', c2.nom, 'dept', c2.departement, 'tier', c2.tier)$b$);
  d := replace(d, $a$'faits', clan_ech_du_jour(v_uid),$a$,
                  $b$'faits', clan_ech_du_jour(v_uid), 'ecart_fait', clan_ech_ecart_fait(v_uid),$b$);
  d := replace(d, $a$'faits', clan_ech_du_jour_avec(v_uid, j.id),$a$,
                  $b$'faits', clan_ech_du_jour_avec(v_uid, j.id), 'ecart_fait', clan_ech_ecart_fait(j.id),$b$);
  if (length(d) - length(replace(d, '''tier'', c1.tier', ''))) / length('''tier'', c1.tier') <> 2
     or (length(d) - length(replace(d, '''tier'', c2.tier', ''))) / length('''tier'', c2.tier') <> 2
     or (length(d) - length(replace(d, 'ecart_fait', ''))) / length('ecart_fait') <> 4 then
    raise exception 's3-76 : etat mal modifiée';
  end if;
  execute d;
end $do$;
