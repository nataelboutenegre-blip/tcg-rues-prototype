-- ===========================================================================
--  TerraFront — boutique en euros : 17. être prévenu d'une demande de
--  remboursement (rétractation d'une livraison différée). Rejouable.
--  À passer AVANT de déployer la fonction « prevenir-retractation » et de
--  pousser patch206.
--
--  - euros_retractations_a_prevenir() : les demandes pas encore signalées
--    (commande payée, rétractation demandée, pas encore remboursée).
--  - euros_retractations_prevenues(ids) : les marque comme signalées, après
--    l'envoi de l'e-mail (une demande n'est jamais signalée deux fois).
--  Les deux ne sont appelables que par la fonction serveur (clé service).
--  Contrôle attendu : true | false | false
-- ===========================================================================
begin;

alter table public.euros_commandes add column if not exists retractation_prevenue_le timestamptz;

create or replace function public.euros_retractations_a_prevenir()
 returns jsonb language sql stable security definer set search_path to 'public'
as $f$
  select coalesce(jsonb_agg(jsonb_build_object(
           'id', c.id, 'pseudo', j.pseudo, 'article', c.nom_article, 'prix_centimes', c.prix_centimes,
           'payee_le', c.payee_le, 'retractation_le', c.retractation_le,
           'rembourser_avant', c.retractation_le + interval '14 days',
           'paiement', c.stripe_paiement) order by c.retractation_le), '[]'::jsonb)
    from euros_commandes c
    left join joueurs j on j.id = c.joueur_id
   where c.retractation_le is not null and c.retractation_prevenue_le is null and c.statut = 'payee'
$f$;

create or replace function public.euros_retractations_prevenues(p_ids uuid[])
 returns integer language sql security definer set search_path to 'public'
as $f$
  with m as (update euros_commandes set retractation_prevenue_le = now()
              where id = any(p_ids) and retractation_prevenue_le is null returning 1)
  select count(*)::integer from m
$f$;

revoke all on function public.euros_retractations_a_prevenir()        from public, anon, authenticated;
revoke all on function public.euros_retractations_prevenues(uuid[])   from public, anon, authenticated;
grant execute on function public.euros_retractations_a_prevenir()      to service_role;
grant execute on function public.euros_retractations_prevenues(uuid[]) to service_role;

commit;

select (select count(*) from information_schema.columns
         where table_schema = 'public' and table_name = 'euros_commandes'
           and column_name = 'retractation_prevenue_le') = 1                                   as colonne_ok,
       has_function_privilege('authenticated', 'public.euros_retractations_a_prevenir()', 'execute') as joueurs_doit_etre_false,
       has_function_privilege('anon', 'public.euros_retractations_prevenues(uuid[])', 'execute')     as anon_doit_etre_false;
