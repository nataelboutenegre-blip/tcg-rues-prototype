-- s3-77 (Bonjean) : notification téléphone quand un joueur te prend une commune.
-- Au plus une toutes les 15 minutes par joueur (un gros joueur peut en prendre 20 d'un coup) :
-- la suivante dit combien de communes ont été perdues dans la journée. Réglage « tel.perdue », actif par défaut.

create table if not exists notif_perdue_vu (joueur_id uuid primary key, le timestamptz not null default now());
alter table notif_perdue_vu enable row level security;   -- aucune politique : lu seulement par les fonctions

do $do$
declare d text; avant text;
begin
  d := pg_get_functiondef('notif_defaut()'::regprocedure); avant := d;
  d := replace(d, '"tel": {"attaque": true,', '"tel": {"attaque": true, "perdue": true,');
  if d = avant then raise exception 's3-77 : notif_defaut non modifiée'; end if;
  execute d;

  d := pg_get_functiondef('regler_notif(text,text,boolean)'::regprocedure); avant := d;
  d := replace(d, $a$(p_canal = 'tel' and p_type in ('attaque','paquet','defense','clan'))$a$,
                  $b$(p_canal = 'tel' and p_type in ('attaque','perdue','paquet','defense','clan'))$b$);
  if d = avant then raise exception 's3-77 : regler_notif non modifiée'; end if;
  execute d;

  d := pg_get_functiondef('notif_coupee(uuid,text)'::regprocedure); avant := d;
  d := replace(d, $a$  if p_tag like 'danger-%' then$a$,
                  $b$  if p_tag like 'perdue-%' then return not coalesce((v_p #>> '{tel,perdue}')::boolean, true); end if;   -- s3-77
  if p_tag like 'danger-%' then$b$);
  if d = avant then raise exception 's3-77 : notif_coupee non modifiée'; end if;
  execute d;
end $do$;

create or replace function notif_commune_perdue() returns trigger
language plpgsql security definer set search_path to 'public' as $$
declare v_n integer; v_pseudo text;
begin
  begin
    if exists (select 1 from notif_perdue_vu v where v.joueur_id = new.cible and v.le > now() - interval '15 minutes') then
      return new;
    end if;
    insert into notif_perdue_vu(joueur_id, le) values (new.cible, now())
      on conflict (joueur_id) do update set le = excluded.le;
    select count(*) into v_n from journal j
     where j.cible = new.cible and j.type = 'conquete' and j.acteur <> new.cible
       and j.cree_le >= (quete_jour()::timestamp at time zone 'Europe/Paris');
    select pseudo into v_pseudo from joueurs where id = new.acteur;
    perform notifier_joueur(new.cible,
      '🏳️ ' || coalesce(new.commune_nom, 'Une commune') || ' est tombée',
      coalesce(v_pseudo, 'Un joueur') || ' t''a pris ' || coalesce(new.commune_nom, 'une commune') || '.'
        || case when v_n > 1 then ' ' || v_n || ' communes perdues aujourd''hui.' else '' end,
      './?onglet=qg', 'perdue-jour');
  exception when others then null;   -- une notification ne doit jamais bloquer une conquête
  end;
  return new;
end; $$;
revoke all on function notif_commune_perdue() from public, anon, authenticated;

drop trigger if exists trg_notif_commune_perdue on journal;
create trigger trg_notif_commune_perdue after insert on journal
  for each row when (new.type = 'conquete' and new.cible is not null and new.cible <> new.acteur)
  execute function notif_commune_perdue();
