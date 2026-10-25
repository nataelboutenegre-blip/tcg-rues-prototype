-- ===========================================================================
--  TerraFront — boutique en euros (Stripe) : 1. les tables
--  Préparé le 19 octobre 2026. RIEN N'EST EN VENTE tant que :
--   - aucun article n'est actif (tous créés avec actif = false) ;
--   - les fonctions Edge ne sont pas déployées avec les clés Stripe.
--
--  Tables :
--   - euros_articles        : le catalogue, prix en centimes, modifiable sans code
--   - euros_commandes       : chaque commande, avec les cases cochées et la
--                             version des CGV (preuve d'acceptation, CGV art. 1)
--   - euros_inventaire      : ce que chaque joueur possède (achats en euros)
--   - euros_naissances      : date de naissance, seulement pour le plafond des
--                             moins de 18 ans (CGV art. 3)
--   - euros_stripe_evenements : les événements Stripe déjà traités
--                             (un paiement n'est jamais compté deux fois)
--   - euros_reglages        : version des CGV, plafond, objectifs du bandeau
--
--  Toutes les tables : RLS active et aucun droit pour les joueurs. On n'y
--  accède que par les fonctions de 2-fonctions.sql.
--  Ne touche à aucune table existante. Rejouable.
-- ===========================================================================

create table if not exists public.euros_articles(
  id            text primary key,
  type          text not null check (type in ('dos', 'skin', 'cadre', 'habillage', 'effet',
                                             'drapeau', 'motif', 'banniere', 'pass')),
  nom           text not null,
  description   text not null default '',
  prix_centimes integer not null check (prix_centimes between 50 and 5000),
  reserve_og    boolean not null default false,
  saison        text,                       -- pass de saison seulement
  actif         boolean not null default false,
  ordre         integer not null default 0,
  check (type <> 'pass' or saison is not null)
);
alter table public.euros_articles enable row level security;
revoke all on public.euros_articles from public, anon, authenticated;

-- Catalogue de départ : grille du 25 octobre (5-prix-25-octobre.sql), INDICATIFS.
-- Tous inactifs : on active article par article quand tout est prêt.
insert into public.euros_articles(id, type, nom, description, prix_centimes, reserve_og, ordre) values
  ('og-paquet-prisme',      'habillage', 'Paquet OG Prisme',      'Habillage de paquet irisé, réservé aux OG',        299, true,  10),
  ('og-paquet-or-noir',     'habillage', 'Paquet OG Or noir',     'Habillage de paquet noir et or, réservé aux OG',   299, true,  20),
  ('og-dos-prisme',         'dos',       'Dos OG Prisme',         'Dos de carte irisé, réservé aux OG',               399, true,  30),
  ('og-dos-constellation',  'dos',       'Dos OG Constellation',  'Dos de carte étoilé, réservé aux OG',              399, true,  40),
  ('paquet-kraft',          'habillage', 'Paquet Kraft',          'Papier kraft et cachet de cire',                   299, false, 50),
  ('paquet-neon',           'habillage', 'Paquet Néon',           'Tubes de néon qui s''allument à l''ouverture',     299, false, 60),
  ('paquet-comete',         'habillage', 'Paquet Comète',         'Traînée d''étoiles',                               349, false, 70),
  ('paquet-maree',          'habillage', 'Paquet Marée',          'Reflets d''eau et écume',                          349, false, 80),
  ('paquet-lave',           'habillage', 'Paquet Lave',           'Fissures incandescentes',                          399, false, 90),
  ('paquet-orage',          'habillage', 'Paquet Orage',          'Éclairs dans les nuages',                          399, false, 100)
on conflict (id) do nothing;   -- rejouable : ne réécrit pas un prix modifié à la main

create table if not exists public.euros_naissances(
  joueur_id      uuid primary key references public.joueurs(id) on delete cascade,
  date_naissance date not null,
  renseignee_le  timestamptz not null default now()
);
alter table public.euros_naissances enable row level security;
revoke all on public.euros_naissances from public, anon, authenticated;

create table if not exists public.euros_commandes(
  id                uuid primary key default gen_random_uuid(),
  -- set null : une commande se garde 10 ans (comptabilité), même si le compte
  -- est supprimé. Stripe garde de son côté le reçu et l'email.
  joueur_id         uuid references public.joueurs(id) on delete set null,
  article_id        text not null references public.euros_articles(id),
  nom_article       text not null,
  prix_centimes     integer not null,
  livraison         text not null check (livraison in ('immediate', 'differee')),
  statut            text not null default 'creee'
                    check (statut in ('creee', 'payee', 'livree', 'remboursee',
                                      'contestee', 'annulee', 'a_verifier')),
  cgv_version       text not null,
  case_cgv          boolean not null,
  case_immediate    boolean not null,
  case_renonciation boolean not null,
  mineur            boolean not null,
  stripe_session    text unique,
  stripe_paiement   text unique,
  cree_le           timestamptz not null default now(),
  payee_le          timestamptz,
  livrer_apres      timestamptz,
  livree_le         timestamptz,
  remboursee_le     timestamptz,
  note              text,
  -- livraison immédiate = les deux cases de renonciation cochées (CGV art. 3)
  check (livraison = 'differee' or (case_immediate and case_renonciation)),
  check (case_cgv)
);
create index if not exists euros_commandes_joueur_le on public.euros_commandes(joueur_id, cree_le);
create index if not exists euros_commandes_a_livrer on public.euros_commandes(livrer_apres) where statut = 'payee';
alter table public.euros_commandes enable row level security;
revoke all on public.euros_commandes from public, anon, authenticated;

create table if not exists public.euros_inventaire(
  joueur_id   uuid not null references public.joueurs(id) on delete cascade,
  article_id  text not null references public.euros_articles(id),
  commande_id uuid references public.euros_commandes(id),
  obtenu_le   timestamptz not null default now(),
  primary key (joueur_id, article_id)
);
alter table public.euros_inventaire enable row level security;
revoke all on public.euros_inventaire from public, anon, authenticated;

create table if not exists public.euros_stripe_evenements(
  id      text primary key,          -- identifiant de l'événement Stripe (evt_...)
  type    text not null,
  recu_le timestamptz not null default now()
);
alter table public.euros_stripe_evenements enable row level security;
revoke all on public.euros_stripe_evenements from public, anon, authenticated;

create table if not exists public.euros_reglages(
  cle    text primary key,
  valeur jsonb not null
);
alter table public.euros_reglages enable row level security;
revoke all on public.euros_reglages from public, anon, authenticated;

insert into public.euros_reglages(cle, valeur) values
  -- à changer à chaque nouvelle version publiée des CGV
  ('cgv_version',             '"2026-10-19-v3"'),
  -- adresse publique du PDF des CGV, jointe à l'email de confirmation (support durable)
  ('cgv_pdf_url',             'null'),
  -- CGV art. 3 : 15 € par mois civil avant 18 ans
  ('plafond_mineur_centimes', '1500'),
  ('age_minimum',             '15'),
  -- bandeau de financement : étape 1 mensuelle, étape 2 cumulée (app mobile)
  ('objectif_mois_centimes',  '3000'),
  ('objectif_app_centimes',   '12400'),
  -- part prélevée sur chaque vente pour calculer le net du bandeau :
  -- commission Stripe (1,5 % + 0,25 €) puis cotisations + versement libératoire.
  -- TAUX À VÉRIFIER sur autoentrepreneur.urssaf.fr (BIC prestations de services).
  ('stripe_pourcent',         '0.015'),
  ('stripe_fixe_centimes',    '25'),
  ('taux_prelevements',       '0.229')
on conflict (cle) do nothing;

select 'tables boutique en euros : OK' as resultat,
       (select count(*) from euros_articles) as articles,
       (select count(*) from euros_articles where actif) as articles_actifs;
