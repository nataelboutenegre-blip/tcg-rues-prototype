-- TerraFront — bandeau de financement en 3 étapes (21 octobre 2026)
-- À coller EN ENTIER dans l'éditeur SQL de Supabase. Ne touche à aucune
-- commande ni à aucun objet : seulement les objectifs et le calcul du bandeau.
--
-- Étape 1 « frais du mois »   : 140 €, remise à zéro chaque mois
--   Claude Max ~97 € TTC, Supabase Pro + Small ~28 €, Revolut 10 €,
--   téléphone 2 €, médiateur CM2C 48 € / 3 ans, domaine ~1 €.
-- Étape 2 « mise en conformité » : 1 500 €, une seule fois
--   relecture des CGV par un juriste, RGPD, dépôt de la marque à l'INPI.
-- Étape 3 « application »      : 124 €, une seule fois
--   Apple Developer 99 $ (par an) + Google Play 25 $.
-- Les étapes 2 et 3 se remplissent avec ce qui dépasse l'étape 1 chaque mois,
-- dans l'ordre, et ne se remettent jamais à zéro.
-- Le bandeau ne compte que les frais du jeu : aucun revenu pour le créateur.

update public.euros_reglages set valeur = '14000' where cle = 'objectif_mois_centimes';
insert into public.euros_reglages(cle, valeur) values ('objectif_conformite_centimes', '150000')
on conflict (cle) do update set valeur = excluded.valeur;

create or replace function public.euros_bandeau()
 returns jsonb language plpgsql stable security definer set search_path to 'public'
as $f$
declare
  v_obj1 numeric := (euros_reglage('objectif_mois_centimes'))::numeric;
  v_obj2 numeric := (euros_reglage('objectif_conformite_centimes'))::numeric;
  v_obj3 numeric := (euros_reglage('objectif_app_centimes'))::numeric;
  v_pct  numeric := (euros_reglage('stripe_pourcent'))::numeric;
  v_fixe numeric := (euros_reglage('stripe_fixe_centimes'))::numeric;
  v_taux numeric := (euros_reglage('taux_prelevements'))::numeric;
  v_mois numeric;
  v_surplus numeric;
begin
  with ventes as (
    select date_trunc('month', c.payee_le at time zone 'Europe/Paris') as mois,
           greatest(0, c.prix_centimes - (c.prix_centimes * v_pct + v_fixe) - c.prix_centimes * v_taux) as net
      from euros_commandes c
     where c.statut in ('payee', 'livree')
  ), par_mois as (
    select mois, sum(net) as net from ventes group by mois
  )
  select coalesce(sum(net) filter (where mois = date_trunc('month', now() at time zone 'Europe/Paris')), 0),
         coalesce(sum(greatest(0, net - v_obj1)), 0)
    into v_mois, v_surplus
    from par_mois;
  return jsonb_build_object(
    'mois_pourcent',       least(100, floor(100 * v_mois / nullif(v_obj1, 0)))::integer,
    'conformite_pourcent', least(100, floor(100 * least(v_surplus, v_obj2) / nullif(v_obj2, 0)))::integer,
    'app_pourcent',        least(100, floor(100 * greatest(0, v_surplus - v_obj2) / nullif(v_obj3, 0)))::integer);
end;
$f$;

-- contrôle attendu : 14000 | 150000 | 12400 | {"mois_pourcent": 0, "app_pourcent": 0, "conformite_pourcent": 0}
select (select valeur from euros_reglages where cle = 'objectif_mois_centimes')       as etape_1,
       (select valeur from euros_reglages where cle = 'objectif_conformite_centimes') as etape_2,
       (select valeur from euros_reglages where cle = 'objectif_app_centimes')        as etape_3,
       euros_bandeau() as bandeau;
