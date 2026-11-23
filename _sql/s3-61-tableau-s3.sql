-- s3-61 (23/11/2026) : le tableau de bord (direct/tableau.html) passe à la saison 3.
-- « rounds d'attaque » et « défenses » lisaient front_rounds / front_defenses (les dés de la S2) : 0 en S3.
-- Maintenant : sièges lancés (front_sieges), défenses = renforts (front_siege_alertes 'defendu'), sièges repoussés
-- (défendus puis tombés ou abandonnés), et les jeux du Mess (421, recensement) dans les mini-jeux.
-- Les courbes par jour (indices 3 et 5) et le top du jour suivent. Les anciennes clés restent pour l'ancien client.
do $do$
declare d text; n text;
begin
  d := pg_get_functiondef('public.tableau_de_bord()'::regprocedure); n := d;
  n := replace(n, 'pj  as (select (le at time zone ''Europe/Paris'')::date d, count(*) n from front_rounds where le >= v_debut group by 1),',
                  'pj  as (select (cree_le at time zone ''Europe/Paris'')::date d, count(*) n from front_sieges where cree_le >= v_debut group by 1),   -- s3-61 : sièges');
  n := replace(n, 'pd  as (select (le at time zone ''Europe/Paris'')::date d, count(*) n from front_defenses where le >= v_debut group by 1),',
                  'pd  as (select (le at time zone ''Europe/Paris'')::date d, count(*) n from front_siege_alertes where type = ''defendu'' and le >= v_debut group by 1),   -- s3-61 : renforts');
  n := replace(n, '''rounds'', (select count(*) from front_rounds where le >= v_minuit),',
                  '''rounds'', (select count(*) from front_rounds where le >= v_minuit),
      ''sieges'', (select count(*) from front_sieges where cree_le >= v_minuit),   -- s3-61
      ''sieges_energie'', (select coalesce(sum(energie_mise), 0) from front_sieges where cree_le >= v_minuit),
      ''sieges_cours'', (select count(*) from front_sieges where fini_le is null),
      ''renforts'', (select count(*) from front_siege_alertes where type = ''defendu'' and le >= v_minuit),
      ''repousses'', (select count(*) from front_sieges where fini_le >= v_minuit and defendu and resultat in (''tombee'', ''abandon'')),
      ''mess421'', (select count(*) from mess_421_parties where le >= v_minuit),
      ''recensement'', (select count(*) from mess_rec_parties where le >= v_minuit),');
  n := replace(n, '''top_jour'', (select coalesce(jsonb_agg(jsonb_build_array(x.id, x.pseudo, x.rounds, x.prises) order by x.rounds desc), ''[]''::jsonb)
                   from (select j.id, j.pseudo, count(r.*) rounds,
                                (select count(*) from front_prises p where p.attaquant = j.id and p.le >= v_minuit) prises
                           from front_rounds r join joueurs j on j.id = r.attaquant_id
                          where r.le >= v_minuit group by j.id, j.pseudo order by count(r.*) desc limit 8) x),',
                  '''top_jour'', (select coalesce(jsonb_agg(jsonb_build_array(x.id, x.pseudo, x.rounds, x.prises) order by x.prises desc, x.rounds desc), ''[]''::jsonb)
                   from (select j.id, j.pseudo, count(r.*) rounds,   -- s3-61 : « rounds » = sièges lancés aujourd''hui, classés par conquêtes
                                (select count(*) from front_sieges p where p.attaquant = j.id and p.fini_le >= v_minuit and p.resultat = ''conquise'') prises
                           from front_sieges r join joueurs j on j.id = r.attaquant
                          where r.cree_le >= v_minuit group by j.id, j.pseudo order by 4 desc limit 8) x),');
  if n = d or position('s3-61 : sièges' in n) = 0 or position('s3-61 : renforts' in n) = 0 or position('''sieges'',' in n) = 0 or position('classés par conquêtes' in n) = 0 then
    raise exception 's3-61 : tableau_de_bord a changé, rien n''est fait'; end if;
  execute n;
end $do$;
