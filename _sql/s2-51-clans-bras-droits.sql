-- ===========================================================================
--  s2-51 — Clans : les bras droits (28/10, aperçu validé par Nataël : « parfait »)
--  - Le chef nomme jusqu'à 2 bras droits et choisit leurs droits :
--    inviter (oui par défaut), exclure (non par défaut).
--  - Un bras droit qui peut exclure n'exclut que les simples membres
--    (ni le chef, ni l'autre bras droit).
--  - Si le chef quitte le clan, un bras droit prend sa place (avant : le plus
--    ancien membre) ; le nouveau chef perd son rôle de bras droit.
--  Nouveau : clan_role(joueur, bras_droit, inviter, exclure), réservé au chef.
--  Modifiées à partir de leur définition en production (texte attendu une
--  fois par fonction, sinon rien ne change) : mon_clan, clan_inviter,
--  clan_exclure, clan_sortir. Recréée : clan_membres_voir (+ bras_droit).
--  Rejouable. Contrôle attendu : true | true | true | true | true | true
-- ===========================================================================
begin;

alter table public.clan_membres add column if not exists bras_droit   boolean not null default false;
alter table public.clan_membres add column if not exists peut_inviter boolean not null default true;
alter table public.clan_membres add column if not exists peut_exclure boolean not null default false;

-- remplace un texte attendu exactement une fois, sinon tout s'arrête
create or replace function pg_temp.remplacer(d text, avant text, apres text, quoi text)
 returns text language plpgsql as $r$
begin
  if (length(d) - length(replace(d, avant, ''))) / length(avant) <> 1 then
    raise exception '% : texte attendu introuvable, rien n''a changé', quoi;
  end if;
  return replace(d, avant, apres);
end $r$;

do $do$
declare d text;
begin
  -- 1. mon_clan : mes droits, et pour chaque membre son rôle et ses droits
  d := pg_get_functiondef('public.mon_clan()'::regprocedure);
  if position('''bras_droit''' in d) = 0 then
    d := pg_temp.remplacer(d, $a$'chef', v_clan.chef = v_uid,$a$,
      $a$'chef', v_clan.chef = v_uid,
      'droits', (select jsonb_build_object('inviter', mm.bras_droit and mm.peut_inviter, 'exclure', mm.bras_droit and mm.peut_exclure)
                   from clan_membres mm where mm.joueur_id = v_uid),$a$, 'mon_clan (droits)');
    d := pg_temp.remplacer(d, $a$'id', j.id, 'pseudo', j.pseudo, 'chef', j.id = v_clan.chef, 'moi', j.id = v_uid,$a$,
      $a$'id', j.id, 'pseudo', j.pseudo, 'chef', j.id = v_clan.chef, 'moi', j.id = v_uid,
                      'bras_droit', m.bras_droit, 'droits', jsonb_build_object('inviter', m.peut_inviter, 'exclure', m.peut_exclure),$a$, 'mon_clan (membres)');
    execute d;
  end if;

  -- 2. clan_inviter : le chef, ou un bras droit qui peut inviter
  d := pg_get_functiondef('public.clan_inviter(text)'::regprocedure);
  if position('bras_droit' in d) = 0 then
    d := pg_temp.remplacer(d, $a$  select c.id into v_clan from clans c where c.chef = v_uid;
  if v_clan is null then raise exception 'Seul le chef peut inviter'; end if;$a$,
      $a$  select c.id into v_clan from clans c where c.chef = v_uid;
  if v_clan is null then   -- s2-51 : un bras droit qui peut inviter
    select m.clan_id into v_clan from clan_membres m where m.joueur_id = v_uid and m.bras_droit and m.peut_inviter;
  end if;
  if v_clan is null then raise exception 'Seul le chef peut inviter'; end if;$a$, 'clan_inviter');
    execute d;
  end if;

  -- 3. clan_exclure : le chef, ou un bras droit qui peut exclure (simples membres seulement)
  d := pg_get_functiondef('public.clan_exclure(uuid)'::regprocedure);
  if position('bras_droit' in d) = 0 then
    d := pg_temp.remplacer(d, $a$  select id into v_clan from clans where chef = v_uid;
  if v_clan is null then raise exception 'Seul le chef peut exclure'; end if;$a$,
      $a$  select id into v_clan from clans where chef = v_uid;
  if v_clan is null then   -- s2-51 : un bras droit qui peut exclure
    select m.clan_id into v_clan from clan_membres m where m.joueur_id = v_uid and m.bras_droit and m.peut_exclure;
    if v_clan is not null and exists(select 1 from clan_membres m2 join clans c2 on c2.id = m2.clan_id
                                       where m2.joueur_id = p_joueur and (m2.bras_droit or c2.chef = p_joueur)) then
      raise exception 'Un bras droit ne peut exclure ni le chef ni un autre bras droit';
    end if;
  end if;
  if v_clan is null then raise exception 'Seul le chef peut exclure'; end if;$a$, 'clan_exclure');
    execute d;
  end if;

  -- 4. clan_sortir : un bras droit succède au chef
  d := pg_get_functiondef('public.clan_sortir(uuid)'::regprocedure);
  if position('bras_droit' in d) = 0 then
    d := pg_temp.remplacer(d, $a$select joueur_id into v_suivant from clan_membres where clan_id = v_clan order by depuis, joueur_id limit 1;$a$,
      $a$select joueur_id into v_suivant from clan_membres where clan_id = v_clan order by bras_droit desc, depuis, joueur_id limit 1;$a$, 'clan_sortir (successeur)');
    d := pg_temp.remplacer(d, $a$    update clans set chef = v_suivant where id = v_clan and (chef = p_uid or chef is null);$a$,
      $a$    update clans set chef = v_suivant where id = v_clan and (chef = p_uid or chef is null);
    -- s2-51 : le nouveau chef n'est plus bras droit
    update clan_membres set bras_droit = false, peut_inviter = true, peut_exclure = false
     where joueur_id = v_suivant and v_suivant = (select chef from clans where id = v_clan);$a$, 'clan_sortir (rôle)');
    execute d;
  end if;
end $do$;

-- 5. clan_role : nommer / retirer un bras droit, choisir ses droits (chef seulement)
create or replace function public.clan_role(p_joueur uuid, p_bras_droit boolean,
                                            p_inviter boolean default true, p_exclure boolean default false)
 returns jsonb language plpgsql security definer set search_path to 'public'
as $f$
declare
  v_uid uuid := auth.uid();
  v_clan uuid;
begin
  if v_uid is null then raise exception 'Non connecte'; end if;
  if not clans_ouverts() then raise exception 'Les clans ouvrent bientot'; end if;
  select id into v_clan from clans where chef = v_uid for update;
  if v_clan is null then raise exception 'Seul le chef peut nommer un bras droit'; end if;
  if p_joueur = v_uid then raise exception 'Le chef ne peut pas être son propre bras droit'; end if;
  if not exists(select 1 from clan_membres where joueur_id = p_joueur and clan_id = v_clan) then
    raise exception 'Ce joueur n''est pas dans ton clan';
  end if;
  if coalesce(p_bras_droit, false)
     and not (select bras_droit from clan_membres where joueur_id = p_joueur)
     and (select count(*) from clan_membres where clan_id = v_clan and bras_droit) >= 2 then
    raise exception 'Deux bras droits au plus : retire le rôle à l''un d''eux';
  end if;
  update clan_membres
     set bras_droit   = coalesce(p_bras_droit, false),
         peut_inviter = case when coalesce(p_bras_droit, false) then coalesce(p_inviter, true) else true end,
         peut_exclure = case when coalesce(p_bras_droit, false) then coalesce(p_exclure, false) else false end
   where joueur_id = p_joueur;
  return mon_clan();
end;
$f$;
revoke all on function public.clan_role(uuid, boolean, boolean, boolean) from public, anon;
grant execute on function public.clan_role(uuid, boolean, boolean, boolean) to authenticated;

-- 6. clan_membres_voir : + bras_droit (le type de retour change : on la recrée)
drop function if exists public.clan_membres_voir(uuid);
create function public.clan_membres_voir(p_clan uuid)
 returns table(joueur_id uuid, pseudo text, chef boolean, communes integer, dernier_jour date, bras_droit boolean)
 language sql
 stable security definer
 set search_path to 'public'
as $f$
  select j.id, j.pseudo::text, (c.chef = j.id),
         (select count(*) from possessions p where p.joueur_id = j.id)::integer,
         (select max(d.jour) from jours_joues d where d.joueur_id = j.id),
         m.bras_droit
    from clan_membres m
    join clans c on c.id = m.clan_id
    join joueurs j on j.id = m.joueur_id
   where m.clan_id = p_clan and auth.uid() is not null
   order by (c.chef = j.id) desc, m.bras_droit desc, 4 desc, j.pseudo;
$f$;
revoke all on function public.clan_membres_voir(uuid) from public, anon;
grant execute on function public.clan_membres_voir(uuid) to authenticated;

commit;

select position('''bras_droit''' in pg_get_functiondef('public.mon_clan()'::regprocedure)) > 0           as mon_clan,
       position('bras_droit' in pg_get_functiondef('public.clan_inviter(text)'::regprocedure)) > 0       as inviter,
       position('bras_droit' in pg_get_functiondef('public.clan_exclure(uuid)'::regprocedure)) > 0       as exclure,
       position('bras_droit' in pg_get_functiondef('public.clan_sortir(uuid)'::regprocedure)) > 0        as succession,
       has_function_privilege('authenticated', 'public.clan_role(uuid,boolean,boolean,boolean)', 'execute') as role_ok,
       has_function_privilege('authenticated', 'public.clan_membres_voir(uuid)', 'execute')            as membres_ok;
