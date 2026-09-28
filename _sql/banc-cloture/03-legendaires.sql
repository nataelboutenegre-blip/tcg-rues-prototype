-- Jeu d'essai centre sur la regle de la legendaire unique.
--
--   Riche   : 8 legendaires + 6 communs, aucun favori
--             -> doit garder 1 legendaire et 4 communs
--   Choisi  : 3 legendaires + 4 rares, 1 legendaire deja favorite
--             -> la legendaire deja choisie reste, la completion n'en
--                ajoute aucune autre
--   Deuxleg : 2 legendaires deja favorites (etat impossible via
--             marquer_gardee, mais on verifie que la cloture ne l'aggrave
--             pas)
--   Pauvre  : 3 legendaires et rien d'autre
--             -> n'en garde qu'une : la regle prime sur le nombre de places
--   Normal  : 10 communs, aucune legendaire -> garde 5 communs

insert into saisons (id, nom, debut, etat) values
  ('saison-1', 'Saison 1', now() - interval '20 days', 'en_cours');

insert into joueurs (id, pseudo, solde) values
  ('aaaaaaaa-0000-0000-0000-000000000001', 'Riche',   5000),
  ('aaaaaaaa-0000-0000-0000-000000000002', 'Choisi',  4000),
  ('aaaaaaaa-0000-0000-0000-000000000003', 'Deuxleg', 3000),
  ('aaaaaaaa-0000-0000-0000-000000000004', 'Pauvre',  2000),
  ('aaaaaaaa-0000-0000-0000-000000000005', 'Normal',  1000);

-- 60 communes : 20 legendaires, 10 rares, 30 communs
insert into communes (code, nom, departement, population, tier, rang, palier_total)
select lpad(i::text, 5, '0'), 'Commune ' || i, (10 + (i % 5))::text,
       case when i <= 20 then 500000 - i * 1000
            when i <= 30 then 50000 - i * 100
            else 900 - i end,
       case when i <= 20 then 'legendaire'
            when i <= 30 then 'rare'
            else 'commun' end,
       i, 60
  from generate_series(1, 60) i;

-- Riche : legendaires 1-8, communs 31-36
insert into possessions (commune_code, joueur_id, saison)
select lpad(i::text,5,'0'), 'aaaaaaaa-0000-0000-0000-000000000001'::uuid, 'saison-1'
  from generate_series(1, 8) i
union all
select lpad(i::text,5,'0'), 'aaaaaaaa-0000-0000-0000-000000000001'::uuid, 'saison-1'
  from generate_series(31, 36) i;

-- Choisi : legendaires 9-11, rares 21-24 ; la legendaire 10 deja favorite
insert into possessions (commune_code, joueur_id, saison)
select lpad(i::text,5,'0'), 'aaaaaaaa-0000-0000-0000-000000000002'::uuid, 'saison-1'
  from generate_series(9, 11) i
union all
select lpad(i::text,5,'0'), 'aaaaaaaa-0000-0000-0000-000000000002'::uuid, 'saison-1'
  from generate_series(21, 24) i;
update possessions set gardee = true where commune_code = '00010';

-- Deuxleg : legendaires 12-14, communs 37-40 ; DEUX legendaires favorites
insert into possessions (commune_code, joueur_id, saison)
select lpad(i::text,5,'0'), 'aaaaaaaa-0000-0000-0000-000000000003'::uuid, 'saison-1'
  from generate_series(12, 14) i
union all
select lpad(i::text,5,'0'), 'aaaaaaaa-0000-0000-0000-000000000003'::uuid, 'saison-1'
  from generate_series(37, 40) i;
update possessions set gardee = true where commune_code in ('00012', '00013');

-- Pauvre : legendaires 15-17, rien d'autre
insert into possessions (commune_code, joueur_id, saison)
select lpad(i::text,5,'0'), 'aaaaaaaa-0000-0000-0000-000000000004'::uuid, 'saison-1'
  from generate_series(15, 17) i;

-- Normal : communs 41-50
insert into possessions (commune_code, joueur_id, saison)
select lpad(i::text,5,'0'), 'aaaaaaaa-0000-0000-0000-000000000005'::uuid, 'saison-1'
  from generate_series(41, 50) i;

insert into historique (commune_code, joueur_id, saison, acquired_at)
select commune_code, joueur_id, 'saison-1', now() - interval '10 days'
  from possessions;
