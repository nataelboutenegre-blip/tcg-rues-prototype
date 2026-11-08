-- s2-124 (8/11/2026, lancé à 21 h 52) : l'énergie du Front se recharge de 1 toutes les 7 min (avant 10).
-- Décision de Nataël (8/11, 21 h 48). On fige d'abord l'énergie de chacun à sa valeur du moment :
-- sinon le temps écoulé depuis sa dernière mise à jour serait recompté au nouveau rythme.
-- Effet : 144 -> 206 énergie par jour au plus ; la réserve de 90 se remplit en 10 h 30 (avant 15 h).
-- Pour revenir à 10 min : même chose avec 600.

update joueurs set front_energie = front_energie_lire(front_energie, front_energie_maj), front_energie_maj = now()
 where front_energie_maj is not null and front_energie < front_energie_reglage('max');

update config_jeu set valeur = (valeur::jsonb || '{"recharge_s": 420}'::jsonb)::text where cle = 'energie_front';

-- Contrôle : 420
select front_energie_reglage('recharge_s') as recharge_s;
