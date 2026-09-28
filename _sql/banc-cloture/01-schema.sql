-- Schema de test : reproduit les tables de TerraFront telles que
-- l'introspection du 28 septembre les decrit. Aucune donnee reelle.

create table communes (
  code text primary key,
  nom text,
  departement text,
  population integer,
  latitude numeric,
  longitude numeric,
  tier text,
  rang integer,
  palier_total integer
);

create table joueurs (
  id uuid primary key,
  pseudo text,
  created_at timestamptz default now(),
  solde integer default 0,
  jetons_gratuits numeric default 0,
  jetons_maj timestamptz default now(),
  paquets_achetes_jour integer default 0,
  paquets_achetes_date date default current_date,
  tirages_restants integer default 0,
  paquet_notif_attendue boolean default false,
  avatar text,
  pseudo_maj timestamptz
);

create table possessions (
  commune_code text primary key,
  joueur_id uuid,
  acquired_at timestamptz default now(),
  bouclier_debut timestamptz,
  bouclier_jusqua timestamptz,
  conquise_le timestamptz,
  saison text not null default 'saison-1',
  gardee boolean not null default false
);
create index possessions_joueur_idx on possessions (joueur_id);
create index possessions_saison_idx on possessions (saison);

create table historique (
  id bigserial primary key,
  commune_code text,
  joueur_id uuid,
  saison text,
  acquired_at timestamptz default now(),
  released_at timestamptz
);

create table saisons (
  id text primary key,
  nom text not null,
  debut timestamptz not null default now(),
  etat text not null default 'en_cours'
       check (etat in ('en_cours', 'compte_a_rebours', 'terminee')),
  seuil_communes integer not null default 3000,
  jours_rebours integer not null default 5,
  fin_prevue timestamptz,
  fin_reelle timestamptz
);

create table classement_saisons (
  saison text not null references saisons(id),
  joueur_id uuid not null,
  pseudo text,
  rang integer not null,
  communes integer not null default 0,
  legendaires integer not null default 0,
  rares integer not null default 0,
  departements integer not null default 0,
  points integer not null default 0,
  cree_le timestamptz not null default now(),
  primary key (saison, joueur_id)
);

create table sieges (
  attacker_id uuid,
  commune_code text,
  victoires_consecutives integer,
  dernier_round timestamptz,
  defense_utilisee boolean
);

create table annonces (
  commune_code text,
  joueur_id uuid,
  prix integer,
  created_at timestamptz default now()
);

create table echanges (
  id bigserial primary key,
  proposant uuid,
  destinataire uuid,
  commune_proposant text,
  commune_destinataire text,
  etat text,
  cree_le timestamptz default now(),
  expire_le timestamptz,
  repondu_le timestamptz,
  message text
);
