\set ON_ERROR_STOP 0
\set A '00000000-0000-0000-0000-00000000000a'
\set D '00000000-0000-0000-0000-00000000000d'
\set E '00000000-0000-0000-0000-00000000000e'
\set B '00000000-0000-0000-0000-00000000000b'
\pset format unaligned
\pset tuples_only on
select setseed(0.42);

\echo '--- 0. éteint : refus'
select set_config('request.jwt.claims', json_build_object('sub', :'A')::text, false);
select siege_vague('C1', 5);
update config_jeu set valeur = (valeur::jsonb || '{"actif": 1}')::text where cle = 'siege';
\echo '--- 0b. ancien combat refusé'
select attaquer('C1');
select set_config('request.jwt.claims', json_build_object('sub', :'D')::text, false);
select defendre('C1', :'A'::uuid, 'normale');
select set_config('request.jwt.claims', json_build_object('sub', :'A')::text, false);

\echo '--- 1. aperçu C1 (commune, 2 communes à A à < 20 km : × 1,1)'
select siege_apercu('C1') - 'siege';
\echo '--- 1b. éclair : 3 ⚡ puis 5 ⚡ (résistance 55, ~11 pts/⚡)'
select jsonb_build_object('degats', v->'degats', 'res', v->'resistance', 'long', v->'long', 'resultat', v->'resultat') from siege_vague('C1', 3) v;
select jsonb_build_object('degats', v->'degats', 'resultat', v->'resultat', 'attente', v->'attente') from siege_vague('C1', 5) v;
select 'proprio C1', (select pseudo from joueurs where id = joueur_id), conquise_le is not null from possessions where commune_code = 'C1';
select 'energie A', round(front_energie_lire(front_energie, front_energie_maj), 1) from joueurs where id = :'A';
select 'journal', string_agg(type || ':' || commune_code, ',') from journal;

\echo '--- 2. garnison C2 (5 ⚡ = bouclier 50) : siège long dès le départ, plafond 10 % de 55 + rythme'
select jsonb_build_object('degats', v->'degats', 'bouclier', v->'bouclier', 'long', v->'long', 'attente', v->'attente', 'plafond', v->'plafond', 'envoyes', v->'envoyes_long') from siege_vague('C2', 10) v;
select 'garnison C2', energie, round(entame, 1) from front_garnisons where commune_code = 'C2';
\echo '--- 2b. une heure plus tard (rythme 55/h), la tâche fait partir l''attente'
update front_sieges set long_depuis = long_depuis - interval '1 hour' where commune_code = 'C2' and fini_le is null;
select siege_tick();
select jsonb_build_object('degats', v->'degats', 'bouclier', v->'bouclier', 'attente', v->'attente', 'resultat', v->'resultat') from (select siege_vue(id) v from front_sieges where commune_code = 'C2' order by id desc limit 1) x;
select 'garnison C2 apres', energie, round(entame, 1), (select garnison_touchee from front_sieges where commune_code = 'C2' order by id desc limit 1) from front_garnisons where commune_code = 'C2';

\echo '--- 3. défense C3 : A met 3 ⚡ (~33/55), D renforce 2 ⚡ (~26 de recul), siège long'
select (v->'degats') from siege_vague('C3', 3) v;
select set_config('request.jwt.claims', json_build_object('sub', :'D')::text, false);
select jsonb_build_object('degats', v->'degats', 'long', v->'long', 'defendu', v->'defendu') from siege_renforcer('C3', :'A'::uuid, 2) v;
select 'D voit', jsonb_array_length(sieges_contre_moi_v2());
select set_config('request.jwt.claims', json_build_object('sub', :'A')::text, false);
\echo '--- 3b. A remet 10 ⚡ : plafonné (5,5 pts tout de suite), le reste attend'
select jsonb_build_object('degats', v->'degats', 'attente', v->'attente', 'plafond', v->'plafond') from siege_vague('C3', 10) v;
\echo '--- 3c. 25 h sans vague : le siège tombe, défense réussie pour D'
update front_sieges set derniere_vague = now() - interval '25 hours' where commune_code = 'C3' and fini_le is null;
select siege_tick();
select 'C3', resultat, attente from front_sieges where commune_code = 'C3' order by id desc limit 1;
select 'journal defense', count(*) from journal where type = 'defense' and commune_code = 'C3';
select 'gains D', string_agg(motif || ':' || pts, ',') from gains where joueur = :'D';
select 'energie A (attente rendue)', round(front_energie_lire(front_energie, front_energie_maj), 1) from joueurs where id = :'A';

\echo '--- 4. légendaire : toujours long ; places'
select jsonb_build_object('long', v->'long', 'res', v->'resistance', 'attente', v->'attente', 'degats', v->'degats') from siege_vague('C4', 20) v;
select 'places', siege_places(:'A'::uuid), 'longs', siege_longs_en_cours(:'A'::uuid);

\echo '--- 5. forteresse sur C5 (rare 65 × 1,5) : long (bâtiment visible)'
select jsonb_build_object('res', v->'resistance', 'long', v->'long', 'forteresse', v->'forteresse') from siege_apercu('C5') v;

\echo '--- 6. épique en éclair : au moins 1 h (10 % tout de suite)'
select jsonb_build_object('long', v->'long', 'degats', v->'degats', 'attente', v->'attente', 'plafond', v->'plafond') from siege_vague('C6', 15) v;

\echo '--- 7. abandon : l''attente revient'
select 'energie avant', round(front_energie_lire(front_energie, front_energie_maj), 1) from joueurs where id = :'A';
select (v->'resultat') from siege_abandonner('C6') v;
select 'energie apres', round(front_energie_lire(front_energie, front_energie_maj), 1) from joueurs where id = :'A';

\echo '--- 8. loin (L1, aucune commune à A à < 20 km : × 0,8)'
select (v->'mult') from siege_apercu('L1') v;

\echo '--- 9. refus : coéquipier, ma commune, bouclier, immunité, trop d''énergie'
select set_config('request.jwt.claims', json_build_object('sub', :'E')::text, false);
select siege_vague('C3', 2);
select set_config('request.jwt.claims', json_build_object('sub', :'A')::text, false);
select siege_vague('A1', 2);
update possessions set bouclier_jusqua = now() + interval '1 hour' where commune_code = 'C5';
select siege_vague('C5', 2);
update possessions set bouclier_jusqua = null, acquired_at = now() - interval '1 hour' where commune_code = 'C5';
select siege_vague('C5', 2);
update possessions set acquired_at = now() - interval '1 day' where commune_code = 'C5';
select siege_vague('C5', 99);

\echo '--- 10. course : B et A assiègent C2 ; la commune change de main par échange au profit de A'
select set_config('request.jwt.claims', json_build_object('sub', :'B')::text, false);
select (v->'degats') from siege_vague('C2', 2) v;
update possessions set joueur_id = :'A', acquired_at = now() where commune_code = 'C2';
select 'C2 sièges', string_agg((select pseudo from joueurs where id = attaquant) || ':' || coalesce(resultat, 'en cours'), ',' order by id) from front_sieges where commune_code = 'C2';

\echo '--- 11. notifications'
select titre from notifs order by ctid;

\echo '--- 12. course : A et B sur C6 (épique, éclair) ; A prend, B est fermé et remboursé'
update possessions set joueur_id = :'D', acquired_at = now() - interval '1 day' where commune_code = 'C6';
select set_config('request.jwt.claims', json_build_object('sub', :'B')::text, false);
update joueurs set front_energie = 100, front_energie_maj = now() where id in (:'A', :'B');
select 'B', (v->'degats'), (v->'attente') from siege_vague('C6', 20) v;
select set_config('request.jwt.claims', json_build_object('sub', :'A')::text, false);
update front_sieges set cree_le = now() - interval '2 hours' where commune_code = 'C6' and fini_le is null and attaquant = :'A';
select 'A', (v->'degats'), (v->'resultat') from siege_vague('C6', 20) v;
update front_sieges set cree_le = now() - interval '2 hours' where commune_code = 'C6' and fini_le is null;
select 'A2', (v->'degats'), (v->'resultat') from siege_vague('C6', 3) v;
select 'C6 sièges', string_agg((select pseudo from joueurs where id = attaquant) || ':' || coalesce(resultat, 'en cours') || ':' || attente, ',' order by id) from front_sieges where commune_code = 'C6';
select 'energie B', round(front_energie_lire(front_energie, front_energie_maj), 1) from joueurs where id = :'B';

\echo '--- 13. légendaire C4 : 16 h plus tard, la tâche finit le travail'
update joueurs set front_energie = 120, front_energie_maj = now() where id = :'A';
select (v->'attente') from siege_vague('C4', 15) v;
update front_sieges set long_depuis = now() - interval '16 hours', derniere_vague = now() where commune_code = 'C4' and fini_le is null;
select siege_tick();
select 'C4', (select pseudo from joueurs where id = joueur_id) from possessions where commune_code = 'C4';
select 'C4 siège', resultat, round(degats), attente from front_sieges where commune_code = 'C4' order by id desc limit 1;
