-- Jeu d'essai construit pour couvrir les cas limites de la cloture.
--
--   Alpha  : 12 communes, aucun favori         -> doit etre complete a 5
--   Beta   :  3 communes, aucun favori         -> en garde 3, pas 5
--   Gamma  :  7 communes, 2 favoris deja poses -> complete a 5
--   Delta  :  0 commune                        -> ne doit rien casser
--
-- Plus, volontairement :
--   - un bouclier en cours sur une commune gardee, qui doit disparaitre
--   - une commune conquise (conquise_le renseigne), idem
--   - 2 lignes d'historique ouvertes SANS possession correspondante,
--     qui reproduisent les 29 lignes fantomes de la base reelle
--   - des sieges, des annonces et des echanges a purger

insert into saisons (id, nom, debut, etat) values
  ('saison-1', 'Saison 1', now() - interval '20 days', 'en_cours');

insert into joueurs (id, pseudo, solde) values
  ('11111111-1111-1111-1111-111111111111', 'Alpha', 9000),
  ('22222222-2222-2222-2222-222222222222', 'Beta',  1500),
  ('33333333-3333-3333-3333-333333333333', 'Gamma',  300),
  ('44444444-4444-4444-4444-444444444444', 'Delta',   50);

-- 30 communes reparties sur 4 paliers et 5 departements
insert into communes (code, nom, departement, population, tier, rang, palier_total)
select lpad(i::text, 5, '0'),
       'Commune ' || i,
       (10 + (i % 5))::text,
       case when i <= 2 then 500000 - i * 1000
            when i <= 6 then 50000 - i * 100
            when i <= 14 then 5000 - i * 10
            else 300 - i end,
       case when i <= 2 then 'legendaire'
            when i <= 6 then 'rare'
            when i <= 14 then 'peucommun'
            else 'commun' end,
       i, 30
  from generate_series(1, 30) i;

-- Alpha : 12 communes, dont les 2 legendaires et 2 rares
insert into possessions (commune_code, joueur_id, saison)
select lpad(i::text, 5, '0'), '11111111-1111-1111-1111-111111111111', 'saison-1'
  from generate_series(1, 12) i;

-- Beta : 3 communes seulement
insert into possessions (commune_code, joueur_id, saison)
select lpad(i::text, 5, '0'), '22222222-2222-2222-2222-222222222222', 'saison-1'
  from generate_series(13, 15) i;

-- Gamma : 7 communes, dont 2 deja marquees favorites
insert into possessions (commune_code, joueur_id, saison)
select lpad(i::text, 5, '0'), '33333333-3333-3333-3333-333333333333', 'saison-1'
  from generate_series(16, 22) i;
update possessions set gardee = true
 where commune_code in ('00016', '00017');

-- un bouclier en cours et une conquete, sur des communes qui seront gardees
update possessions
   set bouclier_debut = now() - interval '1 hour',
       bouclier_jusqua = now() + interval '5 hours'
 where commune_code = '00001';
update possessions set conquise_le = now() - interval '2 days'
 where commune_code = '00016';

-- historique : une ligne ouverte par possession...
insert into historique (commune_code, joueur_id, saison, acquired_at)
select commune_code, joueur_id, 'saison-1', now() - interval '10 days'
  from possessions;

-- ...plus 2 lignes fantomes, ouvertes sans possession correspondante
insert into historique (commune_code, joueur_id, saison, acquired_at) values
  ('00028', '11111111-1111-1111-1111-111111111111', 'saison-1', now() - interval '9 days'),
  ('00029', '22222222-2222-2222-2222-222222222222', 'saison-1', now() - interval '9 days');

-- ...et 3 lignes deja fermees, qui ne doivent pas etre retouchees
insert into historique (commune_code, joueur_id, saison, acquired_at, released_at) values
  ('00030', '33333333-3333-3333-3333-333333333333', 'saison-1',
   now() - interval '8 days', now() - interval '7 days'),
  ('00030', '11111111-1111-1111-1111-111111111111', 'saison-1',
   now() - interval '6 days', now() - interval '5 days'),
  ('00027', '22222222-2222-2222-2222-222222222222', 'saison-1',
   now() - interval '4 days', now() - interval '3 days');

insert into sieges (attacker_id, commune_code, victoires_consecutives, dernier_round, defense_utilisee) values
  ('22222222-2222-2222-2222-222222222222', '00001', 2, now(), false),
  ('11111111-1111-1111-1111-111111111111', '00016', 1, now(), true);

insert into annonces (commune_code, joueur_id, prix) values
  ('00005', '11111111-1111-1111-1111-111111111111', 400),
  ('00013', '22222222-2222-2222-2222-222222222222', 120);

insert into echanges (proposant, destinataire, commune_proposant, commune_destinataire, etat) values
  ('11111111-1111-1111-1111-111111111111', '33333333-3333-3333-3333-333333333333',
   '00003', '00018', 'en_attente'),
  ('33333333-3333-3333-3333-333333333333', '22222222-2222-2222-2222-222222222222',
   '00019', '00014', 'en_attente');
