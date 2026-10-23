-- ===========================================================================
--  TerraFront — saison 2, Terra : un paquet gratuit toutes les 30 minutes
--  (23 octobre 2026, au lieu de 20). Réserve de 3 inchangée. Le Front ne
--  bouge pas (statut_paquets reste à 20 minutes).
--
--  Remplace terra_jetons_lire et terra_statut de s2-4 (1200 s -> 1800 s).
--  Mêmes signatures : rien d'autre à recréer. Terra étant fermé en saison 1,
--  aucun joueur n'est touché avant l'ouverture.
--  Rejouable. Finit par un contrôle (une ligne).
-- ===========================================================================

create or replace function public.terra_jetons_lire(p_val numeric, p_maj timestamptz)
 returns numeric
 language sql
 stable
 set search_path to 'public'
as $f$
  select least(3, p_val + extract(epoch from (now() - p_maj)) / 1800.0);
$f$;

create or replace function public.terra_statut()
 returns table(jetons numeric, prochain_dans integer, achetes_jour integer, achats_max integer,
               prix_paquet integer, solde integer, cartes integer, communes integer)
 language plpgsql
 stable security definer
 set search_path to 'public'
as $f$
declare
  v_uid uuid := auth.uid();
  j joueurs%rowtype;
  v numeric;
  v_jour date := (now() at time zone 'Europe/Paris')::date;
begin
  if v_uid is null then raise exception 'Non connecte'; end if;
  if not terra_ouverte() then raise exception 'Terra n''est pas encore ouvert'; end if;
  select * into j from joueurs where id = v_uid;
  if not found then raise exception 'Joueur inconnu'; end if;
  v := terra_jetons_lire(j.terra_jetons, j.terra_jetons_maj);
  return query select
    round(v, 3),
    case when v >= 3 then null else ceil((1 - (v - floor(v))) * 1800)::integer end,
    case when j.paquets_achetes_date = v_jour then coalesce(j.paquets_achetes_jour, 0) else 0 end,
    5, 200, j.solde,
    (select coalesce(sum(t.exemplaires), 0)::integer from terra_collection t where t.joueur_id = v_uid),
    (select count(*)::integer from terra_collection t where t.joueur_id = v_uid and t.exemplaires > 0);
end;
$f$;

select case
  when pg_get_functiondef('public.terra_jetons_lire(numeric, timestamptz)'::regprocedure) like '%1800.0%'
   and pg_get_functiondef('public.terra_statut()'::regprocedure) like '%* 1800)%'
  then 'OK : Terra recharge un paquet toutes les 30 minutes'
  else 'ECHEC : verifier terra_jetons_lire / terra_statut'
end as controle;
