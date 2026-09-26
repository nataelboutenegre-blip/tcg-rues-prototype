-- =====================================================================
--  TerraFront — offrir un paquet à un joueur
--
--  Pourquoi une fonction plutôt qu'un UPDATE à la main : il y a trois
--  pièges, et on va s'en servir plus d'une fois.
--
--   1. jetons_gratuits est plafonné à 3 par demarrer_paquet, à CHAQUE
--      ouverture. Un quatrième jeton est écrasé sans bruit. La fonction
--      ne donne donc un jeton que s'il reste de la place sous le
--      plafond, et bascule sur 200 points sinon.
--
--   2. jetons_gratuits n'est pas la vraie valeur : le compte réel se
--      recalcule depuis jetons_maj, à raison d'un jeton toutes les
--      20 minutes. On matérialise ce calcul avant d'ajouter, exactement
--      comme le fait demarrer_paquet, sinon on offre un jeton et on en
--      détruit un autre.
--
--   3. tirages_restants n'est PAS un bon cadeau. Ce compteur est crédité
--      à l'ouverture d'un paquet et consommé par les cinq tirages qui
--      suivent ; un reliquat n'est rattrapable par aucun écran. Aldrak
--      en a 20 dont il ne peut rien faire. Tant que ce n'est pas réglé,
--      on n'ajoute rien dessus.
--
--  Réservée à l'administration : personne ne peut l'appeler depuis le
--  jeu, seulement depuis l'éditeur SQL.
-- =====================================================================

create or replace function public.offrir_paquet(p_pseudo text)
returns text
language plpgsql
security definer
set search_path to 'public'
as $function$
declare
  v_id uuid;
  v_jetons numeric;
  v_maj timestamptz;
  v_reel numeric;
begin
  select id, jetons_gratuits, jetons_maj
    into v_id, v_jetons, v_maj
    from joueurs
   where lower(pseudo) = lower(btrim(p_pseudo))
   for update;

  if v_id is null then
    raise exception 'Aucun joueur nommé « % »', p_pseudo;
  end if;

  -- la valeur réelle, accumulation comprise, comme demarrer_paquet la voit
  v_reel := least(3, v_jetons + extract(epoch from (now() - v_maj)) / 1200.0);

  if v_reel + 1 <= 3 then
    update joueurs
       set jetons_gratuits = v_reel + 1,
           jetons_maj = now()          -- l'accumulation vient d'être matérialisée
     where id = v_id;
    return format('%s : +1 paquet gratuit (jetons %s -> %s)',
                  p_pseudo, round(v_reel, 2), round(v_reel + 1, 2));
  else
    -- pas de place sous le plafond : on donne le prix d'un paquet acheté
    update joueurs set solde = solde + 200 where id = v_id;
    return format('%s : jetons déjà à %s sur 3, donc +200 points (un paquet acheté)',
                  p_pseudo, round(v_reel, 2));
  end if;
end;
$function$;

-- Personne d'autre que l'administration.
revoke all on function public.offrir_paquet(text) from public, anon, authenticated;

-- ---------------------------------------------------------------------
--  Utilisation
-- ---------------------------------------------------------------------
select public.offrir_paquet('Abolah');

-- Pour vérifier ensuite :
-- select pseudo, round(jetons_gratuits, 2) as jetons, jetons_maj, solde
--   from joueurs where pseudo = 'Abolah';
-- =====================================================================
