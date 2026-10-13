-- ===========================================================================
--  TerraFront — saison 2 : les quêtes du jour tirées dans une réserve
--  (13 octobre 2026, validé par Nataël ; idée d'Oshannir : « en 2 min tu as
--  tout fait », « forcer le joueur à aller au QG »)
--
--  Terra : une réserve de 10 quêtes, 5 tirées chaque jour (les mêmes pour
--  tout le monde, jour de Paris), 20 pts chacune, + 50 pts quand les 5 sont
--  faites. 150 pts par jour au plus (100 avant).
--    Tirage        Ouvre 2 paquets Terra
--    Collection    Ajoute 3 nouvelles communes
--    Bourse        Vends ou échange un doublon
--    Bourse        Mets une carte en vente
--    Échange       Propose un échange à un joueur
--    Profil        Change ta vitrine
--    QG            Trouve la Commune du jour
--    QG            Joue un duel Radar classé
--    QG            Joue un duel Rafale classé
--    QG            Gagne un duel (Radar ou Rafale)
--  Front : inchangé, + « Gagne un duel Rafale » (+5 énergie). Le plafond de
--  20 d'énergie de quêtes par jour ne bouge pas.
--  Les quêtes uniques ne changent pas.
--
--  Remplace quetes_liste() (même signature) ; quetes() et reclamer_quete()
--  la lisent et ne changent pas : une quête qui n'est pas tirée aujourd'hui
--  n'existe pas pour elles, donc ne peut pas être réclamée.
--  Nouveaux compteurs par des déclencheurs sur terra_annonces, terra_echanges
--  et terra_vitrine (insertion) : aucune fonction existante n'est modifiée.
--
--  À lancer APRÈS s2-12-quetes.sql et rafale-1.sql. Sans effet en saison 1
--  (quete_noter ne compte rien, quetes() refuse). Rejouable.
-- ===========================================================================

-- les compteurs neufs ------------------------------------------------------
create or replace function public.quete_compter_annonce()
 returns trigger language plpgsql security definer set search_path to 'public'
as $f$ begin perform quete_noter(new.vendeur, 'bourse_vente', 1); return new; end; $f$;
create or replace function public.quete_compter_echange()
 returns trigger language plpgsql security definer set search_path to 'public'
as $f$ begin perform quete_noter(new.proposant, 'echange_propose', 1); return new; end; $f$;
create or replace function public.quete_compter_vitrine()
 returns trigger language plpgsql security definer set search_path to 'public'
as $f$ begin perform quete_noter(new.joueur_id, 'vitrine', 1); return new; end; $f$;
revoke all on function public.quete_compter_annonce() from public, anon, authenticated;
revoke all on function public.quete_compter_echange() from public, anon, authenticated;
revoke all on function public.quete_compter_vitrine() from public, anon, authenticated;

drop trigger if exists quete_annonce on public.terra_annonces;
create trigger quete_annonce after insert on public.terra_annonces
  for each row execute function public.quete_compter_annonce();
drop trigger if exists quete_echange on public.terra_echanges;
create trigger quete_echange after insert on public.terra_echanges
  for each row execute function public.quete_compter_echange();
drop trigger if exists quete_vitrine on public.terra_vitrine;
create trigger quete_vitrine after insert on public.terra_vitrine
  for each row execute function public.quete_compter_vitrine();

-- la liste du jour -----------------------------------------------------------
create or replace function public.quetes_liste(p_uid uuid)
 returns table(id text, mode text, categorie text, titre text, detail text,
               avancement integer, cible integer, points integer, energie integer)
 language plpgsql stable security definer set search_path to 'public'
as $f$
declare
  v_jour date := quete_jour();
  v_minuit timestamptz := v_jour::timestamp at time zone 'Europe/Paris';
  c_paquet int; c_doublon int; c_defense int; c_garnison int; c_radar_v int; c_rafale_v int; c_conquete int;
  c_bourse int; c_echange int; c_vitrine int;
  v_nouvelles int; v_cdj int; v_communes int; v_epiques int; v_dept int; v_radar int; v_rafale int;
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
         coalesce(sum(n) filter (where q.cle = 'vitrine'), 0)
    into c_paquet, c_doublon, c_defense, c_garnison, c_radar_v, c_rafale_v, c_conquete, c_bourse, c_echange, c_vitrine
    from quetes_compteurs q where q.joueur_id = p_uid and q.jour = v_jour;
  select count(*) into v_nouvelles from terra_collection t
   where t.joueur_id = p_uid and t.premiere_le >= v_minuit and t.exemplaires > 0;
  select count(*) into v_cdj from cdj_gains g where g.joueur_id = p_uid and g.jour = v_jour;
  select count(*) into v_radar from radar_parties r
   where r.joueur_id = p_uid and r.fini and not r.amical and r.fin_le >= v_minuit;
  select count(*) into v_rafale from rafale_parties r
   where r.joueur_id = p_uid and r.fini and not r.amical and r.fin_le >= v_minuit;
  select count(*), count(*) filter (where c.tier = 'epique')
    into v_communes, v_epiques
    from terra_collection t join communes c on c.code = t.commune_code
   where t.joueur_id = p_uid and t.exemplaires > 0;
  select count(*) into v_dept from (
    select c.departement
      from communes c
      left join terra_collection t on t.commune_code = c.code and t.joueur_id = p_uid and t.exemplaires > 0
     group by c.departement
    having count(*) = count(t.commune_code)) x;

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
    ('t_victoire',  'Gagne un duel',                    'Radar ou Rafale, classé',              c_radar_v + c_rafale_v, 1)),
  -- 5 quêtes du jour, les mêmes pour tous
  du_jour as (
    select r.* from reserve r order by md5(r.id || v_jour::text) limit 5)
  select d.id, 'terra'::text, 'jour'::text, d.titre::text, d.detail::text, d.avancement::int, d.cible::int, 20, 0 from du_jour d
  union all
  select 't_bonus', 'terra', 'jour', 'Termine les 5 quêtes du jour', 'Le bonus du jour',
         (select count(*) from du_jour d where d.avancement >= d.cible)::int, 5, 50, 0
  union all
  select * from (values
    ('f_defense',   'front', 'jour',   'Réussis une défense',            'Défends toi-même une commune attaquée',  c_defense,  1,    0, 5),
    ('f_garnison',  'front', 'jour',   'Mets une commune en garnison',   'Ou recharge une garnison',               c_garnison, 1,    0, 5),
    ('f_paquet',    'front', 'jour',   'Ouvre un paquet Terra',          'Le lien entre les deux modes',           c_paquet,   1,    0, 5),
    ('f_cdj',       'front', 'jour',   'Trouve la Commune du jour',      'Dans le QG',                             v_cdj,      1,    0, 5),
    ('f_radar',     'front', 'jour',   'Gagne un duel Radar',            'Duel classé, dans le QG',                c_radar_v,  1,    0, 5),
    ('f_rafale',    'front', 'jour',   'Gagne un duel Rafale',           'Duel classé, dans le QG',                c_rafale_v, 1,    0, 5),
    ('f_conquete',  'front', 'jour',   'Conquiers une commune',          'Trois victoires d''affilée',             c_conquete, 1,    50, 3),
    ('u_t100',      'terra', 'unique', 'Collectionne 100 communes',      'Communes différentes',                   v_communes, 100,  200, 0),
    ('u_t500',      'terra', 'unique', 'Collectionne 500 communes',      'Communes différentes',                   v_communes, 500,  400, 0),
    ('u_t2000',     'terra', 'unique', 'Collectionne 2 000 communes',    'Communes différentes',                   v_communes, 2000, 600, 0),
    ('u_tdept',     'terra', 'unique', 'Complète un département',        'Toutes ses communes dans ta collection', v_dept,     1,    300, 0),
    ('u_tepique',   'terra', 'unique', 'Obtiens une épique',             'Dans un paquet ou par un contrat',       v_epiques,  1,    200, 0)
  ) as l(id, mode, categorie, titre, detail, avancement, cible, points, energie);
end;
$f$;
revoke all on function public.quetes_liste(uuid) from public, anon, authenticated;

-- Contrôle : les quêtes Terra d'aujourd'hui (pour un joueur fictif : tout à 0)
select id, titre, cible, points
  from public.quetes_liste('00000000-0000-0000-0000-000000000000'::uuid)
 where mode = 'terra' and categorie = 'jour';
