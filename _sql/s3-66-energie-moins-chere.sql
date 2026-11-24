-- s3-66 (24/11/2026) : la conquête coûte moins cher (Nataël : « je ne veux pas ralentir le Front, au contraire »).
-- Constat : une conquête coûtait ≈ 10,7 ⚡ pose comprise en S3 contre 8,5 en S2 (Arkhannou 9,4 contre 6,2).
-- 1. chaque ⚡ fait 12 points au lieu de 10 (attaque ET renfort : siege_renforcer lit le même réglage) ;
-- 2. la pose coûte 1 ⚡ au lieu de 2.
-- Le bouclier de garnison reste à 10 points par ⚡ (non demandé).
-- Retour : update config_jeu set valeur = (valeur::jsonb || '{"points_par_energie": 10, "pose": 2}')::text where cle = 'siege';
update config_jeu set valeur = (valeur::jsonb || '{"points_par_energie": 12, "pose": 1}')::text where cle = 'siege';
