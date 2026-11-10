-- s2-135 (10/11/2026) : le bandeau Discord de l'onglet Clan (demande de Nataël : « l'idéal est d'avoir le même
-- pseudo sur Discord et sur le jeu »). Dit au joueur si le bot des clans l'a trouvé sur le Discord, d'après le
-- dernier passage du bot écrit dans le journal (liste « introuvables »). Lecture seule.
-- 'introuvable' : son pseudo est dans la liste ; 'trouve' : il était déjà dans son clan à ce passage et n'y est pas ;
-- null : pas de clan, pas de passage connu, ou arrivé dans le clan depuis (on ne sait pas encore).
create or replace function public.discord_moi_statut()
returns text
language sql
stable security definer
set search_path to 'public'
as $f$
  with j as (select le, details from discord_sync_journal
              where mode = 'actif' and ok and details ? 'introuvables'
              order by le desc limit 1),
       moi as (select p.pseudo, m.depuis from joueurs p join clan_membres m on m.joueur_id = p.id where p.id = auth.uid())
  select case
    when not exists (select 1 from moi) or not exists (select 1 from j) then null
    when exists (select 1 from j, moi, jsonb_array_elements_text(j.details->'introuvables') x where x = moi.pseudo) then 'introuvable'
    when (select depuis from moi) > (select le from j) then null
    else 'trouve' end;
$f$;
revoke execute on function public.discord_moi_statut() from public, anon;
grant execute on function public.discord_moi_statut() to authenticated;
notify pgrst, 'reload schema';
