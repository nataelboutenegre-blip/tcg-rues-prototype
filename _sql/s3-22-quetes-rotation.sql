-- ===========================================================================
--  s3-22 (18/11/2026) — les quêtes du Front tournent chaque jour
--  Idée d'un joueur (18/11) : « crée plein de missions et fais une rotation tous les
--  jours, c'est un peu redondant ». Validé par Nataël (11 h 22) : 2 quêtes fixes,
--  le reste tiré chaque jour, mêmes quêtes pour tous ; récompenses 10 énergie
--  (15 pour les plus dures), bonus « Termine tes 7 quêtes » 15 énergie + 1 lingot.
--
--  Front : 2 fixes (Commune du jour, Conquiers une commune) + 5 tirées dans une
--  réserve de 32, par familles (combat 2, mini-jeux 1, économie 1, Mess ou clan 1),
--  une quête n'étant tirée que si elle est jouable (siège, Mess, Suisse ouverts).
--  Terra : réserve de 11 → 16, 5 tirées + bonus (inchangé).
--  Plafond d'énergie des quêtes : 80 → 100 par jour (config_jeu 'quetes'.energie_jour).
--  Nouveaux compteurs : siege_vague (siege_vague), renfort (siege_renforcer).
--  Contrôle attendu (dernière ligne) : 8 | 6 | true | true | true
-- ===========================================================================

insert into public.config_jeu (cle, valeur)
values ('quetes', '{"energie_jour": 100, "terra_tirees": 5}')
on conflict (cle) do nothing;

create or replace function public.quetes_cfg_int(p_cle text, p_defaut integer)
 returns integer language sql stable security definer set search_path to 'public'
as $f$ select coalesce((select (c.valeur::jsonb ->> p_cle)::int from config_jeu c where c.cle = 'quetes'), p_defaut); $f$;

create or replace function public.quetes_liste(p_uid uuid)
 RETURNS TABLE(id text, mode text, categorie text, titre text, detail text, avancement integer, cible integer, points integer, energie integer)
 LANGUAGE plpgsql
 STABLE SECURITY DEFINER
 SET search_path TO 'public'
AS $function$
declare
  v_jour date := quete_jour();
  v_minuit timestamptz := v_jour::timestamp at time zone 'Europe/Paris';
  c_paquet int; c_doublon int; c_defense int; c_garnison int; c_radar_v int; c_rafale_v int; c_conquete int;
  c_bourse int; c_echange int; c_vitrine int; c_energie int; c_vague int; c_renfort int;
  v_nouvelles int; v_cdj int; v_cdj3 int; v_communes int; v_epiques int; v_dept int; v_radar int; v_rafale int; v_pom int; v_depts int; v_tenue int;
  v_radar_perf int; v_rafale_perf int; v_pom_perf int;
  v_conq_rare int; v_conq_ch int; v_sieges int; v_bat int; v_roue int; v_tickets int; v_421 int; v_rec int; v_clan_ech int; v_clan_msg int;
  v_nouv_rare int; v_achat_bourse int; v_eclat int; v_dep3 int;
  b_siege boolean := coalesce(siege_actif(), false);
  b_mess boolean := coalesce((select (c.valeur::jsonb ->> 'actif')::int = 1 from config_jeu c where c.cle = 'mess'), false);
  b_suisse boolean := exists (select 1 from communes c where c.code like 'CH%');
  b_clan boolean := exists (select 1 from clan_membres cm where cm.joueur_id = p_uid);
  n_terra int := quetes_cfg_int('terra_tirees', 5);
begin
  select coalesce(sum(n) filter (where q.cle = 'terra_paquet'), 0),
         coalesce(sum(n) filter (where q.cle = 'doublon'), 0),
         coalesce(sum(n) filter (where q.cle = 'defense'), 0),
         coalesce(sum(n) filter (where q.cle = 'garnison'), 0),
         coalesce(sum(n) filter (where q.cle = 'radar_victoire'), 0),
         coalesce(sum(n) filter (where q.cle = 'rafale_victoire'), 0),
         coalesce(sum(n) filter (where q.cle = 'conquete'), 0),
         coalesce(sum(n) filter (where q.cle = 'bourse_vente'), 0),
         coalesce(sum(n) filter (where q.cle = 'echange_propose'), 0),
         coalesce(sum(n) filter (where q.cle = 'vitrine'), 0),
         coalesce(sum(n) filter (where q.cle = 'energie'), 0),
         coalesce(sum(n) filter (where q.cle = 'siege_vague'), 0),
         coalesce(sum(n) filter (where q.cle = 'renfort'), 0)
    into c_paquet, c_doublon, c_defense, c_garnison, c_radar_v, c_rafale_v, c_conquete, c_bourse, c_echange, c_vitrine, c_energie, c_vague, c_renfort
    from quetes_compteurs q where q.joueur_id = p_uid and q.jour = v_jour;
  select count(*), count(*) filter (where c.tier in ('rare', 'epique', 'legendaire'))
    into v_nouvelles, v_nouv_rare
    from terra_collection t join communes c on c.code = t.commune_code
   where t.joueur_id = p_uid and t.premiere_le >= v_minuit and t.exemplaires > 0;
  select coalesce(max(n), 0) into v_dep3 from (select c.departement, count(*) n from terra_collection t join communes c on c.code = t.commune_code
   where t.joueur_id = p_uid and t.premiere_le >= v_minuit and t.exemplaires > 0 group by c.departement) x;
  select count(*) into v_eclat from terra_collection t where t.joueur_id = p_uid and t.eclat_le >= v_minuit;
  select count(*) into v_achat_bourse from mouvements_points m where m.joueur_id = p_uid and m.motif = 'terra_bourse' and m.montant < 0 and m.cree_le >= v_minuit;
  select count(*), count(*) filter (where g.essais <= 3) into v_cdj, v_cdj3 from cdj_gains g where g.joueur_id = p_uid and g.jour = v_jour;
  select count(*) into v_pom from pom_parties pp where pp.joueur_id = p_uid and pp.jour = v_jour and pp.fini;
  select count(distinct c.departement), count(*) filter (where c.tier in ('rare', 'epique', 'legendaire')), count(*) filter (where c.code like 'CH%')
    into v_depts, v_conq_rare, v_conq_ch
    from front_victoires fv join communes c on c.code = fv.commune_code
   where fv.joueur_id = p_uid and fv.type = 'conquete' and fv.le >= v_minuit;
  select count(*) into v_tenue
    from front_victoires fv
    join possessions p on p.commune_code = fv.commune_code and p.joueur_id = p_uid
   where fv.joueur_id = p_uid and fv.type = 'conquete'
     and fv.le >= v_minuit - interval '24 hours' and fv.le < v_minuit;
  select count(*) into v_radar from radar_parties r
   where r.joueur_id = p_uid and r.fini and not r.amical and r.fin_le >= v_minuit;
  select count(*) into v_rafale from rafale_parties r
   where r.joueur_id = p_uid and r.fini and not r.amical and r.fin_le >= v_minuit;
  select count(*) into v_radar_perf from radar_parties r
   where r.joueur_id = p_uid and r.fini and not r.amical and r.fin_le >= v_minuit and r.total_km < 400;
  select count(*) into v_rafale_perf from rafale_parties r
   where r.joueur_id = p_uid and r.fini and not r.amical and r.fin_le >= v_minuit and r.score >= 6;
  select count(*) into v_pom_perf from pom_parties pp
   where pp.joueur_id = p_uid and pp.jour = v_jour and pp.fini and pp.justes >= 7;
  v_pom_perf := v_pom_perf + (select count(*) from pom_duels pd
    where pd.joueur_id = p_uid and pd.fini and pd.justes >= 7 and pd.fin_le >= v_minuit);
  select count(*) into v_sieges from front_sieges s where s.attaquant = p_uid and s.cree_le >= v_minuit;
  select count(*) into v_bat from batiments_historique b where b.joueur_id = p_uid and b.cree_le >= v_minuit;
  select count(*) into v_roue from roue_front_tours r where r.joueur_id = p_uid and r.le >= v_minuit;
  select coalesce((select sum(t.mise) from mess_tirages t where t.joueur_id = p_uid and t.le >= v_minuit), 0)
       + coalesce((select sum(t.mise) from mess_421_parties t where t.joueur_id = p_uid and t.le >= v_minuit), 0)
       + coalesce((select sum(t.mise) from mess_rec_parties t where t.joueur_id = p_uid and t.le >= v_minuit), 0)
    into v_tickets;
  select count(*) into v_421 from mess_421_parties t where t.joueur_id = p_uid and t.fini_le >= v_minuit and t.resultat in ('421', '421sec');
  select count(*) into v_rec from mess_rec_parties t where t.joueur_id = p_uid and t.fini_le >= v_minuit and t.resultat in ('gagne', 'parfait');
  select count(*) into v_clan_ech from clan_echanges e where e.inter and e.etat = 'accepte' and e.repondu_le >= v_minuit
     and (e.proposant = p_uid or e.destinataire = p_uid);
  select count(*) into v_clan_msg from clan_messages m where m.auteur = p_uid and m.le >= v_minuit and not coalesce(m.supprime, false);
  select count(*), count(*) filter (where c.tier = 'epique')
    into v_communes, v_epiques
    from terra_collection t join communes c on c.code = t.commune_code
   where t.joueur_id = p_uid and t.exemplaires > 0;
  if exists (select 1 from quetes_reclamees r where r.joueur_id = p_uid and r.quete = 'u_tdept') then
    v_dept := 1;
  else
    select count(*) into v_dept
      from (select c.departement, count(*) as n
              from terra_collection t join communes c on c.code = t.commune_code
             where t.joueur_id = p_uid and t.exemplaires > 0 and est_metropole(c.departement)
             group by c.departement) m
      join (select c2.departement, count(*) as n from communes c2 group by c2.departement) tot
        on tot.departement = m.departement and tot.n = m.n;
  end if;

  return query
  with reserve(id, titre, detail, avancement, cible) as (values
    ('t_paquets',   'Ouvre 2 paquets Terra',            'Gratuits ou achetés',                  c_paquet,              2),
    ('t_nouvelles', 'Ajoute 3 nouvelles communes',      'Des communes que tu n''avais pas',     v_nouvelles,           3),
    ('t_doublon',   'Vends ou échange un doublon',      'Au jeu, à la Bourse ou en échange',    c_doublon,             1),
    ('t_bourse',    'Mets une carte en vente',          'À la Bourse',                          c_bourse,              1),
    ('t_echange',   'Propose un échange',               'À n''importe quel joueur',             c_echange,             1),
    ('t_vitrine',   'Change ta vitrine',                'Dans ton profil',                      c_vitrine,             1),
    ('t_cdj',       'Trouve la Commune du jour',        'Dans le QG',                           v_cdj,                 1),
    ('t_radar',     'Joue un duel Radar',               'Duel classé, dans le QG',              v_radar,               1),
    ('t_rafale',    'Joue un duel Rafale',              'Duel classé, dans le QG',              v_rafale,              1),
    ('t_victoire',  'Gagne un duel',                    'Radar ou Rafale, classé',              c_radar_v + c_rafale_v, 1),
    ('t_pom',       'Joue à Plus ou moins',             'Les 10 duels, dans le QG',             v_pom,                 1),
    -- s3-22 : 5 de plus
    ('t_rare',      'Ajoute une rare ou mieux',         'Une rare, épique ou légendaire que tu n''avais pas', v_nouv_rare, 1),
    ('t_paquets4',  'Ouvre 4 paquets Terra',            'Gratuits ou achetés',                  c_paquet,              4),
    ('t_achat',     'Achète une carte à la Bourse',     'Une carte mise en vente par un joueur', v_achat_bourse,       1),
    ('t_eclat',     'Fais briller une carte',           'Un éclat sur une carte de ta collection', v_eclat,            1),
    ('t_dep3',      '3 nouvelles d''un même département', 'Trois communes que tu n''avais pas, du même département', v_dep3, 3)),
  t_jour as (
    select r.* from reserve r order by md5(r.id || v_jour::text) limit n_terra),
  -- le Front : (id, famille, titre, détail, avancement, cible, points, énergie, jouable)
  front(id, famille, titre, detail, avancement, cible, points, energie, jouable) as (values
    -- fixes
    ('f_cdj',         'fixe',   'Trouve la Commune du jour',        'Dans le QG',                                    v_cdj,       1, 0,  10, true),
    ('f_conquete',    'fixe',   'Conquiers une commune',            case when b_siege then 'Un siège mené jusqu''au bout' else 'Trois victoires, pas forcément d''affilée' end, c_conquete, 1, 50, 10, true),
    -- combat
    ('f_conq3',       'combat', 'Conquiers 3 communes',             'Trois prises dans la journée',                  c_conquete,  3, 0,  15, true),
    ('f_depts',       'combat', 'Conquiers dans 2 départements',    'Deux départements différents',                  v_depts,     2, 0,  15, true),
    ('f_tenir',       'combat', 'Garde une commune prise hier',     'Toujours à toi aujourd''hui',                   v_tenue,     1, 0,  10, true),
    ('f_defense',     'combat', 'Réussis une défense',              case when b_siege then 'Un siège contre toi qui échoue' else 'Défends toi-même une commune attaquée' end, c_defense, 1, 0, 10, true),
    ('f_garnison',    'combat', 'Mets une commune en garnison',     'Ou recharge une garnison',                      c_garnison,  1, 0,  10, true),
    ('f_garnison2',   'combat', 'Pose 2 garnisons',                 'Ou recharge-les',                               c_garnison,  2, 0,  15, true),
    ('f_rare',        'combat', 'Conquiers une rare ou mieux',      'Rare, épique ou légendaire',                    v_conq_rare, 1, 0,  15, true),
    ('f_suisse',      'combat', 'Conquiers une commune suisse',     'Dans n''importe quel canton',                   v_conq_ch,   1, 0,  15, b_suisse),
    ('f_siege',       'combat', 'Lance 2 sièges',                   'Deux communes différentes',                     v_sieges,    2, 0,  10, b_siege),
    ('f_vagues',      'combat', 'Envoie 5 vagues',                  'Sur un ou plusieurs sièges',                    c_vague,     5, 0,  10, b_siege),
    ('f_renfort',     'combat', 'Renforce une commune assiégée',    'Envoie de l''énergie à une de tes communes',    c_renfort,   1, 0,  10, b_siege),
    -- mini-jeux
    ('f_cdj3',        'jeux',   'Commune du jour en 3 essais',      'Ou moins',                                      v_cdj3,      1, 0,  15, true),
    ('f_pom',         'jeux',   'Joue à Plus ou moins',             'Les 10 duels, dans le QG',                      v_pom,       1, 0,  10, true),
    ('f_pom_perf',    'jeux',   'Plus ou moins : 7 sur 10',         'Partie du jour ou duel classé',                 v_pom_perf,  1, 0,  15, true),
    ('f_radar',       'jeux',   'Joue 2 duels Radar',               'Classés, gagnés ou perdus, dans le QG',         v_radar,     2, 0,  10, true),
    ('f_radar_perf',  'jeux',   'Radar : moins de 400 km',          'Une partie classée, au total',                  v_radar_perf, 1, 0, 15, true),
    ('f_rafale',      'jeux',   'Joue 2 duels Rafale',              'Classés, gagnés ou perdus, dans le QG',         v_rafale,    2, 0,  10, true),
    ('f_rafale_perf', 'jeux',   'Rafale : 6 communes',              'Dans une partie classée',                       v_rafale_perf, 1, 0, 15, true),
    ('f_victoires',   'jeux',   'Gagne 2 duels classés',            'Radar ou Rafale',                               c_radar_v + c_rafale_v, 2, 0, 15, true),
    -- économie
    ('f_batiment',    'eco',    'Construis ou améliore un bâtiment', 'N''importe lequel',                            v_bat,       1, 0,  10, true),
    ('f_roue',        'eco',    'Fais 10 tours de roue',            'La roue du Front, dans Tirage',                 v_roue,     10, 0,  10, true),
    ('f_paquet',      'eco',    'Ouvre un paquet Terra',            'Le lien entre les deux modes',                  c_paquet,    1, 0,  10, true),
    ('f_paquet3',     'eco',    'Ouvre 3 paquets Terra',            'Gratuits ou achetés',                           c_paquet,    3, 0,  10, true),
    ('f_energie',     'eco',    'Dépense 60 énergie',               'Sièges, garnisons, renforts',                   c_energie,  60, 0,  15, true),
    -- Mess et clan
    ('f_tickets',     'social', 'Joue 3 tickets au Mess',           'Machine, Recensement ou 421',                   v_tickets,   3, 0,  10, b_mess),
    ('f_421',         'social', 'Fais un 4-2-1 au 421',             'Au Mess, du premier coup ou en relançant',      v_421,       1, 0,  15, b_mess),
    ('f_recensement', 'social', 'Réussis un Recensement',           'Au Mess : bats le Préfet sans franchir 50 000', v_rec,       1, 0,  15, b_mess),
    ('f_clan_ech',    'social', 'Fais un échange avec un autre clan', 'Proposé ou accepté, il doit être conclu',     v_clan_ech,  1, 0,  15, b_clan),
    ('f_clan_msg',    'social', 'Écris dans le tchat de ton clan',  'Un petit mot pour ton clan',                    v_clan_msg,  1, 0,  10, b_clan),
    ('f_duel',        'social', 'Joue un duel classé',              'Radar, Rafale, ou la partie du jour de Plus ou moins', v_radar + v_rafale + v_pom, 1, 0, 10, true)),
  -- tirage du jour : les mêmes pour tous, parmi les quêtes jouables ; quotas par famille
  rangs as (
    select f.*, row_number() over (partition by f.famille order by md5(f.id || v_jour::text)) rg
      from front f where f.jouable and f.famille <> 'fixe'),
  f_jour as (
    select f.* from front f where f.famille = 'fixe'
    union all
    select r.id, r.famille, r.titre, r.detail, r.avancement, r.cible, r.points, r.energie, r.jouable from rangs r
     where (r.famille = 'combat' and r.rg <= 2) or (r.famille in ('jeux', 'eco', 'social') and r.rg <= 1))
  select d.id, 'terra'::text, 'jour'::text, d.titre::text, d.detail::text, d.avancement::int, d.cible::int, 20, 0 from t_jour d
  union all
  select 't_bonus', 'terra', 'jour', 'Termine les ' || n_terra || ' quêtes du jour', 'Le bonus du jour',
         (select count(*) from t_jour d where d.avancement >= d.cible)::int, n_terra, 50, 0
  union all
  select f.id::text, 'front'::text, 'jour'::text, f.titre::text, f.detail::text, f.avancement::int, f.cible::int, f.points::int, f.energie::int from f_jour f
  union all
  select 'f_bonus', 'front', 'jour', 'Termine tes ' || (select count(*) from f_jour) || ' quêtes du Front', 'Le bonus du jour : 15 énergie et 1 lingot',
         (select count(*) from f_jour f where f.avancement >= f.cible)::int, (select count(*) from f_jour)::int, 0, 15
  union all
  select * from (values
    ('u_t100',      'terra', 'unique', 'Collectionne 100 communes',      'Communes différentes',                   v_communes, 100,  200, 0),
    ('u_t500',      'terra', 'unique', 'Collectionne 500 communes',      'Communes différentes',                   v_communes, 500,  400, 0),
    ('u_t2000',     'terra', 'unique', 'Collectionne 2 000 communes',    'Communes différentes',                   v_communes, 2000, 600, 0),
    ('u_tdept',     'terra', 'unique', 'Complète un département',        'Toutes ses communes dans ta collection', v_dept,     1,    300, 0),
    ('u_tepique',   'terra', 'unique', 'Obtiens une épique',             'Dans un paquet ou par un contrat',       v_epiques,  1,    200, 0)
  ) as l(id, mode, categorie, titre, detail, avancement, cible, points, energie);
end;
$function$;

-- reclamer_quete : plafond d'énergie réglable (100), et le lingot du bonus du Front
do $do$
declare d text; a text; b text; k integer;
begin
  d := pg_get_functiondef('public.reclamer_quete(text)'::regprocedure);
  if position('s3-22' in d) = 0 then
    for a, b in values
      ('v_e := least(q.energie, greatest(0, 80 - v_deja));', 'v_e := least(q.energie, greatest(0, quetes_cfg_int(''energie_jour'', 100) - v_deja));   -- s3-22'),
      ('(plafond du jour atteint : 80 / 80)', '(plafond du jour atteint : '' || quetes_cfg_int(''energie_jour'', 100) || '' / '' || quetes_cfg_int(''energie_jour'', 100) || '')'),
      ('plus d''''énergie de quête aujourd''''hui (80 / 80)', 'plus d''''énergie de quête aujourd''''hui ('' || quetes_cfg_int(''energie_jour'', 100) || '' / '' || quetes_cfg_int(''energie_jour'', 100) || '')'),
      (E'  insert into quetes_reclamees(joueur_id, quete, jour, points, energie)',
       E'  if p_id = ''f_bonus'' then   -- s3-22 : 1 lingot, dans la limite du porte-monnaie\n    declare l numeric; begin\n      l := lingots_figer(v_uid);\n      update joueurs set lingots = greatest(l, least(lingots_max(v_uid), l + 1)) where id = v_uid;\n    end;\n  end if;\n  insert into quetes_reclamees(joueur_id, quete, jour, points, energie)')
    loop
      k := (length(d) - length(replace(d, a, ''))) / length(a);
      if k <> 1 then raise exception 's3-22 : reclamer_quete a changé (% fois : %)', k, left(a, 60); end if;
      d := replace(d, a, b);
    end loop;
    execute d;
  end if;

  -- les deux compteurs du siège
  d := pg_get_functiondef('public.siege_vague(text,integer)'::regprocedure);
  if position('s3-22' in d) = 0 then
    a := E'  v_reste := siege_appliquer(v_id, p_energie + coalesce(v_att, 0));';
    if (length(d) - length(replace(d, a, ''))) / length(a) <> 1 then raise exception 's3-22 : siege_vague a changé'; end if;
    execute replace(d, a, E'  perform quete_noter(v_uid, ''siege_vague'', 1);   -- s3-22\n' || a);
  end if;
  d := pg_get_functiondef('public.siege_renforcer(text,uuid,integer)'::regprocedure);
  if position('s3-22' in d) = 0 then
    a := E'  return siege_vue(s.id);';
    if (length(d) - length(replace(d, a, ''))) / length(a) <> 1 then raise exception 's3-22 : siege_renforcer a changé'; end if;
    execute replace(d, a, E'  perform quete_noter(v_uid, ''renfort'', 1);   -- s3-22\n' || a);
  end if;
end $do$;

select (select count(*) from quetes_liste((select id from joueurs where pseudo = 'Nataël')) where mode = 'front' and categorie = 'jour') front_du_jour,
       (select count(*) from quetes_liste((select id from joueurs where pseudo = 'Nataël')) where mode = 'terra' and categorie = 'jour') terra_du_jour,
       position('s3-22' in pg_get_functiondef('public.reclamer_quete(text)'::regprocedure)) > 0 reclamer,
       position('s3-22' in pg_get_functiondef('public.siege_vague(text,integer)'::regprocedure)) > 0 vague,
       position('s3-22' in pg_get_functiondef('public.siege_renforcer(text,uuid,integer)'::regprocedure)) > 0 renfort;
