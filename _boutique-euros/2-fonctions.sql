-- ===========================================================================
--  TerraFront — boutique en euros (Stripe) : 2. les fonctions
--  À passer APRÈS 1-tables.sql. Rejouable.
--
--  Pour le joueur connecté (appelées par le jeu ou par la fonction Edge
--  creer-paiement avec le jeton du joueur) :
--   - euros_catalogue()          : articles actifs, ce que le joueur possède,
--                                  plafond restant, version des CGV
--   - euros_preparer_commande()  : contrôle tout AVANT d'envoyer vers Stripe
--   - euros_mes_commandes()      : l'historique du joueur
--   - euros_bandeau()            : les deux pourcentages du bandeau
--
--  Pour le serveur seulement (clé service_role, jamais le jeu) :
--   - euros_lier_session()       : relie la commande à la session Stripe
--   - euros_confirmer_paiement() : paiement reçu -> livraison ou attente 14 j
--   - euros_livrer_differees()   : livre les commandes dont les 14 j sont passés
--   - euros_annuler_remboursee() : remboursement ou contestation -> objet retiré
--   - euros_expirer()            : paiement abandonné
--
--  Règles de sécurité :
--   - le prix vient TOUJOURS de euros_articles, jamais du navigateur ;
--   - un objet n'est ajouté que par euros_confirmer_paiement, appelée par la
--     fonction Edge après vérification de la signature Stripe ;
--   - chaque événement Stripe est enregistré dans la même transaction que
--     son effet : s'il est rejoué, il ne fait rien ; si l'effet échoue,
--     l'enregistrement est annulé et Stripe peut réessayer.
-- ===========================================================================

-- ---------- outils internes ----------

create or replace function public.euros_reglage(p_cle text)
 returns jsonb language sql stable security definer set search_path to 'public'
as $f$ select valeur from euros_reglages where cle = p_cle $f$;

create or replace function public.euros_age(p_uid uuid)
 returns integer language sql stable security definer set search_path to 'public'
as $f$
  select extract(year from age((now() at time zone 'Europe/Paris')::date, n.date_naissance))::integer
    from euros_naissances n where n.joueur_id = p_uid
$f$;

-- ce que le joueur a dépensé ce mois civil (heure de Paris), commandes en
-- cours de paiement comprises (sinon deux onglets ouverts passeraient le plafond)
create or replace function public.euros_depense_du_mois(p_uid uuid)
 returns integer language sql stable security definer set search_path to 'public'
as $f$
  select coalesce(sum(c.prix_centimes), 0)::integer
    from euros_commandes c
   where c.joueur_id = p_uid
     and date_trunc('month', coalesce(c.payee_le, c.cree_le) at time zone 'Europe/Paris')
         = date_trunc('month', now() at time zone 'Europe/Paris')
     and (c.statut in ('payee', 'livree', 'contestee', 'a_verifier')
          or (c.statut = 'creee' and c.cree_le > now() - interval '35 minutes'))
$f$;

create or replace function public.euros_est_og(p_uid uuid)
 returns boolean language sql stable security definer set search_path to 'public'
as $f$ select exists(select 1 from joueur_badges b where b.joueur_id = p_uid and b.badge = 'og') $f$;

create or replace function public.euros_livrer(p_commande uuid)
 returns void language plpgsql security definer set search_path to 'public'
as $f$
declare c euros_commandes%rowtype;
begin
  select * into c from euros_commandes where id = p_commande for update;
  if not found or c.statut <> 'payee' then return; end if;
  if c.joueur_id is not null then
    insert into euros_inventaire(joueur_id, article_id, commande_id)
    values (c.joueur_id, c.article_id, c.id)
    on conflict (joueur_id, article_id) do nothing;
  end if;
  update euros_commandes set statut = 'livree', livree_le = now() where id = c.id;
end;
$f$;

-- ---------- joueur ----------

create or replace function public.euros_catalogue()
 returns jsonb language plpgsql stable security definer set search_path to 'public'
as $f$
declare
  v_uid uuid := auth.uid();
  v_age integer;
  v_plafond integer := (euros_reglage('plafond_mineur_centimes'))::integer;
begin
  if v_uid is null then raise exception 'Non connecte'; end if;
  v_age := euros_age(v_uid);
  return jsonb_build_object(
    'cgv_version', euros_reglage('cgv_version'),
    'naissance_connue', v_age is not null,
    'mineur', v_age is not null and v_age < 18,
    'plafond_restant', case when v_age is not null and v_age < 18
                            then greatest(0, v_plafond - euros_depense_du_mois(v_uid)) end,
    'og', euros_est_og(v_uid),
    'articles', coalesce((
      select jsonb_agg(jsonb_build_object(
               'id', a.id, 'type', a.type, 'nom', a.nom, 'description', a.description,
               'prix_centimes', a.prix_centimes, 'reserve_og', a.reserve_og, 'saison', a.saison,
               'possede', exists(select 1 from euros_inventaire i where i.joueur_id = v_uid and i.article_id = a.id),
               'livraison_le', (select c.livrer_apres from euros_commandes c
                                 where c.joueur_id = v_uid and c.article_id = a.id and c.statut = 'payee'
                                 order by c.cree_le desc limit 1))
             order by a.ordre)
        from euros_articles a where a.actif), '[]'::jsonb));
end;
$f$;

create or replace function public.euros_preparer_commande(
  p_article           text,
  p_livraison         text,
  p_case_cgv          boolean,
  p_case_immediate    boolean,
  p_case_renonciation boolean,
  p_cgv_version       text,
  p_date_naissance    date default null)
 returns jsonb language plpgsql security definer set search_path to 'public'
as $f$
declare
  v_uid uuid := auth.uid();
  a euros_articles%rowtype;
  v_age integer;
  v_plafond integer := (euros_reglage('plafond_mineur_centimes'))::integer;
  v_min integer := (euros_reglage('age_minimum'))::integer;
  v_id uuid;
  v_imm boolean;
begin
  if v_uid is null then raise exception 'Non connecte'; end if;
  -- verrou sur le joueur : deux commandes simultanées passent l'une après l'autre
  perform 1 from joueurs where id = v_uid for update;
  if not found then raise exception 'Joueur inconnu'; end if;

  select * into a from euros_articles where id = p_article and actif;
  if not found then raise exception 'Article introuvable'; end if;

  if p_cgv_version is distinct from (euros_reglage('cgv_version') #>> '{}') then
    raise exception 'Les conditions de vente ont change : recharge la page';
  end if;
  if not coalesce(p_case_cgv, false) then
    raise exception 'Coche l''acceptation des conditions de vente';
  end if;
  if p_livraison not in ('immediate', 'differee') then raise exception 'Choix de livraison invalide'; end if;
  v_imm := p_livraison = 'immediate';
  if v_imm and not (coalesce(p_case_immediate, false) and coalesce(p_case_renonciation, false)) then
    raise exception 'Pour recevoir l''objet tout de suite, coche les deux cases';
  end if;

  if a.reserve_og and not euros_est_og(v_uid) then
    raise exception 'Cet objet est reserve aux joueurs OG';
  end if;
  if exists(select 1 from euros_inventaire i where i.joueur_id = v_uid and i.article_id = a.id) then
    raise exception 'Tu l''as deja';
  end if;
  if exists(select 1 from euros_commandes c where c.joueur_id = v_uid and c.article_id = a.id
             and c.statut in ('payee', 'a_verifier')) then
    raise exception 'Tu as deja paye cet objet, il arrive bientot';
  end if;
  if a.type = 'pass' and a.saison is distinct from
     (select s.id from saison_courante() s where s.etat = 'en_cours') then
    raise exception 'Ce pass n''est pas celui de la saison en cours';
  end if;

  -- date de naissance : demandée une seule fois (CGV art. 3)
  v_age := euros_age(v_uid);
  if v_age is null then
    if p_date_naissance is null then raise exception 'Indique ta date de naissance'; end if;
    if p_date_naissance < date '1900-01-01' or p_date_naissance > (now() at time zone 'Europe/Paris')::date then
      raise exception 'Date de naissance invalide';
    end if;
    insert into euros_naissances(joueur_id, date_naissance) values (v_uid, p_date_naissance);
    v_age := euros_age(v_uid);
  end if;
  if v_age < v_min then raise exception 'La boutique est reservee aux joueurs de % ans et plus', v_min; end if;

  -- un paiement abandonné de ce même objet ne bloque pas : on l'annule
  update euros_commandes set statut = 'annulee', note = 'remplacee par une nouvelle commande'
   where joueur_id = v_uid and article_id = a.id and statut = 'creee';

  if v_age < 18 and euros_depense_du_mois(v_uid) + a.prix_centimes > v_plafond then
    raise exception 'Plafond de % € par mois atteint pour les moins de 18 ans (reste % €)',
      replace(to_char(v_plafond / 100.0, 'FM990.00'), '.', ','),
      replace(to_char(greatest(0, v_plafond - euros_depense_du_mois(v_uid)) / 100.0, 'FM990.00'), '.', ',');
  end if;

  insert into euros_commandes(joueur_id, article_id, nom_article, prix_centimes, livraison,
                              cgv_version, case_cgv, case_immediate, case_renonciation, mineur)
  values (v_uid, a.id, a.nom, a.prix_centimes, p_livraison,
          p_cgv_version, true, v_imm and p_case_immediate, v_imm and p_case_renonciation, v_age < 18)
  returning id into v_id;

  return jsonb_build_object('commande_id', v_id, 'nom', a.nom, 'description', a.description,
                            'prix_centimes', a.prix_centimes, 'livraison', p_livraison);
end;
$f$;

create or replace function public.euros_mes_commandes()
 returns jsonb language plpgsql stable security definer set search_path to 'public'
as $f$
declare v_uid uuid := auth.uid();
begin
  if v_uid is null then raise exception 'Non connecte'; end if;
  return coalesce((
    select jsonb_agg(jsonb_build_object(
             'id', c.id, 'article', c.nom_article, 'prix_centimes', c.prix_centimes,
             'statut', c.statut, 'livraison', c.livraison, 'payee_le', c.payee_le,
             'livrer_apres', c.livrer_apres, 'livree_le', c.livree_le) order by c.cree_le desc)
      from euros_commandes c
     where c.joueur_id = v_uid and c.statut <> 'creee' and c.statut <> 'annulee'), '[]'::jsonb);
end;
$f$;

-- Bandeau de financement : seulement des pourcentages, jamais de montant.
-- Net d'une vente = prix - commission Stripe - prélèvements (taux en réglage).
-- Étape 1 : objectif du mois, remis à zéro chaque mois.
-- Étape 2 : application mobile, se remplit avec ce qui dépasse l'étape 1
--           chaque mois, ne se remet jamais à zéro.
create or replace function public.euros_bandeau()
 returns jsonb language plpgsql stable security definer set search_path to 'public'
as $f$
declare
  v_obj1 numeric := (euros_reglage('objectif_mois_centimes'))::numeric;
  v_obj2 numeric := (euros_reglage('objectif_app_centimes'))::numeric;
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
    'mois_pourcent', least(100, floor(100 * v_mois / nullif(v_obj1, 0)))::integer,
    'app_pourcent',  least(100, floor(100 * v_surplus / nullif(v_obj2, 0)))::integer);
end;
$f$;

-- ---------- serveur (service_role) ----------

create or replace function public.euros_lier_session(p_commande uuid, p_session text)
 returns void language plpgsql security definer set search_path to 'public'
as $f$
begin
  update euros_commandes set stripe_session = p_session
   where id = p_commande and statut = 'creee' and stripe_session is null;
  if not found then raise exception 'Commande introuvable ou deja liee'; end if;
end;
$f$;

-- renvoie : 'livree', 'en_attente_14_jours', 'deja_traite' ou 'a_verifier'
create or replace function public.euros_confirmer_paiement(
  p_evenement text, p_session text, p_paiement text, p_montant integer, p_devise text)
 returns text language plpgsql security definer set search_path to 'public'
as $f$
declare c euros_commandes%rowtype;
begin
  insert into euros_stripe_evenements(id, type) values (p_evenement, 'paiement')
  on conflict (id) do nothing;
  if not found then return 'deja_traite'; end if;

  select * into c from euros_commandes where stripe_session = p_session for update;
  if not found then raise exception 'Aucune commande pour la session %', p_session; end if;
  if c.statut in ('payee', 'livree') then return 'deja_traite'; end if;

  -- le paiement fait foi, même pour une commande annulée entre-temps ;
  -- mais un montant ou une devise inattendus ne livrent rien
  if p_montant is distinct from c.prix_centimes or lower(p_devise) is distinct from 'eur' then
    update euros_commandes set statut = 'a_verifier', stripe_paiement = p_paiement, payee_le = now(),
           note = format('montant recu %s %s, attendu %s eur', p_montant, p_devise, c.prix_centimes)
     where id = c.id;
    return 'a_verifier';
  end if;

  update euros_commandes
     set statut = 'payee', stripe_paiement = p_paiement, payee_le = now(),
         livrer_apres = case when livraison = 'immediate' then now() else now() + interval '14 days' end
   where id = c.id;
  if c.livraison = 'immediate' then
    perform euros_livrer(c.id);
    return 'livree';
  end if;
  return 'en_attente_14_jours';
end;
$f$;

-- à lancer régulièrement (3-livraisons-cron.sql) : livre ce qui a fini ses 14 jours
create or replace function public.euros_livrer_differees()
 returns integer language plpgsql security definer set search_path to 'public'
as $f$
declare r record; n integer := 0;
begin
  for r in select id from euros_commandes
            where statut = 'payee' and livrer_apres <= now()
            order by livrer_apres for update skip locked loop
    perform euros_livrer(r.id);
    n := n + 1;
  end loop;
  return n;
end;
$f$;

-- remboursement total (charge.refunded) ou contestation bancaire (charge.dispute.created)
create or replace function public.euros_annuler_remboursee(
  p_evenement text, p_paiement text, p_motif text)
 returns text language plpgsql security definer set search_path to 'public'
as $f$
declare c euros_commandes%rowtype;
begin
  if p_motif not in ('remboursement', 'contestation') then raise exception 'Motif invalide'; end if;
  insert into euros_stripe_evenements(id, type) values (p_evenement, p_motif)
  on conflict (id) do nothing;
  if not found then return 'deja_traite'; end if;

  select * into c from euros_commandes where stripe_paiement = p_paiement for update;
  if not found then return 'commande_inconnue'; end if;
  delete from euros_inventaire where commande_id = c.id;
  update euros_commandes
     set statut = case when p_motif = 'remboursement' then 'remboursee' else 'contestee' end,
         remboursee_le = now()
   where id = c.id;
  return 'objet_retire';
end;
$f$;

create or replace function public.euros_expirer(p_evenement text, p_session text)
 returns text language plpgsql security definer set search_path to 'public'
as $f$
begin
  insert into euros_stripe_evenements(id, type) values (p_evenement, 'expiration')
  on conflict (id) do nothing;
  if not found then return 'deja_traite'; end if;
  update euros_commandes set statut = 'annulee', note = 'paiement abandonne'
   where stripe_session = p_session and statut = 'creee';
  return 'annulee';
end;
$f$;

-- ---------- droits ----------
-- Par défaut, PostgreSQL laisse tout le monde exécuter une fonction : on
-- retire tout, puis on redonne seulement ce qu'il faut.

revoke all on function public.euros_reglage(text)                      from public, anon, authenticated;
revoke all on function public.euros_age(uuid)                          from public, anon, authenticated;
revoke all on function public.euros_depense_du_mois(uuid)              from public, anon, authenticated;
revoke all on function public.euros_est_og(uuid)                       from public, anon, authenticated;
revoke all on function public.euros_livrer(uuid)                       from public, anon, authenticated;
revoke all on function public.euros_catalogue()                        from public, anon;
revoke all on function public.euros_preparer_commande(text, text, boolean, boolean, boolean, text, date) from public, anon;
revoke all on function public.euros_mes_commandes()                    from public, anon;
revoke all on function public.euros_bandeau()                          from public, anon;
revoke all on function public.euros_lier_session(uuid, text)           from public, anon, authenticated;
revoke all on function public.euros_confirmer_paiement(text, text, text, integer, text) from public, anon, authenticated;
revoke all on function public.euros_livrer_differees()                 from public, anon, authenticated;
revoke all on function public.euros_annuler_remboursee(text, text, text) from public, anon, authenticated;
revoke all on function public.euros_expirer(text, text)                from public, anon, authenticated;

grant execute on function public.euros_catalogue()                     to authenticated;
grant execute on function public.euros_preparer_commande(text, text, boolean, boolean, boolean, text, date) to authenticated;
grant execute on function public.euros_mes_commandes()                 to authenticated;
grant execute on function public.euros_bandeau()                       to authenticated;

grant execute on function public.euros_lier_session(uuid, text)        to service_role;
grant execute on function public.euros_confirmer_paiement(text, text, text, integer, text) to service_role;
grant execute on function public.euros_livrer_differees()              to service_role;
grant execute on function public.euros_annuler_remboursee(text, text, text) to service_role;
grant execute on function public.euros_expirer(text, text)             to service_role;

-- contrôle : aucune fonction serveur ne doit être ouverte aux joueurs
select 'fonctions boutique en euros : OK' as resultat,
       bool_and(not has_function_privilege('authenticated', p.oid, 'execute')) as serveur_ferme_aux_joueurs,
       bool_and(not has_function_privilege('anon', p.oid, 'execute'))          as serveur_ferme_aux_anonymes
  from pg_proc p
 where p.pronamespace = 'public'::regnamespace
   and p.proname in ('euros_lier_session', 'euros_confirmer_paiement', 'euros_livrer_differees',
                     'euros_annuler_remboursee', 'euros_expirer', 'euros_livrer');
