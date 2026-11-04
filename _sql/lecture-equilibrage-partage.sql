-- ===========================================================================
--  LECTURE SEULE — Chiffres d'équilibrage du Front, à partager (4/11/2026)
--  Pour Oshannir et les joueurs qui veulent proposer des réglages (salon
--  Discord « équilibrage »). Va avec le dossier _partage/equilibrage-front.md.
--  UNIQUEMENT DES CHIFFRES AGRÉGÉS : aucun pseudo, aucune commune, aucun
--  département, aucun emplacement de bâtiment, rien sur les Centres de
--  recherche (secrets), rien qui désigne un joueur ou une cible.
--  Fenêtres : 7 jours pour les conquêtes ; les rounds ne sont notés que
--  depuis le 3/11 vers midi (s2-87) ; les sièges et bâtiments, maintenant.
--  Ne modifie rien. Un seul tableau (l'éditeur Supabase n'affiche que le
--  dernier résultat).
-- ===========================================================================
with auj as (select (now() at time zone 'Europe/Paris')::date as d),
ot(tier, o, nom) as (values ('commun', 1, 'commun'), ('peucommun', 2, 'peu commun'), ('rare', 3, 'rare'),
                            ('epique', 4, 'épique'), ('legendaire', 5, 'légendaire')),
dernier as (select joueur_id, max(jour) as j from jours_joues group by 1),
tenants as (select joueur_id, count(*) as n from possessions group by 1),
actifs as (select t.joueur_id, t.n from tenants t join dernier d on d.joueur_id = t.joueur_id
            where d.j >= (select d from auj) - 2),
cat as (select c.code, c.tier, length(c.departement) = 2 as metro from communes c),
pris7 as (select p.commune_code, p.attaquant, p.victime, p.le, c.tier, (p.le at time zone 'Europe/Paris')::date as jour,
                 (select d.j from dernier d where d.joueur_id = p.victime) as victime_dernier
            from front_prises p left join cat c on c.code = p.commune_code
           where p.le > now() - interval '7 days'),
jours7 as (select greatest(1, count(distinct jour)) as n from pris7),
rd as (select attaquant_id, tier, gagne, victoires, le from front_rounds),
rd_jours as (select greatest(1, extract(epoch from now() - min(le)) / 86400) as n from rd),
clanj as (select distinct joueur_id from clan_membres)
-- 1. CONTEXTE ---------------------------------------------------------------
select 10 as tri, 'CONTEXTE' as section, 'joueurs actifs au Front (jeu ouvert depuis 2 jours, au moins 1 commune)' as ligne,
       (select count(*) from actifs)::text as valeur
union all
select 11, 'CONTEXTE', 'joueurs qui tiennent au moins 1 commune', (select count(*) from tenants)::text
union all
select 12, 'CONTEXTE', 'joueurs actifs dans un clan',
       (select count(*) filter (where joueur_id in (select joueur_id from clanj)) || ' sur ' || count(*) from actifs)
-- 2. LE POT -----------------------------------------------------------------
union all
select 20 + o.o, 'POT (métropole)', o.nom,
       count(*) filter (where p.commune_code is not null) || ' tenues · '
       || count(*) filter (where p.commune_code is null) || ' libres · '
       || round(100.0 * count(*) filter (where p.commune_code is not null) / nullif(count(*), 0)) || ' % prises'
  from cat c join ot o on o.tier = c.tier
  left join possessions p on p.commune_code = c.code
 where c.metro
 group by o.o, o.nom
union all
select 26, 'POT (outre-mer)', 'toutes raretés',
       count(*) filter (where p.commune_code is not null) || ' tenues · ' || count(*) filter (where p.commune_code is null) || ' libres'
  from cat c left join possessions p on p.commune_code = c.code
 where not c.metro
-- 3. RÉPARTITION ------------------------------------------------------------
union all
select 30, 'RÉPARTITION', 'communes par joueur actif',
       'médiane ' || percentile_disc(0.5) within group (order by n)
       || ' · 75 % en ont moins de ' || percentile_disc(0.75) within group (order by n)
       || ' · 90 % moins de ' || percentile_disc(0.9) within group (order by n)
       || ' · maximum ' || max(n)
  from actifs
union all
select 31, 'RÉPARTITION', 'part des communes tenues par les 10 % de joueurs qui en ont le plus',
       coalesce(round(100.0 * sum(n) filter (where rang <= greatest(1, ceil(nb * 0.1))) / nullif(sum(n), 0)) || ' %', '—')
  from (select n, row_number() over (order by n desc) as rang, count(*) over () as nb from tenants) x
-- 4. CONQUÊTES (7 jours) ------------------------------------------------------
union all
select 40, 'CONQUÊTES 7 j', 'toutes',
       count(*) || ' (' || round(count(*)::numeric / (select n from jours7)) || ' par jour) · '
       || count(distinct attaquant) || ' conquérants différents · '
       || count(distinct victime) || ' victimes différentes'
  from pris7
union all
select 40 + o.o, 'CONQUÊTES 7 j', o.nom,
       count(p.*) || ' (' || round(count(p.*)::numeric / (select n from jours7), 1) || ' par jour)'
  from ot o left join pris7 p on p.tier = o.tier
 group by o.o, o.nom
union all
select 46, 'CONQUÊTES 7 j', 'prises à un joueur absent depuis 3 jours ou plus',
       coalesce(round(100.0 * count(*) filter (where victime_dernier < (select d from auj) - 3 or victime_dernier is null)
                      / nullif(count(*), 0)) || ' %', '—')
  from pris7
union all
select 47, 'CONQUÊTES 7 j', 'faites par un joueur en clan',
       coalesce(round(100.0 * count(*) filter (where attaquant in (select joueur_id from clanj)) / nullif(count(*), 0)) || ' %', '—')
  from pris7
-- 5. ROUNDS (depuis le 3/11 midi) --------------------------------------------
union all
select 50, 'ROUNDS', 'période couverte',
       coalesce(round((select n from rd_jours)::numeric, 1) || ' jours · ' || count(*) || ' rounds · '
       || count(distinct attaquant_id) || ' attaquants', 'aucun round noté')
  from rd
union all
select 50 + o.o, 'ROUNDS', o.nom,
       count(r.*) || ' rounds · ' || coalesce(round(100.0 * count(*) filter (where r.gagne) / nullif(count(r.*), 0)) || ' % gagnés', '—')
       || ' · ' || count(*) filter (where r.gagne and r.victoires >= 3) || ' conquêtes · '
       || coalesce(round(count(r.*)::numeric / nullif(count(*) filter (where r.gagne and r.victoires >= 3), 0), 1) || ' rounds par conquête', '—')
  from ot o left join rd r on r.tier = o.tier
 group by o.o, o.nom
-- 6. SIÈGES (maintenant) -----------------------------------------------------
union all
select 60 + o.o, 'SIÈGES en cours', o.nom,
       count(s.*) || ' sièges · ' || count(*) filter (where s.victoires_consecutives >= 2) || ' à 2 victoires · '
       || count(*) filter (where coalesce(s.defenses_faites, 0) > 0) || ' où le défenseur a déjà défendu'
  from ot o
  left join (select x.victoires_consecutives, x.defenses_faites, c.tier from sieges x join cat c on c.code = x.commune_code
              where coalesce(x.victoires_consecutives, 0) > 0) s on s.tier = o.tier
 group by o.o, o.nom
-- 7. VICTOIRES AU SCORE (saison) ---------------------------------------------
union all
select 70, 'VICTOIRES au score', 'par type (une seule fois par commune et par type)',
       coalesce(string_agg(t || ' ' || n, ' · ' order by n desc), 'aucune')
  from (select type::text as t, count(*) as n from front_victoires group by 1) v
-- 8. BÂTIMENTS (maintenant) --------------------------------------------------
union all
select 80, 'BÂTIMENTS', 'joueurs actifs avec au moins 1 Fonderie',
       count(*) filter (where exists (select 1 from batiments b where b.joueur_id = a.joueur_id and b.type = 'fonderie'))
       || ' sur ' || count(*) || ' · avec 2 Fonderies : '
       || count(*) filter (where (select count(*) from batiments b where b.joueur_id = a.joueur_id and b.type = 'fonderie') >= 2)
  from actifs a
union all
select 81, 'BÂTIMENTS', 'Forteresses',
       count(*) || ' posées · ' || count(distinct joueur_id) || ' joueurs'
  from batiments where type = 'forteresse'
union all
select 82, 'BÂTIMENTS', 'lingots en réserve (joueurs avec une Fonderie prête)',
       coalesce('médiane ' || floor((percentile_cont(0.5) within group (order by l))::numeric)
       || ' · réserve pleine : ' || count(*) filter (where l >= m) || ' sur ' || count(*), 'aucun')
  from (select coalesce(lingots_lire(x.joueur_id), 0) as l, lingots_max(x.joueur_id) as m
          from (select distinct joueur_id from batiments where type = 'fonderie' and pret_le <= now()) x) y
union all
select 83, 'BÂTIMENTS', 'bombes lâchées depuis le début', (select count(*) from bombes)::text
-- 9. CLANS ------------------------------------------------------------------
union all
select 90, 'CLANS', 'clans avec au moins 1 membre · taille',
       count(*) || ' clans · médiane ' || percentile_disc(0.5) within group (order by n) || ' membres · maximum ' || max(n)
  from (select clan_id, count(*) as n from clan_membres group by 1) x
-- 10. RÉGLAGES ----------------------------------------------------------------
union all
select 100, 'RÉGLAGES', 'bonus de proximité, en points de chance, selon le nombre de tes communes à moins de 20 km de la cible (0 à 10)',
       string_agg(n || ' → ' || round(bonus_proximite(n) * 100), ' · ' order by n)
  from generate_series(0, 10) n
union all
select 101, 'RÉGLAGES', 'bâtiments (config_jeu)', (select valeur::text from config_jeu where cle = 'batiments')
union all
select 102, 'RÉGLAGES', 'réserve d''accueil (config_jeu)', (select valeur::text from config_jeu where cle = 'reserve_accueil')
order by 1, 3;
