-- ===========================================================================
--  TerraFront — les clans en formation (25 octobre 2026)
--  Le classement ne montre que les clans d'au moins 3 membres : un clan de
--  1 ou 2 joueurs était invisible, personne ne pouvait demander à le rejoindre.
--  clans_en_formation() : nom, sigle, couleur, nombre de membres et chef.
--  Lecture seule. Rejouable. Contrôle attendu : true | le nombre de clans de 1 ou 2 membres.
-- ===========================================================================
create or replace function public.clans_en_formation()
 returns table(clan_id uuid, nom text, tag text, couleur text, membres integer, chef text)
 language plpgsql stable security definer set search_path to 'public'
as $f$
begin
  if auth.uid() is null then raise exception 'Non connecte'; end if;
  if not clans_ouverts() then raise exception 'Les clans ouvrent bientot'; end if;
  return query
  select c.id, c.nom, c.tag, c.couleur, x.n::integer, (select j.pseudo from joueurs j where j.id = c.chef)
    from clans c
    join lateral (select count(*) n from clan_membres m where m.clan_id = c.id) x on true
   where x.n between 1 and 2
   order by x.n desc, c.cree_le;
end;
$f$;
revoke all on function public.clans_en_formation() from public, anon;
grant execute on function public.clans_en_formation() to authenticated;

select has_function_privilege('authenticated', 'public.clans_en_formation()', 'execute') as ouvert_aux_joueurs,
       (select count(*) from public.clans c where (select count(*) from public.clan_membres m where m.clan_id = c.id) between 1 and 2) as clans_en_formation;
