-- =====================================================================
--  TerraFront — les chances d'attaque, pour plusieurs communes d'un coup
--
--  Oshannir : « bug de calcul ou d'affichage ? entre attaquer sur le
--  territoire vs attaquer dans la page combat ». Saint-Genis-Laval
--  affichait 35 % dans l'onglet Combat et 50 % sur la carte.
--
--  C'est un bug d'affichage, et la carte dit vrai. L'onglet Combat
--  n'appelait pas le serveur : il lisait une constante du navigateur,
--  le taux nominal de l'intensité (Prudente 35, Normale 50, Offensive
--  65), identique pour les 34 739 communes. La proximité — 28 communes
--  à moins de 20 km dans son cas — n'entrait pas dans le calcul.
--
--  On ne corrige pas le second calcul, on le supprime. Cette fonction
--  répond pour une liste de communes en un appel, avec exactement les
--  mêmes règles que apercu_attaque : aucune formule n'est réécrite,
--  elles sont seulement appelées en lot.
--
--  Idempotent.
-- =====================================================================

create or replace function public.apercu_attaques(p_codes text[],
                                                  p_intensite text default 'normale')
returns table(commune_code text, chances integer, cout integer,
              proches integer, a_distance boolean)
language plpgsql
stable
security definer
set search_path to 'public'
as $function$
declare
  v_uid uuid := auth.uid();
  v_base numeric;
begin
  if v_uid is null then raise exception 'Non connecté'; end if;

  v_base := chance_intensite(p_intensite);
  if v_base is null then raise exception 'Intensité inconnue'; end if;

  -- Un garde-fou : le navigateur n'envoie que ce qu'il affiche, mais une
  -- liste sans limite ferait de cette fonction une arme contre la base.
  if array_length(p_codes, 1) > 400 then
    raise exception 'Trop de communes demandées d''un coup (maximum 400)';
  end if;

  return query
  select c.code,
         -- mêmes bornes que apercu_attaque : jamais moins de 10 %, jamais
         -- plus de 90 %, quelle que soit la proximité
         round(greatest(0.10, least(0.90, v_base + bonus_proximite(p.nb))) * 100)::integer,
         greatest(1, round(cout_attaque(c.tier) * cout_intensite(p_intensite)))::integer,
         p.nb,
         p.nb <= 0
    from unnest(p_codes) as u(code)
    -- une jointure plutôt qu'une exception : un code inconnu est ignoré,
    -- le reste de la liste répond quand même
    join communes c on c.code = u.code
    cross join lateral (select communes_proches(v_uid, c.code, 20) as nb) p;
end;
$function$;

grant execute on function public.apercu_attaques(text[], text) to authenticated;

-- =====================================================================
--  MESURE — à lancer avant que je branche le navigateur dessus
-- =====================================================================
--  communes_proches est appelée une fois par cible. Sur un joueur qui
--  possède beaucoup de communes et sur une longue liste de cibles, ça
--  peut coûter cher. Cette mesure le dit au lieu de le supposer.
--
--  L'éditeur SQL n'est connecté à aucun joueur, donc auth.uid() est
--  vide : on se fait passer pour Maroli, qui a le plus de communes et
--  donc le pire cas.

select set_config(
  'request.jwt.claims',
  json_build_object('sub', (select id from joueurs where pseudo = 'Maroli'))::text,
  true);

explain analyze
select * from public.apercu_attaques(
  array(select p.commune_code
          from possessions p
          join communes c on c.code = p.commune_code
         where c.tier in ('rare', 'legendaire')
           and p.joueur_id <> (select id from joueurs where pseudo = 'Maroli')
         limit 200),
  'normale');

--  Ce qui m'intéresse est la dernière ligne, « Execution Time ».
--    sous 300 ms   -> on branche tel quel
--    300 ms à 2 s  -> il faut réduire la liste ou garder en cache
--    au-delà       -> communes_proches est à revoir avant d'aller plus loin
--
--  Si « set_config » ne suffit pas et que la fonction répond
--  « Non connecté », dis-le-moi : je ferai la mesure autrement.
-- =====================================================================
