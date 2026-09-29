-- ===========================================================================
--  TerraFront — le poids de la legendaire passe de 0,5 a 1,0
--
--  POURQUOI
--    A 0,09 %, un joueur qui ouvre ses 3 paquets gratuits quotidiens tire
--    une legendaire tous les 74 jours. Une saison en dure 46. Le palier
--    etait donc hors d'atteinte sur une saison entiere.
--
--    A 1,0 : 0,18 %, une legendaire tous les 111 paquets.
--
--  POURQUOI PAS PLUS
--    Le taux est borne par le stock, pas par l'envie. Il reste 58
--    legendaires libres. Au pire cas — douze joueurs ouvrant leurs huit
--    paquets tous les jours — le stock tient :
--
--      poids 1,0  ->  67 jours     (saison de 46 : il reste de la marge)
--      poids 1,5  ->  45 jours     (pile la saison, zero marge)
--      poids 2,0  ->  33 jours     (le palier se vide avant la fin)
--
--    Et la conquete prend des legendaires en plus du tirage. 1,0 est le
--    dernier reglage qui laisse le palier vivant jusqu'au bout.
--
--  LE PLANCHER RESTE
--    Il empeche le taux de s'effondrer quand le palier se vide. Avec le
--    nouveau poids il s'active sous 15 libres au lieu de 30 : il ne sert
--    plus qu'aux situations extremes, ce qui est son role.
--
--  Une seule ligne change. Le reste de la fonction est identique.
-- ===========================================================================

create or replace function public.poids_tirage()
returns numeric[]
language sql
stable
security definer
set search_path to 'public'
as $$
  select array[
    greatest(
      -- 1,0 depuis le 29/09 (etait 0,5) : voir l'en-tete de ce fichier
      count(*) filter (where c.tier = 'legendaire') * 1.0,
      case when count(*) filter (where c.tier = 'legendaire') > 0 then 15 else 0 end
    ),
    count(*) filter (where c.tier = 'rare')      * 3.0,
    count(*) filter (where c.tier = 'peucommun') * 1.2,
    count(*) filter (where c.tier = 'commun')    * 1.0
  ]
  from communes c
  left join possessions p on p.commune_code = c.code
  where p.commune_code is null;
$$;

revoke all on function public.poids_tirage() from public, anon;
grant execute on function public.poids_tirage() to authenticated;


-- ---------------------------------------------------------------------------
--  Verification : les nouveaux taux, tout de suite
-- ---------------------------------------------------------------------------
select tier as palier, libres, chance as "chance %"
  from taux_actuels()
 order by chance;
