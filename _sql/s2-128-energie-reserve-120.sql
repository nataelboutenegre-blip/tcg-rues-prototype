-- s2-128 (9/11/2026, lancé à 16 h 16) : réserve d'énergie du Front 90 -> 120, plafond des bonus 100 -> 130.
-- Décision de Nataël (« 120 tout de suite », 16 h 14), après les plaintes « pas assez d'énergie ».
-- On fige l'énergie de chacun avant : sinon le temps passé plein à 90 serait recompté jusqu'à 120.
-- 1) ceux qui étaient sous 90 (31 joueurs) :
update joueurs set front_energie = front_energie_lire(front_energie, front_energie_maj), front_energie_maj = now()
 where front_energie_maj is not null and front_energie < front_energie_reglage('max');
-- 2) le réglage :
update config_jeu set valeur = (valeur::jsonb || '{"max": 120, "plafond": 130}'::jsonb)::text where cle = 'energie_front';
-- 3) ceux qui étaient pleins à 90 ou au-dessus (137 joueurs) repartent de là maintenant :
update joueurs set front_energie_maj = now()
 where front_energie_maj is not null and front_energie >= 90 and front_energie < 120
   and front_energie_maj < now() - interval '2 minutes';
-- Contrôle : 120 | 130 ; après coup, personne au-dessus de 100 (5 joueurs entre 95 et 100, des bonus).
select front_energie_reglage('max') as max, front_energie_reglage('plafond') as plafond;
