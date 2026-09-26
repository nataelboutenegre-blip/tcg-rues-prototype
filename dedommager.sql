-- =====================================================================
--  TerraFront — dédommager un joueur au nombre de cartes
--
--  offrir_paquet() donne un paquet entier, ce qui ne convient pas ici :
--  Maroli a perdu 18 cartes, soit 3,6 paquets, et le plafond de 3 jetons
--  gratuits interdit de lui en donner quatre. boisdon.iris en a perdu 3,
--  et lui donner un paquet entier serait payer le double.
--
--  Cette fonction paie au plus juste :
--    - des paquets gratuits tant qu'il reste de la place sous le plafond
--    - le reste en points, au prix d'une carte : 200 / 5 = 40 points
--
--  Le plafond n'est donc jamais dépassé, et rien n'est perdu en chemin.
--
--  Réservée à l'administration, comme offrir_paquet.
-- =====================================================================

create or replace function public.dedommager(p_pseudo text, p_cartes integer)
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
  v_restant integer := p_cartes;
  v_paquets integer := 0;
  v_points integer;
begin
  if p_cartes is null or p_cartes <= 0 then
    raise exception 'Nombre de cartes invalide : %', p_cartes;
  end if;

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

  -- des paquets gratuits tant que le plafond le permet
  while v_restant >= 5 and v_reel + 1 <= 3 loop
    v_reel := v_reel + 1;
    v_restant := v_restant - 5;
    v_paquets := v_paquets + 1;
  end loop;

  -- le reste en points : 200 points le paquet, donc 40 la carte
  v_points := v_restant * 40;

  update joueurs
     set jetons_gratuits = v_reel,
         jetons_maj = now(),        -- l'accumulation vient d'être matérialisée
         solde = solde + v_points
   where id = v_id;

  return format('%s : %s carte(s) dues -> %s paquet(s) gratuit(s) + %s points',
                p_pseudo, p_cartes, v_paquets, v_points);
end;
$function$;

revoke all on function public.dedommager(text, integer) from public, anon, authenticated;

-- ---------------------------------------------------------------------
--  Les deux joueurs restants
-- ---------------------------------------------------------------------
--  Abolah n'est PAS dans la liste : ses 5 cartes dues ont déjà été
--  payées par le paquet offert tout à l'heure. Le rappeler ici éviterait
--  de le payer deux fois.
select public.dedommager('Maroli', 18)
union all
select public.dedommager('boisdon.iris', 3);

-- Vérification :
-- select pseudo, round(jetons_gratuits, 2) as jetons, solde
--   from joueurs where pseudo in ('Maroli', 'boisdon.iris', 'Abolah');
-- =====================================================================
