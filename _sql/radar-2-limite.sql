-- =====================================================================
--  TerraFront — Radar : 15 duels par jour au lieu de 5
--
--  Décidé avec Nataël le 5 octobre au soir : 5 était trop bas pour un duel
--  d'une minute et demie. On passe à 15 et on regarde dans une semaine si
--  un joueur remplit toute la file à lui seul.
--
--  Seule la valeur 'par_jour' change. Le reste est identique à radar-1.sql
--  (et radar-1.sql est mis à jour aussi, pour qu'une relance ne revienne
--  pas à 5). Rejouable.
-- =====================================================================

create or replace function public.radar_reglage(p text)
returns integer language sql immutable
set search_path to 'public'
as $$
  select case p
    when 'manches'    then 5
    when 'secondes'   then 15
    when 'marge'      then 2
    when 'penalite'   then 1000
    when 'par_jour'   then 15
    when 'k'          then 24
    when 'population' then 15000
  end;
$$;

-- vérification : doit afficher 15
select radar_reglage('par_jour') as duels_par_jour;
