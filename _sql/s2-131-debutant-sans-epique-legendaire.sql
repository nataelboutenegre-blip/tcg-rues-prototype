-- s2-131 (9/11/2026, lancé vers 18 h 15) : le bonus de débutant (au moins 85 %) ne joue plus
-- contre une épique ni une légendaire : chances normales sur ces raretés (Nataël : « Oui je préférerais »).
-- chance_debutant sert à attaquer, apercu_attaque et apercu_attaques : un seul endroit à changer.
-- Test annulé avant : légendaire 0.50 -> 0.50, commune 0.50 -> 0.85, sans bonus 0.50 -> 0.50.
-- Retour arrière : enlever la ligne « and coalesce((select k.tier ...) not in ('epique', 'legendaire') ».
create or replace function public.chance_debutant(p_actif boolean, p_uid uuid, p_code text, p_chance numeric)
 returns numeric language sql stable security definer set search_path to 'public'
as $b$
  select case
    when coalesce(p_actif, false) and not garnison_active(p_code)
         and coalesce((select k.tier from communes k where k.code = p_code), '') not in ('epique', 'legendaire')   -- s2-131 : pas sur une épique ni une légendaire
      then least(0.90, greatest(p_chance,
             coalesce((select (c.valeur::jsonb->>'chances')::numeric from config_jeu c where c.cle = 'debutant'), 0.85)
             + bonus_batiments(p_uid, p_code)))
    else p_chance end;
$b$;
