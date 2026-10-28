-- ===========================================================================
--  s2-52 — Clans : modifier le clan et créer son blason
--  (28/10, aperçu validé par Nataël : « c'est parfait »)
--  - clans.blason (jsonb) : forme, partition, couleurs, meuble, nombre, bordure.
--    Seules les valeurs de la liste ci-dessous sont acceptées (le jeu les
--    dessine en SVG : rien d'autre ne doit pouvoir y entrer).
--  - clan_modifier(nom, sigle, couleur, blason) : chef seulement.
--    Nom et sigle : une modification par semaine, toujours uniques.
--    Couleur sur la carte et blason : quand on veut.
--  - clans_blasons() : le blason de chaque clan, par sigle, pour l'affichage.
--  - Bras droits : un 3e droit, « modifier le clan » (non par défaut), que le
--    chef peut donner. clan_role prend un 5e paramètre (p_modifier) ; mon_clan
--    renvoie ce droit.
--  Rejouable. Contrôle attendu : true | true | true | true
-- ===========================================================================
begin;

alter table public.clans add column if not exists blason jsonb;
alter table public.clans add column if not exists nom_change_le timestamptz;
alter table public.clan_membres add column if not exists peut_modifier boolean not null default false;

-- le blason, ramené aux seules clés connues ; null s'il n'est pas valide
create or replace function public.blason_propre(b jsonb)
 returns jsonb language sql immutable set search_path to 'public'
as $f$
  with e as (select array['or','argent','gueules','azur','sinople','sable','pourpre','orange','ciel','rose','turquoise','brun'] as emaux)
  select case when jsonb_typeof(b) = 'object'
     and (b->>'forme')     = any(array['francais','ancien','banniere','rond'])
     and (b->>'partition') = any(array['plein','parti','coupe','tranche','taille','ecartele','chef','fasce','pal','bande',
                                        'chevron','croix','sautoir','echiquete','fusele','gironne'])
     and (b->>'c1') = any(e.emaux) and (b->>'c2') = any(e.emaux) and (b->>'cm') = any(e.emaux)
     and (b->>'meuble')    = any(array['aucun','lys','etoile','croissant','tour','couronne','epee','cle','ancre','arbre',
                                        'coeur','coquille','hermine','aigle','soleil','epis'])
     and (b->>'nombre') in ('1', '3')
     and (b->>'bordure') = any(e.emaux || 'aucune'::text)
    then jsonb_build_object('forme', b->>'forme', 'partition', b->>'partition', 'c1', b->>'c1', 'c2', b->>'c2',
                            'meuble', b->>'meuble', 'cm', b->>'cm', 'nombre', (b->>'nombre')::int, 'bordure', b->>'bordure')
  end from e;
$f$;

create or replace function public.clan_modifier(p_nom text, p_tag text, p_couleur text, p_blason jsonb)
 returns jsonb language plpgsql security definer set search_path to 'public'
as $f$
declare
  v_uid uuid := auth.uid();
  v_clan clans%rowtype;
  v_nom text := btrim(regexp_replace(coalesce(p_nom, ''), '\s+', ' ', 'g'));
  v_tag text := upper(btrim(coalesce(p_tag, '')));
  v_blason jsonb;
  v_change boolean;
begin
  if v_uid is null then raise exception 'Non connecte'; end if;
  if not clans_ouverts() then raise exception 'Les clans ouvrent bientot'; end if;
  select * into v_clan from clans where chef = v_uid for update;
  if v_clan.id is null then   -- un bras droit qui a le droit de modifier
    select c.* into v_clan from clans c join clan_membres m on m.clan_id = c.id
     where m.joueur_id = v_uid and m.bras_droit and m.peut_modifier for update of c;
  end if;
  if v_clan.id is null then raise exception 'Seul le chef peut modifier le clan'; end if;

  if char_length(v_nom) not between 3 and 24 then raise exception 'Nom du clan : 3 a 24 caracteres'; end if;
  if v_tag !~ '^[A-Z0-9]{2,4}$' then raise exception 'Sigle : 2 a 4 lettres ou chiffres'; end if;
  v_change := v_nom <> v_clan.nom or v_tag <> v_clan.tag;
  if v_change then
    if v_clan.nom_change_le > now() - interval '7 days' then
      raise exception 'Nom et sigle : une modification par semaine (prochaine le %)',
        to_char((v_clan.nom_change_le + interval '7 days') at time zone 'Europe/Paris', 'DD/MM à HH24"h"MI');
    end if;
    if exists(select 1 from clans where lower(nom) = lower(v_nom) and id <> v_clan.id) then raise exception 'Ce nom de clan est deja pris'; end if;
    if exists(select 1 from clans where tag = v_tag and id <> v_clan.id) then raise exception 'Ce sigle est deja pris'; end if;
  end if;

  if p_couleur is null or upper(p_couleur) <> all(array['#E07A2E','#4C9BE8','#C45BD6','#2BB673','#E5484D','#E8C547',
                                                     '#1ABC9C','#8E9AAF','#F06EA9','#7DD3FC','#A3E635','#F97316']) then
    raise exception 'Couleur inconnue';
  end if;
  if p_blason is not null then
    v_blason := blason_propre(p_blason);
    if v_blason is null then raise exception 'Blason invalide'; end if;
  end if;

  update clans set nom = v_nom, tag = v_tag, couleur = upper(p_couleur),
                   blason = coalesce(v_blason, blason),
                   nom_change_le = case when v_change then now() else nom_change_le end
   where id = v_clan.id;
  return mon_clan();
end;
$f$;

create or replace function public.clans_blasons()
 returns table(tag text, blason jsonb, nom_libre_le timestamptz)
 language sql stable security definer set search_path to 'public'
as $f$
  select c.tag::text, c.blason, c.nom_change_le + interval '7 days'
    from clans c
   where auth.uid() is not null and (c.blason is not null or c.nom_change_le is not null);
$f$;

revoke all on function public.blason_propre(jsonb)                   from public, anon, authenticated;
revoke all on function public.clan_modifier(text, text, text, jsonb) from public, anon;
revoke all on function public.clans_blasons()                        from public, anon;
grant execute on function public.clan_modifier(text, text, text, jsonb) to authenticated;
grant execute on function public.clans_blasons()                        to authenticated;

-- le droit « modifier » des bras droits
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
  d := pg_get_functiondef('public.mon_clan()'::regprocedure);
  if position('peut_modifier' in d) = 0 then
    d := pg_temp.remplacer(d, $a$'exclure', mm.bras_droit and mm.peut_exclure)$a$,
                              $a$'exclure', mm.bras_droit and mm.peut_exclure, 'modifier', mm.bras_droit and mm.peut_modifier)$a$, 'mon_clan (mes droits)');
    d := pg_temp.remplacer(d, $a$jsonb_build_object('inviter', m.peut_inviter, 'exclure', m.peut_exclure)$a$,
                              $a$jsonb_build_object('inviter', m.peut_inviter, 'exclure', m.peut_exclure, 'modifier', m.peut_modifier)$a$, 'mon_clan (membres)');
    execute d;
  end if;
end $do$;

drop function if exists public.clan_role(uuid, boolean, boolean, boolean);
create or replace function public.clan_role(p_joueur uuid, p_bras_droit boolean,
                                            p_inviter boolean default true, p_exclure boolean default false,
                                            p_modifier boolean default false)
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
     set bras_droit    = coalesce(p_bras_droit, false),
         peut_inviter  = case when coalesce(p_bras_droit, false) then coalesce(p_inviter, true) else true end,
         peut_exclure  = case when coalesce(p_bras_droit, false) then coalesce(p_exclure, false) else false end,
         peut_modifier = case when coalesce(p_bras_droit, false) then coalesce(p_modifier, false) else false end
   where joueur_id = p_joueur;
  return mon_clan();
end;
$f$;
revoke all on function public.clan_role(uuid, boolean, boolean, boolean, boolean) from public, anon;
grant execute on function public.clan_role(uuid, boolean, boolean, boolean, boolean) to authenticated;

commit;

select has_function_privilege('authenticated', 'public.clan_modifier(text,text,text,jsonb)', 'execute') as modifier_ok,
       has_function_privilege('authenticated', 'public.clans_blasons()', 'execute')                    as blasons_ok,
       has_function_privilege('authenticated', 'public.clan_role(uuid,boolean,boolean,boolean,boolean)', 'execute') as role_ok,
       public.blason_propre(jsonb '{"forme":"francais","partition":"coupe","c1":"azur","c2":"or","meuble":"lys","cm":"or","nombre":3,"bordure":"aucune"}') is not null as validation_ok;
